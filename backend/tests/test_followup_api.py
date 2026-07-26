import requests
import json

def run():
    url = "http://localhost:8000/query"
    payload = {
        "question": "what happens before it?",
        "history": [
            {
                "role": "user",
                "content": "What is Model Building?"
            },
            {
                "role": "assistant",
                "content": "There is 1 stage of Model Building explicitly mentioned in the provided context. The stage is: Model Building. In the context of data science, Model Building is defined as the step where the actual model building starts, and the data scientist distributes datasets for training and testing [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 16]. During this step, techniques like association, classification, and clustering are applied to the training data set, and the model, once prepared, is tested against the \"testing\" dataset [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 16]. Model Building is part of the Data Science Process, which includes several stages such as Discovery, Preparation, Planning, Model Building, and Operation [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 12]."
            }
        ]
    }
    
    print("Querying live FastAPI endpoint with multi-turn history...")
    try:
        response = requests.post(url, json=payload, timeout=15)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    run()
