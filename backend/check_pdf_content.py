import os
import sys

# Disable TensorFlow imports in HuggingFace transformers to prevent Keras 3 conflicts
os.environ["TRANSFORMERS_NO_TF"] = "1"

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from ingestion.document_loader import UniversalDocumentLoader

def run():
    pdf_path = None
    # Look in data/ and uploads/
    possible_dirs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "data")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
    ]
    import glob
    for d in possible_dirs:
        if os.path.exists(d):
            matches = glob.glob(os.path.join(d, "*basics-of-data-science-kpk.pdf"))
            if matches:
                pdf_path = matches[0]
                break

    if not pdf_path:
        print("PDF file basics-of-data-science-kpk.pdf not found in data/ or uploads/")
        return

    print(f"Target PDF Path: {pdf_path}")
    loader = UniversalDocumentLoader()
    raw_docs = loader.load_document(pdf_path)
    print(f"Total pages extracted: {len(raw_docs)}")

    target_pages = [10, 11, 12, 13, 14, 15, 16] # 0-indexed for Pages 11 to 17
    for p in target_pages:
        if p < len(raw_docs):
            print("\n" + "="*50)
            print(f" PAGE {p+1} EXTRACTED TEXT ")
            print("="*50)
            print(raw_docs[p].page_content[:1000])
        else:
            print(f"\nPage {p+1} does not exist in the extracted pages.")

if __name__ == "__main__":
    run()
