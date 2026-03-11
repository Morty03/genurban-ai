from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="GENURBAN API",
    description="Generative Satellite Vision for Urban Morphology Simulation"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic routes without Earth Engine dependencies
@app.get("/")
async def root():
    return {
        "message": "GENURBAN API - Generative Urban Morphology Simulation",
        "version": "1.0",
        "status": "API is running (Earth Engine disabled for testing)"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "earth_engine": "disabled"}

@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working!", "test_data": {
        "urban_density": 0.45,
        "vegetation_cover": 0.32,
        "built_up_area": 0.51
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)