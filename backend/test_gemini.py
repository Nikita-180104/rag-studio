import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]

for model in models_to_try:
    print(f"Trying model: {model}")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=settings.google_api_key,
            temperature=0,
        )
        res = llm.invoke("Hello, say 'Test successful!' in exactly 2 words.")
        print(f"Success for {model}: {res.content}")
        break
    except Exception as e:
        print(f"Failed for {model}: {e}")
