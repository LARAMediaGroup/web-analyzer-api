#!/usr/bin/env python3
import requests
import json
import sys

# API credentials
API_URL = "https://web-analyzer-api.onrender.com"
API_KEY = "j75x+z5imUKNHIyLk7zTNSTF/juUlwf4"
SITE_ID = "thevou"

def test_bulk_endpoint():
    """Test the bulk processing endpoint"""
    url = f"{API_URL}/bulk/process"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Simple test content
    data = {
        "content_items": [
            {
                "content": "This is a test article about fashion. We're testing the bulk processing endpoint.",
                "title": "Test Article for Bulk Processing",
                "url": "https://example.com/test",
                "id": "test123"
            }
        ],
        "site_id": SITE_ID,
        "batch_size": 1,
        "knowledge_building": True
    }
    
    try:
        print(f"Testing bulk processing endpoint with URL: {url}")
        print(f"Using API Key: {API_KEY} for site ID: {SITE_ID}")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Bulk endpoint status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing bulk endpoint: {str(e)}")
        return False

def main():
    print("Testing Bulk Processing Endpoint...")
    
    # Test bulk endpoint
    print("\n=== Testing Bulk Processing Endpoint ===")
    bulk_ok = test_bulk_endpoint()
    
    # Summary
    print("\n=== Summary ===")
    print(f"Bulk processing endpoint: {'OK' if bulk_ok else 'FAILED'}")
    
    if bulk_ok:
        print("\nBulk Processing test PASSED!")
        return 0
    else:
        print("\nBulk Processing test FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())