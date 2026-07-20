import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retrieval.vector_store import VectorStoreManager
from utils.document_db import DocumentMetadataStore
from ingestion.document_loader import UniversalDocumentLoader
from ingestion.chunker import DocumentChunker

def run():
    vsm = VectorStoreManager()
    doc_store = DocumentMetadataStore()
    loader = UniversalDocumentLoader()
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    
    docs = doc_store.list_documents()
    print(f"Found {len(docs)} documents in system store to re-index.")
    
    for d in docs:
        filename = d["filename"]
        filepath = d["filepath"]
        print(f"\nRe-indexing {filename} ({filepath})...")
        
        # 1. Delete old vectors
        try:
            vsm.delete_document(filepath)
            print("  Deleted old vectors.")
        except Exception as e:
            print(f"  Error deleting old vectors: {e}")
            
        # 2. Reload and chunk
        if not os.path.exists(filepath):
            print(f"  Warning: File does not exist at {filepath}. Skipping.")
            continue
            
        try:
            raw_docs = loader.load_document(filepath)
            chunked_docs = chunker.chunk_documents(raw_docs)
            print(f"  Loaded and split into {len(chunked_docs)} chunks.")
            
            # 3. Add to Chroma/BM25
            if chunked_docs:
                vsm.add_documents(chunked_docs)
                print(f"  Successfully added to vector store.")
                
                # Update chunk count in sqlite
                doc_store.add_document(
                    filename=filename,
                    sha256=d["sha256"],
                    chunks=len(chunked_docs),
                    filepath=filepath,
                    status="Indexed"
                )
        except Exception as e:
            print(f"  Failed to index: {e}")

if __name__ == "__main__":
    run()
