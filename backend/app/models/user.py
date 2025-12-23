"""
User Database Model

Represents a user account in the system.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    User account model.
    
    Attributes:
        id: Unique user identifier (UUID).
        email: User's email address (unique, used for login).
        full_name: Optional full name for display.
        hashed_password: Bcrypt hash of user's password.
        is_active: Whether the account is active (can log in).
        created_at: Account creation timestamp.
        updated_at: Last update timestamp.
        gardens: Relationship to user's gardens (one-to-many).
    """
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    gardens = relationship("Garden", back_populates="owner", cascade="all, delete-orphan")
