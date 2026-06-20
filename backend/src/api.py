import os
import sys
sys.modules["tensorflow"] = None
sys.modules["keras"] = None
sys.modules["tf_keras"] = None
os.environ["TRANSFORMERS_NO_TF"] = "1"
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Ensure src is in the python path
sys.path.append(os.path.dirname(__file__))

from config import settings
from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline
from utils.cache import SQLiteRAGCache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize rate limiter based on client IP
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI App
app = FastAPI(
    title="Project Antigravity Production RAG Q&A API",
    description="Enterprise-grade production API serving domain-specific document RAG with two-layer grounding guardrails and precise cost tracking.",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure cross-origin integrations for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State container for RAG components (Singleton lifetime management)
class RAGState:
    vector_store_manager = None
    pipeline = None
    cache = None

    @classmethod
    def get_pipeline(cls) -> GenerationPipeline:
        if cls.pipeline is None:
            logger.info("Initializing lazy loading of Generation Pipeline & models...")
            cls.vector_store_manager = VectorStoreManager()
            cls.pipeline = GenerationPipeline(cls.vector_store_manager)
        return cls.pipeline

    @classmethod
    def get_cache(cls) -> SQLiteRAGCache:
        if cls.cache is None:
            cls.cache = SQLiteRAGCache()
        return cls.cache

# Pydantic Request/Response validation schemas
class QueryPayload(BaseModel):
    question: str = Field(..., description="Query string to process through the grounded RAG pipeline")

class CitationSchema(BaseModel):
    source: str
    page: Any
    re_rank_score: float

class TelemetrySchema(BaseModel):
    provider: str
    prompt_version: str
    reranking_enabled: bool
    chunks_count: int
    max_re_rank_score: float
    l1_relevance_check: str
    l2_grounding_check: str
    input_tokens: int
    output_tokens: int
    transaction_cost_usd: float
    elapsed_seconds: float
    cached: bool

class QueryResponse(BaseModel):
    answer: str
    contexts: List[str]
    citations: List[CitationSchema]
    telemetry: TelemetrySchema

@app.on_event("shutdown")
def shutdown_event():
    if RAGState.vector_store_manager:
        logger.info("Closing active Vector Store connections...")
        RAGState.vector_store_manager.close()

@app.get("/health")
def health_check():
    """Provides downstream operational telemetry and system settings."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "vector_db_provider": settings.vector_db_provider,
        "active_prompt_version": settings.active_prompt_version,
        "enable_reranking": settings.enable_reranking
    }

@app.post("/query", response_model=QueryResponse)
@limiter.limit("5/minute")
def query_rag(
    request: Request, 
    payload: QueryPayload, 
    pipeline: GenerationPipeline = Depends(RAGState.get_pipeline), 
    cache: SQLiteRAGCache = Depends(RAGState.get_cache)
):
    """
    Core RAG retrieval and generation endpoint.
    Protected by rate-limiting (5 requests/minute).
    Consults persistent SQLite cache first for instant hits (0 tokens, 0 cost).
    Falls back to BGE-hybrid search, re-ranking, and Gemini generation on miss.
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question payload cannot be empty.")
        
    import time
    start_time = time.time()
    
    # 1. Probe Persistent Cache
    prompt_version = settings.active_prompt_version
    cached_result = cache.get(question, prompt_version)
    
    if cached_result:
        elapsed = time.time() - start_time
        telemetry = {
            "provider": settings.vector_db_provider,
            "prompt_version": prompt_version,
            "reranking_enabled": settings.enable_reranking,
            "chunks_count": len(cached_result["contexts"]),
            "max_re_rank_score": max([c.get("re_rank_score", 0.0) for c in cached_result["citations"]]) if cached_result["citations"] else 0.0,
            "l1_relevance_check": "PASSED (CACHED)",
            "l2_grounding_check": "PASSED (CACHED)",
            "input_tokens": 0,
            "output_tokens": 0,
            "transaction_cost_usd": 0.0,
            "elapsed_seconds": elapsed,
            "cached": True
        }
        return {
            "answer": cached_result["answer"],
            "contexts": cached_result["contexts"],
            "citations": cached_result["citations"],
            "telemetry": telemetry
        }
        
    # 2. Cache MISS: Run complete retrieval & LLM pipeline
    logger.info(f"Cache miss for query '{question}'. Dispatching active pipeline.")
    try:
        pipeline_res = pipeline.answer_question(question)
        elapsed = time.time() - start_time
        
        # 3. Store in persistent SQLite cache if response is grounded
        # Avoid caching guardrail fallbacks ("I don't know based on...") to allow future retrieval when documents update.
        is_guardrail_rejection = "I don't know based on the provided documents" in pipeline_res["answer"]
        if not is_guardrail_rejection:
            cache.set(
                query=question,
                prompt_version=prompt_version,
                answer=pipeline_res["answer"],
                citations=pipeline_res["citations"],
                contexts=pipeline_res["contexts"]
            )
            
        telemetry_payload = pipeline_res["telemetry"]
        telemetry_payload["cached"] = False
        
        return {
            "answer": pipeline_res["answer"],
            "contexts": pipeline_res["contexts"],
            "citations": pipeline_res["citations"],
            "telemetry": telemetry_payload
        }
        
    except Exception as e:
        logger.error(f"Internal endpoint execution failure: {e}")
        err_msg = str(e)
        if "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower() or "429" in err_msg:
            raise HTTPException(
                status_code=503,
                detail="Gemini API rate limit or daily free-tier quota exceeded (RESOURCE_EXHAUSTED / 429). Please verify your Google API key and billing details."
            )
        raise HTTPException(status_code=500, detail=f"Internal RAG pipeline failure: {err_msg}")

@app.post("/cache/clear")
def clear_cache(cache: SQLiteRAGCache = Depends(RAGState.get_cache)):
    """Clears all cached query sessions."""
    cache.clear()
    return {"status": "success", "message": "Persistent cache cleared successfully."}
