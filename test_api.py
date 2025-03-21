import requests
import json
import time

# Test the API locally
def test_health():
    response = requests.get("http://localhost:8000/health")
    print(f"Health check status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_analyze_content():
    url = "http://localhost:8000/analyze/content"
    
    payload = {
        "content": """Old money fashion is characterized by timeless elegance and understated luxury. 
        Classic pieces like tailored blazers, Oxford shirts, and quality knitwear form the foundation of 
        this sophisticated style. Unlike new money fashion, which often showcases flashy logos and 
        trending items, old money style emphasizes heritage, craftsmanship, and subtle refinement.""",
        "title": "Introduction to Old Money Fashion",
        "url": "https://example.com/test-article",
        "site_id": "test-site"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    print(f"Analyze content status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Waiting 2 seconds for the server to start...")
    time.sleep(2)
    
    try:
        test_health()
        test_analyze_content()
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        print("Make sure the API server is running (python run_local.py)")