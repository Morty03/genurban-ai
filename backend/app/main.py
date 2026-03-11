# main.py - GENURBAN Backend (Clean & Fixed)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from pathlib import Path

# Ensure routes can be imported correctly
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import routers
try:
    from routes.generate import router as generate_router
    from routes.health import router as health_router
    from routes.places import router as places_router
    from routes.predict import router as predict_router
    print("✅ All routes imported successfully")
except Exception as e:
    print(f"❌ Route import error: {e}")
    routes_path = current_dir / "routes"
    print("📁 Available route files:")
    for f in routes_path.glob("*.py"):
        print("  -", f.name)


# -------------------------------------------------------------
#  Create FastAPI App
# -------------------------------------------------------------
def create_app():
    app = FastAPI(
        title="GENURBAN Backend API",
        description="Generative Satellite Vision for Urban Morphology & Climate Simulation",
        version="1.0.0",
    )

    # ---------------------------------------------------------
    # CORS — REQUIRED FOR FRONTEND TO WORK (IMPORTANT)
    # Vite DEFAULT = http://localhost:5173
    # React CRA = http://localhost:3000
    # ---------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",   # Vite
            "http://127.0.0.1:5173",
            "http://localhost:3000",   # CRA
            "http://127.0.0.1:3000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------------------------------------------------------
    # Routers
    # ---------------------------------------------------------
    app.include_router(generate_router, prefix="/api/v1/generate", tags=["generation"])
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
    app.include_router(places_router, prefix="/api/v1", tags=["places"])
    app.include_router(predict_router, prefix="/api/v1", tags=["prediction"])

    # ---------------------------------------------------------
    # Root endpoint
    # ---------------------------------------------------------
    @app.get("/")
    async def root():
        return {
            "message": "GENURBAN Backend API",
            "version": "1.0.0",
            "endpoints": {
                "generate_scenarios": "/api/v1/generate/scenarios",
                "search_location": "/api/v1/search-location",
                "analyze_urban": "/api/v1/analyze-urban-morphology",
                "urban_growth": "/api/v1/urban-growth",
                "health": "/api/v1/health"
            }
        }

    return app


# Shared app instance
app = create_app()


# -------------------------------------------------------------
# Run Uvicorn
# -------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting GENURBAN Backend Server...")
    print("🌏 Earth Engine Initiated...")
    print("📊 Available endpoints:")
    print("   - http://localhost:8001/")
    print("   - http://localhost:8001/docs")
    print("   - http://localhost:8001/api/v1/health")
    

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
