import ee
import logging
from typing import Dict, List, Optional
from workers.gee_fetcher import gee_fetcher
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self):
        self.gee_fetcher = gee_fetcher
        self.climate_datasets_initialized = False
        self._initialize_climate_datasets()

    def _initialize_climate_datasets(self):
        """Initialize climate datasets for analysis"""
        try:
            # Climate datasets
            self.flood_risk_data = ee.ImageCollection("WWF/HydroSHEDS/15ACC")
            self.heat_data = ee.ImageCollection("MODIS/061/MOD11A1")  # Land Surface Temperature
            self.precipitation_data = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
            self.elevation_data = ee.Image("USGS/SRTMGL1_003")
            
            self.climate_datasets_initialized = True
            logger.info("✅ Climate datasets initialized successfully")
        except Exception as e:
            logger.error(f"❌ Climate datasets initialization failed: {e}")
            self.climate_datasets_initialized = False

    async def analyze_urban_morphology(self, location_data: Dict) -> Dict:
        """Main analysis endpoint for urban morphology with climate integration"""
        try:
            lat, lng = location_data['lat'], location_data['lng']
            years = location_data.get('years', 5)

            logger.info(f"🌍 Starting comprehensive urban analysis for {lat}, {lng}")

            # Get current urban structure
            current_analysis = await asyncio.get_event_loop().run_in_executor(
                None, self.gee_fetcher.get_urban_morphology, lat, lng, years
            )

            # Add climate pressure factors
            climate_impact = await self.assess_climate_pressure(lat, lng)
            
            # Calculate future projections
            future_scenario = await self.project_urban_future(current_analysis, climate_impact, years)
            
            # Generate comprehensive analysis
            comprehensive_analysis = {
                **current_analysis,
                'climate_risk': climate_impact,
                'vulnerability_score': self.calculate_vulnerability(current_analysis, climate_impact),
                'future_projections': future_scenario,
                'adaptation_recommendations': self.generate_adaptation_strategies(current_analysis, climate_impact),
                'analysis_timestamp': datetime.now().isoformat(),
                'scenario_parameters': {
                    'time_horizon_years': years,
                    'climate_scenario': 'moderate',
                    'urban_growth_assumption': 'current_trend'
                }
            }

            logger.info("✅ Comprehensive urban morphology analysis completed")
            return comprehensive_analysis

        except Exception as e:
            logger.error(f"Urban morphology analysis failed: {e}")
            raise

    async def assess_climate_pressure(self, lat: float, lng: float) -> Dict:
        """Assess multiple climate pressure factors"""
        if not self.climate_datasets_initialized:
            return await self._get_fallback_climate_data(lat, lng)

        try:
            point = ee.Geometry.Point([lng, lat])
            bbox = self.gee_fetcher.create_bounding_box(lat, lng)

            # Run climate assessments in parallel
            flood_task = self._get_flood_risk(point, bbox)
            heat_task = self._get_heat_island_effect(point, bbox)
            precipitation_task = self._get_precipitation_changes(point, bbox)
            elevation_task = self._get_elevation_data(point)

            # Wait for all climate assessments
            flood_risk, heat_effect, precipitation_trends, elevation_info = await asyncio.gather(
                flood_task, heat_task, precipitation_task, elevation_task,
                return_exceptions=True
            )

            # Handle any failed assessments
            climate_impact = {
                'flood_risk': flood_risk if not isinstance(flood_risk, Exception) else await self._get_fallback_flood_risk(lat, lng),
                'heat_island_effect': heat_effect if not isinstance(heat_effect, Exception) else await self._get_fallback_heat_data(lat, lng),
                'precipitation_changes': precipitation_trends if not isinstance(precipitation_trends, Exception) else await self._get_fallback_precipitation(lat, lng),
                'elevation': elevation_info if not isinstance(elevation_info, Exception) else {'elevation': 0, 'slope': 0},
                'composite_risk_score': self._calculate_composite_climate_risk(
                    flood_risk if not isinstance(flood_risk, Exception) else {'risk_level': 'medium'},
                    heat_effect if not isinstance(heat_effect, Exception) else {'risk_level': 'medium'}
                )
            }

            return climate_impact

        except Exception as e:
            logger.error(f"Climate pressure assessment failed: {e}")
            return await self._get_fallback_climate_data(lat, lng)

    async def _get_flood_risk(self, point: ee.Geometry, bbox: ee.Geometry) -> Dict:
        """Calculate flood risk based on elevation and hydrography"""
        try:
            elevation = self.elevation_data.select('elevation')
            elevation_value = elevation.reduceRegion(
                ee.Reducer.mean(), point, 1000
            ).getInfo().get('elevation', 0)

            # Simple flood risk model (can be enhanced)
            if elevation_value < 10:
                risk_level = "high"
                risk_score = 0.8
            elif elevation_value < 50:
                risk_level = "medium"
                risk_score = 0.5
            else:
                risk_level = "low"
                risk_score = 0.2

            return {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'elevation_m': elevation_value,
                'factors': ['elevation'],
                'description': self._get_flood_risk_description(risk_level, elevation_value)
            }
        except Exception as e:
            logger.error(f"Flood risk assessment failed: {e}")
            raise

    async def _get_heat_island_effect(self, point: ee.Geometry, bbox: ee.Geometry) -> Dict:
        """Assess urban heat island effect"""
        try:
            # Get land surface temperature data
            lst_collection = self.heat_data.filterBounds(bbox) \
                .filterDate('2020-01-01', '2020-12-31') \
                .select('LST_Day_1km')

            mean_temp = lst_collection.mean().multiply(0.02).subtract(273.15)  # Convert to Celsius
            
            temp_stats = mean_temp.reduceRegion(
                ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
                bbox, 1000
            ).getInfo()

            mean_temp_value = temp_stats.get('LST_Day_1km_mean', 25)
            std_temp = temp_stats.get('LST_Day_1km_stdDev', 2)

            # Heat island effect assessment
            if mean_temp_value > 30:
                heat_level = "high"
                heat_score = 0.8
            elif mean_temp_value > 25:
                heat_level = "medium"
                heat_score = 0.5
            else:
                heat_level = "low"
                heat_score = 0.2

            return {
                'risk_level': heat_level,
                'risk_score': heat_score,
                'mean_temperature_c': round(mean_temp_value, 1),
                'temperature_std': round(std_temp, 1),
                'description': self._get_heat_risk_description(heat_level, mean_temp_value)
            }
        except Exception as e:
            logger.error(f"Heat island assessment failed: {e}")
            raise

    async def _get_precipitation_changes(self, point: ee.Geometry, bbox: ee.Geometry) -> Dict:
        """Analyze precipitation patterns and changes"""
        try:
            # Get recent precipitation data
            recent_precip = self.precipitation_data \
                .filterBounds(bbox) \
                .filterDate('2020-01-01', '2020-12-31') \
                .select('precipitation')

            annual_precip = recent_precip.sum()
            
            precip_stats = annual_precip.reduceRegion(
                ee.Reducer.mean(), bbox, 5000
            ).getInfo()

            annual_mm = precip_stats.get('precipitation', 800)

            # Precipitation risk assessment
            if annual_mm > 2000:
                precip_risk = "high_flood_risk"
                risk_score = 0.7
            elif annual_mm < 500:
                precip_risk = "high_drought_risk"
                risk_score = 0.7
            else:
                precip_risk = "moderate"
                risk_score = 0.3

            return {
                'risk_level': precip_risk,
                'risk_score': risk_score,
                'annual_precipitation_mm': round(annual_mm, 1),
                'description': self._get_precipitation_description(precip_risk, annual_mm)
            }
        except Exception as e:
            logger.error(f"Precipitation analysis failed: {e}")
            raise

    async def _get_elevation_data(self, point: ee.Geometry) -> Dict:
        """Get elevation and slope data"""
        try:
            elevation = self.elevation_data.select('elevation')
            elevation_value = elevation.reduceRegion(
                ee.Reducer.mean(), point, 1000
            ).getInfo().get('elevation', 0)

            # Simple slope calculation (can be enhanced)
            terrain = ee.Terrain.products(self.elevation_data)
            slope = terrain.select('slope')
            slope_value = slope.reduceRegion(
                ee.Reducer.mean(), point, 1000
            ).getInfo().get('slope', 0)

            return {
                'elevation': round(elevation_value, 1),
                'slope': round(slope_value, 1),
                'topography': self._classify_topography(elevation_value, slope_value)
            }
        except Exception as e:
            logger.error(f"Elevation analysis failed: {e}")
            raise

    def calculate_vulnerability(self, urban_data: Dict, climate_impact: Dict) -> Dict:
        """Calculate comprehensive vulnerability score"""
        try:
            urban_density = urban_data['urban_density']['mean']
            vegetation_cover = urban_data['vegetation_cover']['mean']
            flood_risk = climate_impact['flood_risk']['risk_score']
            heat_risk = climate_impact['heat_island_effect']['risk_score']
            precip_risk = climate_impact['precipitation_changes']['risk_score']

            # Weighted vulnerability calculation
            weights = {
                'urban_density': 0.3,
                'vegetation_cover': 0.2,
                'flood_risk': 0.2,
                'heat_risk': 0.2,
                'precip_risk': 0.1
            }

            vulnerability_score = (
                urban_density * weights['urban_density'] +
                (1 - vegetation_cover) * weights['vegetation_cover'] +
                flood_risk * weights['flood_risk'] +
                heat_risk * weights['heat_risk'] +
                precip_risk * weights['precip_risk']
            )

            # Classify vulnerability
            if vulnerability_score > 0.7:
                level = "high"
            elif vulnerability_score > 0.4:
                level = "medium"
            else:
                level = "low"

            return {
                'score': round(vulnerability_score, 3),
                'level': level,
                'components': {
                    'urban_density_impact': round(urban_density * weights['urban_density'], 3),
                    'vegetation_protection': round((1 - vegetation_cover) * weights['vegetation_cover'], 3),
                    'flood_vulnerability': round(flood_risk * weights['flood_risk'], 3),
                    'heat_vulnerability': round(heat_risk * weights['heat_risk'], 3)
                }
            }
        except Exception as e:
            logger.error(f"Vulnerability calculation failed: {e}")
            return {'score': 0.5, 'level': 'unknown', 'components': {}}

    async def project_urban_future(self, current_analysis: Dict, climate_impact: Dict, years: int) -> Dict:
        """Project future urban morphology under climate pressure"""
        try:
            growth_trend = current_analysis.get('growth_trend', {})
            current_urban = current_analysis['urban_density']['mean']
            current_vegetation = current_analysis['vegetation_cover']['mean']

            # Simple projection model (enhance with ML later)
            urban_growth_rate = growth_trend.get('urban_growth_rate', 0.05)
            climate_pressure_factor = climate_impact['composite_risk_score']['risk_score']

            # Project future values
            future_urban = min(1.0, current_urban * (1 + urban_growth_rate * years))
            future_vegetation = max(0.0, current_vegetation * (1 - urban_growth_rate * years * (1 + climate_pressure_factor)))

            return {
                'projected_urban_density': round(future_urban, 3),
                'projected_vegetation_cover': round(future_vegetation, 3),
                'urban_growth_percentage': round((future_urban - current_urban) / current_urban * 100, 1),
                'vegetation_loss_percentage': round((current_vegetation - future_vegetation) / current_vegetation * 100, 1),
                'climate_impact_factor': round(climate_pressure_factor, 3),
                'time_horizon_years': years
            }
        except Exception as e:
            logger.error(f"Future projection failed: {e}")
            return {}

    def generate_adaptation_strategies(self, urban_data: Dict, climate_impact: Dict) -> List[Dict]:
        """Generate climate adaptation strategies"""
        strategies = []
        vulnerability = self.calculate_vulnerability(urban_data, climate_impact)
        
        if vulnerability['level'] == 'high':
            strategies.extend([
                {
                    'type': 'urgent',
                    'category': 'flood_protection',
                    'strategy': 'Implement green infrastructure for stormwater management',
                    'priority': 'high'
                },
                {
                    'type': 'urgent', 
                    'category': 'heat_mitigation',
                    'strategy': 'Increase urban green spaces and cool roofs',
                    'priority': 'high'
                }
            ])
        
        if urban_data['vegetation_cover']['mean'] < 0.3:
            strategies.append({
                'type': 'planning',
                'category': 'greening',
                'strategy': 'Develop urban forest and green corridor networks',
                'priority': 'medium'
            })
        
        if climate_impact['flood_risk']['risk_level'] == 'high':
            strategies.append({
                'type': 'infrastructure',
                'category': 'resilience',
                'strategy': 'Elevate critical infrastructure and implement flood-proofing',
                'priority': 'high'
            })
        
        return strategies

    # Helper methods for descriptions and classifications
    def _get_flood_risk_description(self, risk_level: str, elevation: float) -> str:
        descriptions = {
            'high': f"High flood risk due to low elevation ({elevation:.1f}m). Consider flood protection measures.",
            'medium': f"Moderate flood risk at {elevation:.1f}m elevation. Monitor drainage capacity.",
            'low': f"Low flood risk at {elevation:.1f}m elevation. Standard drainage sufficient."
        }
        return descriptions.get(risk_level, "Flood risk assessment unavailable.")

    def _get_heat_risk_description(self, risk_level: str, temperature: float) -> str:
        descriptions = {
            'high': f"High heat risk ({temperature:.1f}°C). Urban heat island effect significant.",
            'medium': f"Moderate heat risk ({temperature:.1f}°C). Consider heat mitigation strategies.", 
            'low': f"Low heat risk ({temperature:.1f}°C). Thermal comfort generally maintained."
        }
        return descriptions.get(risk_level, "Heat risk assessment unavailable.")

    def _get_precipitation_description(self, risk_level: str, precipitation: float) -> str:
        descriptions = {
            'high_flood_risk': f"High precipitation ({precipitation:.0f}mm/year) indicates flood risk.",
            'high_drought_risk': f"Low precipitation ({precipitation:.0f}mm/year) indicates drought risk.",
            'moderate': f"Moderate precipitation ({precipitation:.0f}mm/year). Balanced water availability."
        }
        return descriptions.get(risk_level, "Precipitation assessment unavailable.")

    def _classify_topography(self, elevation: float, slope: float) -> str:
        if elevation < 10:
            return "lowland"
        elif elevation < 100:
            return "plain" if slope < 5 else "rolling_hills"
        else:
            return "upland" if slope < 10 else "mountainous"

    def _calculate_composite_climate_risk(self, flood_risk: Dict, heat_effect: Dict) -> Dict:
        flood_score = flood_risk.get('risk_score', 0.5)
        heat_score = heat_effect.get('risk_score', 0.5)
        composite_score = (flood_score + heat_score) / 2
        
        if composite_score > 0.7:
            level = "high"
        elif composite_score > 0.4:
            level = "medium" 
        else:
            level = "low"
            
        return {'risk_score': round(composite_score, 3), 'risk_level': level}

    # Fallback methods for when climate datasets fail
    async def _get_fallback_climate_data(self, lat: float, lng: float) -> Dict:
        logger.warning("Using fallback climate data")
        return {
            'flood_risk': await self._get_fallback_flood_risk(lat, lng),
            'heat_island_effect': await self._get_fallback_heat_data(lat, lng),
            'precipitation_changes': await self._get_fallback_precipitation(lat, lng),
            'elevation': {'elevation': 0, 'slope': 0, 'topography': 'unknown'},
            'composite_risk_score': {'risk_score': 0.5, 'risk_level': 'medium'}
        }

    async def _get_fallback_flood_risk(self, lat: float, lng: float) -> Dict:
        return {'risk_level': 'medium', 'risk_score': 0.5, 'elevation_m': 0, 'factors': ['fallback'], 'description': 'Using estimated flood risk'}

    async def _get_fallback_heat_data(self, lat: float, lng: float) -> Dict:
        return {'risk_level': 'medium', 'risk_score': 0.5, 'mean_temperature_c': 25.0, 'description': 'Using estimated heat risk'}

    async def _get_fallback_precipitation(self, lat: float, lng: float) -> Dict:
        return {'risk_level': 'moderate', 'risk_score': 0.3, 'annual_precipitation_mm': 800, 'description': 'Using estimated precipitation'}

# Singleton instance
analysis_service = AnalysisService()