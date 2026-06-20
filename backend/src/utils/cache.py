import os
import sqlite3
import json
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SQLiteRAGCache:
    """
    SQLite-backed precise cache for RAG responses.
    Caches the generated answer, raw retrieved contexts, citations,
    and the prompt version. Cache lookup is invalidated/missed if prompt version differs.
    """
    
    def __init__(self, db_path: str = "d:/RAG/backend/data/rag_cache.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initializes the SQLite cache table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_cache (
                        query TEXT NOT NULL,
                        prompt_version TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        citations TEXT NOT NULL,
                        contexts TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (query, prompt_version)
                    )
                """)
                conn.commit()
                logger.info(f"SQLite RAG Cache initialized at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite cache database: {e}")
            
    def get(self, query: str, prompt_version: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cached response for the exact query and prompt version.
        Returns a dictionary or None on miss.
        """
        # Normalize query (lowercase, stripped) to avoid misses on simple spaces/casing
        normalized_query = query.strip().lower()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT answer, citations, contexts FROM query_cache WHERE LOWER(TRIM(query)) = ? AND prompt_version = ?",
                    (normalized_query, prompt_version)
                )
                row = cursor.fetchone()
                if row:
                    logger.info(f"Cache HIT for query: '{query}' [Version: {prompt_version}]")
                    return {
                        "answer": row["answer"],
                        "citations": json.loads(row["citations"]),
                        "contexts": json.loads(row["contexts"]),
                        "cached": True
                    }
        except Exception as e:
            logger.error(f"Error querying SQLite RAG cache: {e}")
            
        logger.info(f"Cache MISS for query: '{query}' [Version: {prompt_version}]")
        return None
        
    def set(self, query: str, prompt_version: str, answer: str, citations: list, contexts: list):
        """Saves a response inside the cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO query_cache (query, prompt_version, answer, citations, contexts, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        query.strip(),
                        prompt_version,
                        answer,
                        json.dumps(citations),
                        json.dumps(contexts)
                    )
                )
                conn.commit()
                logger.info(f"Successfully cached response for query: '{query}'")
        except Exception as e:
            logger.error(f"Error setting cache entry in SQLite: {e}")
            
    def clear(self):
        """Clears all cache entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM query_cache")
                conn.commit()
                logger.info("Cleared all RAG cache entries.")
        except Exception as e:
            logger.error(f"Failed to clear RAG cache: {e}")
