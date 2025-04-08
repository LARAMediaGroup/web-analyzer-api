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

def test_key(key_name, key_value):
    print(f"\nTesting {key_name} key...")
    print(f"Key value: {key_value}")
    
    try:
        response = requests.get(
            f"{API_URL}/health",
            headers={"X-API-Key": key_value},
            timeout=15
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    print(f"Testing API keys at {datetime.now()}")
    print(f"API URL: {API_URL}")
    
    results = {}
    for key_name, key_value in KEYS.items():
        results[key_name] = test_key(key_name, key_value)
    
    print("\n=== Summary ===")
    for key_name, success in results.items():
        print(f"{key_name}: {'OK' if success else 'FAILED'}")

if __name__ == "__main__":
    main() 