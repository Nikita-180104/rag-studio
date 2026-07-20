import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from config import settings
from ingestion.document_loader import UniversalDocumentLoader
from ingestion.chunker import DocumentChunker
from retrieval.vector_store import VectorStoreManager

def debug():
    # 1. Find PDF file in data/ or uploads/
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "basics-of-data-science-kpk.pdf"))
    if not os.path.exists(pdf_path):
        # Look in uploads/
        uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
        import glob
        matches = glob.glob(os.path.join(uploads_dir, "*basics-of-data-science-kpk.pdf"))
        if matches:
            pdf_path = matches[0]
        else:
            # Fallback check for any PDF in uploads
            matches = glob.glob(os.path.join(uploads_dir, "*.pdf"))
            if matches:
                pdf_path = matches[0]

    print(f"Target PDF Path: {pdf_path}\n")

    if not os.path.exists(pdf_path):
        print("ERROR: Could not find the PDF file 'basics-of-data-science-kpk.pdf'. Please upload it first.")
        return

    # ----------------------------------------------------
    # 1. Raw Extracted Text / OCR for Page 7
    # ----------------------------------------------------
    print("="*60)
    print(" 1. RAW EXTRACTED TEXT FOR PAGE 7 (Index 6)")
    print("="*60)
    loader = UniversalDocumentLoader()
    raw_docs = loader.load_document(pdf_path)
    
    # Page 7 is index 6 (0-indexed)
    if len(raw_docs) > 6:
        page7 = raw_docs[6]
        print(f"Page metadata: {page7.metadata}")
        print(f"Extracted Character Count: {len(page7.page_content)}")
        print("\n--- CONTENT START ---")
        print(page7.page_content[:1500])
        print("--- CONTENT END ---\n")
    else:
        print(f"Error: PDF only has {len(raw_docs)} pages. Cannot extract Page 7.")
        return

    # ----------------------------------------------------
    # 2. Chunk Contents after Chunking
    # ----------------------------------------------------
    print("="*60)
    print(" 2. CHUNKS GENERATED FROM PAGE 7")
    print("="*60)
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk_documents(raw_docs)
    
    page7_chunks = [c for c in chunks if c.metadata.get("page") == 6]
    print(f"Found {len(page7_chunks)} chunks associated with Page 7:\n")
    for idx, chunk in enumerate(page7_chunks):
        print(f"--- Chunk {idx+1} ---")
        print(chunk.page_content)
        print("-" * 30)

    # ----------------------------------------------------
    # 3. Retrieved Chunks and Reranked Chunks
    # ----------------------------------------------------
    print("\n" + "="*60)
    print(" 3. RETRIEVAL & RE-RANKING FOR TARGET QUERY")
    print("="*60)
    query = "What are the components of Data Science?"
    print(f"Query: '{query}'\n")
    
    vsm = VectorStoreManager()
    
    # Get raw candidates (top-20)
    base_retriever = vsm.get_retriever(k=20)
    retrieved_docs = base_retriever.invoke(query)
    print(f"Initial Retrieval: Found {len(retrieved_docs)} raw candidate chunks.")
    
    # Check if page 7 is in candidates
    p7_candidates = [d for d in retrieved_docs if d.metadata.get("page") == 6]
    print(f"Is Page 7 in raw candidates? {'YES' if p7_candidates else 'NO'} ({len(p7_candidates)} chunks)\n")
    
    # Re-rank execution
    if settings.enable_reranking:
        from retrieval.re_ranker import LocalCrossEncoderReranker
        reranker = LocalCrossEncoderReranker(model_name=settings.reranker_model_name, top_n=4)
        compressed_docs = reranker.compress_documents(retrieved_docs, query)
        
        print("\nRe-ranked Top Chunks sent as Context:")
        for idx, doc in enumerate(compressed_docs):
            source_file = doc.metadata.get("source", "").split("\\")[-1].split("/")[-1]
            page_num = doc.metadata.get("page", 0) + 1
            score = doc.metadata.get("re_rank_score", 0.0)
            print(f"\nRank {idx+1} [Source: {source_file}, Page: {page_num}] (Reranker Score: {score:.4f}):")
            print(doc.page_content[:300] + "...")
            print("-" * 40)
            
    vsm.close()

if __name__ == "__main__":
    debug()
