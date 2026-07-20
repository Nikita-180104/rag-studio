import os
import pickle

def run():
    pkl_path = r"d:\RAG\backend\data\chroma\documents.pkl"
    if not os.path.exists(pkl_path):
        print(f"Pickle file not found at: {pkl_path}")
        return
        
    print(f"Loading documents pickle from: {pkl_path}")
    with open(pkl_path, 'rb') as f:
        documents = pickle.load(f)
        
    print(f"Total document chunks in BM25 index: {len(documents)}")
    sources = {}
    for doc in documents:
        source = doc.metadata.get("source", "Unknown")
        sources[source] = sources.get(source, 0) + 1
        
    print("\nIndexed files and chunk counts:")
    for src, count in sources.items():
        print(f"  - {src}: {count} chunks")

if __name__ == "__main__":
    run()
