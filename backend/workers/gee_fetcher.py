# workers/gee_fetcher.py
import ee
import geemap
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import os
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class GEEFetcher:
    def __init__(self):
        self.initialized = False
        self.initialize_earth_engine()
    
    def initialize_earth_engine(self):
        """Initialize Earth Engine with service account"""
        try:
            # FIXED: Use correct relative path
            service_account_file = Path("keys/gee-sa.json")
            
            if not service_account_file.exists():
                logger.error(f"Service account file not found: {service_account_file}")
                raise FileNotFoundError(f"Service account file not found: {service_account_file}")
            
            # Try to initialize with service account
            credentials = ee.ServiceAccountCredentials(
                'genurban-service@ee-kgoutham386.iam.gserviceaccount.com',  # FIXED: Correct email
                str(service_account_file)
            )
            ee.Initialize(credentials)
            self.initialized = True
            logger.info("✅ Earth Engine initialized with service account")
        except Exception as e:
            logger.warning(f"Service account initialization failed: {e}")
            try:
                # Fallback to personal authentication
                ee.Initialize(project="ee-kgoutham386")
                self.initialized = True
                logger.info("✅ Earth Engine initialized with personal account")
            except Exception as e:
                logger.error(f"Earth Engine initialization failed: {e}")
                self.initialized = False
                # Don't raise here - let the app start without GEE

    def create_bounding_box(self, lat: float, lng: float, radius_km: float = 10) -> ee.Geometry:
        """Create bounding box around coordinates for urban analysis"""
        try:
            point = ee.Geometry.Point([lng, lat])
            # Create rectangle around point (adjust based on urban analysis needs)
            offset = radius_km / 111.0  # Approximate degrees per km
            bbox = ee.Geometry.Rectangle([
                lng - offset, lat - offset,
                lng + offset, lat + offset
            ])
            return bbox
        except Exception as e:
            logger.error(f"Error creating bounding box: {e}")
            raise

    def mask_clouds_sentinel2(self, image: ee.Image) -> ee.Image:
        """Mask clouds and shadows in Sentinel-2 imagery - FROM YOUR NOTEBOOK"""
        try:
            # Cloud mask from QA60 band (bits 10 and 11)
            qa = image.select('QA60')
            cloud_bitmask = 1 << 10
            cirrus_bitmask = 1 << 11
            mask = qa.bitwiseAnd(cloud_bitmask).eq(0) \
                    .And(qa.bitwiseAnd(cirrus_bitmask).eq(0))
            
            return image.updateMask(mask).divide(10000)  # Scale reflectance to 0-1
        except Exception as e:
            logger.error(f"Error in cloud masking: {e}")
            return image

    def get_historical_data(self, geometry: ee.Geometry, years: int = 5) -> ee.ImageCollection:
        """Get multi-year Sentinel-2 data for urban analysis - FROM YOUR NOTEBOOK"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years*365)
            
            collection = ee.ImageCollection("COPERNICUS/S2_SR") \
                .filterBounds(geometry) \
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))  # Low cloud cover
            
            # Apply cloud masking
            collection_clean = collection.map(self.mask_clouds_sentinel2)
            
            logger.info(f"📊 Loaded {collection_clean.size().getInfo()} Sentinel-2 images")
            return collection_clean
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise

    def calculate_urban_indices(self, image_collection: ee.ImageCollection) -> Dict:
        """Calculate urban morphology indices - FROM YOUR NOTEBOOK"""
        try:
            # NDVI calculation
            def add_ndvi(image):
                ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                return image.addBands(ndvi)

            # NDBI calculation  
            def add_ndbi(image):
                ndbi = image.normalizedDifference(['B11', 'B8']).rename('NDBI')
                return image.addBands(ndbi)

            # Urban Index calculation
            def add_urban_index(image):
                ndvi = image.normalizedDifference(['B8', 'B4'])
                ndbi = image.normalizedDifference(['B11', 'B8'])
                urban_index = ndbi.subtract(ndvi).rename('URBAN_INDEX')
                return image.addBands(urban_index)

            # Apply all indices
            collection_with_indices = image_collection \
                .map(add_ndvi) \
                .map(add_ndbi) \
                .map(add_urban_index)

            # Get median composites
            ndvi_median = collection_with_indices.select('NDVI').median()
            ndbi_median = collection_with_indices.select('NDBI').median()
            urban_index_median = collection_with_indices.select('URBAN_INDEX').median()

            return {
                'ndvi': ndvi_median,
                'ndbi': ndbi_median, 
                'urban_index': urban_index_median,
                'composite': collection_with_indices.median()  # RGB composite
            }
            
        except Exception as e:
            logger.error(f"Error calculating urban indices: {e}")
            raise

    def calculate_growth_trend(self, image_collection: ee.ImageCollection) -> Dict:
        """Calculate urban growth trend over time"""
        try:
            # Simplified trend analysis - you can enhance this
            yearly_trend = {
                'urban_growth_rate': 0.05,  # Placeholder - implement actual trend analysis
                'vegetation_change': -0.02,
                'built_up_change': 0.08
            }
            return yearly_trend
        except Exception as e:
            logger.warning(f"Growth trend calculation failed: {e}")
            return {'urban_growth_rate': 0, 'vegetation_change': 0, 'built_up_change': 0}

    def get_urban_statistics(self, image: ee.Image, geometry: ee.Geometry) -> Dict:
        """Calculate statistics for urban analysis - FROM YOUR NOTEBOOK"""
        try:
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    reducer2=ee.Reducer.stdDev(), 
                    sharedInputs=True
                ),
                geometry=geometry,
                scale=100,  # 100m scale for urban analysis
                bestEffort=True
            )
            return stats.getInfo()
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    def get_urban_morphology(self, lat: float, lng: float, years: int = 5) -> Dict:
        """Get urban morphology data for any Indian location - MAIN METHOD"""
        if not self.initialized:
            raise RuntimeError("Earth Engine not initialized")
        
        try:
            logger.info(f"🌍 Analyzing urban morphology for location: {lat}, {lng}")
            
            # Create study area
            bbox = self.create_bounding_box(lat, lng, radius_km=15)
            
            # Get historical satellite data
            historical_data = self.get_historical_data(bbox, years)
            
            # Calculate urban indices
            urban_indices = self.calculate_urban_indices(historical_data)
            
            # Calculate statistics
            urban_stats = self.get_urban_statistics(urban_indices['urban_index'], bbox)
            ndvi_stats = self.get_urban_statistics(urban_indices['ndvi'], bbox)
            ndbi_stats = self.get_urban_statistics(urban_indices['ndbi'], bbox)
            
            # Calculate growth trend
            growth_trend = self.calculate_growth_trend(historical_data)
            
            # Prepare response
            result = {
                'location': {
                    'lat': lat, 
                    'lng': lng,
                    'bbox': bbox.getInfo()['coordinates']
                },
                'urban_density': {
                    'mean': urban_stats.get('URBAN_INDEX_mean', 0),
                    'std': urban_stats.get('URBAN_INDEX_stdDev', 0)
                },
                'vegetation_cover': {
                    'mean': ndvi_stats.get('NDVI_mean', 0),
                    'std': ndvi_stats.get('NDVI_stdDev', 0)
                },
                'built_up_area': {
                    'mean': ndbi_stats.get('NDBI_mean', 0),
                    'std': ndbi_stats.get('NDBI_stdDev', 0)
                },
                'growth_trend': growth_trend,
                'timestamp': datetime.now().isoformat(),
                'data_quality': {
                    'images_used': historical_data.size().getInfo(),
                    'analysis_years': years
                }
            }
            
            logger.info("✅ Urban morphology analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Urban morphology analysis failed: {e}")
            raise

    def export_urban_data(self, lat: float, lng: float, output_folder: str = "GENURBAN_DATA"):
        """Export urban data for ML training - FROM YOUR NOTEBOOK"""
        try:
            bbox = self.create_bounding_box(lat, lng)
            historical_data = self.get_historical_data(bbox, years=1)
            urban_indices = self.calculate_urban_indices(historical_data)
            
            # Export tasks (similar to your notebook)
            export_tasks = []
            
            for name, image in urban_indices.items():
                task = ee.batch.Export.image.toDrive(
                    image=image,
                    description=f'urban_{name}_{lat}_{lng}',
                    folder=output_folder,
                    fileNamePrefix=f'urban_{name}',
                    scale=10,
                    region=bbox,
                    maxPixels=1e9
                )
                export_tasks.append(task)
                # task.start()  # Uncomment when ready to export
                
            return export_tasks
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise

# Singleton instance for easy access
gee_fetcher = GEEFetcher()