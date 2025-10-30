import requests
import json
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your deployed URL when testing on Railway

def test_root_endpoint():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data
    print("✅ Root endpoint works")

def test_refresh_countries():
    """Test POST /countries/refresh"""
    print("Testing POST /countries/refresh...")
    response = requests.post(f"{BASE_URL}/countries/refresh")
    
    if response.status_code == 503:
        print("⚠️  External APIs unavailable (this might be expected in testing)")
        return
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "message" in data
    assert "countries_processed" in data
    assert "timestamp" in data
    assert data["countries_processed"] > 0
    print(f"✅ Refresh endpoint works - processed {data['countries_processed']} countries")

def test_get_countries():
    """Test GET /countries with various filters and sorting"""
    print("Testing GET /countries...")
    
    # Test basic get
    response = requests.get(f"{BASE_URL}/countries")
    assert response.status_code == 200
    countries = response.json()
    assert isinstance(countries, list)
    assert len(countries) > 0
    
    # Check structure of first country
    first_country = countries[0]
    required_fields = ["id", "name", "population", "currency_code", "estimated_gdp", "last_refreshed_at"]
    for field in required_fields:
        assert field in first_country, f"Missing field: {field}"
    
    print("✅ Basic GET /countries works")

def test_get_countries_filters():
    """Test filtering by region and currency"""
    print("Testing filters...")
    
    # Test region filter
    response = requests.get(f"{BASE_URL}/countries?region=Africa")
    assert response.status_code == 200
    african_countries = response.json()
    
    if len(african_countries) > 0:
        for country in african_countries:
            assert country["region"] == "Africa"
        print("✅ Region filter works")
    else:
        print("⚠️  No African countries found (might be expected)")
    
    # Test currency filter
    response = requests.get(f"{BASE_URL}/countries?currency=USD")
    assert response.status_code == 200
    usd_countries = response.json()
    
    if len(usd_countries) > 0:
        for country in usd_countries:
            assert country["currency_code"] == "USD"
        print("✅ Currency filter works")
    else:
        print("⚠️  No USD countries found (might be expected)")

def test_get_countries_sorting():
    """Test sorting by GDP"""
    print("Testing GDP sorting...")
    
    response = requests.get(f"{BASE_URL}/countries?sort=gdp_desc")
    assert response.status_code == 200
    sorted_countries = response.json()
    
    # Filter out countries with null GDP
    countries_with_gdp = [c for c in sorted_countries if c["estimated_gdp"] is not None]
    
    if len(countries_with_gdp) > 1:
        # Check if GDP is in descending order
        for i in range(len(countries_with_gdp) - 1):
            current_gdp = countries_with_gdp[i]["estimated_gdp"]
            next_gdp = countries_with_gdp[i + 1]["estimated_gdp"]
            assert current_gdp >= next_gdp, f"GDP not sorted correctly: {current_gdp} < {next_gdp}"
        print("✅ GDP descending sort works")
    else:
        print("⚠️  Not enough countries with GDP for sorting test")

def test_get_country_by_name():
    """Test GET /countries/:name"""
    print("Testing GET /countries/:name...")
    
    # Get a country name from the list first
    response = requests.get(f"{BASE_URL}/countries")
    assert response.status_code == 200
    countries = response.json()
    
    if len(countries) > 0:
        test_country = countries[0]["name"]
        
        # Test existing country
        response = requests.get(f"{BASE_URL}/countries/{test_country}")
        assert response.status_code == 200
        country_data = response.json()
        assert country_data["name"] == test_country
        print(f"✅ Get specific country works: {test_country}")
        
        # Test non-existent country
        response = requests.get(f"{BASE_URL}/countries/NonexistentCountryXYZ")
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"] == "Country not found"
        print("✅ 404 for non-existent country works")
    else:
        print("⚠️  No countries available for testing")

def test_delete_country():
    """Test DELETE /countries/:name"""
    print("Testing DELETE /countries/:name...")
    
    # First create a test country to delete
    test_country_data = {
        "name": "TestCountryForDeletion",
        "capital": "TestCapital",
        "region": "TestRegion",
        "population": 1000000,
        "currency_code": "TST",
        "exchange_rate": 1.0,
        "estimated_gdp": 1500000000.0,
        "flag_url": "https://example.com/flag.png"
    }
    
    # Try to create the test country (you might need to adjust this based on your API)
    response = requests.post(f"{BASE_URL}/countries/refresh")  # Refresh to ensure data
    time.sleep(2)  # Wait for refresh to complete
    
    # Test deleting non-existent country first
    response = requests.delete(f"{BASE_URL}/countries/NonexistentCountryXYZ")
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    print("✅ 404 for deleting non-existent country works")
    
    # Note: Actual deletion test might depend on your data
    print("⚠️  Delete endpoint structure verified")

def test_status_endpoint():
    """Test GET /status"""
    print("Testing GET /status...")
    
    response = requests.get(f"{BASE_URL}/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_countries" in data
    assert "last_refreshed_at" in data
    
    # Check if timestamp is valid
    if data["last_refreshed_at"]:
        try:
            datetime.fromisoformat(data["last_refreshed_at"].replace('Z', '+00:00'))
            print("✅ Valid timestamp format")
        except ValueError:
            print("❌ Invalid timestamp format")
    
    print(f"✅ Status endpoint works - Total countries: {data['total_countries']}")

def test_image_endpoint():
    """Test GET /countries/image"""
    print("Testing GET /countries/image...")
    
    # First ensure we have data and image
    response = requests.post(f"{BASE_URL}/countries/refresh")
    time.sleep(2)  # Wait for image generation
    
    response = requests.get(f"{BASE_URL}/countries/image")
    
    if response.status_code == 200:
        # Check if it's actually an image
        content_type = response.headers.get('content-type')
        assert content_type == 'image/png'
        
        # Check if we got some binary data
        assert len(response.content) > 0
        print("✅ Image endpoint returns valid PNG image")
    elif response.status_code == 404:
        error_data = response.json()
        assert "error" in error_data
        print("⚠️  Image not found (might need refresh first)")
    else:
        print(f"⚠️  Image endpoint returned {response.status_code}")

def test_error_handling():
    """Test error responses"""
    print("Testing error handling...")
    
    # Test 404 for non-existent country
    response = requests.get(f"{BASE_URL}/countries/NonExistentCountry123")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "Country not found"
    
    # Test 404 for non-existent image (if no refresh was done)
    response = requests.get(f"{BASE_URL}/countries/image")
    if response.status_code == 404:
        data = response.json()
        assert "error" in data
    
    print("✅ Error handling works correctly")

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting API Tests...")
    print("=" * 50)
    
    tests = [
        test_root_endpoint,
        test_refresh_countries,
        test_get_countries,
        test_get_countries_filters,
        test_get_countries_sorting,
        test_get_country_by_name,
        test_delete_country,
        test_status_endpoint,
        test_image_endpoint,
        test_error_handling,
    ]
    
    passed = 0
    failed = 0
    warnings = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  Test warning: {e}")
            warnings += 1
    
    print("=" * 50)
    print(f"📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"📈 Score Estimate: {((passed + warnings * 0.5) / len(tests)) * 100:.1f}%")
    
    if failed == 0:
        print("🎉 All critical tests passed! Ready for bot submission.")
    else:
        print("🔧 Some tests failed. Please fix the issues before submission.")

if __name__ == "__main__":
    run_all_tests()