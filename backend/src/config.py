"""
Configuration management for the RAG system.
"""
import os
import sys
sys.modules["tensorflow"] = None
sys.modules["keras"] = None
sys.modules["tf_keras"] = None
os.environ["TRANSFORMERS_NO_TF"] = "1"

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from pathlib import Path

# Centralized base directory (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # LLM Settings
    google_api_key: str = Field(
        default="your_gemini_api_key_here", 
        description="Google Gemini API Key"
    )
    active_llm_model: str = Field(
        default="gemini-2.5-flash-lite",
        description="Active Gemini LLM model ID"
    )
    llm_provider: str = Field(
        default="google",
        description="LLM provider (google or groq)"
    )
    groq_api_key: str = Field(
        default="your_groq_api_key_here", 
        description="Groq API Key"
    )
    groq_model_name: str = Field(
        default="llama-3.3-70b-versatile",
        description="Active Groq LLM model ID"
    )
    
    # Vector DB Settings
    vector_db_provider: str = Field(
        default="chroma",
        description="Vector database provider (chroma or weaviate)"
    )
    chroma_db_dir: str = Field(
        default=str(BASE_DIR / "data" / "chroma"),
        description="Directory to store Chroma DB files"
    )
    rag_cache_db_path: str = Field(
        default=str(BASE_DIR / "data" / "rag_cache.db"),
        description="Path to SQLite RAG Cache database file"
    )
    weaviate_url: str = Field(
        default="http://localhost:8080", 
        description="URL for Weaviate instance"
    )
    weaviate_api_key: str = Field(
        default="", 
        description="API key for Weaviate (empty if local w/o auth)"
    )
    
    # Hybrid Search Settings
    hybrid_search_alpha: float = Field(
        default=0.5,
        description="Weight balance between sparse BM25 (0.0) and dense vector (1.0) search"
    )
    
    # Re-ranking Settings
    enable_reranking: bool = Field(
        default=True,
        description="Enable second-stage Cross-Encoder re-ranking"
    )
    reranker_model_name: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Local Cross-Encoder model ID for candidate re-scoring"
    )
    top_n_context: int = Field(
        default=8,
        description="Number of final context chunks to send to the LLM (after re-ranking)"
    )
    
    # Grounding Settings
    min_relevance_score: float = Field(
        default=-4.0,
        description="Minimum Cross-Encoder score to proceed to LLM generation"
    )
    
    # Prompt Settings
    active_prompt_version: str = Field(
        default="v3",
        description="Active prompt version ID from prompts.yaml"
    )
    
    # Embeddings Settings
    embedding_model_name: str = Field(
        default="BAAI/bge-small-en",
        description="HuggingFace embedding model ID"
    )
    
    # App Settings
    environment: str = Field(default="development")

    # Load from .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate a global settings object to be imported across the app
settings = Settings()

if __name__ == "__main__":
    print(f"Loaded config for environment: {settings.environment}")
    print(f"Embedding model: {settings.embedding_model_name}")
    print(f"Vector DB Provider: {settings.vector_db_provider}")
    print(f"Chroma DB Directory: {settings.chroma_db_dir}")
    print(f"Hybrid Search Alpha: {settings.hybrid_search_alpha}")
    print(f"Enable Re-ranking: {settings.enable_reranking}")
    print(f"Reranker Model Name: {settings.reranker_model_name}")
    print(f"Min Relevance Score: {settings.min_relevance_score}")
    print(f"Active Prompt Version: {settings.active_prompt_version}")
