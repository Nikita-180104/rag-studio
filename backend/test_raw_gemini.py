import os
import google.generativeai as genai
from config import settings

print(f"Testing direct Gemini SDK with API Key: {settings.google_api_key[:10]}...")

genai.configure(api_key=settings.google_api_key)

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say 'Test successful!' in exactly 2 words.")
    print("Success:", response.text)
except Exception as e:
    print("Failed direct SDK:", e)
