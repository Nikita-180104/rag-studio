import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline

def run():
    vsm = VectorStoreManager()
    pipeline = GenerationPipeline(vsm)
    
    question = "what is sample_doc.md?"
    print(f"--- Running Query: '{question}' ---")
    
    # 1. Retrieve chunks
    docs = pipeline.vector_store_manager.get_retriever(k=settings.top_n_context if hasattr(settings, "top_n_context") else 8).invoke(question)
    print(f"\nRetrieved {len(docs)} chunks:")
    for idx, doc in enumerate(docs):
        print(f"\n[Chunk {idx+1}] Source: {doc.metadata.get('source')} Page: {doc.metadata.get('page')}")
        clean_content = doc.page_content[:300].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(f"Content:\n{clean_content}...")

    # 2. Format context
    formatted_context = pipeline._format_docs(docs)
    
    # 3. Generate answer
    prompt_input = pipeline.prompt.format_messages(
        context=formatted_context,
        question=question
    )
    gen_res = pipeline.llm.invoke(prompt_input)
    answer = gen_res.content.strip()
    print("\n--- Generated Answer ---")
    print(answer)
    
    # 4. Run Guardrail Audit
    is_grounded, reason = pipeline.guardrail.verify_post_generation(formatted_context, answer)
    print("\n--- Guardrail Verification ---")
    print(f"Is Grounded: {is_grounded}")
    print(f"Reason: {reason}")

if __name__ == "__main__":
    from config import settings
    run()
