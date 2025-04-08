#!/usr/bin/env python3
import requests
import json
import sys

# API credentials
API_URL = "https://web-analyzer-api.onrender.com"
API_KEY = "development_key_only_for_testing"
SITE_ID = "thevou_new"

def test_knowledge_stats():
    """Test the knowledge database stats endpoint"""
    url = f"{API_URL}/knowledge/stats?site_id={SITE_ID}"
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Knowledge stats endpoint status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing knowledge stats endpoint: {str(e)}")
        return False

def main():
    print("Testing Knowledge Database API...")
    
    # Test knowledge stats endpoint
    print("\n=== Testing Knowledge Database Stats Endpoint ===")
    stats_ok = test_knowledge_stats()
    
    # Summary
    print("\n=== Summary ===")
    print(f"Knowledge stats endpoint: {'OK' if stats_ok else 'FAILED'}")
    
    if stats_ok:
        print("\nKnowledge Database API test PASSED!")
        return 0
    else:
        print("\nKnowledge Database API test FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())