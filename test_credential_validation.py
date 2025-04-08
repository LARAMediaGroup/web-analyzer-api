#!/usr/bin/env python3
import requests
import json
import sys

# Try the alternate API key that was found in original test_api_connection.py
API_URL = "https://web-analyzer-api.onrender.com"
API_KEY = "u1HG8J0uUenblA7KJuUhVlTX"
SITE_ID = "thevou"

def test_credentials():
    """Validate the API credentials"""
    print(f"Testing credentials...")
    print(f"API URL: {API_URL}")
    print(f"API Key: {API_KEY}")
    print(f"Site ID: {SITE_ID}")
    
    # Test health endpoint (no auth)
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
            print("  ✅ Health endpoint OK")
        else:
            print(f"  ❌ Health endpoint failed")
            return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False
    
    # Test auth with API key
    print("\n2. Testing API key authentication...")
    try:
        response = requests.get(
            f"{API_URL}/bulk/jobs",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ API key authentication OK")
        else:
            print(f"  ❌ API key authentication failed: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False
    
    # Test site ID specifics
    print("\n3. Testing site configuration...")
    try:
        # Simple content for testing
        test_data = {
            "content": "This is a test content",
            "title": "Test Title",
            "site_id": SITE_ID
        }
        
        response = requests.post(
            f"{API_URL}/analyze/content",
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            json=test_data,
            timeout=20
        )
        
        print(f"  Status: {response.status_code}")
        
        # Either 200 or 422 is OK (422 means validation error with the content, which is expected)
        if response.status_code in [200, 422]:
            print("  ✅ Site configuration OK")
            return True
        else:
            print(f"  ❌ Site configuration failed: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if test_credentials():
        print("\n✅ All credential tests PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Credential tests FAILED!")
        sys.exit(1)