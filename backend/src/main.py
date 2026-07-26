import os
import sys
os.environ["TRANSFORMERS_NO_TF"] = "1"
import logging

from config import settings
from ingestion.document_loader import UniversalDocumentLoader
from ingestion.chunker import DocumentChunker
from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline

# Configure logging for the main execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # 1. Initialize our components
    logger.info("--- Initializing RAG System ---")
    
    try:
        vector_store_manager = VectorStoreManager()
    except Exception as e:
        logger.error(f"Could not initialize Vector Store. Error: {e}")
        sys.exit(1)
        
    loader = UniversalDocumentLoader()
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    pipeline = GenerationPipeline(vector_store_manager)
    
    # 2. Check if there are documents to ingest
    logger.info("--- Ingestion Phase ---")
    raw_docs = loader.load_directory(data_dir)
    
    if not raw_docs:
        logger.warning(f"No documents found in {data_dir}.")
        logger.warning("Please place a .txt, .pdf, or .md file in the data folder and run again.")
    else:
        # 3. Chunk and Embed
        logger.info("--- Chunking and Embedding Phase ---")
        chunked_docs = chunker.chunk_documents(raw_docs)
        vector_store_manager.add_documents(chunked_docs)
        logger.info(f"Successfully stored {len(chunked_docs)} chunks in Vector Store.")
        
    # 4. Interactive Q&A Loop
    logger.info("--- Generation Phase ---")
    print("\n" + "="*50)
    print("RAG System Ready! Type 'exit' to quit.")
    print("="*50 + "\n")
    
    while True:
        try:
            query = input("\nAsk a question about your documents: ")
            if query.lower() in ['exit', 'quit']:
                break
                
            if not query.strip():
                continue
                
            print("\nThinking...")
            answer = pipeline.answer_question(query)
            
            print("\n" + "-"*50)
            print("ANSWER:")
            print(answer)
            print("-"*50)
            
        except KeyboardInterrupt:
            break
            
    # Cleanup
    logger.info("Shutting down...")
    vector_store_manager.close()

if __name__ == "__main__":
    main()
