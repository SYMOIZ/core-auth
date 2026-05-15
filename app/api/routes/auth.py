from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.redis import blacklist_token
from app.schemas.user import UserCreate, UserRegistrationResponse
from app.schemas.token import TokenExchangeResponse, StandardActionResponse, RefreshTokenRequest
from app.services.auth_service import create_user, authenticate_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)

router = APIRouter()


@router.post("/register", response_model=UserRegistrationResponse, status_code=201)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    user = await create_user(db, user_in)
    return user


@router.post("/login", response_model=TokenExchangeResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    return TokenExchangeResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenExchangeResponse)
async def refresh_token(
    body: RefreshTokenRequest,
):
    payload = decode_refresh_token(body.refresh_token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )
    access_token = create_access_token({"sub": email})
    new_refresh_token = create_refresh_token({"sub": email})
    return TokenExchangeResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout", response_model=StandardActionResponse)
async def logout(
    body: RefreshTokenRequest,
):
    payload = decode_access_token(body.refresh_token)
    exp = payload.get("exp")
    if exp:
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = exp - now
        if ttl > 0:
            await blacklist_token(body.refresh_token, ttl)
    return StandardActionResponse(detail="Successfully logged out")
