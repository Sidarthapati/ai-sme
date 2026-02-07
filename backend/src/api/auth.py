"""
Authentication endpoints for Google OAuth.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict

from ..database import get_db, User
from ..auth import verify_google_token, create_access_token, verify_token, security
from ..utils import log

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleTokenRequest(BaseModel):
    """Request model for Google OAuth token."""
    token: Optional[str] = None  # ID token


class GoogleUserInfoRequest(BaseModel):
    """Request model for Google user info (from access token)."""
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    google_id: str


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """Response model for user info."""
    id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    request: GoogleTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with Google OAuth ID token.
    Creates user if doesn't exist, returns JWT access token.
    """
    try:
        if not request.token:
            raise HTTPException(status_code=400, detail="Token is required")
        
        # Verify Google ID token
        google_user_info = verify_google_token(request.token)
        
        if not google_user_info.get("email_verified"):
            raise HTTPException(
                status_code=400,
                detail="Email not verified by Google"
            )
        
        email = google_user_info["email"]
        google_id = google_user_info["google_id"]
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        # Create user if doesn't exist
        if user is None:
            user = User(
                email=email,
                name=google_user_info.get("name"),
                picture=google_user_info.get("picture"),
                google_id=google_id,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            log.info(f"Created new user: {email}")
        else:
            # Update user info if changed
            if user.google_id != google_id:
                user.google_id = google_id
            if user.name != google_user_info.get("name"):
                user.name = google_user_info.get("name")
            if user.picture != google_user_info.get("picture"):
                user.picture = google_user_info.get("picture")
            await db.commit()
            await db.refresh(user)
        
        # Create JWT token
        access_token = create_access_token(user.id, user.email)
        
        return AuthResponse(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
            }
        )
        
    except ValueError as e:
        log.error(f"Google auth error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        log.error(f"Unexpected auth error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user info.
    """
    from ..auth.jwt import get_current_user
    
    user = await get_current_user(credentials, db)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
    )


@router.post("/google/userinfo", response_model=AuthResponse)
async def google_auth_userinfo(
    request: GoogleUserInfoRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with Google user info (from access token).
    Alternative to ID token flow - uses user info directly.
    """
    try:
        email = request.email
        google_id = request.google_id
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        # Create user if doesn't exist
        if user is None:
            user = User(
                email=email,
                name=request.name,
                picture=request.picture,
                google_id=google_id,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            log.info(f"Created new user: {email}")
        else:
            # Update user info if changed
            if user.google_id != google_id:
                user.google_id = google_id
            if user.name != request.name:
                user.name = request.name
            if user.picture != request.picture:
                user.picture = request.picture
            await db.commit()
            await db.refresh(user)
        
        # Create JWT token
        access_token = create_access_token(user.id, user.email)
        
        return AuthResponse(
            access_token=access_token,
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
            }
        )
        
    except Exception as e:
        log.error(f"Google auth userinfo error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal).
    Since we use stateless JWT, logout is handled client-side.
    """
    return {"message": "Logged out successfully"}
