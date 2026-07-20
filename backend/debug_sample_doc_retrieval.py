import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retrieval.vector_store import VectorStoreManager

def run():
    vsm = VectorStoreManager()
    
    query = "sample_doc.md"
    print(f"--- Direct Chroma Dense Similarity Search for: '{query}' ---")
    results = vsm.manager.vector_store.similarity_search_with_relevance_scores(query, k=5)
    for idx, (doc, score) in enumerate(results):
        print(f"  {idx+1}. Score: {score:.4f} | Source: {doc.metadata.get('source')} Page: {doc.metadata.get('page')}")
        print(f"     Content preview: {doc.page_content[:150].replace('\n', ' ')}...")
        
    print(f"\n--- Direct BM25 Sparse Search via get_retriever for: '{query}' ---")
    retriever = vsm.get_retriever(k=5)
    docs = retriever.invoke(query)
    for idx, doc in enumerate(docs):
        print(f"  {idx+1}. Source: {doc.metadata.get('source')} Page: {doc.metadata.get('page')}")
        print(f"     Content preview: {doc.page_content[:150].replace('\n', ' ')}...")

if __name__ == "__main__":
    run()
