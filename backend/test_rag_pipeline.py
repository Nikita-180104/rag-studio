import os
import sys
sys.modules["tensorflow"] = None
sys.modules["keras"] = None
sys.modules["tf_keras"] = None
os.environ["TRANSFORMERS_NO_TF"] = "1"
import logging

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from config import settings
from ingestion.document_loader import UniversalDocumentLoader
from ingestion.chunker import DocumentChunker
from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline

# Configure logging to show pipeline steps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_test():
    logger.info("Starting End-to-End RAG Verification Test...")
    
    # 1. Initialize DB Manager
    vector_store_manager = VectorStoreManager()
    
    # 2. Ingest Sample Document
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    sample_file = os.path.join(data_dir, "sample_doc.md")
    
    loader = UniversalDocumentLoader()
    raw_docs = loader.load_document(sample_file)
    logger.info(f"Loaded {len(raw_docs)} raw documents.")
    
    # 3. Chunk Documents
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    chunked_docs = chunker.chunk_documents(raw_docs)
    logger.info(f"Created {len(chunked_docs)} semantic chunks.")
    
    # 4. Embed & Index in Chroma
    vector_store_manager.add_documents(chunked_docs)
    logger.info("Successfully indexed chunks in Chroma DB.")
    
    # 5. Initialize Generation Pipeline
    pipeline = GenerationPipeline(vector_store_manager)
    
    # 6. Ask Question
    query = "What consensus engine does Project Antigravity use, and what is its peak throughput capacity?"
    logger.info(f"Executing Query: '{query}'")
    
    result = pipeline.answer_question(query)
    answer = result["answer"]
    
    print("\n" + "="*80)
    print("QUESTION:")
    print(query)
    print("="*80)
    print("ANSWER WITH CITATIONS:")
    print(answer)
    print("="*80 + "\n")
    
    # Clean up
    vector_store_manager.close()
    logger.info("Test finished and connections closed.")

if __name__ == "__main__":
    run_test()
