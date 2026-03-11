from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize geocoder
geolocator = Nominatim(user_agent="genurban_app")

class LocationRequest(BaseModel):
    lat: float
    lng: float
    years: int = 5

class LocationSearchResponse(BaseModel):
    name: str
    lat: float
    lng: float
    address: str
    importance: Optional[float] = None

class UrbanMorphologyResponse(BaseModel):
    status: str
    data: Dict
    title: str
    location_info: Dict

# FIXED: Removed duplicate /api from route paths
@router.get("/search-location", response_model=List[LocationSearchResponse])
async def search_location(
    query: str = Query(..., description="Location name to search within India"),
    limit: int = Query(5, description="Number of results to return")
):
    """Search for locations within India"""
    try:
        if not query or len(query.strip()) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters long")
        
        locations = geolocator.geocode(
            f"{query}, India", 
            exactly_one=False,
            limit=limit,
            addressdetails=True
        )
        
        if not locations:
            return []
        
        results = []
        for location in locations:
            # Ensure location is in India
            address = location.raw.get('address', {})
            country = address.get('country', '').lower()
            
            if 'india' in country or not country:  # Sometimes country is not returned
                results.append(LocationSearchResponse(
                    name=address.get('city') or address.get('town') or address.get('village') or location.address.split(',')[0],
                    lat=location.latitude,
                    lng=location.longitude,
                    address=location.address,
                    importance=location.raw.get('importance')
                ))
        
        # Sort by importance if available
        results.sort(key=lambda x: x.importance or 0, reverse=True)
        
        logger.info(f"📍 Location search: '{query}' found {len(results)} results")
        return results[:limit]
        
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.error(f"Geocoding service error: {e}")
        raise HTTPException(status_code=503, detail="Location service temporarily unavailable")
    except Exception as e:
        logger.error(f"Location search error: {e}")
        raise HTTPException(status_code=500, detail=f"Location search failed: {str(e)}")

# FIXED: Removed duplicate /api
@router.get("/reverse-geocode")
async def reverse_geocode(lat: float = Query(...), lng: float = Query(...)):
    """Get location name from coordinates"""
    try:
        # Validate Indian coordinates first
        if not (8.0 <= lat <= 37.0 and 68.0 <= lng <= 97.0):
            raise HTTPException(status_code=400, detail="Coordinates must be within India")
        
        location = geolocator.reverse(f"{lat}, {lng}", exactly_one=True, language='en')
        
        if not location:
            return {"address": "Unknown location in India"}
        
        address = location.raw.get('address', {})
        return {
            "name": address.get('city') or address.get('town') or address.get('village') or location.address.split(',')[0],
            "address": location.address,
            "details": address
        }
        
    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        raise HTTPException(status_code=500, detail=f"Reverse geocoding failed: {str(e)}")

# FIXED: Removed duplicate /api
@router.post("/analyze-urban-morphology", response_model=UrbanMorphologyResponse)
async def analyze_urban_morphology(request: LocationRequest):
    """API endpoint for urban morphology analysis"""
    try:
        # Validate Indian coordinates
        if not (8.0 <= request.lat <= 37.0 and 68.0 <= request.lng <= 97.0):
            raise HTTPException(
                status_code=400, 
                detail="Location must be within India (Latitude: 8°-37°N, Longitude: 68°-97°E)"
            )
        
        # Validate years parameter
        if not (1 <= request.years <= 10):
            raise HTTPException(
                status_code=400,
                detail="Years must be between 1 and 10"
            )
        
        logger.info(f"🏙️ Starting urban morphology analysis for {request.lat}, {request.lng} ({request.years} years)")
        
        # Get location name for better response
        location_name = await reverse_geocode(request.lat, request.lng)
        
        # TODO: Import and use the GEE fetcher - for now return mock data
        urban_data = await get_mock_urban_data(request.lat, request.lng, request.years)
        
        # Enhance response with interpretation
        enhanced_data = await enhance_urban_interpretation(urban_data)
        
        response = UrbanMorphologyResponse(
            status="success",
            data=enhanced_data,
            title="Generative Satellite Vision for Simulating Future Urban Morphology Under Climate Pressure",
            location_info=location_name
        )
        
        logger.info(f"✅ Urban morphology analysis completed for {location_name.get('name', 'unknown location')}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Urban morphology analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Urban analysis failed: {str(e)}")

# FIXED: Removed duplicate /api
@router.get("/india-boundaries")
async def get_india_boundaries():
    """Get approximate India boundaries for frontend map"""
    return {
        "bounds": {
            "north": 37.0,
            "south": 8.0,
            "east": 97.0,
            "west": 68.0
        },
        "center": {
            "lat": 20.5937,
            "lng": 78.9629
        },
        "major_cities": [
            {"name": "Delhi", "lat": 28.6139, "lng": 77.2090},
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
            {"name": "Bangalore", "lat": 12.9716, "lng": 77.5946},
            {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
            {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639},
            {"name": "Hyderabad", "lat": 17.3850, "lng": 78.4867}
        ]
    }

# FIXED: Added mock data function since GEE fetcher might not be available yet
async def get_mock_urban_data(lat: float, lng: float, years: int) -> Dict:
    """Mock urban data for testing until GEE fetcher is ready"""
    import random
    return {
        'urban_density': {
            'mean': random.uniform(0.1, 0.8),
            'std': random.uniform(0.05, 0.2),
            'trend': random.uniform(-0.1, 0.3)
        },
        'vegetation_cover': {
            'mean': random.uniform(0.1, 0.7),
            'std': random.uniform(0.05, 0.15),
            'trend': random.uniform(-0.2, 0.1)
        },
        'built_up_area': {
            'mean': random.uniform(0.2, 0.9),
            'std': random.uniform(0.1, 0.3),
            'trend': random.uniform(0.0, 0.4)
        }
    }

async def enhance_urban_interpretation(urban_data: Dict) -> Dict:
    """Enhance raw urban data with human-readable interpretations"""
    try:
        urban_mean = urban_data['urban_density']['mean']
        vegetation_mean = urban_data['vegetation_cover']['mean']
        built_up_mean = urban_data['built_up_area']['mean']
        
        # Urban density interpretation
        if urban_mean > 0.3:
            urban_level = "High Urban Density"
            urban_description = "Densely built-up urban area with limited green spaces"
        elif urban_mean > 0.1:
            urban_level = "Medium Urban Density" 
            urban_description = "Moderate urban development with mixed land use"
        else:
            urban_level = "Low Urban Density"
            urban_description = "Mostly rural or peri-urban area with significant green cover"
        
        # Vegetation interpretation
        if vegetation_mean > 0.5:
            vegetation_level = "High Vegetation"
            vegetation_description = "Abundant green spaces and vegetation cover"
        elif vegetation_mean > 0.2:
            vegetation_level = "Medium Vegetation"
            vegetation_description = "Moderate vegetation with urban green spaces"
        else:
            vegetation_level = "Low Vegetation"
            vegetation_description = "Limited vegetation, predominantly built environment"
        
        return {
            **urban_data,
            "interpretation": {
                "urban_density": {
                    "level": urban_level,
                    "description": urban_description,
                    "score": urban_mean
                },
                "vegetation_cover": {
                    "level": vegetation_level,
                    "description": vegetation_description,
                    "score": vegetation_mean
                },
                "built_up_area": {
                    "score": built_up_mean,
                    "description": "Built-up and impervious surfaces"
                },
                "recommendations": generate_recommendations(urban_mean, vegetation_mean)
            }
        }
    except Exception as e:
        logger.warning(f"Interpretation enhancement failed: {e}")
        return urban_data

def generate_recommendations(urban_score: float, vegetation_score: float) -> List[str]:
    """Generate urban planning recommendations"""
    recommendations = []
    
    if urban_score > 0.3 and vegetation_score < 0.2:
        recommendations.extend([
            "Consider green infrastructure development",
            "Explore urban greening strategies",
            "Assess heat island mitigation options"
        ])
    elif vegetation_score > 0.5:
        recommendations.extend([
            "Maintain existing green corridors",
            "Protect natural vegetation from urban expansion",
            "Consider sustainable development practices"
        ])
    else:
        recommendations.extend([
            "Monitor urban growth patterns",
            "Plan for balanced development",
            "Consider mixed-use zoning strategies"
        ])
    
    return recommendations

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Urban Morphology API",
        "geocoder_ready": True
    }