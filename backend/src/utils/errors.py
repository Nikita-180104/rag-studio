class RAGException(Exception):
    """Base exception class for all RAG pipeline errors."""
    pass

class IngestionError(RAGException):
    """Exception raised for errors during document loading, parsing, or chunking."""
    pass

class RetrievalError(RAGException):
    """Exception raised for vector database connectivity, indexing, or retrieval failures."""
    pass

class GenerationError(RAGException):
    """Exception raised for LLM generation, prompt compiling, or guardrail audit failures."""
    pass
