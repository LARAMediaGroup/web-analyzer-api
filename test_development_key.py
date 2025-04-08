#!/usr/bin/env python3
"""Simple script to test the development key"""
import requests

API_URL = "https://web-analyzer-api.onrender.com"
API_KEY = "development_key_only_for_testing"

def test_auth():
    print(f"Testing auth with development key: {API_KEY}")
    
    # Test bulk/jobs endpoint
    response = requests.get(
        f"{API_URL}/bulk/jobs",
        headers={"X-API-Key": API_KEY},
        timeout=15
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.text}")

if __name__ == "__main__":
    test_auth()