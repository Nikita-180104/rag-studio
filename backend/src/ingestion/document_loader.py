import os
from typing import List
import logging

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader
)

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversalDocumentLoader:
    """
    A unified interface to load various document types into LangChain Document objects.
    Ensures standard metadata (like source file path) is attached to every document.
    """
    
    def __init__(self):
        # Map file extensions to their corresponding LangChain loaders
        self.loaders = {
            ".pdf": PyPDFLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
            ".docx": UnstructuredWordDocumentLoader,
        }

    def load_document(self, file_path: str) -> List[Document]:
        """
        Loads a single document and returns a list of LangChain Document objects.
        For PDFs, it usually returns one Document per page.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found at: {file_path}")

        # Extract the extension to determine the right loader
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        loader_class = self.loaders.get(extension)
        
        if not loader_class:
            raise ValueError(f"Unsupported file extension: {extension}. Supported formats: {list(self.loaders.keys())}")

        try:
            logger.info(f"Loading {file_path} using {loader_class.__name__}")
            loader = loader_class(file_path)
            documents = loader.load()
            
            # Post-processing: Ensure 'source' metadata is strictly set (useful for citation layer later)
            for doc in documents:
                if "source" not in doc.metadata:
                    doc.metadata["source"] = file_path
                    
            return documents
        
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {str(e)}")
            raise

    def load_directory(self, directory_path: str) -> List[Document]:
        """
        Scans a directory for supported files and loads them all.
        """
        all_documents = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file_path)
                
                # Only attempt to load supported files
                if ext.lower() in self.loaders:
                    docs = self.load_document(file_path)
                    all_documents.extend(docs)
                else:
                    logger.warning(f"Skipping unsupported file: {file_path}")
                    
        return all_documents

if __name__ == "__main__":
    # Quick manual test block
    loader = UniversalDocumentLoader()
    # E.g., docs = loader.load_directory("./data/raw_docs")
    print("UniversalDocumentLoader initialized and ready.")
