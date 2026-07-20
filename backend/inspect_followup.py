import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline

def run():
    vsm = VectorStoreManager()
    pipeline = GenerationPipeline(vsm)
    
    # Simulate chat history
    history = [
        {"role": "user", "content": "What is Model Building?"},
        {"role": "assistant", "content": "Model Building is a step in the data science process where the actual model building starts. Data scientist distributes datasets for training and testing. Techniques like association, classification, and clustering are applied."}
    ]
    
    question = "what happens before it?"
    print(f"--- Chat History ---")
    for msg in history:
        print(f"{msg['role'].upper()}: {msg['content']}")
        
    print(f"\n--- Follow-up Question: '{question}' ---")
    
    # 1. Test Query Condensation
    formatted_history = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
    from generation.pipeline import CONDENSE_PROMPT_TEMPLATE
    condense_prompt = CONDENSE_PROMPT_TEMPLATE.format(
        chat_history=formatted_history,
        question=question
    )
    condense_res = pipeline.llm.invoke(condense_prompt)
    search_query = condense_res.content.strip()
    print(f"\nCondensed Standalone Query:\n'{search_query}'")
    
    # 2. Retrieve chunks for search_query
    docs = pipeline.vector_store_manager.get_retriever(k=8).invoke(search_query)
    print(f"\nRetrieved {len(docs)} chunks for '{search_query}':")
    for idx, doc in enumerate(docs):
        print(f"  - Chunk {idx+1}: Source: {doc.metadata.get('source')} Page: {doc.metadata.get('page')}")
        print(f"    Content preview: {doc.page_content[:150]}...")
        
    # 3. Format context
    formatted_context = pipeline._format_docs(docs)
    
    # 4. Generate answer
    prompt_input = pipeline.prompt.format_messages(
        context=formatted_context,
        question=search_query
    )
    gen_res = pipeline.llm.invoke(prompt_input)
    answer = gen_res.content.strip()
    print(f"\nGenerated Answer:\n{answer}")
    
    # 5. Run Guardrail Audit
    is_grounded, reason = pipeline.guardrail.verify_post_generation(formatted_context, answer)
    print(f"\nGuardrail Grounding Audit:")
    print(f"Is Grounded: {is_grounded}")
    print(f"Reason: {reason}")

if __name__ == "__main__":
    run()
