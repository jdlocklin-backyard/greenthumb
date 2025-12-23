"""
Plant Database Model

Represents individual plants within a garden.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Plant(Base):
    """
    Plant model for tracking individual plants in gardens.
    
    Attributes:
        id: Unique plant identifier (UUID).
        garden_id: Foreign key to parent garden.
        name: Common plant name (e.g., "Tomato").
        scientific_name: Optional Latin name (e.g., "Solanum lycopersicum").
        variety: Optional variety (e.g., "Cherry").
        plant_date: When the plant was planted.
        harvest_date: Expected or actual harvest date.
        notes: Freeform notes about growth, care, etc.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.
        garden: Relationship to Garden model.
    """
    
    __tablename__ = "plants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    garden_id = Column(UUID(as_uuid=True), ForeignKey("gardens.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    scientific_name = Column(String(255), nullable=True)
    variety = Column(String(255), nullable=True)
    
    plant_date = Column(DateTime, nullable=True)
    harvest_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    garden = relationship("Garden", back_populates="plants")
