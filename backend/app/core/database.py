"""
Database Configuration and Session Management

This module sets up SQLAlchemy with async support for PostgreSQL.
It provides the database engine, session factory, and helper functions
for database initialization.

Usage:
    from app.core.database import get_db
    
    @app.get("/items")
    async def read_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Convert standard PostgreSQL URL to async version
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
# echo=True enables SQL query logging (disable in production for performance)
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10,
)

# Session factory for creating database sessions
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)

# Base class for SQLAlchemy models
Base = declarative_base()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    This function creates all tables defined in SQLAlchemy models.
    In production, use Alembic migrations instead for better control.
    
    Raises:
        Exception: If database connection or table creation fails.
    """
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered
        from app.models import user, garden, plant, weather  # noqa: F401
        
        # Create all tables (use alembic for production)
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that provides a database session.
    
    This is used with FastAPI's dependency injection to provide
    a database session to route handlers. The session is automatically
    closed after the request completes.
    
    Yields:
        AsyncSession: Database session for the current request.
        
    Example:
        >>> @app.get("/users")
        >>> async def get_users(db: AsyncSession = Depends(get_db)):
        >>>     result = await db.execute(select(User))
        >>>     return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
