"""
Application Configuration Module

This module loads and validates all configuration from environment variables.
Uses Pydantic Settings for type-safe configuration management.

The configuration is loaded once at startup and validated immediately,
ensuring the application fails fast if required settings are missing.
"""

from typing import List
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are validated at startup using Pydantic.
    Missing required settings will cause the application to fail immediately.
    
    Attributes:
        APP_NAME: Application name for logging and API docs.
        VERSION: Current version of the application.
        ENVIRONMENT: Deployment environment (development/staging/production).
        API_HOST: Host to bind the API server to.
        API_PORT: Port to bind the API server to.
        API_RELOAD: Enable auto-reload for development.
        API_LOG_LEVEL: Logging verbosity level.
        DATABASE_URL: PostgreSQL connection string.
        REDIS_URL: Redis connection string.
        SECRET_KEY: JWT signing key (must be kept secret!).
        ALGORITHM: JWT signing algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time.
        CORS_ORIGINS: Allowed CORS origins for frontend.
        API_V1_PREFIX: URL prefix for API v1 endpoints.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application
    APP_NAME: str = Field(default="GreenThumb", description="Application name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="production", description="Environment")
    
    # API Server
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_RELOAD: bool = Field(default=False, description="Enable auto-reload")
    API_LOG_LEVEL: str = Field(default="INFO", description="Log level")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")
    
    # Database
    POSTGRES_USER: str = Field(..., description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_HOST: str = Field(..., description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Construct PostgreSQL connection URL from components.
        
        Returns:
            str: Full database connection URL.
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Redis
    REDIS_HOST: str = Field(..., description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: str = Field(..., description="Redis password")
    
    @property
    def REDIS_URL(self) -> str:
        """
        Construct Redis connection URL from components.
        
        Returns:
            str: Full Redis connection URL.
        """
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    # Security
    SECRET_KEY: str = Field(
        ...,
        description="Secret key for JWT signing (generate with: openssl rand -hex 32)"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration in minutes"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "https://green.lab"],
        description="Allowed CORS origins"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """
        Parse CORS origins from string or list.
        
        Allows environment variable to be comma-separated string.
        
        Args:
            v: CORS origins as string or list.
            
        Returns:
            List[str]: Parsed list of origins.
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


# Create global settings instance
# This is loaded once at module import and reused throughout the application
settings = Settings()
