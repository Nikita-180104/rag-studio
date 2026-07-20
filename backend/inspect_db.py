import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from config import settings
from retrieval.vector_store import VectorStoreManager
from utils.document_db import DocumentMetadataStore

def run():
    print("--- SQLite Document Metadata Store ---")
    doc_store = DocumentMetadataStore()
    docs = doc_store.list_documents()
    for doc in docs:
        print(f"Filename: {doc['filename']}")
        print(f"  Filepath: {doc['filepath']}")
        print(f"  Chunks: {doc['chunks']}")
        print(f"  Status: {doc['status']}")
        
    print("\n--- Chroma DB Indexed Sources ---")
    vsm = VectorStoreManager()
    collection = vsm.manager.vector_store._collection
    results = collection.get(include=["metadatas", "documents"])
    
    unique_sources = set()
    antigravity_count = 0
    groundlens_count = 0
    
    for i, meta in enumerate(results["metadatas"]):
        source = meta.get("source")
        unique_sources.add(source)
        doc_text = results["documents"][i]
        if "antigravity" in doc_text.lower():
            antigravity_count += 1
        if "groundlens" in doc_text.lower():
            groundlens_count += 1
            
    print(f"Total vector chunks: {len(results['metadatas'])}")
    print("Unique sources in Chroma:")
    for s in unique_sources:
        print(f"  - {s}")
        
    print(f"\nChunks containing 'Antigravity': {antigravity_count}")
    print(f"Chunks containing 'GroundLens': {groundlens_count}")

if __name__ == "__main__":
    run()
