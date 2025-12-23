"""
Plants API Endpoints (Stub)

Provides CRUD operations for plants within gardens.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_plants():
    """List all plants (to be implemented)"""
    return {"message": "Plants endpoint - to be implemented"}


@router.post("/")
async def create_plant():
    """Create a new plant (to be implemented)"""
    return {"message": "Create plant - to be implemented"}
