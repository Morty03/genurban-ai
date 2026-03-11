# services/storage_service.py
import numpy as np
import joblib
from pathlib import Path
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self):
        # FIXED: Use relative paths that work with your structure
        self.data_dir = Path("storage/data")
        self.models_dir = Path("ml_engine/models")
        self.setup_directories()
    
    def setup_directories(self):
        """Ensure directories exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Storage directories initialized")
    
    def load_urban_data(self, city: str = "Bangalore"):
        """Load or generate urban data"""
        try:
            features_path = self.data_dir / "features.npy"
            climate_path = self.data_dir / "climate_features.pkl"
            
            if features_path.exists() and climate_path.exists():
                # Load existing data
                features = np.load(features_path)
                climate_data = joblib.load(climate_path)
                logger.info("✅ Loaded existing urban data")
            else:
                # Generate sample data
                features, climate_data = self.generate_sample_data(city)
                logger.info("✅ Generated sample urban data")
            
            return {
                'features': features.tolist(),
                'climate': climate_data,
                'shape': list(features.shape) if hasattr(features, 'shape') else [256, 256, 5]
            }
        except Exception as e:
            logger.error(f"Failed to load urban data: {e}")
            # Return mock data as fallback
            return self.generate_mock_data(city)
    
    def generate_sample_data(self, city: str):
        """Generate sample urban data"""
        logger.info(f"🎲 Generating sample data for {city}...")
        
        # Create realistic urban patterns (256x256 grid, 5 features)
        height, width, channels = 256, 256, 5
        features = np.zeros((height, width, channels))
        
        # Simulate urban patterns
        for i in range(height):
            for j in range(width):
                # Urban density (higher in center)
                dist_from_center = np.sqrt((i - height/2)**2 + (j - width/2)**2)
                density = np.exp(-dist_from_center / 50)
                features[i, j, 0] = density
                
                # Other features
                features[i, j, 1] = np.random.rand() * 0.5  # Land use
                features[i, j, 2] = np.random.rand() * 0.3  # Infrastructure
                features[i, j, 3] = np.random.rand() * 0.7  # Green spaces
                features[i, j, 4] = np.random.rand() * 0.2  # Water bodies
        
        # Climate data
        climate_data = {
            'avg_temperature': 25.6,
            'total_precipitation': 890,
            'urban_heat_island_effect': 2.3,
            'humidity': 65,
            'co2_emissions': 4.2,
            'city': city
        }
        
        # Save for future use
        np.save(self.data_dir / "features.npy", features)
        joblib.dump(climate_data, self.data_dir / "climate_features.pkl")
        
        return features, climate_data

    def generate_mock_data(self, city: str):
        """Generate lightweight mock data for API responses"""
        logger.info(f"🎲 Generating mock data for {city}...")
        
        # Simple mock features (smaller for API responses)
        features = np.random.rand(10, 10, 5).tolist()
        
        climate_data = {
            'avg_temperature': 25.6,
            'total_precipitation': 890,
            'urban_heat_island_effect': 2.3,
            'humidity': 65,
            'co2_emissions': 4.2,
            'city': city
        }
        
        return features, climate_data
    
    def save_prediction(self, prediction_data: Dict, scenario_name: str):
        """Save prediction results"""
        try:
            predictions_dir = self.data_dir / "predictions"
            predictions_dir.mkdir(exist_ok=True)
            
            file_path = predictions_dir / f"{scenario_name}.json"
            with open(file_path, 'w') as f:
                json.dump(prediction_data, f, indent=2)
            
            logger.info(f"✅ Saved prediction: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
            return None

# Singleton instance
data_manager = DataManager()