import requests
import json

BASE_URL = "http://localhost:8000"

def test_local_api():
    """Test the API with local SQLite database"""
    print("🧪 Testing API with local SQLite database...")
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    print(f"✅ Root endpoint: {response.status_code}")
    
    # Test refresh endpoint
    print("🔄 Testing refresh endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/countries/refresh")
        print(f"✅ Refresh endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Processed {data['countries_processed']} countries")
    except Exception as e:
        print(f"❌ Refresh failed: {e}")
    
    # Test get countries
    response = requests.get(f"{BASE_URL}/countries")
    print(f"✅ Get countries: {response.status_code}")
    
    # Test status endpoint
    response = requests.get(f"{BASE_URL}/status")
    print(f"✅ Status endpoint: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total countries: {data['total_countries']}")
    
    print("🎉 Local API testing complete!")

if __name__ == "__main__":
    test_local_api()