import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retrieval.vector_store import VectorStoreManager

def run():
    vsm = VectorStoreManager()
    query = "what are the components of data science"
    
    print(f"--- Querying Ensemble Retriever with: '{query}' ---")
    retriever = vsm.get_retriever(k=8)
    docs = retriever.invoke(query)
    for idx, doc in enumerate(docs):
        print(f"  {idx+1}. Source: {doc.metadata.get('source')} Page: {doc.metadata.get('page')}")
        print(f"     Content preview: {doc.page_content[:150].replace('\n', ' ')}...")

if __name__ == "__main__":
    run()
