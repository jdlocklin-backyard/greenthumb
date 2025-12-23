"""
Weather Database Model

Stores historical weather data for gardens.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Weather(Base):
    """
    Weather data model for storing historical weather conditions.
    
    Data is collected by the autonomous agent from external APIs.
    
    Attributes:
        id: Unique weather record identifier (UUID).
        garden_id: Foreign key to garden this data applies to.
        temperature: Temperature in Celsius.
        humidity: Relative humidity percentage (0-100).
        precipitation: Precipitation in mm.
        wind_speed: Wind speed in km/h.
        condition: Weather condition description (e.g., "Clear", "Rainy").
        recorded_at: When this weather data was recorded.
        created_at: Database record creation timestamp.
    """
    
    __tablename__ = "weather"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    garden_id = Column(UUID(as_uuid=True), ForeignKey("gardens.id"), nullable=False, index=True)
    
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    precipitation = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    condition = Column(String(100), nullable=False)
    
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
