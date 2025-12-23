"""
API Router Configuration

This module aggregates all API routes and includes them under the /api/v1 prefix.
New route modules should be imported and included here.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import gardens, plants, weather, auth

# Create main API router
api_router = APIRouter()

# Include sub-routers with tags for OpenAPI documentation
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    gardens.router,
    prefix="/gardens",
    tags=["Gardens"]
)

api_router.include_router(
    plants.router,
    prefix="/plants",
    tags=["Plants"]
)

api_router.include_router(
    weather.router,
    prefix="/weather",
    tags=["Weather"]
)
