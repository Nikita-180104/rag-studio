import os
import logging
from typing import List, Dict, Any

from langchain_core.documents import Document
from config import settings
from embedding.embedder import BGEEmbedder
from utils.errors import RetrievalError, RAGException

logger = logging.getLogger(__name__)

class ChromaManager:
    """
    Manages the connection to Chroma DB and provides methods to insert and retrieve
    documents using LangChain's VectorStore interface with local Sparse-Dense Hybrid 
    and metadata filtering support.
    """
    
    def __init__(self, collection_name: str = "RAG_Documents"):
        self.collection_name = collection_name
        logger.info(f"Initializing Chroma DB at: {settings.chroma_db_dir}...")
        
        try:
            # Lazy load to avoid importing if not active/installed
            from langchain_chroma import Chroma
            
            # Ensure directories exist
            os.makedirs(settings.chroma_db_dir, exist_ok=True)
            
            self.embedder = BGEEmbedder()
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                persist_directory=settings.chroma_db_dir,
                embedding_function=self.embedder.get_embeddings()
            )
            logger.info("Chroma DB initialization complete.")
        except Exception as e:
            raise RetrievalError(f"Failed to initialize Chroma DB connection: {e}") from e

    def add_documents(self, documents: List[Document]):
        if not documents:
            logger.warning("No documents provided to insert.")
            return

        try:
            logger.info(f"Adding {len(documents)} documents to Chroma collection: {self.collection_name}...")
            self.vector_store.add_documents(documents)
            
            # Persist raw documents locally to fit the BM25 sparse retriever later
            import pickle
            pkl_path = os.path.join(settings.chroma_db_dir, "documents.pkl")
            
            existing_docs = []
            if os.path.exists(pkl_path):
                with open(pkl_path, 'rb') as f:
                    existing_docs = pickle.load(f)
            
            # Combine
            all_docs = existing_docs + documents
            with open(pkl_path, 'wb') as f:
                pickle.dump(all_docs, f)
            logger.info(f"Successfully persisted document metadata for local BM25 indexing at: {pkl_path}")
        except Exception as e:
            raise RetrievalError(f"Failed to index documents in Chroma DB: {e}") from e

    def get_retriever(self, k: int = 4, search_filter: Dict[str, Any] = None):
        """
        Builds a dynamic Sparse-Dense hybrid ensemble using local BM25 + dense Chroma vector DB,
        supporting metadata pre-filtering across both channels.
        """
        import pickle
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers.ensemble import EnsembleRetriever
        
        pkl_path = os.path.join(settings.chroma_db_dir, "documents.pkl")
        
        # Fallback dense configurations
        dense_search_kwargs = {"k": k}
        if search_filter:
            dense_search_kwargs["filter"] = search_filter
            logger.info(f"Applying metadata filter to dense retrieval: {search_filter}")
            
        # Fallback to pure dense search if no documents were persisted yet
        if not os.path.exists(pkl_path):
            logger.warning("No persisted documents found for local BM25 retriever. Falling back to pure semantic search.")
            return self.vector_store.as_retriever(search_kwargs=dense_search_kwargs)
            
        try:
            with open(pkl_path, 'rb') as f:
                documents = pickle.load(f)
            
            # Apply metadata pre-filtering to local documents list for BM25
            if search_filter:
                filtered_docs = []
                for doc in documents:
                    match = True
                    for key, val in search_filter.items():
                        if doc.metadata.get(key) != val:
                            match = False
                            break
                    if match:
                        filtered_docs.append(doc)
                documents = filtered_docs
                logger.info(f"Applying metadata filter to local BM25: Retained {len(documents)} matching chunks.")
            
            if not documents:
                logger.warning("No documents matching metadata filters. Falling back to pure dense retrieval.")
                return self.vector_store.as_retriever(search_kwargs=dense_search_kwargs)
                
            # 1. Instantiate local BM25 sparse keyword retriever with punctuation-aware tokenization
            import re
            bm25_retriever = BM25Retriever.from_documents(
                documents, 
                preprocess_func=lambda text: re.findall(r'\w+(?:\.\w+)*', text.lower())
            )
            bm25_retriever.k = k
            
            # 2. Instantiate dense vector retriever
            dense_retriever = self.vector_store.as_retriever(search_kwargs=dense_search_kwargs)
            
            # 3. Blending weights mapped to hybrid_search_alpha
            alpha = settings.hybrid_search_alpha
            weights = [1.0 - alpha, alpha]
            
            # 4. Combine retrievers using Reciprocal Rank Fusion (RRF)
            ensemble_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, dense_retriever],
                weights=weights
            )
            logger.info(f"Initialized local Hybrid Ensemble Retriever (RRF weights: BM25={weights[0]:.2f}, Dense={weights[1]:.2f})")
            return ensemble_retriever
            
        except Exception as e:
            logger.error(f"Failed to build hybrid ensemble retriever: {e}. Falling back to pure dense.")
            return self.vector_store.as_retriever(search_kwargs=dense_search_kwargs)
        
    def is_empty(self) -> bool:
        try:
            return self.vector_store._collection.count() == 0
        except Exception as e:
            logger.warning(f"Error checking if Chroma is empty: {e}")
            return True

    def delete_document(self, filepath: str):
        """
        Deletes all chunks associated with a document (identified by filepath) from:
        1. Chroma dense vector store
        2. Local documents.pkl file (BM25 index)
        """
        try:
            logger.info(f"Deleting document chunks for source: {filepath} from Chroma...")
            norm_filepath = os.path.abspath(filepath)
            
            # Query for the IDs matching the source filepath
            results = self.vector_store.get(where={"source": norm_filepath})
            ids = results.get("ids", [])
            if ids:
                logger.info(f"Found {len(ids)} chunks in Chroma to delete.")
                self.vector_store.delete(ids=ids)
                logger.info("Deleted chunks from Chroma DB.")
            else:
                logger.warning(f"No chunks found in Chroma for source: {norm_filepath}")
                
            # Now delete from local documents.pkl
            pkl_path = os.path.join(settings.chroma_db_dir, "documents.pkl")
            if os.path.exists(pkl_path):
                import pickle
                with open(pkl_path, 'rb') as f:
                    documents = pickle.load(f)
                
                # Filter out documents matching the source path
                filtered_docs = [doc for doc in documents if os.path.abspath(doc.metadata.get("source", "")) != norm_filepath]
                
                if len(filtered_docs) < len(documents):
                    logger.info(f"Filtered out {len(documents) - len(filtered_docs)} chunks from BM25 storage.")
                    with open(pkl_path, 'wb') as f:
                        pickle.dump(filtered_docs, f)
                else:
                    logger.info("No matching chunks found in BM25 storage.")
        except Exception as e:
            raise RetrievalError(f"Failed to delete document from Chroma DB: {e}") from e

    def close(self):
        pass

class WeaviateManager:
    """
    Manages the connection to Weaviate and provides methods to insert and retrieve
    documents using LangChain's VectorStore interface with Native Hybrid Search
    and metadata filtering support.
    """
    
    def __init__(self, index_name: str = "RAG_Documents"):
        self.index_name = index_name
        logger.info(f"Connecting to Weaviate at {settings.weaviate_url}...")
        
        try:
            # Lazy load to avoid importing if not active/installed
            import weaviate
            from weaviate.classes.init import Auth
            from langchain_weaviate.vectorstores import WeaviateVectorStore
            
            if settings.weaviate_api_key:
                auth_credentials = Auth.api_key(settings.weaviate_api_key)
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=settings.weaviate_url,
                    auth_credentials=auth_credentials
                )
            else:
                url = settings.weaviate_url.replace("http://", "").replace("https://", "")
                host = url.split(":")[0] if ":" in url else url
                port = int(url.split(":")[1]) if ":" in url else 8080
                self.client = weaviate.connect_to_local(host=host, port=port)

            logger.info("Weaviate connection established.")
            
            self.embedder = BGEEmbedder()
            self.vector_store = WeaviateVectorStore(
                client=self.client,
                index_name=self.index_name,
                text_key="text",
                embedding=self.embedder.get_embeddings()
            )
        except Exception as e:
            raise RetrievalError(f"Failed to connect to Weaviate instance: {e}") from e

    def add_documents(self, documents: List[Document]):
        if not documents:
            logger.warning("No documents provided to insert.")
            return

        try:
            logger.info(f"Adding {len(documents)} documents to Weaviate index: {self.index_name}...")
            self.vector_store.add_documents(documents)
            logger.info("Documents successfully added to Weaviate.")
        except Exception as e:
            raise RetrievalError(f"Failed to index documents in Weaviate: {e}") from e

    def get_retriever(self, k: int = 4, search_filter: Dict[str, Any] = None):
        """
        Exposes Native Weaviate Hybrid Search blending sparse BM25 and dense BGE vectors
        with metadata filtering hooks.
        """
        logger.info(f"Initializing native Weaviate Hybrid Retriever with alpha={settings.hybrid_search_alpha}...")
        
        search_kwargs = {
            "alpha": settings.hybrid_search_alpha,
            "k": k
        }
        
        if search_filter:
            search_kwargs["where"] = search_filter
            logger.info(f"Applying native metadata filter to Weaviate query: {search_filter}")
            
        return self.vector_store.as_retriever(
            search_type="hybrid",
            search_kwargs=search_kwargs
        )
        
    def is_empty(self) -> bool:
        return False

    def delete_document(self, filepath: str):
        pass

    def close(self):
        try:
            if hasattr(self, "client"):
                self.client.close()
                logger.info("Weaviate connection closed.")
        except Exception as e:
            logger.warning(f"Error closing Weaviate connection: {e}")


class VectorStoreManager:
    """
    Unified manager acting as a factory and dispatcher.
    Decouples client components from the underlying vector database.
    """
    
    def __init__(self, index_name: str = "RAG_Documents"):
        self.provider = settings.vector_db_provider.lower()
        logger.info(f"Unified VectorStoreManager selecting provider: '{self.provider}'")
        
        if self.provider == "weaviate":
            self.manager = WeaviateManager(index_name=index_name)
        elif self.provider == "chroma":
            self.manager = ChromaManager(collection_name=index_name)
        else:
            raise ValueError(f"Unsupported VECTOR_DB_PROVIDER: '{self.provider}'. Use 'chroma' or 'weaviate'.")

    def add_documents(self, documents: List[Document]):
        try:
            self.manager.add_documents(documents)
        except RAGException:
            raise
        except Exception as e:
            raise RetrievalError(f"Unhandled vector store error during insert: {e}") from e

    def get_retriever(self, k: int = 4, search_filter: Dict[str, Any] = None):
        try:
            return self.manager.get_retriever(k=k, search_filter=search_filter)
        except Exception as e:
            raise RetrievalError(f"Failed to generate retriever for {self.provider}: {e}") from e

    def is_empty(self) -> bool:
        if hasattr(self.manager, "is_empty"):
            return self.manager.is_empty()
        return True

    def delete_document(self, filepath: str):
        if hasattr(self.manager, "delete_document"):
            self.manager.delete_document(filepath)

    def close(self):
        self.manager.close()

if __name__ == "__main__":
    # Test initialization
    logging.basicConfig(level=logging.INFO)
    manager = VectorStoreManager()
    print(f"VectorStoreManager initialized with: {manager.provider}")
    manager.close()
