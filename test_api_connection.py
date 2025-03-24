#!/usr/bin/env python3
import requests
import json
import sys

# API credentials
API_URL = "https://web-analyzer-api.onrender.com"
API_KEY = "thevou_api_key_2025_03_24"
SITE_ID = "thevou"

def test_health():
    """Test the health endpoint"""
    url = f"{API_URL}/health"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Health endpoint status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing health endpoint: {str(e)}")
        return False

def test_analyze_content():
    """Test the analyze content endpoint"""
    url = f"{API_URL}/analyze/content"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Simple test content
    data = {
        "content": "This is a test article about fashion. We're testing connection to the API.",
        "title": "Test Article for API Connection",
        "site_id": SITE_ID
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        print(f"Analyze content endpoint status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing analyze content endpoint: {str(e)}")
        return False

def test_auth_only():
    """Test authentication only"""
    # Let's test a simple endpoint to check auth
    url = f"{API_URL}/bulk/jobs"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Auth test status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing authentication: {str(e)}")
        return False

def main():
    print("Testing API connection...")
    
    # Test health endpoint
    print("\n=== Testing Health Endpoint ===")
    health_ok = test_health()
    
    # Test auth only
    print("\n=== Testing Authentication ===")
    auth_ok = test_auth_only()
    
    # Test analyze content
    print("\n=== Testing Analyze Content Endpoint ===")
    content_ok = test_analyze_content()
    
    # Summary
    print("\n=== Summary ===")
    print(f"Health endpoint: {'OK' if health_ok else 'FAILED'}")
    print(f"Authentication: {'OK' if auth_ok else 'FAILED'}")
    print(f"Analyze content: {'OK' if content_ok else 'FAILED'}")
    
    if health_ok and auth_ok and content_ok:
        print("\nAll tests PASSED!")
        return 0
    else:
        print("\nSome tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())