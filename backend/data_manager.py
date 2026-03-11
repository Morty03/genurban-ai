# data_manager.py
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
import requests
import json
from typing import Dict, Any
import os

class UrbanDataManager:
    def __init__(self, data_dir="../data"):
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir = self.data_dir / "raw"
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary directories"""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_urban_data(self, city_name="Bangalore"):
        """Fetch urban data from various sources"""
        print(f"🌐 Fetching urban data for {city_name}...")
        
        # Sample data generation (replace with actual API calls)
        urban_data = self.generate_sample_urban_data()
        
        # Save raw data
        np.save(self.raw_dir / "urban_raw.npy", urban_data)
        print("✅ Raw urban data saved")
        
        return urban_data
    
    def fetch_climate_data(self, city_name="Bangalore"):
        """Fetch climate data from APIs"""
        print(f"🌦️ Fetching climate data for {city_name}...")
        
        climate_data = {
            'avg_temperature': 25.6,
            'total_precipitation': 890,
            'urban_heat_island_effect': 2.3,
            'humidity': 65,
            'co2_emissions': 4.2
        }
        
        # Save climate data
        joblib.dump(climate_data, self.raw_dir / "climate_raw.pkl")
        print("✅ Climate data saved")
        
        return climate_data
    
    def preprocess_data(self):
        """Process raw data for AI model"""
        print("🔄 Preprocessing data...")
        
        # Load raw data
        try:
            urban_data = np.load(self.raw_dir / "urban_raw.npy")
            climate_data = joblib.load(self.raw_dir / "climate_raw.pkl")
        except FileNotFoundError:
            print("❌ No raw data found. Generating sample data...")
            urban_data = self.generate_sample_urban_data()
            climate_data = self.fetch_climate_data()
        
        # Preprocessing steps
        processed_features = self.normalize_urban_data(urban_data)
        processed_climate = self.process_climate_features(climate_data)
        
        # Save processed data
        np.save(self.processed_dir / "features.npy", processed_features)
        joblib.dump(processed_climate, self.processed_dir / "climate_features.pkl")
        
        print("✅ Data preprocessing completed")
        return processed_features, processed_climate
    
    def normalize_urban_data(self, data):
        """Normalize urban data to [-1, 1] range for GAN"""
        normalized = (data - data.min()) / (data.max() - data.min()) * 2 - 1
        return normalized
    
    def process_climate_features(self, climate_data):
        """Process climate data for model input"""
        return {
            'avg_temperature': climate_data.get('avg_temperature', 25),
            'total_precipitation': climate_data.get('total_precipitation', 900),
            'urban_heat_island_effect': climate_data.get('urban_heat_island_effect', 2.5),
            'humidity': climate_data.get('humidity', 60),
            'co2_emissions': climate_data.get('co2_emissions', 4.0)
        }
    
    def generate_sample_urban_data(self, width=256, height=256, channels=5):
        """Generate sample urban data if no real data available"""
        print("🎲 Generating sample urban data...")
        
        # Create realistic urban patterns
        data = np.zeros((height, width, channels))
        
        # Channel 0: Urban density (centers are more dense)
        for i in range(height):
            for j in range(width):
                # Create urban center pattern
                dist_from_center = np.sqrt((i - height/2)**2 + (j - width/2)**2)
                density = np.exp(-dist_from_center / 50)
                data[i, j, 0] = density
        
        # Channel 1: Land use patterns
        data[:, :, 1] = np.random.rand(height, width) * 0.5
        
        # Channel 2: Infrastructure
        data[:, :, 2] = np.random.rand(height, width) * 0.3
        
        # Channel 3: Green spaces
        data[:, :, 3] = np.random.rand(height, width) * 0.7
        
        # Channel 4: Water bodies
        data[:, :, 4] = np.random.rand(height, width) * 0.2
        
        return data
    
    def get_data_status(self):
        """Check what data is available"""
        status = {
            'raw_urban': (self.raw_dir / "urban_raw.npy").exists(),
            'raw_climate': (self.raw_dir / "climate_raw.pkl").exists(),
            'processed_features': (self.processed_dir / "features.npy").exists(),
            'processed_climate': (self.processed_dir / "climate_features.pkl").exists()
        }
        return status

# Singleton instance
data_manager = UrbanDataManager()