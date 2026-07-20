import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline

def run():
    vsm = VectorStoreManager()
    pipeline = GenerationPipeline(vsm)
    
    # Simulating the exact 5-turn conversation history
    history = [
        {"role": "user", "content": "what are the compnents of data science"},
        {"role": "assistant", "content": "There are 7 components of Data Science: Domain Expertise, Statistics, Data Engineering, Mean, Data, Standard Deviation, Visualization and Advanced Computing."},
        {"role": "user", "content": "what is model buidling"},
        {"role": "assistant", "content": "The process of model building involves distributing datasets for training and testing..."},
        {"role": "user", "content": "what is the process before that?"},
        {"role": "assistant", "content": "There are 3 stages that come before Model Building: Discovery, Preparation, and Planning."},
        {"role": "user", "content": "what is machine learning deep learning?"},
        {"role": "assistant", "content": "Machine Learning is a subset of AI... Deep learning is a machine learning technique..."}
    ]
    
    question = "give summary of the git sheat document"
    
    print("--- Simulating Chat History ---")
    for msg in history:
        print(f"{msg['role'].upper()}: {msg['content'][:120]}...")
        
    print(f"\nUser: {question}")
    
    # 1. Run Query Condensation
    formatted_history = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
    from generation.pipeline import CONDENSE_PROMPT_TEMPLATE
    condense_prompt = CONDENSE_PROMPT_TEMPLATE.format(
        chat_history=formatted_history,
        question=question
    )
    condense_res = pipeline.llm.invoke(condense_prompt)
    search_query = condense_res.content.strip()
    print(f"\n--- Condensed Standalone Query ---")
    print(f"'{search_query}'")

if __name__ == "__main__":
    run()
