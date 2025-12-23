"""
Pydantic Schemas for API Request/Response Validation

This module defines all Pydantic models used for API serialization
and validation. These ensure type safety and automatic validation
of incoming requests and outgoing responses.

Why separate schemas from database models:
- Database models (SQLAlchemy) handle persistence
- Schemas (Pydantic) handle API serialization/validation
- This separation allows flexibility in API design without affecting DB
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Base Schemas
# =============================================================================

class TimestampMixin(BaseModel):
    """
    Mixin for models with timestamp fields.
    
    Attributes:
        created_at: When the record was created.
        updated_at: When the record was last updated.
    """
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Garden Schemas
# =============================================================================

class GardenBase(BaseModel):
    """
    Base garden schema with shared fields.
    
    Attributes:
        name: Garden name (e.g., "Backyard Vegetable Garden").
        description: Optional detailed description.
        latitude: Geographic latitude for weather data.
        longitude: Geographic longitude for weather data.
    """
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class GardenCreate(GardenBase):
    """
    Schema for creating a new garden.
    
    Inherits all fields from GardenBase.
    User ID will be extracted from JWT token.
    """
    pass


class GardenUpdate(BaseModel):
    """
    Schema for updating an existing garden.
    
    All fields are optional to support partial updates.
    
    Attributes:
        name: Updated garden name.
        description: Updated description.
        latitude: Updated latitude.
        longitude: Updated longitude.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class GardenResponse(GardenBase, TimestampMixin):
    """
    Schema for garden responses.
    
    Includes all garden data plus metadata (ID, timestamps).
    
    Attributes:
        id: Unique garden identifier.
        user_id: Owner's user ID.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID


# =============================================================================
# Plant Schemas
# =============================================================================

class PlantBase(BaseModel):
    """
    Base plant schema with shared fields.
    
    Attributes:
        name: Plant common name (e.g., "Tomato").
        scientific_name: Optional Latin name (e.g., "Solanum lycopersicum").
        variety: Optional variety (e.g., "Cherry").
        plant_date: When the plant was planted.
        harvest_date: Expected or actual harvest date.
        notes: Freeform notes about the plant.
    """
    name: str = Field(..., min_length=1, max_length=255)
    scientific_name: Optional[str] = Field(None, max_length=255)
    variety: Optional[str] = Field(None, max_length=255)
    plant_date: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2000)


class PlantCreate(PlantBase):
    """
    Schema for creating a new plant.
    
    Attributes:
        garden_id: ID of the garden this plant belongs to.
    """
    garden_id: UUID


class PlantUpdate(BaseModel):
    """
    Schema for updating an existing plant.
    
    All fields are optional to support partial updates.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    scientific_name: Optional[str] = Field(None, max_length=255)
    variety: Optional[str] = Field(None, max_length=255)
    plant_date: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2000)


class PlantResponse(PlantBase, TimestampMixin):
    """
    Schema for plant responses.
    
    Attributes:
        id: Unique plant identifier.
        garden_id: Parent garden ID.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    garden_id: UUID


# =============================================================================
# Weather Schemas
# =============================================================================

class WeatherData(BaseModel):
    """
    Current weather conditions for a location.
    
    Data sourced from Open-Meteo or OpenWeatherMap API.
    
    Attributes:
        temperature: Current temperature in Celsius.
        humidity: Relative humidity percentage (0-100).
        precipitation: Precipitation in mm.
        wind_speed: Wind speed in km/h.
        condition: Weather condition description (e.g., "Clear", "Rainy").
        timestamp: When this data was recorded.
    """
    temperature: float
    humidity: float = Field(..., ge=0, le=100)
    precipitation: float = Field(..., ge=0)
    wind_speed: float = Field(..., ge=0)
    condition: str
    timestamp: datetime


class WeatherResponse(BaseModel):
    """
    Response schema for weather data requests.
    
    Attributes:
        garden_id: ID of the garden this weather applies to.
        current: Current weather conditions.
    """
    garden_id: UUID
    current: WeatherData


# =============================================================================
# User Schemas
# =============================================================================

class UserBase(BaseModel):
    """
    Base user schema with shared fields.
    
    Attributes:
        email: User's email address (used for login).
        full_name: Optional full name for display.
    """
    email: str = Field(..., max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """
    Schema for user registration.
    
    Attributes:
        password: Plain text password (will be hashed before storage).
    """
    password: str = Field(..., min_length=8)


class UserResponse(UserBase, TimestampMixin):
    """
    Schema for user responses.
    
    Note: Password hash is never included in responses.
    
    Attributes:
        id: Unique user identifier.
        is_active: Whether the account is active.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool


# =============================================================================
# Authentication Schemas
# =============================================================================

class Token(BaseModel):
    """
    JWT token response.
    
    Attributes:
        access_token: JWT token string.
        token_type: Token type (always "bearer").
    """
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Data extracted from JWT token.
    
    Attributes:
        user_id: Authenticated user's ID.
        email: Authenticated user's email.
    """
    user_id: UUID
    email: str
