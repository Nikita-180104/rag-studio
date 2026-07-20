import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from config import settings
from retrieval.vector_store import VectorStoreManager
from utils.document_db import DocumentMetadataStore

def run():
    print("Initializing cleanup of stale 'Project Antigravity' database chunks...")
    vsm = VectorStoreManager()
    collection = vsm.manager.vector_store._collection
    results = collection.get(include=["metadatas", "documents"])
    
    ids_to_delete = []
    for i, meta in enumerate(results["metadatas"]):
        source = meta.get("source", "")
        doc_text = results["documents"][i]
        if "sample_doc.md" in source or "antigravity" in doc_text.lower():
            ids_to_delete.append(results["ids"][i])
            
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        print(f"Successfully deleted {len(ids_to_delete)} stale chunks from Chroma.")
    else:
        print("No stale chunks found in Chroma.")

    # Re-index the current sample_doc.md containing GroundLens AI
    print("Re-indexing 'sample_doc.md'...")
    doc_store = DocumentMetadataStore()
    doc_record = doc_store.get_document("sample_doc.md")
    
    if doc_record:
        filepath = doc_record["filepath"]
        if os.path.exists(filepath):
            # Delete any remaining vectors specifically matching the current path to prevent overlap
            vsm.delete_document(filepath)
            
            # Loader & Chunker
            from ingestion.document_loader import UniversalDocumentLoader
            from ingestion.chunker import DocumentChunker
            
            loader = UniversalDocumentLoader()
            chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
            
            raw_docs = loader.load_document(filepath)
            chunked_docs = chunker.chunk_documents(raw_docs)
            if chunked_docs:
                vsm.add_documents(chunked_docs)
                print(f"Successfully re-indexed {len(chunked_docs)} chunks for GroundLens AI.")
            else:
                print("No chunks generated for sample_doc.md.")
        else:
            print(f"File not found at {filepath}")
    else:
        print("Metadata record for sample_doc.md not found.")

if __name__ == "__main__":
    run()
