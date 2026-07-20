from typing import List
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentChunker:
    """
    Handles splitting large Document objects into smaller, semantically meaningful chunks.
    This is required because Embedding models have strict token limits.
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: The target size for each chunk. We use character count here, 
                        though in an advanced setup we might use a TokenSplitter.
                        Assuming ~4 chars per token, 500 chars is roughly 125 tokens.
                        For a 500-token target, chunk_size should be ~2000 chars.
            chunk_overlap: The number of characters to overlap between consecutive chunks.
                           This prevents cutting a concept in half at chunk boundaries.
        """
        # We adjust the inputs slightly to better align with the "500-800 token" requirement 
        # using character estimation (1 token ≈ 4 characters in English).
        # So 600 tokens ≈ 2400 chars. 100 token overlap ≈ 400 chars.
        char_chunk_size = chunk_size * 4
        char_overlap = chunk_overlap * 4
        
        # RecursiveCharacterTextSplitter is the industry standard.
        # It tries to split on paragraphs (\n\n) first, then single newlines (\n), then spaces.
        # This keeps natural paragraphs together instead of brutally slicing mid-sentence.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=char_chunk_size,
            chunk_overlap=char_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Takes a list of raw Documents (e.g., 1 doc per PDF page) and returns
        a list of smaller chunked Documents.
        """
        if not documents:
            logger.warning("No documents provided to chunk.")
            return []

        logger.info(f"Splitting {len(documents)} raw documents into chunks...")
        
        # This applies the splitting logic and automatically duplicates the metadata
        # (like 'source' and 'page') from the parent doc into all its child chunks.
        chunks = self.text_splitter.split_documents(documents)
        
        # Prepend document name prefix to enable keyword-based matching for specific files
        import os
        for chunk in chunks:
            source = chunk.metadata.get("source", "")
            if source:
                filename = os.path.basename(source)
                chunk.page_content = f"Document Source filename: {filename}\n{chunk.page_content}"
        
        logger.info(f"Successfully generated {len(chunks)} chunks.")
        return chunks

if __name__ == "__main__":
    # Quick manual test block
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    
    sample_doc = Document(
        page_content="This is a very long sentence. " * 50, 
        metadata={"source": "test.txt"}
    )
    chunks = chunker.chunk_documents([sample_doc])
    print(f"Split test document into {len(chunks)} chunks.")
