import requests
import json
import time

def test_api_key_authentication():
    # Health check (no auth required)
    print("\n=== Testing health check ===")
    response = requests.get("http://localhost:8000/health")
    print(f"Health check status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test without API key
    print("\n=== Testing without API key ===")
    url = "http://localhost:8000/analyze/content"
    
    payload = {
        "content": "Sample content for testing",
        "title": "Test Article",
        "url": "https://example.com/test-article"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    print(f"No API key status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test with invalid API key
    print("\n=== Testing with invalid API key ===")
    headers["X-API-Key"] = "invalid_key"
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    print(f"Invalid API key status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test with valid API key
    print("\n=== Testing with valid API key ===")
    headers["X-API-Key"] = "development_key_only_for_testing"  # Default key from site_credentials.json
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    print(f"Valid API key status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test caching (should be faster on second request)
    print("\n=== Testing caching ===")
    
    # First request
    start_time = time.time()
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    first_duration = time.time() - start_time
    
    # Second request (should be cached)
    start_time = time.time()
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    second_duration = time.time() - start_time
    
    # Third request with different content (should not be cached)
    payload["content"] = "Different content for testing caching"
    start_time = time.time()
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    third_duration = time.time() - start_time
    
    print(f"First request duration: {first_duration:.4f} seconds")
    print(f"Second request duration: {second_duration:.4f} seconds")
    print(f"Third request (different content) duration: {third_duration:.4f} seconds")
    print(f"Cached improvement: {(first_duration - second_duration) / first_duration * 100:.2f}%")
    
    # Test different site
    print("\n=== Testing with different site API key ===")
    headers["X-API-Key"] = "thevou_production_key_12345"
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    print(f"TheVOU API key status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Waiting 2 seconds for the server to start...")
    time.sleep(2)
    
    try:
        test_api_key_authentication()
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        print("Make sure the API server is running (python run_local.py)")