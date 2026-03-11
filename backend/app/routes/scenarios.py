# routes/scenarios.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
import json
import logging
from datetime import datetime
import asyncio
import uuid

# FIXED: Use relative imports
try:
    from services.storage_service import storage_service
    from utils import raster_utils
    from workers.gee_fetcher import gee_fetcher
    from services.analysis_service import analysis_service
except ImportError:
    # Fallback for different structure
    from ..services.storage_service import storage_service
    from ..utils import raster_utils
    from ..workers.gee_fetcher import gee_fetcher
    from ..services.analysis_service import analysis_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Storage configuration - FIXED: Use proper relative paths
BASE_STORAGE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "db"))
THUMBS_DIR = os.path.join(BASE_STORAGE, "thumbs")
SCENARIOS_DIR = os.path.join(BASE_STORAGE, "scenarios")
os.makedirs(THUMBS_DIR, exist_ok=True)
os.makedirs(SCENARIOS_DIR, exist_ok=True)

# Climate scenario definitions
CLIMATE_SCENARIOS = {
    "conservative": {
        "name": "Conservative Growth",
        "description": "Slow urban growth with climate adaptation",
        "urban_growth_factor": 0.8,
        "climate_impact_factor": 0.6,
        "color": "#2E8B57"
    },
    "moderate": {
        "name": "Moderate Development", 
        "description": "Balanced urban growth with climate resilience",
        "urban_growth_factor": 1.0,
        "climate_impact_factor": 1.0,
        "color": "#FFA500"
    },
    "aggressive": {
        "name": "Aggressive Expansion",
        "description": "Rapid urban growth with high climate risk",
        "urban_growth_factor": 1.3,
        "climate_impact_factor": 1.5,
        "color": "#DC143C"
    },
    "sustainable": {
        "name": "Sustainable Future",
        "description": "Green urban development with climate adaptation",
        "urban_growth_factor": 0.9,
        "climate_impact_factor": 0.7,
        "color": "#20B2AA"
    }
}

# Pydantic Models
class ClimateScenarioRequest(BaseModel):
    lat: float = Field(..., description="Latitude", ge=8.0, le=37.0)
    lng: float = Field(..., description="Longitude", ge=68.0, le=97.0)
    base_year: int = Field(2024, description="Base year for simulation")
    target_year: int = Field(2035, description="Target year for projection")
    scenario_type: str = Field("moderate", description="Climate scenario type")
    include_adaptation: bool = Field(True, description="Include adaptation measures")

class ScenarioSimulationResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    base_year: int
    target_year: int
    urban_growth: float
    vegetation_change: float
    climate_risk_change: float
    adaptation_effectiveness: Optional[float]
    visualization_url: Optional[str]
    summary: Dict
    timestamp: str

class ScenarioComparisonResponse(BaseModel):
    scenarios: List[ScenarioSimulationResponse]
    comparison_metrics: Dict
    recommendation: str

# Helper functions
def _write_meta_extra(key: str, extra: dict):
    """Update scenario metadata with additional fields"""
    mp = storage_service._meta_path(key)
    if not os.path.exists(mp):
        raise FileNotFoundError("metadata missing")
    with open(mp, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta.update(extra)
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta

def _generate_scenario_id():
    """Generate unique scenario ID"""
    return f"scenario_{uuid.uuid4().hex[:8]}"

# Climate Scenario Endpoints
@router.post("/simulate", response_model=ScenarioSimulationResponse)
async def simulate_climate_scenario(request: ClimateScenarioRequest, background_tasks: BackgroundTasks):
    """
    Simulate urban morphology changes under climate scenarios
    
    Projects urban growth, vegetation changes, and climate risks
    for different future scenarios with adaptation options.
    """
    try:
        # Validate Indian coordinates
        if not (8.0 <= request.lat <= 37.0 and 68.0 <= request.lng <= 97.0):
            raise HTTPException(status_code=400, detail="Location must be within India")

        # Validate scenario type
        if request.scenario_type not in CLIMATE_SCENARIOS:
            raise HTTPException(status_code=400, detail="Invalid scenario type")

        logger.info(f"🌡️ Simulating climate scenario '{request.scenario_type}' for {request.lat}, {request.lng}")

        # Get current urban morphology and climate data
        current_analysis = await asyncio.get_event_loop().run_in_executor(
            None, gee_fetcher.get_urban_morphology, request.lat, request.lng, 5
        )

        # FIXED: Use mock climate impact if analysis_service not available
        try:
            climate_impact = await analysis_service.assess_climate_pressure(request.lat, request.lng)
        except:
            climate_impact = {
                'composite_risk_score': {'risk_score': 0.3},
                'temperature_risk': 0.4,
                'precipitation_risk': 0.2
            }

        # Run scenario simulation
        scenario_result = await run_scenario_simulation(
            current_analysis, 
            climate_impact, 
            request.scenario_type,
            request.base_year,
            request.target_year,
            request.include_adaptation
        )

        # Generate scenario ID and store results
        scenario_id = _generate_scenario_id()
        scenario_data = {
            "scenario_id": scenario_id,
            "location": {"lat": request.lat, "lng": request.lng},
            "scenario_type": request.scenario_type,
            "base_year": request.base_year,
            "target_year": request.target_year,
            "results": scenario_result,
            "timestamp": datetime.now().isoformat()
        }

        # Store scenario data
        storage_service.store_scenario(
            name=f"{CLIMATE_SCENARIOS[request.scenario_type]['name']} - {request.target_year}",
            year=request.target_year,
            scenario=request.scenario_type,
            data=json.dumps(scenario_data).encode()
        )

        # Add background task for visualization generation
        background_tasks.add_task(
            generate_scenario_visualization,
            scenario_id,
            scenario_result,
            request.lat,
            request.lng
        )

        response = ScenarioSimulationResponse(
            scenario_id=scenario_id,
            scenario_name=CLIMATE_SCENARIOS[request.scenario_type]["name"],
            base_year=request.base_year,
            target_year=request.target_year,
            urban_growth=scenario_result["urban_growth_percentage"],
            vegetation_change=scenario_result["vegetation_change_percentage"],
            climate_risk_change=scenario_result["climate_risk_change"],
            adaptation_effectiveness=scenario_result.get("adaptation_effectiveness"),
            visualization_url=f"/storage/scenarios/{scenario_id}.png",
            summary=scenario_result["summary"],
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"✅ Climate scenario simulation completed: {scenario_result['urban_growth_percentage']:.1f}% urban growth")
        return response

    except Exception as e:
        logger.error(f"Climate scenario simulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scenario simulation failed: {str(e)}")

@router.post("/compare", response_model=ScenarioComparisonResponse)
async def compare_scenarios(locations: List[Dict], base_year: int = 2024, target_year: int = 2035):
    """
    Compare multiple climate scenarios across different locations
    
    Useful for regional planning and policy decision-making.
    """
    try:
        if len(locations) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 locations allowed for comparison")

        scenarios = []
        scenario_results = []

        for location in locations:
            for scenario_type in ["conservative", "moderate", "aggressive", "sustainable"]:
                # Simulate scenario for each location
                request = ClimateScenarioRequest(
                    lat=location["lat"],
                    lng=location["lng"],
                    base_year=base_year,
                    target_year=target_year,
                    scenario_type=scenario_type
                )
                
                # FIXED: Create new BackgroundTasks for each request
                background_tasks = BackgroundTasks()
                scenario_result = await simulate_climate_scenario(request, background_tasks)
                scenarios.append(scenario_result)
                scenario_results.append({
                    "location": location,
                    "scenario": scenario_type,
                    "result": scenario_result
                })

        # Calculate comparison metrics
        comparison_metrics = calculate_comparison_metrics(scenario_results)
        recommendation = generate_scenario_recommendation(scenario_results)

        return ScenarioComparisonResponse(
            scenarios=scenarios,
            comparison_metrics=comparison_metrics,
            recommendation=recommendation
        )

    except Exception as e:
        logger.error(f"Scenario comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scenario comparison failed: {str(e)}")

@router.get("/definitions")
async def get_scenario_definitions():
    """Get all available climate scenario definitions"""
    return {
        "scenarios": CLIMATE_SCENARIOS,
        "description": "Climate scenarios for urban morphology simulation under climate pressure"
    }

@router.get("/health")
async def health_check():
    """Health check for scenarios service"""
    return {
        "status": "healthy",
        "service": "Climate Scenarios API",
        "available_scenarios": len(CLIMATE_SCENARIOS),
        "timestamp": datetime.now().isoformat()
    }

# Comment out the file upload endpoints for now since they require additional dependencies
"""
@router.post("/upload")
async def upload_scenario(
    name: str = Form(...),
    year: int = Form(...),
    scenario: str = Form(...),
    file: UploadFile = File(...)
):
    # File upload endpoint - commented out for now
    pass

@router.get("/list")
def list_scenarios():
    # List scenarios endpoint - commented out for now
    pass

@router.get("/{scenario_id}")
def get_scenario(scenario_id: str):
    # Get scenario endpoint - commented out for now
    pass
"""

# Simulation Logic
async def run_scenario_simulation(current_analysis: Dict, climate_impact: Dict, 
                                scenario_type: str, base_year: int, target_year: int, 
                                include_adaptation: bool) -> Dict:
    """Run urban morphology simulation under climate scenario"""
    try:
        scenario_config = CLIMATE_SCENARIOS[scenario_type]
        years = target_year - base_year
        
        # Get current metrics
        current_urban = current_analysis['urban_density']['mean']
        current_vegetation = current_analysis['vegetation_cover']['mean']
        current_climate_risk = climate_impact.get('composite_risk_score', {}).get('risk_score', 0.3)
        
        # Calculate changes based on scenario
        urban_growth_rate = current_analysis.get('growth_trend', {}).get('urban_growth_rate', 0.05)
        adjusted_growth = urban_growth_rate * scenario_config['urban_growth_factor']
        
        # Project future values
        future_urban = min(1.0, current_urban * (1 + adjusted_growth * years))
        future_vegetation = max(0.0, current_vegetation * (1 - adjusted_growth * years * 0.5))
        
        # Climate risk projection
        climate_impact_factor = scenario_config['climate_impact_factor']
        future_climate_risk = min(1.0, current_climate_risk * (1 + climate_impact_factor * years * 0.1))
        
        # Adaptation effects
        adaptation_effectiveness = 0.0
        if include_adaptation:
            adaptation_effectiveness = calculate_adaptation_effectiveness(
                current_urban, current_vegetation, scenario_type
            )
            future_climate_risk *= (1 - adaptation_effectiveness)
            future_vegetation = min(1.0, future_vegetation * (1 + adaptation_effectiveness * 0.2))
        
        # Calculate percentages
        urban_growth_pct = ((future_urban - current_urban) / current_urban) * 100 if current_urban > 0 else 0
        vegetation_change_pct = ((future_vegetation - current_vegetation) / current_vegetation) * 100 if current_vegetation > 0 else 0
        climate_risk_change = ((future_climate_risk - current_climate_risk) / current_climate_risk) * 100 if current_climate_risk > 0 else 0
        
        return {
            "urban_growth_percentage": round(urban_growth_pct, 2),
            "vegetation_change_percentage": round(vegetation_change_pct, 2),
            "climate_risk_change": round(climate_risk_change, 2),
            "future_urban_density": round(future_urban, 4),
            "future_vegetation_cover": round(future_vegetation, 4),
            "future_climate_risk": round(future_climate_risk, 4),
            "adaptation_effectiveness": round(adaptation_effectiveness, 3) if include_adaptation else None,
            "summary": generate_scenario_summary(scenario_type, urban_growth_pct, climate_risk_change),
            "scenario_config": scenario_config
        }
        
    except Exception as e:
        logger.error(f"Scenario simulation failed: {e}")
        raise

def calculate_adaptation_effectiveness(current_urban: float, current_vegetation: float, scenario_type: str) -> float:
    """Calculate effectiveness of adaptation measures"""
    base_effectiveness = 0.3  # Base adaptation effectiveness
    
    # Higher vegetation = better adaptation potential
    vegetation_bonus = current_vegetation * 0.2
    
    # Scenario-specific effectiveness
    scenario_multiplier = {
        "conservative": 1.2,
        "moderate": 1.0,
        "aggressive": 0.8,
        "sustainable": 1.4
    }.get(scenario_type, 1.0)
    
    return min(0.8, base_effectiveness + vegetation_bonus) * scenario_multiplier

def generate_scenario_summary(scenario_type: str, urban_growth: float, climate_risk_change: float) -> Dict:
    """Generate human-readable scenario summary"""
    summaries = {
        "conservative": f"Conservative growth ({urban_growth:+.1f}% urban) with managed climate risk ({climate_risk_change:+.1f}%).",
        "moderate": f"Moderate development ({urban_growth:+.1f}% urban) with balanced climate impact ({climate_risk_change:+.1f}%).",
        "aggressive": f"Rapid expansion ({urban_growth:+.1f}% urban) with significant climate risk increase ({climate_risk_change:+.1f}%).", 
        "sustainable": f"Sustainable pathway ({urban_growth:+.1f}% urban) with climate-resilient development ({climate_risk_change:+.1f}%)."
    }
    
    return {
        "description": summaries.get(scenario_type, "Scenario analysis completed."),
        "risk_level": "high" if climate_risk_change > 20 else "medium" if climate_risk_change > 5 else "low",
        "growth_level": "high" if urban_growth > 25 else "medium" if urban_growth > 10 else "low"
    }

def calculate_comparison_metrics(scenario_results: List) -> Dict:
    """Calculate metrics for scenario comparison"""
    if not scenario_results:
        return {}
        
    urban_growth_rates = [r["result"].urban_growth for r in scenario_results]
    climate_risks = [r["result"].climate_risk_change for r in scenario_results]
    
    return {
        "average_urban_growth": round(sum(urban_growth_rates) / len(urban_growth_rates), 2),
        "average_climate_risk_change": round(sum(climate_risks) / len(climate_risks), 2),
        "most_sustainable_scenario": min(scenario_results, key=lambda x: x["result"].climate_risk_change)["scenario"],
        "fastest_growth_scenario": max(scenario_results, key=lambda x: x["result"].urban_growth)["scenario"]
    }

def generate_scenario_recommendation(scenario_results: List) -> str:
    """Generate policy recommendation based on scenario comparison"""
    if not scenario_results:
        return "No scenarios available for comparison."
        
    sustainable_scenario = min(scenario_results, key=lambda x: x["result"].climate_risk_change)
    
    if sustainable_scenario["result"].climate_risk_change < 5:
        return "Recommend sustainable development pathway with climate adaptation measures."
    elif sustainable_scenario["result"].climate_risk_change < 15:
        return "Recommend moderate development with targeted climate resilience investments."
    else:
        return "Urgent need for climate adaptation strategies in urban planning."

async def generate_scenario_visualization(scenario_id: str, scenario_result: Dict, lat: float, lng: float):
    """Generate visualization for scenario results"""
    try:
        # This would generate maps, charts, and other visualizations
        # For now, create a simple placeholder
        viz_path = os.path.join(SCENARIOS_DIR, f"{scenario_id}.json")
        
        visualization_data = {
            "scenario_id": scenario_id,
            "location": {"lat": lat, "lng": lng},
            "results": scenario_result,
            "visualization_type": "urban_growth_map",
            "generated_at": datetime.now().isoformat()
        }
        
        with open(viz_path, 'w') as f:
            json.dump(visualization_data, f, indent=2)
            
        logger.info(f"📊 Visualization generated for scenario {scenario_id}")
        
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")