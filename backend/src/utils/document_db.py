import os
import sqlite3
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

def get_file_sha256(filepath: str) -> str:
    """Computes the SHA256 checksum of a file on disk."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_upload_file_sha256(file) -> str:
    """Computes the SHA256 checksum of an uploaded FastAPI file object."""
    sha256_hash = hashlib.sha256()
    file.seek(0)
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.seek(0)
    return sha256_hash.hexdigest()

class DocumentMetadataStore:
    """
    SQLite-backed store to manage uploaded and bootstrapped document metadata.
    Provides functions for listing, checking duplicates, adding, and deleting documents.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.rag_cache_db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initializes the document metadata table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS uploaded_documents (
                        filename TEXT PRIMARY KEY,
                        sha256 TEXT NOT NULL,
                        upload_date TEXT NOT NULL,
                        chunks INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        filepath TEXT NOT NULL
                    )
                """)
                conn.commit()
                logger.info(f"SQLite Document Metadata Store initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite document metadata database: {e}")
            
    def add_document(self, filename: str, sha256: str, chunks: int, filepath: str, status: str = "Indexed") -> bool:
        """Adds or updates a document metadata entry."""
        try:
            upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO uploaded_documents (filename, sha256, upload_date, chunks, status, filepath)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (filename, sha256, upload_date, chunks, status, filepath)
                )
                conn.commit()
                logger.info(f"Successfully saved metadata for document: '{filename}'")
                return True
        except Exception as e:
            logger.error(f"Error saving document metadata in SQLite: {e}")
            return False
            
    def get_document(self, filename: str) -> Optional[Dict[str, Any]]:
        """Retrieves a document metadata by filename."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT filename, sha256, upload_date, chunks, status, filepath FROM uploaded_documents WHERE filename = ?",
                    (filename,)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"Error querying document metadata: {e}")
        return None

    def check_duplicate(self, filename: str, sha256: str) -> bool:
        """Checks if a document with BOTH filename AND sha256 exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM uploaded_documents WHERE filename = ? AND sha256 = ?",
                    (filename, sha256)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking duplicate document: {e}")
            return False
            
    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all document metadata rows."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT filename, upload_date, chunks, status, filepath FROM uploaded_documents ORDER BY upload_date DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
            
    def delete_document(self, filename: str) -> Optional[str]:
        """
        Deletes a document entry by filename.
        Returns the filepath of the deleted document so the physical file can be removed.
        """
        doc = self.get_document(filename)
        if not doc:
            return None
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM uploaded_documents WHERE filename = ?", (filename,))
                conn.commit()
                logger.info(f"Deleted metadata for document: '{filename}'")
                return doc["filepath"]
        except Exception as e:
            logger.error(f"Failed to delete document metadata: {e}")
            return None
