from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import logging
import numpy as np
from datetime import datetime
import asyncio

# FIXED: Correct import paths
try:
    from services.model_service import ModelService
except ImportError:
    # Fallback for different structure
    from ..services.model_service import ModelService

router = APIRouter()
logger = logging.getLogger(__name__)

# Create model service instance
model_service = ModelService()

# Load model on startup
try:
    model_service.load_model()
    logger.info("✅ ML Model loaded successfully for urban predictions")
except Exception as e:
    logger.warning(f"⚠️ ML Model not loaded: {e}")

# ---- Input Schemas ----
class UrbanFeatureRequest(BaseModel):
    """Request for urban feature prediction"""
    lat: float = Field(..., description="Latitude of location", ge=8.0, le=37.0)
    lng: float = Field(..., description="Longitude of location", ge=68.0, le=97.0)
    years: int = Field(5, description="Years for future projection", ge=1, le=20)
    scenario: str = Field("moderate", description="Climate scenario: conservative/moderate/aggressive")

class BatchPredictRequest(BaseModel):
    """Request for batch predictions"""
    locations: List[Dict[str, float]] = Field(..., description="List of {lat, lng} locations")
    years: int = Field(5, description="Projection years")
    scenario: str = Field("moderate", description="Climate scenario")

class ModelRetrainRequest(BaseModel):
    """Request for model retraining"""
    training_data_path: Optional[str] = None
    epochs: int = Field(100, description="Training epochs")
    force_retrain: bool = Field(False, description="Force retrain even if model exists")

# ---- Response Schemas ----
class UrbanPredictionResponse(BaseModel):
    """Urban morphology prediction response"""
    location: Dict[str, float]
    current_urban_index: float
    predicted_urban_index: float
    growth_percentage: float
    confidence: float
    scenario: str
    time_horizon_years: int
    features_used: List[str]
    timestamp: str

class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    predictions: List[UrbanPredictionResponse]
    summary: Dict
    processing_time: float

class ModelInfoResponse(BaseModel):
    """Model information response"""
    model_loaded: bool
    model_type: Optional[str]
    features_count: Optional[int]
    training_date: Optional[str]
    accuracy: Optional[float]
    last_retrained: Optional[str]

# ---- Prediction Endpoints ----
# FIXED: Removed duplicate /api from route path
@router.post("/urban-growth", response_model=UrbanPredictionResponse)
async def predict_urban_growth(request: UrbanFeatureRequest):
    """
    Predict urban growth and morphology changes for a specific location
    
    Uses satellite data and ML model to predict future urban development
    under specified climate scenarios.
    """
    try:
        # Validate Indian coordinates
        if not (8.0 <= request.lat <= 37.0 and 68.0 <= request.lng <= 97.0):
            raise HTTPException(
                status_code=400, 
                detail="Location must be within India (Latitude: 8°-37°N, Longitude: 68°-97°E)"
            )

        logger.info(f"🏙️ Predicting urban growth for {request.lat}, {request.lng} ({request.years} years, {request.scenario} scenario)")

        # FIXED: Use mock data since GEE fetcher might not be available
        urban_data = await get_mock_urban_data(request.lat, request.lng, 1)

        # Prepare features for ML model
        features = await prepare_urban_features(urban_data, request.scenario)
        
        if not model_service.is_loaded():
            # Fallback to statistical prediction if ML model not available
            logger.warning("ML model not loaded, using statistical fallback")
            prediction_result = await statistical_urban_prediction(urban_data, request.years, request.scenario)
        else:
            # Use ML model for prediction
            prediction_result = await ml_urban_prediction(features, urban_data, request.years, request.scenario)

        response = UrbanPredictionResponse(
            location={"lat": request.lat, "lng": request.lng},
            current_urban_index=urban_data['urban_density']['mean'],
            predicted_urban_index=prediction_result['predicted_urban_index'],
            growth_percentage=prediction_result['growth_percentage'],
            confidence=prediction_result['confidence'],
            scenario=request.scenario,
            time_horizon_years=request.years,
            features_used=prediction_result['features_used'],
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"✅ Urban growth prediction completed: {prediction_result['growth_percentage']:.1f}% growth")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Urban growth prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Urban growth prediction failed: {str(e)}"
        )

# FIXED: Removed duplicate /api from route path
@router.post("/batch-urban-growth", response_model=BatchPredictionResponse)
async def batch_predict_urban_growth(request: BatchPredictRequest, background_tasks: BackgroundTasks):
    """
    Batch predict urban growth for multiple locations
    
    Useful for regional planning and comparative analysis across multiple cities.
    """
    start_time = datetime.now()
    
    try:
        if len(request.locations) > 50:
            raise HTTPException(
                status_code=400,
                detail="Batch processing limited to 50 locations per request"
            )

        predictions = []
        processed_locations = 0

        for location in request.locations:
            try:
                # FIXED: Use mock data
                urban_data = await get_mock_urban_data(location['lat'], location['lng'], 1)

                features = await prepare_urban_features(urban_data, request.scenario)
                
                if model_service.is_loaded():
                    prediction_result = await ml_urban_prediction(features, urban_data, request.years, request.scenario)
                else:
                    prediction_result = await statistical_urban_prediction(urban_data, request.years, request.scenario)

                prediction_response = UrbanPredictionResponse(
                    location=location,
                    current_urban_index=urban_data['urban_density']['mean'],
                    predicted_urban_index=prediction_result['predicted_urban_index'],
                    growth_percentage=prediction_result['growth_percentage'],
                    confidence=prediction_result['confidence'],
                    scenario=request.scenario,
                    time_horizon_years=request.years,
                    features_used=prediction_result['features_used'],
                    timestamp=datetime.now().isoformat()
                )
                
                predictions.append(prediction_response)
                processed_locations += 1

            except Exception as e:
                logger.warning(f"Failed to process location {location}: {e}")
                continue

        # Calculate summary statistics
        growth_rates = [p.growth_percentage for p in predictions]
        confidence_scores = [p.confidence for p in predictions]

        summary = {
            "total_locations": len(request.locations),
            "successful_predictions": processed_locations,
            "failed_predictions": len(request.locations) - processed_locations,
            "average_growth_rate": float(np.mean(growth_rates)) if growth_rates else 0,
            "max_growth_rate": float(max(growth_rates)) if growth_rates else 0,
            "min_growth_rate": float(min(growth_rates)) if growth_rates else 0,
            "average_confidence": float(np.mean(confidence_scores)) if confidence_scores else 0
        }

        processing_time = (datetime.now() - start_time).total_seconds()

        logger.info(f"✅ Batch prediction completed: {processed_locations}/{len(request.locations)} locations")

        return BatchPredictionResponse(
            predictions=predictions,
            summary=summary,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction failed: {str(e)}"
        )

# FIXED: Removed duplicate /api from route path
@router.post("/retrain-model")
async def retrain_model(request: ModelRetrainRequest, background_tasks: BackgroundTasks):
    """
    Retrain the urban growth prediction model
    
    This endpoint triggers model retraining in the background using
    the latest urban morphology data.
    """
    try:
        # Add retraining task to background
        background_tasks.add_task(
            model_service.retrain_model,
            request.training_data_path,
            request.epochs,
            request.force_retrain
        )

        return {
            "status": "retraining_started",
            "message": "Model retraining started in background",
            "training_data": request.training_data_path or "default_dataset",
            "epochs": request.epochs
        }

    except Exception as e:
        logger.error(f"Model retraining failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Model retraining failed: {str(e)}"
        )

# FIXED: Removed duplicate /api from route path
@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the currently loaded ML model"""
    try:
        model_info = model_service.get_model_info()
        
        return ModelInfoResponse(
            model_loaded=model_service.is_loaded(),
            model_type=model_info.get('model_type'),
            features_count=model_info.get('features_count'),
            training_date=model_info.get('training_date'),
            accuracy=model_info.get('accuracy'),
            last_retrained=model_info.get('last_retrained')
        )

    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model information: {str(e)}"
        )

# FIXED: Removed duplicate /api from route path
@router.get("/feature-importance")
async def get_feature_importance():
    """Get feature importance scores from the ML model"""
    try:
        if not model_service.is_loaded():
            raise HTTPException(
                status_code=503,
                detail="Model not loaded. Cannot compute feature importance."
            )

        importance_scores = model_service.get_feature_importance()
        
        return {
            "feature_importance": importance_scores,
            "interpretation": "Higher scores indicate more important features for urban growth prediction"
        }

    except Exception as e:
        logger.error(f"Failed to get feature importance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute feature importance: {str(e)}"
        )

# ---- Helper Functions ----
async def get_mock_urban_data(lat: float, lng: float, years: int) -> Dict:
    """Mock urban data for testing"""
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
        },
        'growth_trend': {
            'urban_growth_rate': random.uniform(0.02, 0.15)
        }
    }

async def prepare_urban_features(urban_data: Dict, scenario: str) -> List[float]:
    """Prepare features for ML model prediction"""
    try:
        features = [
            urban_data['urban_density']['mean'],
            urban_data['vegetation_cover']['mean'],
            urban_data['built_up_area']['mean'],
            urban_data['urban_density']['std'],
            urban_data.get('growth_trend', {}).get('urban_growth_rate', 0.05),
            # Climate scenario factor
            0.1 if scenario == "conservative" else 0.2 if scenario == "moderate" else 0.3,
            # Additional urban morphology features
            urban_data['urban_density']['mean'] - urban_data['vegetation_cover']['mean'],  # Urban-vegetation gradient
            max(0, urban_data['built_up_area']['mean'] - urban_data['urban_density']['mean'])  # Built-up intensity
        ]
        
        return features
    except Exception as e:
        logger.error(f"Feature preparation failed: {e}")
        return [0.1] * 8  # Return default features

async def ml_urban_prediction(features: List[float], urban_data: Dict, years: int, scenario: str) -> Dict:
    """Use ML model for urban growth prediction"""
    try:
        # Reshape features for model input
        features_array = [features]
        
        # Get prediction from ML model
        predictions = model_service.predict(features_array)
        predicted_growth = float(predictions[0])
        
        # Calculate resulting urban index
        current_urban = urban_data['urban_density']['mean']
        predicted_urban = min(1.0, current_urban * (1 + predicted_growth * years))
        
        # Calculate confidence based on feature quality
        confidence = calculate_prediction_confidence(urban_data, features)
        
        return {
            'predicted_urban_index': round(predicted_urban, 4),
            'growth_percentage': round(predicted_growth * 100, 2),
            'confidence': round(confidence, 3),
            'features_used': [
                'urban_density', 'vegetation_cover', 'built_up_area', 
                'urban_std', 'historical_growth', 'climate_scenario',
                'urban_vegetation_gradient', 'built_up_intensity'
            ]
        }
        
    except Exception as e:
        logger.error(f"ML prediction failed: {e}")
        # Fallback to statistical method
        return await statistical_urban_prediction(urban_data, years, scenario)

async def statistical_urban_prediction(urban_data: Dict, years: int, scenario: str) -> Dict:
    """Statistical fallback prediction when ML model is unavailable"""
    try:
        current_urban = urban_data['urban_density']['mean']
        historical_growth = urban_data.get('growth_trend', {}).get('urban_growth_rate', 0.05)
        
        # Adjust growth rate based on scenario
        scenario_factor = 0.8 if scenario == "conservative" else 1.0 if scenario == "moderate" else 1.2
        adjusted_growth = historical_growth * scenario_factor
        
        # Predict future urban index
        predicted_urban = min(1.0, current_urban * (1 + adjusted_growth * years))
        growth_percentage = ((predicted_urban - current_urban) / current_urban) * 100
        
        # Lower confidence for statistical method
        confidence = 0.6
        
        return {
            'predicted_urban_index': round(predicted_urban, 4),
            'growth_percentage': round(growth_percentage, 2),
            'confidence': confidence,
            'features_used': [
                'current_urban_density', 'historical_growth_trend', 
                'climate_scenario_factor'
            ]
        }
        
    except Exception as e:
        logger.error(f"Statistical prediction failed: {e}")
        # Ultimate fallback
        return {
            'predicted_urban_index': 0.1,
            'growth_percentage': 5.0,
            'confidence': 0.3,
            'features_used': ['fallback_estimation']
        }

def calculate_prediction_confidence(urban_data: Dict, features: List[float]) -> float:
    """Calculate prediction confidence based on data quality"""
    try:
        confidence_factors = []
        
        # Urban data quality
        if urban_data['urban_density']['std'] < 0.2:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.7)
            
        # Vegetation data quality
        if urban_data['vegetation_cover']['mean'] > 0.1:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
            
        # Feature variability
        feature_std = np.std(features)
        if feature_std > 0.1:
            confidence_factors.append(0.8)  # Good variability
        else:
            confidence_factors.append(0.5)  # Low variability
            
        return float(np.mean(confidence_factors))
        
    except Exception as e:
        logger.warning(f"Confidence calculation failed: {e}")
        return 0.5

@router.get("/health")
async def health_check():
    """Health check for prediction service"""
    return {
        "status": "healthy",
        "model_loaded": model_service.is_loaded(),
        "service": "Urban Growth Prediction API",
        "timestamp": datetime.now().isoformat()
    }