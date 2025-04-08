#!/usr/bin/env python3
"""Simple script to test the new API key"""
import requests
import time

API_URL = "https://web-analyzer-api.onrender.com"
API_KEY = "development_key_only_for_testing"
SITE_ID = "thevou_new"

def test_auth():
    print(f"Testing auth with new API key: {API_KEY}")
    
    # Test bulk/jobs endpoint
    response = requests.get(
        f"{API_URL}/bulk/jobs?site_id={SITE_ID}",
        headers={"X-API-Key": API_KEY},
        timeout=15
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Test analyze/content endpoint
    if response.status_code == 200:
        print("\nTesting analyze/content endpoint...")
        test_data = {
            "content": "This is a test content.",
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
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:100]}...")

if __name__ == "__main__":
    test_auth()