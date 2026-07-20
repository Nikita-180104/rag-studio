import requests
import json

def run():
    # Programmatically clear the SQLite cache to bypass the stale cached response
    import sys
    sys.path.append("src")
    from utils.cache import SQLiteRAGCache
    SQLiteRAGCache().clear()
    print("Persistent query cache successfully cleared.")

    url = "http://localhost:8000/query"
    payload = {
        "question": "what are the components of data science",
        "history": []
    }
    
    print("Querying live FastAPI endpoint with 5-turn history...")
    try:
        response = requests.post(url, json=payload, timeout=20)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    run()
