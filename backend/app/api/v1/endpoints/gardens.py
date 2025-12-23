"""
Gardens API Endpoints

This module provides CRUD operations for gardens.
All endpoints require authentication (JWT token).

Endpoints:
    GET /api/v1/gardens - List user's gardens
    POST /api/v1/gardens - Create new garden
    GET /api/v1/gardens/{garden_id} - Get garden details
    PUT /api/v1/gardens/{garden_id} - Update garden
    DELETE /api/v1/gardens/{garden_id} - Delete garden
"""

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.garden import Garden
from app.models.user import User
from app.schemas import GardenCreate, GardenUpdate, GardenResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[GardenResponse])
async def list_gardens(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> List[Garden]:
    """
    Retrieve all gardens owned by the authenticated user.
    
    Args:
        db: Database session (injected).
        current_user: Authenticated user (injected from JWT).
        skip: Number of records to skip (pagination).
        limit: Maximum number of records to return.
        
    Returns:
        List[Garden]: User's gardens.
        
    Raises:
        HTTPException: 401 if not authenticated.
    """
    result = await db.execute(
        select(Garden)
        .where(Garden.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    gardens = result.scalars().all()
    return gardens


@router.post("/", response_model=GardenResponse, status_code=status.HTTP_201_CREATED)
async def create_garden(
    garden_in: GardenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Garden:
    """
    Create a new garden for the authenticated user.
    
    Args:
        garden_in: Garden data from request body.
        db: Database session (injected).
        current_user: Authenticated user (injected from JWT).
        
    Returns:
        Garden: Created garden with generated ID.
        
    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 422 if validation fails.
    """
    garden = Garden(
        **garden_in.model_dump(),
        user_id=current_user.id
    )
    db.add(garden)
    await db.commit()
    await db.refresh(garden)
    return garden


@router.get("/{garden_id}", response_model=GardenResponse)
async def get_garden(
    garden_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Garden:
    """
    Retrieve a specific garden by ID.
    
    Args:
        garden_id: UUID of the garden to retrieve.
        db: Database session (injected).
        current_user: Authenticated user (injected from JWT).
        
    Returns:
        Garden: Requested garden.
        
    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if garden belongs to another user.
        HTTPException: 404 if garden not found.
    """
    result = await db.execute(
        select(Garden).where(Garden.id == garden_id)
    )
    garden = result.scalar_one_or_none()
    
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Garden not found"
        )
    
    # Ensure user owns this garden
    if garden.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this garden"
        )
    
    return garden


@router.put("/{garden_id}", response_model=GardenResponse)
async def update_garden(
    garden_id: UUID,
    garden_in: GardenUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Garden:
    """
    Update an existing garden.
    
    Only provided fields will be updated (partial update).
    
    Args:
        garden_id: UUID of the garden to update.
        garden_in: Garden data to update (partial).
        db: Database session (injected).
        current_user: Authenticated user (injected from JWT).
        
    Returns:
        Garden: Updated garden.
        
    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if garden belongs to another user.
        HTTPException: 404 if garden not found.
    """
    result = await db.execute(
        select(Garden).where(Garden.id == garden_id)
    )
    garden = result.scalar_one_or_none()
    
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Garden not found"
        )
    
    if garden.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this garden"
        )
    
    # Update only provided fields
    update_data = garden_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(garden, field, value)
    
    await db.commit()
    await db.refresh(garden)
    return garden


@router.delete("/{garden_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_garden(
    garden_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a garden and all associated plants.
    
    Args:
        garden_id: UUID of the garden to delete.
        db: Database session (injected).
        current_user: Authenticated user (injected from JWT).
        
    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 403 if garden belongs to another user.
        HTTPException: 404 if garden not found.
    """
    result = await db.execute(
        select(Garden).where(Garden.id == garden_id)
    )
    garden = result.scalar_one_or_none()
    
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Garden not found"
        )
    
    if garden.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this garden"
        )
    
    await db.delete(garden)
    await db.commit()
