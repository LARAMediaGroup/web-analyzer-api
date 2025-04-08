#!/usr/bin/env python3
"""Script to check what API keys are currently cached"""
import requests

def test_simple_keys():
    """Test various simple key formats to see if any of them work"""
    API_URL = "https://web-analyzer-api.onrender.com"
    
    # List of keys to try
    keys = [
        "development_key_only_for_testing",
        "development_key_thevou",
        "thevou_api_key_2025_03_24",
        "default_api_key",
        "thevou",
        "thevou_key"
    ]
    
    # Site IDs to try
    site_ids = [
        "default",
        "thevou",
        "thevou_new",
        "testsite"
    ]
    
    # First test all keys without site_id
    print("TESTING KEYS WITHOUT SITE_ID:")
    for key in keys:
        print(f"\nTesting key: {key}")
        
        response = requests.get(
            f"{API_URL}/bulk/jobs",
            headers={"X-API-Key": key},
            timeout=15
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: This key works!")
            print(f"Response body: {response.text}")
        else:
            print(f"Response body: {response.text}")
    
    # Now test development key with all site IDs
    print("\n\nTESTING DEVELOPMENT KEY WITH DIFFERENT SITE_IDs:")
    for site_id in site_ids:
        print(f"\nTesting site_id: {site_id}")
        
        response = requests.get(
            f"{API_URL}/bulk/jobs?site_id={site_id}",
            headers={"X-API-Key": "development_key_only_for_testing"},
            timeout=15
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: This site_id works!")
            print(f"Response body: {response.text}")
        else:
            print(f"Response body: {response.text}")

if __name__ == "__main__":
    test_simple_keys()