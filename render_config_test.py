import requests
import time

def test_api_key(api_url, api_key, site_id):
    """Test if the API accepts a specific key and site ID combination"""
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Use a minimal content request
    test_data = {
        "content": "This is a test.",
        "title": "API Key Test",
        "site_id": site_id
    }
    
    print(f"Testing API key '{api_key}' with site ID '{site_id}'...")
    
    try:
        response = requests.post(
            f"{api_url}/analyze/content",
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key accepted!")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed: Invalid API key")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Raw response: {response.text}")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Raw response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    # The base URL for the API
    api_url = "https://web-analyzer-api.onrender.com"
    
    # Test with the original placeholder key
    original_key = "thevou_production_key_12345"
    test_api_key(api_url, original_key, "thevou")
    
    print("\n" + "-"*40 + "\n")
    
    # Test with the new key we tried to update to
    new_key = "u1HG8J0uUenblA7KJuUhVlTX"
    test_api_key(api_url, new_key, "thevou")
    
    print("\n" + "-"*40 + "\n")
    
    # Test with the development key
    dev_key = "development_key_only_for_testing"
    test_api_key(api_url, dev_key, "default")
    
    print("\nTests complete.")