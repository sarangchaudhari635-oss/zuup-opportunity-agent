"""
Auth API routes — register, login, refresh, Google OAuth, logout.
"""
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_async_redis
from app.core.security import (
    create_access_token, create_refresh_token,
    decode_token, hash_password, verify_password,
)
from app.models.models import NotificationSettings, StudentProfile, User
from app.schemas.schemas import (
    LoginRequest, MessageResponse, RefreshRequest,
    RegisterRequest, TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


# ── Register ─────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create user
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()  # Get user.id

    # Create empty profile
    profile = StudentProfile(user_id=user.id)
    db.add(profile)

    # Default notification settings
    notif_settings = NotificationSettings(user_id=user.id)
    db.add(notif_settings)

    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


# ── Login ─────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


# ── Refresh Token ─────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        user_id = data["sub"]
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    # Check token not blacklisted
    redis = get_async_redis()
    blacklisted = await redis.get(f"blacklist:refresh:{payload.refresh_token}")
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


# ── Logout ────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(payload: RefreshRequest):
    """Blacklist the refresh token in Redis."""
    try:
        data = decode_token(payload.refresh_token)
        exp = data.get("exp", 0)
        ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))
    except JWTError:
        return MessageResponse(message="Logged out.")

    redis = get_async_redis()
    await redis.setex(f"blacklist:refresh:{payload.refresh_token}", ttl, "1")
    return MessageResponse(message="Logged out successfully.")


# ── Google OAuth ───────────────────────────────────────────────

@router.get("/google")
async def google_oauth_start():
    """Redirect URL for Google OAuth — frontend uses this to start the flow."""
    if not settings.google_client_id or "SECRET" in settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth is not configured. Please register and login using email/password.",
        )
        
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return {"auth_url": f"https://accounts.google.com/o/oauth2/v2/auth?{query}"}


@router.get("/google/callback", response_model=TokenResponse)
async def google_oauth_callback(code: str, db: Session = Depends(get_db)):
    """Exchange Google auth code for user info, create or link account."""
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google auth code.")

        id_token = token_resp.json().get("access_token")

        # Get user info
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {id_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user info.")

        userinfo = userinfo_resp.json()
        google_id = userinfo["id"]
        email = userinfo["email"]
        name = userinfo.get("name", "")

    # Find or create user
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        # Check if email exists (link accounts)
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
        else:
            user = User(email=email, google_id=google_id, is_active=True, is_verified=True)
            db.add(user)
            db.flush()
            profile = StudentProfile(user_id=user.id, name=name)
            db.add(profile)
            notif_settings = NotificationSettings(user_id=user.id)
            db.add(notif_settings)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
