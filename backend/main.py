"""
GreenThumb Backend API - FastAPI Application

This module serves as the entry point for the GreenThumb REST API.
It provides endpoints for managing gardens, plants, weather data, and user profiles.

The API follows RESTful conventions and includes:
- Automatic OpenAPI/Swagger documentation at /docs
- CORS support for frontend integration
- Health check endpoint for monitoring
- JWT-based authentication

Example:
    Run the application with uvicorn:
    
    $ uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import engine, init_db
from app.api.v1.router import api_router
from app.core.logging_config import setup_logging

# Configure structured logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database connection pool
    - Shutdown: Close database connections gracefully
    
    Args:
        app: The FastAPI application instance.
        
    Yields:
        None: Control flow during application lifetime.
        
    Raises:
        Exception: If database initialization fails (app won't start).
    """
    logger.info("Starting GreenThumb API", extra={
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    })
    
    try:
        # Initialize database (create tables if needed)
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        sys.exit(1)
    
    yield
    
    # Shutdown: Close connections
    logger.info("Shutting down GreenThumb API")
    await engine.dispose()


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Self-hosted gardening platform for home lab enthusiasts",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# =============================================================================
# Middleware Configuration
# =============================================================================

# CORS middleware - allows frontend to make requests
# In production, restrict origins to your actual frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed error messages.
    
    Args:
        request: The incoming HTTP request.
        exc: The validation error exception.
        
    Returns:
        JSONResponse: Formatted error response with field-level details.
    """
    logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Global exception handler for unhandled errors.
    
    Logs the full exception and returns a generic error to the client
    to avoid leaking internal implementation details.
    
    Args:
        request: The incoming HTTP request.
        exc: The unhandled exception.
        
    Returns:
        JSONResponse: Generic 500 error response.
    """
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# =============================================================================
# Routes
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns a simple status response to verify the API is running.
    Used by Docker healthcheck and Traefik.
    
    Returns:
        dict: Status message indicating the API is healthy.
        
    Example:
        >>> GET /health
        {"status": "healthy"}
    """
    return {"status": "healthy"}


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """
    Root endpoint with API information.
    
    Returns:
        dict: API name and version information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }


# Include API router with versioned endpoints
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.API_LOG_LEVEL.lower()
    )
