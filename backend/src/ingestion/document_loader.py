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
    
class OcrPdfLoader:
    """
    A PDF loader that renders each page as an image using PyMuPDF (fitz)
    and runs RapidOCR to extract all text (including text inside diagrams/images).
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        import fitz  # PyMuPDF
        from rapidocr_onnxruntime import RapidOCR
        
        logger.info(f"Running ONNX-driven OCR on PDF: {self.file_path}...")
        
        engine = RapidOCR()
        documents = []
        
        # Open PDF
        doc = fitz.open(self.file_path)
        
        for page_idx in range(len(doc)):
            logger.info(f"Processing page {page_idx + 1}/{len(doc)} via OCR...")
            page = doc[page_idx]
            
            # Render page to a high-resolution image (2x zoom = ~150 DPI)
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert pixmap to PNG bytes
            img_bytes = pix.tobytes("png")
            
            # Run OCR
            ocr_result, _ = engine(img_bytes)
            
            page_text = ""
            if ocr_result:
                formatted_lines = []
                for line in ocr_result:
                    box, text, conf = line
                    if not text or not text.strip():
                        continue
                    
                    # Calculate bounding box height (proxy for font size)
                    # Coordinates format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                    y1 = box[0][1]
                    y2 = box[1][1]
                    y3 = box[2][1]
                    y4 = box[3][1]
                    height = int(((y4 - y1) + (y3 - y2)) / 2)
                    
                    # Apply semantic hierarchy based on box height threshold
                    if height >= 35:
                        formatted_lines.append(f"# {text.strip()}")
                    elif height >= 22:
                        formatted_lines.append(f"## {text.strip()}")
                    else:
                        formatted_lines.append(f"- [Illustration Detail]: {text.strip()}")
                page_text = "\n".join(formatted_lines)
            
            # Fallback to standard digital text if OCR is empty
            if not page_text.strip():
                logger.info(f"OCR returned empty text for page {page_idx + 1}. Falling back to digital text.")
                page_text = page.get_text()
                
            metadata = {
                "source": self.file_path,
                "page": page_idx
            }
            
            documents.append(Document(page_content=page_text, metadata=metadata))
            
        doc.close()
        logger.info(f"OCR load complete for {self.file_path}. Extracted {len(documents)} pages.")
        return documents

class UniversalDocumentLoader:
    """
    A unified interface to load various document types into LangChain Document objects.
    Ensures standard metadata (like source file path) is attached to every document.
    """
    
    def __init__(self):
        # Map file extensions to their corresponding LangChain loaders
        self.loaders = {
            ".pdf": OcrPdfLoader,
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
