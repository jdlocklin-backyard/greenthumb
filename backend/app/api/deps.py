"""
Authentication Dependencies

This module provides dependency functions for FastAPI routes that require
authentication. It handles JWT token validation and user retrieval.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas import TokenData

# HTTP Bearer token scheme for Swagger UI
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token and retrieve the current authenticated user.
    
    This dependency is used in protected routes to ensure the user is authenticated.
    The JWT token is extracted from the Authorization header (Bearer scheme).
    
    Args:
        credentials: HTTP Bearer token from Authorization header.
        db: Database session (injected).
        
    Returns:
        User: The authenticated user object.
        
    Raises:
        HTTPException: 401 if token is invalid or user not found.
        
    Example:
        >>> @app.get("/protected")
        >>> async def protected_route(user: User = Depends(get_current_user)):
        >>>     return {"user_id": user.id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract user ID from token
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        user_id = UUID(user_id_str)
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user
