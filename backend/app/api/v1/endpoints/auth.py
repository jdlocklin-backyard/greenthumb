"""
Authentication Endpoints

Provides user registration and login functionality with JWT tokens.

Endpoints:
    POST /api/v1/auth/register - Create new user account
    POST /api/v1/auth/login - Authenticate and receive JWT token
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas import UserCreate, UserResponse, Token

router = APIRouter()

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password to verify.
        hashed_password: The bcrypt hash to verify against.
        
    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash.
        
    Returns:
        str: Bcrypt hash of the password.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to encode in the token.
              Must include "sub" (subject) claim with user ID.
              
    Returns:
        str: Encoded JWT token.
        
    Example:
        >>> token = create_access_token({"sub": str(user.id)})
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Register a new user account.
    
    Args:
        user_in: User registration data (email, password, full_name).
        db: Database session (injected).
        
    Returns:
        User: Created user object (without password hash).
        
    Raises:
        HTTPException: 400 if email already registered.
        HTTPException: 422 if validation fails.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_in.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Authenticate user and return JWT token.
    
    Uses OAuth2 password flow (username/password in form data).
    The "username" field should contain the email address.
    
    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session (injected).
        
    Returns:
        dict: JWT access token and token type.
        
    Raises:
        HTTPException: 401 if credentials are invalid.
        
    Example:
        >>> # Client request
        >>> POST /api/v1/auth/login
        >>> Content-Type: application/x-www-form-urlencoded
        >>> 
        >>> username=user@example.com&password=secret
        >>>
        >>> # Response
        >>> {"access_token": "eyJ...", "token_type": "bearer"}
    """
    # Fetch user by email (form_data.username contains email)
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
