# routes/__init__.py
from .places import router as places_router
from .predict import router as predict_router  
from .generate import router as generate_router
from .health import router as health_router

# Only include routes that actually exist
__all__ = ["places_router", "predict_router", "generate_router", "health_router"]