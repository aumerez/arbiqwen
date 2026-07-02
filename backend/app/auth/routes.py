"""Authentication routes: login, token refresh, and current-user lookup."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.jwt import (
    _parse_duration_minutes,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.auth.models import RefreshToken, User
from app.auth.password import verify_password
from app.auth.schemas import LoginSchema, RefreshSchema, TokenSchema, UserResponseSchema
from app.config import settings
from app.database.connection import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


def _claims(user: User) -> dict:
    return {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": user.tenant_id,
        "email_verified": user.email_verified,
        "role": user.role,
    }


def _refresh_days() -> int:
    return _parse_duration_minutes(settings.REFRESH_TOKEN_EXPIRES_IN) // 1440 or 7


async def _store_refresh_token(session: AsyncSession, user_id: int, token: str) -> None:
    session.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(days=_refresh_days()),
        )
    )


@router.post("/login", response_model=TokenSchema, response_model_exclude_none=True)
async def login(login_data: LoginSchema, session: AsyncSession = Depends(get_session)):
    """Authenticate with email/password and return access + refresh tokens."""
    user = (await session.execute(select(User).where(User.email == login_data.email))).scalar_one_or_none()
    if user is None or user.password_hash is None or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled")

    access_token = create_access_token(_claims(user))
    refresh_token = create_refresh_token({"sub": str(user.id)}, expires_days=_refresh_days())
    await _store_refresh_token(session, user.id, refresh_token)

    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "email_verified": user.email_verified,
        },
    }


@router.post("/refresh", response_model=TokenSchema, response_model_exclude_none=True)
async def refresh(refresh_data: RefreshSchema, session: AsyncSession = Depends(get_session)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    payload = decode_token(refresh_data.refresh_token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    incoming_hash = hash_token(refresh_data.refresh_token)
    stored = (
        await session.execute(select(RefreshToken).where(RefreshToken.token_hash == incoming_hash))
    ).scalar_one_or_none()
    if stored is None or stored.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not recognized")

    user = (await session.execute(select(User).where(User.id == int(payload["sub"])))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer active")

    # Rotate: revoke the presented token and issue a fresh pair.
    stored.revoked = True
    access_token = create_access_token(_claims(user))
    new_refresh_token = create_refresh_token({"sub": str(user.id)}, expires_days=_refresh_days())
    await _store_refresh_token(session, user.id, new_refresh_token)

    return {"accessToken": access_token, "refreshToken": new_refresh_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponseSchema)
async def me(current=Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Return the authenticated user's profile."""
    user = (await session.execute(select(User).where(User.id == current["id"]))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponseSchema(
        id=user.id,
        email=user.email,
        tenant_id=user.tenant_id,
        email_verified=user.email_verified,
        role=user.role,
    )
