import os
import sys
sys.modules["tensorflow"] = None
sys.modules["keras"] = None
sys.modules["tf_keras"] = None
os.environ["TRANSFORMERS_NO_TF"] = "1"
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import shutil

# Ensure src is in the python path
sys.path.append(os.path.dirname(__file__))

from config import settings
from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline
from utils.cache import SQLiteRAGCache
from utils.document_db import DocumentMetadataStore, get_file_sha256, get_upload_file_sha256

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize rate limiter based on client IP
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI App
app = FastAPI(
    title="GroundLens AI Production RAG Q&A API",
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
    def get_vector_store_manager(cls) -> VectorStoreManager:
        if cls.vector_store_manager is None:
            logger.info("Initializing lazy loading of Vector Store Manager...")
            cls.vector_store_manager = VectorStoreManager()
        return cls.vector_store_manager

    @classmethod
    def get_pipeline(cls) -> GenerationPipeline:
        if cls.pipeline is None:
            logger.info("Initializing lazy loading of Generation Pipeline & models...")
            vsm = cls.get_vector_store_manager()
            cls.pipeline = GenerationPipeline(vsm)
        return cls.pipeline

    @classmethod
    def get_cache(cls) -> SQLiteRAGCache:
        if cls.cache is None:
            cls.cache = SQLiteRAGCache()
        return cls.cache

# Pydantic Request/Response validation schemas
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the speaker: 'user' or 'assistant'")
    content: str = Field(..., description="Content of the message")

class QueryPayload(BaseModel):
    question: str = Field(..., description="Query string to process through the grounded RAG pipeline")
    history: List[ChatMessage] = Field(default=[], description="List of previous conversation messages")

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
        history_dicts = [h.dict() for h in payload.history] if payload.history else []
        pipeline_res = pipeline.answer_question(question, history=history_dicts)
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

# Dedicated uploads directory
UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Register pre-existing/bootstrapped data files if they exist in backend/data
def register_existing_data_files():
    try:
        import glob
        from ingestion.document_loader import UniversalDocumentLoader
        from ingestion.chunker import DocumentChunker
        
        data_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
        if not os.path.exists(data_dir):
            return
            
        loader = UniversalDocumentLoader()
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        doc_store = DocumentMetadataStore()
        
        supported_files = []
        for ext in loader.loaders.keys():
            supported_files.extend(glob.glob(os.path.join(data_dir, f"*{ext}")))
            supported_files.extend(glob.glob(os.path.join(data_dir, f"**/*{ext}"), recursive=True))
            
        for filepath in set(supported_files):
            filepath = os.path.abspath(filepath)
            # Skip chroma dir and cache file
            if "data" + os.sep + "chroma" in filepath or "rag_cache.db" in filepath:
                continue
                
            filename = os.path.basename(filepath)
            if not doc_store.get_document(filename):
                logger.info(f"Registering pre-indexed file: {filename} in metadata database.")
                try:
                    raw_docs = loader.load_document(filepath)
                    chunks = chunker.chunk_documents(raw_docs)
                    sha256 = get_file_sha256(filepath)
                    doc_store.add_document(
                        filename=filename,
                        sha256=sha256,
                        chunks=len(chunks),
                        filepath=filepath,
                        status="Indexed"
                    )
                except Exception as e:
                    logger.warning(f"Could not register pre-indexed file {filename}: {e}")
    except Exception as e:
        logger.error(f"Error registering existing data files: {e}")

# Bootstrap data files inside data/ if empty
def bootstrap_data(vector_store_manager: VectorStoreManager):
    try:
        from ingestion.document_loader import UniversalDocumentLoader
        from ingestion.chunker import DocumentChunker
        
        data_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
        if not os.path.exists(data_dir):
            logger.warning(f"Data directory does not exist at {data_dir}. Cannot bootstrap.")
            return
            
        loader = UniversalDocumentLoader()
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        
        raw_docs = loader.load_directory(data_dir)
        if not raw_docs:
            logger.info("No documents found in data directory for bootstrapping.")
            return
            
        chunked_docs = chunker.chunk_documents(raw_docs)
        if chunked_docs:
            vector_store_manager.add_documents(chunked_docs)
            logger.info(f"Indexed {len(chunked_docs)} chunks from bootstrap.")
            
            # Register in metadata store
            from collections import defaultdict
            chunks_by_file = defaultdict(list)
            for doc in chunked_docs:
                src = doc.metadata.get("source")
                if src:
                    chunks_by_file[src].append(doc)
                    
            doc_store = DocumentMetadataStore()
            for src_path, file_chunks in chunks_by_file.items():
                src_path = os.path.abspath(src_path)
                filename = os.path.basename(src_path)
                sha256 = get_file_sha256(src_path)
                doc_store.add_document(
                    filename=filename,
                    sha256=sha256,
                    chunks=len(file_chunks),
                    filepath=src_path,
                    status="Indexed"
                )
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")

@app.on_event("startup")
def startup_event():
    try:
        vector_store_manager = RAGState.get_vector_store_manager()
        
        if vector_store_manager.is_empty():
            logger.info("Chroma DB is empty. Running bootstrap ingestion for backend/data...")
            bootstrap_data(vector_store_manager)
        else:
            logger.info("Chroma DB already contains data. Skipping startup bootstrap.")
            register_existing_data_files()
    except Exception as e:
        logger.error(f"Error during startup bootstrap: {e}")

@app.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    vector_store_manager: VectorStoreManager = Depends(RAGState.get_vector_store_manager)
):
    filename = file.filename
    _, ext = os.path.splitext(filename)
    if ext.lower() not in [".pdf", ".docx", ".txt", ".md"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file extension: {ext}. Supported formats: PDF, DOCX, TXT, MD"
        )
        
    sha256 = get_upload_file_sha256(file.file)
    doc_store = DocumentMetadataStore()
    
    if doc_store.check_duplicate(filename, sha256):
        logger.info(f"Duplicate upload detected: {filename}")
        return {
            "success": True,
            "filename": filename,
            "chunks_created": 0,
            "message": "Document already exists and is indexed."
        }
        
    import time
    unique_name = f"{int(time.time())}_{filename}"
    saved_filepath = os.path.abspath(os.path.join(UPLOADS_DIR, unique_name))
    
    try:
        with open(saved_filepath, "wb") as buffer:
            file.file.seek(0)
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file on server: {str(e)}")
        
    try:
        from ingestion.document_loader import UniversalDocumentLoader
        from ingestion.chunker import DocumentChunker
        
        existing_doc = doc_store.get_document(filename)
        if existing_doc:
            logger.info(f"Document {filename} already exists. Overwriting/updating vectors...")
            vector_store_manager.delete_document(existing_doc["filepath"])
            if os.path.exists(existing_doc["filepath"]) and UPLOADS_DIR in existing_doc["filepath"]:
                try:
                    os.remove(existing_doc["filepath"])
                except Exception as e:
                    logger.warning(f"Failed to remove old file {existing_doc['filepath']}: {e}")
                    
        loader = UniversalDocumentLoader()
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        
        raw_docs = loader.load_document(saved_filepath)
        chunked_docs = chunker.chunk_documents(raw_docs)
        
        if chunked_docs:
            vector_store_manager.add_documents(chunked_docs)
            chunks_created = len(chunked_docs)
        else:
            chunks_created = 0
            
        doc_store.add_document(
            filename=filename,
            sha256=sha256,
            chunks=chunks_created,
            filepath=saved_filepath,
            status="Indexed"
        )
        
        cache = RAGState.get_cache()
        cache.clear()
        
        return {
            "success": True,
            "filename": filename,
            "chunks_created": chunks_created,
            "message": "Document indexed successfully."
        }
        
    except Exception as e:
        logger.error(f"Failed to index document: {e}")
        if os.path.exists(saved_filepath):
            try:
                os.remove(saved_filepath)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")

@app.get("/documents")
def list_documents():
    doc_store = DocumentMetadataStore()
    docs = doc_store.list_documents()
    return [
        {
            "filename": d["filename"],
            "upload_date": d["upload_date"],
            "chunks": d["chunks"],
            "status": d["status"]
        }
        for d in docs
    ]

@app.delete("/documents/{filename}")
def delete_document(
    filename: str,
    vector_store_manager: VectorStoreManager = Depends(RAGState.get_vector_store_manager)
):
    doc_store = DocumentMetadataStore()
    doc = doc_store.get_document(filename)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {filename} not found.")
        
    filepath = doc["filepath"]
    try:
        vector_store_manager.delete_document(filepath)
    except Exception as e:
        logger.error(f"Failed to delete vectors for {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document vectors: {str(e)}")
        
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info(f"Deleted file from disk: {filepath}")
        except Exception as e:
            logger.warning(f"Could not delete file {filepath} from disk: {e}")
            
    doc_store.delete_document(filename)
    
    cache = RAGState.get_cache()
    cache.clear()
    
    return {
        "success": True,
        "message": f"Document '{filename}' deleted successfully."
    }

@app.post("/documents/{filename}/reindex")
def reindex_document(
    filename: str,
    vector_store_manager: VectorStoreManager = Depends(RAGState.get_vector_store_manager)
):
    doc_store = DocumentMetadataStore()
    doc = doc_store.get_document(filename)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {filename} not found.")
        
    filepath = doc["filepath"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Document file not found on server disk at {filepath}.")
        
    try:
        vector_store_manager.delete_document(filepath)
        
        from ingestion.document_loader import UniversalDocumentLoader
        from ingestion.chunker import DocumentChunker
        
        loader = UniversalDocumentLoader()
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        
        raw_docs = loader.load_document(filepath)
        chunked_docs = chunker.chunk_documents(raw_docs)
        
        if chunked_docs:
            vector_store_manager.add_documents(chunked_docs)
            chunks_created = len(chunked_docs)
        else:
            chunks_created = 0
            
        sha256 = get_file_sha256(filepath)
        doc_store.add_document(
            filename=filename,
            sha256=sha256,
            chunks=chunks_created,
            filepath=filepath,
            status="Indexed"
        )
        
        cache = RAGState.get_cache()
        cache.clear()
        
        return {
            "success": True,
            "filename": filename,
            "chunks_created": chunks_created,
            "message": f"Document '{filename}' re-indexed successfully."
        }
        
    except Exception as e:
        logger.error(f"Failed to re-index document {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to re-index document: {str(e)}")
