import requests
import json
import time

def test_specific_fashion_content():
    url = "http://localhost:8000/analyze/content"
    
    payload = {
        "content": """
        The preppy style for men originated from the Ivy League universities in the northeastern United States. 
        This classic look is characterised by oxford shirts, navy blazers, and penny loafers that create an effortlessly 
        polished appearance. Unlike more casual fashion trends, the preppy style for gentlemen emphasizes quality materials and 
        traditional silhouettes.

        A true spring colour palette is perfect for men who have warm undertones in their skin. 
        These vibrant, clear colours include warm greens, bright yellows, and coral hues that enhance 
        natural colouring. Colour analysis for men can significantly improve your wardrobe choices by ensuring
        every item complements your natural features.

        Men with an inverted triangle body shape, characterised by broad shoulders and a narrower waist, 
        should focus their styling on balancing proportions. Choosing tailored blazers with structured
        shoulders can create a more harmonious silhouette for these gentlemen.
        
        How to style oxford shirts for different occasions remains an essential skill for the modern gentleman.
        These versatile shirts can be dressed up with a tailored suit for formal settings or paired with
        chino trousers for a smart-casual look that works well in most social situations.
        """,
        "title": "Men's Complete Fashion Guide: Body Shapes and Colour Analysis",
        "url": "https://example.com/test-article",
        "site_id": "test-site"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    print(f"Analyze content status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Waiting 2 seconds for the server to start...")
    time.sleep(2)
    
    try:
        test_specific_fashion_content()
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        print("Make sure the API server is running (python run_local.py)")