"""
Authentication API Routes with User Profile Management and Role-Based Access
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta

from database.models import UserLogin, Token, UserProfile, UserRole
from database.mongodb import get_users_collection
from core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user
)
from config import settings

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access tokens with last_login update"""
    user = await authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last_login timestamp
    users_collection = get_users_collection()
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Enforce single admin access
    if user.get("role", UserRole.ADMIN) != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access only"
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user["email"], "role": UserRole.ADMIN},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user["email"]})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    role = current_user.get("role", UserRole.ADMIN)
    return UserProfile(
        id=str(current_user["_id"]),
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        role=role,
        phone=current_user.get("phone"),
        organization=current_user.get("organization"),
        profile_picture_url=current_user.get("profile_picture_url"),
        preferences=current_user.get("preferences", {}),
        created_at=current_user.get("created_at"),
        last_login=current_user.get("last_login")
    )


