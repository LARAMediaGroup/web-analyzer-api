#!/usr/bin/env python3
"""Script to check what's in the site_credentials.json file"""
import requests

def check_credentials():
    API_URL = "https://web-analyzer-api.onrender.com"
    API_KEY = "development_key_only_for_testing"
    
    # Make a simple GET request to test the API
    response = requests.get(
        f"{API_URL}/health",
        headers={"X-API-Key": API_KEY},
        timeout=15
    )
    
    print(f"Health check status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # This endpoint doesn't exist, but the error message might contain useful information
    response = requests.get(
        f"{API_URL}/debug/credentials",
        headers={"X-API-Key": API_KEY},
        timeout=15
    )
    
    print(f"\nCredentials debug status code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    check_credentials()