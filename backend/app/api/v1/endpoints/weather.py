"""
Weather API Endpoints (Stub)

Provides weather data for gardens using external APIs.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_weather():
    """Get weather data (to be implemented)"""
    return {"message": "Weather endpoint - to be implemented"}
