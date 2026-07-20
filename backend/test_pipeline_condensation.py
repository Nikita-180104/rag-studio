import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline

def run():
    vsm = VectorStoreManager()
    pipeline = GenerationPipeline(vsm)
    
    question = "give summary of the git sheat document"
    history = [
        {"role": "user", "content": "what are the compnents of data science"},
        {"role": "assistant", "content": "There are 7 components of Data Science. The components are: 1. Domain Expertise 2. Statistics 3. Data Engineering 4. Mean 5. Data 6. Standard Deviation 7. Visualization and Advanced Computing. [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 7]"},
        {"role": "user", "content": "what is model buidling"},
        {"role": "assistant", "content": "The process of model building in data science involves distributing datasets for training and testing, and applying techniques like association, classification, and clustering to the training data set [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 16]..."},
        {"role": "user", "content": "what is the process before that?"},
        {"role": "assistant", "content": "There are several stages that precede the model building process in data science. There are 3 stages that come before Model Building: Discovery, Preparation, and Planning. [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 12]"},
        {"role": "user", "content": "what is machine learning deep learning?"},
        {"role": "assistant", "content": "There are 2 key concepts related to machine learning and deep learning in the context of data science. Machine Learning is a subset of Artificial Intelligence... [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 9]"}
    ]
    
    res = pipeline.answer_question(question, history=history)
    print("\n--- Pipeline Result Answer ---")
    print(res["answer"])
    print("\nCitations:")
    for c in res["citations"]:
        print(f"  - {c['source']} page {c['page']}")

if __name__ == "__main__":
    run()
