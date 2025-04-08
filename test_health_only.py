#!/usr/bin/env python3
import requests

# Health check only (no auth required)
url = "https://web-analyzer-api.onrender.com/health"
print(f"Testing health endpoint: {url}")

try:
    response = requests.get(url, timeout=10)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    print("Health check successful!")
except Exception as e:
    print(f"Error: {e}")