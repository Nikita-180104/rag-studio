import pickle

def run():
    with open(r"d:\RAG\backend\data\chroma\documents.pkl", "rb") as f:
        docs = pickle.load(f)
        
    for doc in docs:
        source = doc.metadata.get("source", "")
        page = doc.metadata.get("page", None)
        if "basics-of-data-science-kpk.pdf" in source and page == 6: # fitz page index 6 is page 7
            print("====================================")
            print(f"Source: {source} Page: {page + 1}")
            print(f"Content:\n{doc.page_content}")
            print("====================================")

if __name__ == "__main__":
    run()
