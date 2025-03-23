import requests
import json
import time
from datetime import datetime

def test_api_health(api_url, api_key):
    """Test the API health endpoint"""
    headers = {"X-API-Key": api_key}
    
    try:
        print(f"Testing connection to {api_url}/health...")
        response = requests.get(f"{api_url}/health", headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("status") == "ok":
                print("\n✅ API health check successful!")
                return True
            else:
                print("\n❌ API returned unexpected response.")
                return False
        else:
            print("\n❌ API health check failed.")
            return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def test_analyze_endpoint(api_url, api_key, site_id):
    """Test the content analysis endpoint with a sample request"""
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    sample_data = {
        "content": "Old money aesthetic is a popular fashion style among young men. It reflects a classic, timeless approach to dressing that emphasizes quality over trends. Men with an inverted triangle body shape often look good in this style, especially when wearing true spring colors.",
        "title": "Test Fashion Content",
        "site_id": site_id
    }
    
    try:
        print(f"\nTesting content analysis endpoint {api_url}/analyze/content...")
        start_time = time.time()
        response = requests.post(
            f"{api_url}/analyze/content", 
            headers=headers, 
            json=sample_data, 
            timeout=30
        )
        end_time = time.time()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print condensed version of the response
            print(f"\nReceived {len(data.get('link_suggestions', []))} link suggestions")
            print(f"Processing time: {data.get('processing_time', 0):.2f} seconds")
            print(f"Status: {data.get('status', 'unknown')}")
            
            if data.get("status") == "success" and len(data.get("link_suggestions", [])) > 0:
                print("\n✅ Content analysis successful!")
                
                # Print first suggestion as example
                if data.get("link_suggestions"):
                    suggestion = data["link_suggestions"][0]
                    print("\nSample suggestion:")
                    print(f"Anchor text: {suggestion.get('anchor_text')}")
                    print(f"Target URL: {suggestion.get('target_url')}")
                    print(f"Confidence: {suggestion.get('confidence')}")
                
                return True
            else:
                print("\n⚠️ Analysis completed but no suggestions found or unexpected status.")
                return False
        else:
            print("\n❌ Content analysis request failed.")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    api_url = "https://web-analyzer-api.onrender.com"  # No trailing slash
    api_key = "thevou_production_key_12345"  # Replace with actual key if needed
    site_id = "thevou"
    
    print(f"=== Web Analyzer API Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    # Test health endpoint
    health_ok = test_api_health(api_url, api_key)
    
    # Test analyze endpoint if health check passes
    if health_ok:
        test_analyze_endpoint(api_url, api_key, site_id)
    
    print("\n=== Test Complete ===")