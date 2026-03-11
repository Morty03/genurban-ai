import requests
import json

BASE_URL = "http://localhost:8001"

def test_all_correct_endpoints():
    """Test all endpoints with their correct paths"""
    print("🎯 Testing All Endpoints with Correct Paths")
    print("=" * 60)
    
    endpoints = [
        # Basic endpoints
        ("GET", "/", "Root"),
        ("GET", "/health", "Health Check"),
        ("GET", "/test", "Test Endpoint"),
        ("GET", "/api", "API Info"),
        
        # Places endpoints - CORRECT PATHS
        ("GET", "/api/v1/api/search-location?query=Delhi&limit=3", "Location Search"),
        ("GET", "/api/v1/api/india-boundaries", "India Boundaries"),
        ("POST", "/api/v1/api/analyze-urban-morphology", "Urban Analysis"),
        ("GET", "/api/v1/api/reverse-geocode?lat=28.6139&lng=77.2090", "Reverse Geocode"),
        
        # ML endpoints
        ("GET", "/api/v1/model-info", "Model Info"),
        ("GET", "/api/v1/feature-importance", "Feature Importance"),
        ("POST", "/api/v1/urban-growth", "Urban Growth Prediction"),
        ("POST", "/api/v1/batch-urban-growth", "Batch Prediction"),
        
        # Scenario endpoints
        ("GET", "/api/v1/definitions", "Scenario Definitions"),
        ("GET", "/api/v1/list", "Scenario List"),
        ("POST", "/api/v1/simulate", "Climate Scenario"),
        
        # Generation endpoints
        ("POST", "/api/v1/from_noise", "AI Generation"),
        ("POST", "/api/v1/urban-morphology", "Urban Generation"),
    ]
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                # Add appropriate data for POST requests
                data = {}
                if "analyze-urban" in endpoint:
                    data = {"lat": 28.6139, "lng": 77.2090, "years": 3}
                elif "urban-growth" in endpoint:
                    data = {"lat": 28.6139, "lng": 77.2090, "years": 5, "scenario": "moderate"}
                elif "simulate" in endpoint:
                    data = {"lat": 28.6139, "lng": 77.2090, "base_year": 2024, "target_year": 2030, "scenario_type": "moderate"}
                elif "urban-morphology" in endpoint:
                    data = {"lat": 28.6139, "lng": 77.2090, "n_samples": 1, "scenario_type": "moderate", "target_year": 2030}
                elif "from_noise" in endpoint:
                    data = {"n_samples": 1, "store": False}
                
                response = requests.post(f"{BASE_URL}{endpoint}", json=data)
            
            status_emoji = "✅" if response.status_code == 200 else "⚠️" if response.status_code < 500 else "❌"
            print(f"{status_emoji} {description}: {response.status_code}")
            
            # Show response for successful endpoints
            if response.status_code == 200 and any(x in description for x in ["Search", "Analysis", "Prediction"]):
                data = response.json()
                if "search" in endpoint.lower():
                    locations = data if isinstance(data, list) else data.get('results', [])
                    print(f"   📍 Found {len(locations)} locations")
                elif "analyze" in endpoint.lower():
                    urban_data = data.get('data', {})
                    print(f"   📊 Urban Density: {urban_data.get('urban_density', {}).get('mean', 'N/A')}")
                elif "growth" in endpoint.lower():
                    print(f"   📈 Growth: {data.get('growth_percentage', 'N/A')}%")
                    
        except Exception as e:
            print(f"❌ {description}: ERROR - {e}")

def test_urban_analysis_detailed():
    """Test urban analysis with detailed output"""
    print("\n🏙️ Detailed Urban Analysis Test")
    print("=" * 40)
    
    analysis_data = {
        "lat": 28.6139,  # Delhi
        "lng": 77.2090,
        "years": 3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/api/analyze-urban-morphology",
            json=analysis_data
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            
            print("✅ Urban Analysis Successful!")
            print(f"   📍 Location: {data.get('location', {})}")
            print(f"   📊 Urban Density: {data.get('urban_density', {}).get('mean', 'N/A')}")
            print(f"   🌿 Vegetation Cover: {data.get('vegetation_cover', {}).get('mean', 'N/A')}")
            print(f"   🏢 Built-up Area: {data.get('built_up_area', {}).get('mean', 'N/A')}")
            
            if 'climate_risk' in data:
                climate = data['climate_risk']
                print(f"   🌡️ Climate Risk: {climate.get('composite_risk_score', {}).get('risk_level', 'N/A')}")
                
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")

def test_location_search_detailed():
    """Test location search with detailed output"""
    print("\n📍 Detailed Location Search Test")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/api/search-location?query=Bangalore&limit=5")
        
        if response.status_code == 200:
            locations = response.json()
            print(f"✅ Found {len(locations)} locations:")
            
            for i, loc in enumerate(locations[:3], 1):
                print(f"   {i}. {loc.get('name', 'N/A')} - {loc.get('lat', 'N/A')}, {loc.get('lng', 'N/A')}")
                print(f"      📍 {loc.get('address', 'N/A')}")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Search error: {e}")

if __name__ == "__main__":
    print("🚀 GENURBAN API - Testing with Correct Paths")
    print("=" * 60)
    
    test_all_correct_endpoints()
    test_urban_analysis_detailed()
    test_location_search_detailed()
    
    print("\n" + "=" * 60)
    print("🎉 Testing Complete!")
    print("📖 API Documentation: http://localhost:8001/docs")