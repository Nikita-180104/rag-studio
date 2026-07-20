import pickle

def run():
    with open(r"d:\RAG\backend\data\chroma\documents.pkl", "rb") as f:
        docs = pickle.load(f)
        
    for doc in docs:
        if "sample_doc.md" in doc.metadata.get("source", ""):
            print("====================================")
            print(f"Source: {doc.metadata.get('source')}")
            print(f"Content:\n{doc.page_content}")
            print("====================================")

if __name__ == "__main__":
    run()
