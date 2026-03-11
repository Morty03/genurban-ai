from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def health():
    """
    Simple health endpoint to check the service is alive.
    """
    return {"status": "ok"}
