"""
Garden Database Model

Represents a physical garden location with geospatial data.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.core.database import Base


class Garden(Base):
    """
    Garden model with PostGIS support for geospatial queries.
    
    Attributes:
        id: Unique garden identifier (UUID).
        user_id: Foreign key to owner's user ID.
        name: Garden name (e.g., "Backyard Vegetable Garden").
        description: Optional detailed description.
        latitude: Geographic latitude (-90 to 90).
        longitude: Geographic longitude (-180 to 180).
        location: PostGIS geography point (auto-calculated from lat/lng).
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        owner: Relationship to User model.
        plants: Relationship to Plant models (one-to-many).
    """
    
    __tablename__ = "gardens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Geospatial data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # PostGIS geography column for spatial queries
    # This is auto-populated from latitude/longitude via trigger
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    owner = relationship("User", back_populates="gardens")
    plants = relationship("Plant", back_populates="garden", cascade="all, delete-orphan")
