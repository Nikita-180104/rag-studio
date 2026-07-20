import requests
import json

def run():
    url = "http://localhost:8000/query"
    payload = {
        "question": "give summary of the git sheat document",
        "history": [
            {
                "role": "user",
                "content": "what are the compnents of data science"
            },
            {
                "role": "assistant",
                "content": "There are 7 components of Data Science. The components are: 1. Domain Expertise 2. Statistics 3. Data Engineering 4. Mean 5. Data 6. Standard Deviation 7. Visualization and Advanced Computing. [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 7]"
            },
            {
                "role": "user",
                "content": "what is model buidling"
            },
            {
                "role": "assistant",
                "content": "The process of model building in data science involves distributing datasets for training and testing, and applying techniques like association, classification, and clustering to the training data set [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 16]..."
            },
            {
                "role": "user",
                "content": "what is the process before that?"
            },
            {
                "role": "assistant",
                "content": "There are several stages that precede the model building process in data science. There are 3 stages that come before Model Building: Discovery, Preparation, and Planning. [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 12]"
            },
            {
                "role": "user",
                "content": "what is machine learning deep learning?"
            },
            {
                "role": "assistant",
                "content": "There are 2 key concepts related to machine learning and deep learning in the context of data science. Machine Learning is a subset of Artificial Intelligence... [Source: 1783775440_basics-of-data-science-kpk.pdf, Page: 9]"
            }
        ]
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
