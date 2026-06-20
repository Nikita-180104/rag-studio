import logging
from typing import Sequence, Optional

from pydantic import Field, PrivateAttr
from langchain_core.documents import Document
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.callbacks import Callbacks

logger = logging.getLogger(__name__)

class LocalCrossEncoderReranker(BaseDocumentCompressor):
    """
    A modular document compressor wrapper for local Cross-Encoder re-ranking models
    implemented using SentenceTransformers.
    Complying with LangChain's BaseDocumentCompressor allows seamless integration
    into any LangChain expression or retrieval chain.
    """
    
    model_name: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2", 
        description="Local Cross-Encoder model ID from HuggingFace"
    )
    top_n: int = Field(
        default=4, 
        description="Number of high-precision documents to return after re-ranking"
    )
    
    # Declare private attribute to store the model object and avoid Pydantic serialization errors
    _model: any = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from sentence_transformers import CrossEncoder
        
        logger.info(f"Initializing local Cross-Encoder re-ranker: '{self.model_name}' on CPU...")
        try:
            self._model = CrossEncoder(self.model_name, device="cpu")
            logger.info("Cross-Encoder re-ranker successfully loaded.")
        except Exception as e:
            logger.error(f"Failed to load Cross-Encoder model: {e}")
            raise

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """
        Calculates full query-document cross-attention relevance scores,
        re-orders the candidates in descending order of score, and selects the top_n.
        """
        if not documents:
            logger.warning("No documents provided to re-ranker.")
            return []
            
        logger.info(f"Re-ranking {len(documents)} documents for query: '{query}'...")
        
        # 1. Construct input pairs: (query, chunk_text)
        pairs = [(query, doc.page_content) for doc in documents]
        
        try:
            # 2. Predict relevance scores
            scores = self._model.predict(pairs)
            
            # 3. Associate score with documents and sort descending
            ranked_docs = []
            for doc, score in zip(documents, scores):
                # Duplicate doc to avoid mutating original objects in-place
                doc_copy = Document(
                    page_content=doc.page_content, 
                    metadata=doc.metadata.copy()
                )
                doc_copy.metadata["re_rank_score"] = float(score)
                ranked_docs.append(doc_copy)
                
            # Sort by re_rank_score descending
            ranked_docs.sort(key=lambda x: x.metadata["re_rank_score"], reverse=True)
            
            # 4. Extract top_n elements
            compressed_docs = ranked_docs[:self.top_n]
            logger.info(f"Selected top {len(compressed_docs)} high-precision chunks from {len(ranked_docs)} candidates.")
            return compressed_docs
            
        except Exception as e:
            logger.error(f"Error during re-ranking execution: {e}. Returning unranked top_n candidates.")
            return list(documents[:self.top_n])

if __name__ == "__main__":
    # Diagnostic check
    logging.basicConfig(level=logging.INFO)
    reranker = LocalCrossEncoderReranker(top_n=2)
    sample_docs = [
        Document(page_content="Paris is the capital of France.", metadata={"source": "doc1"}),
        Document(page_content="Distributed ledgers store transactions.", metadata={"source": "doc2"}),
        Document(page_content="The Eiffel Tower is in Paris.", metadata={"source": "doc3"}),
    ]
    query = "What is the capital city of France?"
    result = reranker.compress_documents(sample_docs, query)
    for i, doc in enumerate(result):
        print(f"Rank {i+1}: {doc.metadata['source']} (Score: {doc.metadata['re_rank_score']:.4f}) -> {doc.page_content}")
