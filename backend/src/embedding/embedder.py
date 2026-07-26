import logging
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# Import our typed settings
from config import settings

logger = logging.getLogger(__name__)

class BGEEmbedder:
    """
    A wrapper around LangChain's HuggingFaceBgeEmbeddings.
    BGE models are highly optimized for RAG and require a specific 
    instruction prefix for queries to achieve maximum MTEB scores.
    """
    
    def __init__(self):
        logger.info(f"Initializing BGE Embedding model: {settings.embedding_model_name}")
        
        # BGE models use a specific query instruction to distinguish between
        # 'passages' (documents) and 'queries' (user questions).
        # This is a key reason why BGE performs so well.
        model_kwargs = {'device': 'cpu'} # Change to 'cuda' or 'mps' if GPU is available
        encode_kwargs = {'normalize_embeddings': True} # Crucial for cosine similarity
        
        try:
            self.embeddings = HuggingFaceBgeEmbeddings(
                model_name=settings.embedding_model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
                query_instruction="Represent this sentence for searching relevant passages: "
            )
            logger.info("Successfully loaded embedding model.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise

    def get_embeddings(self):
        """
        Returns the underlying LangChain embedding object.
        This allows us to pass it directly into LangChain VectorStores like Weaviate.
        """
        return self.embeddings

if __name__ == "__main__":
    # Quick manual test block
    embedder = BGEEmbedder()
    embeddings_model = embedder.get_embeddings()
    
    # Test embedding a single query
    vector = embeddings_model.embed_query("What is the capital of France?")
    print(f"Generated vector of dimension: {len(vector)}")
    print("BGE embedder initialized and working.")
