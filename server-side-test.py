#!/usr/bin/env python3
"""
Server-side test for API key validation
This script tests whether the API key is being properly validated
"""

import requests
import json
import base64

# API credentials
API_URL = "https://web-analyzer-api.onrender.com"
SITE_ID = "thevou"

# Keys to test
KEYS = {
    "Current Render Key": "rnd_j4XBsK41N71qzDIy7Q7x7kFIyWLX",
    "Old Key": "j75x+z5imUKNHIyLk7zTNSTF/juUlwf4",
    "Previous Key": "u1HG8J0uUenblA7KJuUhVlTX",
    "Development Key": "development_key_only_for_testing"
}

def test_api_key(key_label, api_key):
    """Test a single API key against multiple endpoints"""
    print(f"\nTESTING: {key_label} - {api_key}")
    print("-" * 50)
    
    # 1. Test health endpoint
    print("1. Health Endpoint Test:")
    try:
        response = requests.get(
            f"{API_URL}/health",
            headers={"X-API-Key": api_key},
            timeout=15
        )
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # 2. Test bulk/jobs endpoint (requires auth)
    print("\n2. Auth Endpoint Test (bulk/jobs):")
    try:
        response = requests.get(
            f"{API_URL}/bulk/jobs",
            headers={"X-API-Key": api_key},
            timeout=15
        )
        print(f"   Status Code: {response.status_code}")
        response_text = response.text
        if len(response_text) > 100:
            response_text = response_text[:100] + "..."
        print(f"   Response: {response_text}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # 3. Test analyze/content endpoint
    print("\n3. Content Analysis Test:")
    data = {
        "content": "This is a test content for API key validation.",
        "title": "API Key Test",
        "site_id": SITE_ID,
        "url": "https://example.com/test"
    }
    try:
        response = requests.post(
            f"{API_URL}/analyze/content",
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            json=data,
            timeout=30
        )
        print(f"   Status Code: {response.status_code}")
        response_text = response.text
        if len(response_text) > 100:
            response_text = response_text[:100] + "..."
        print(f"   Response: {response_text}")
    except Exception as e:
        print(f"   Error: {str(e)}")

def main():
    """Test all API keys"""
    print("WEB ANALYZER SERVER-SIDE API KEY TEST")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print(f"Site ID: {SITE_ID}")
    
    # Test each key
    for label, key in KEYS.items():
        test_api_key(label, key)
    
    # Special Base64 test
    print("\nSPECIAL BASE64 DECODE TEST")
    print("=" * 50)
    
    # Try to decode the key as Base64
    key = KEYS["Old Key"]
    try:
        # Fix padding if needed
        padded_key = key
        padding = len(padded_key) % 4
        if padding:
            padded_key += '=' * (4 - padding)
        
        # Try standard Base64
        decoded = base64.b64decode(padded_key)
        print(f"Base64 decoded value: {decoded}")
        
        # Try URL-safe Base64
        safe_key = key.replace('+', '-').replace('/', '_')
        decoded = base64.urlsafe_b64decode(safe_key + '==')
        print(f"URL-safe Base64 decoded value: {decoded}")
    except Exception as e:
        print(f"Error decoding as Base64: {str(e)}")
    
    # Test header inspection
    print("\nHTTP HEADER INSPECTION")
    print("=" * 50)
    try:
        response = requests.get(
            f"{API_URL}/bulk/jobs",
            headers={"X-API-Key": KEYS["Current Render Key"]},
            timeout=15
        )
        print(f"Request Headers: {response.request.headers}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {response.headers}")
    except Exception as e:
        print(f"Error in header inspection: {str(e)}")

if __name__ == "__main__":
    main()