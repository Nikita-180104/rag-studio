import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from retrieval.vector_store import VectorStoreManager
from generation.pipeline import GenerationPipeline, CONDENSE_PROMPT_TEMPLATE

def run():
    vsm = VectorStoreManager()
    pipeline = GenerationPipeline(vsm)
    
    question = "what are the components of data science"
    history = [
        {"role": "user", "content": "summarize the git sheet"},
        {"role": "assistant", "content": "There are 6 main sections in the Git cheat sheet: 1. Installation & GUIs... 6. Share & Update..."},
        {"role": "user", "content": "whatare data science components??"},
        {"role": "assistant", "content": "There are 5 components of data science: Domain Expertise, Statistics, Data Engineering, Visualization, and Advanced Computing."},
        {"role": "user", "content": "what is model buidling?"},
        {"role": "assistant", "content": "Model building in data science is the step where the actual model building starts..."},
        {"role": "user", "content": "what is difference between deep and machine learning??"},
        {"role": "assistant", "content": "Machine Learning is a subset of AI... Deep learning is a machine learning technique..."},
        {"role": "user", "content": "what is sample_doc.md summarize it"},
        {"role": "assistant", "content": "The document sample_doc.md provides an overview of GroundLens AI system, its consensus engine GravityConsensus..."}
    ]
    
    CONDENSE_PROMPT_TEMPLATE = """Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question (which can be understood without context).

Guidelines:
1. If the follow-up question references pronouns, abbreviations, or context from the chat history (e.g., "what happens before it?", "explain that step"), rewrite it to be explicit using terms from the history.
2. If the follow-up question introduces a completely new topic, asks about a different document, or does not refer to the history (e.g., "give summary of the git sheat document", "what is git?"), do NOT merge it with the history. Keep the original question's intent intact and only correct minor spelling errors (e.g. "git sheat" -> "git cheat sheet") or make it a clear standalone search query.
3. Do NOT reply to the question, just return the rephrased standalone question.

Chat History:
{chat_history}

Follow-up Question: {question}

Standalone Question:"""
    
    formatted_history = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
    condense_prompt = CONDENSE_PROMPT_TEMPLATE.format(
        chat_history=formatted_history,
        question=question
    )
    condense_res = pipeline.llm.invoke(condense_prompt)
    search_query = condense_res.content.strip()
    print("====================================")
    print("REFORMULATED STANDALONE QUERY:")
    print(f"'{search_query}'")
    print("====================================")

if __name__ == "__main__":
    run()
