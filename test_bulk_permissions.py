#!/usr/bin/env python3
import requests
import json
from datetime import datetime

API_URL = "https://web-analyzer-api.onrender.com"

# Test keys
KEYS = {
    "production": "p6fHDUXqGRgV4SNIXrxLG-Z01TVXVjtIk5ODiMmj6F8",
    "new_test": "thevou_api_key_2025_03_24",
    "development": "development_key_only_for_testing"
}

def test_bulk_permissions(key_name, key_value):
    print(f"\nTesting {key_name} key for bulk processing...")
    print(f"Key value: {key_value}")
    
    # Test data
    data = {
        "content_items": [
            {
                "content": "This is a test article about fashion trends.",
                "title": "Test Article",
                "url": "https://thevou.com/test",
                "id": "test123"
            }
        ],
        "site_id": "thevou",
        "batch_size": 1,
        "knowledge_building": True
    }
    
    try:
        response = requests.post(
            f"{API_URL}/bulk/process",
            headers={
                "X-API-Key": key_value,
                "Content-Type": "application/json"
            },
            json=data,
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    print(f"Testing bulk processing permissions at {datetime.now()}")
    print(f"API URL: {API_URL}")
    
    results = {}
    for key_name, key_value in KEYS.items():
        results[key_name] = test_bulk_permissions(key_name, key_value)
    
    print("\n=== Summary ===")
    for key_name, success in results.items():
        print(f"{key_name}: {'OK' if success else 'FAILED'}")

if __name__ == "__main__":
    main() 