from fastapi import FastAPI
import uvicorn

app = FastAPI(title="GENURBAN Test API")

@app.get("/")
def root():
    return {"message": "GENURBAN API is working!", "status": "online"}

@app.get("/health")
def health():
    return {"status": "healthy", "earth_engine": "checking..."}

@app.get("/test")
def test():
    return {"test": "success", "data": {"urban_density": 0.45, "vegetation": 0.32}}

if __name__ == "__main__":
    print("🚀 Starting test server on http://localhost:8000")
    print("📡 Access at: http://localhost:8000")
    print("❌ Press CTRL+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)  # reload=False for direct run