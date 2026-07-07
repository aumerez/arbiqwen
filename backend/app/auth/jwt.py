import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

ALGORITHM = "HS256"


def _parse_duration_minutes(duration_str: str) -> int:
    """Parse duration string like '15m', '2h', '1d' to minutes."""
    duration_str = duration_str.strip().lower()
    if duration_str.endswith("d"):
        return int(duration_str[:-1]) * 1440
    if duration_str.endswith("h"):
        return int(duration_str[:-1]) * 60
    if duration_str.endswith("m"):
        return int(duration_str[:-1])
    return int(duration_str)


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    """Create an access token (HS256, signed with settings.JWT_SECRET).

    Uses JWT_EXPIRES_IN from settings when no explicit expiry is given. A unique
    `jti` is added for symmetry with refresh tokens.
    """
    if expires_minutes is None:
        expires_minutes = _parse_duration_minutes(settings.JWT_EXPIRES_IN)
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    to_encode["exp"] = int(expire.timestamp())
    to_encode["jti"] = uuid.uuid4().hex
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_days: int = 7) -> str:
    """Create a refresh token (HS256, default 7-day expiry).

    A unique `jti` per call guarantees two refreshes for the same user in the
    same second produce different tokens, so their SHA-256 hashes don't collide
    on the UNIQUE constraint over refresh_tokens.token_hash.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=expires_days)
    to_encode["exp"] = int(expire.timestamp())
    to_encode["jti"] = uuid.uuid4().hex
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns the payload, or None if invalid/expired.

    Allows 30s of leeway on exp/nbf so small clock drift between client and
    backend doesn't flap an otherwise-valid session into a 401.
    """
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[ALGORITHM],
            leeway=timedelta(seconds=30),
        )
    except jwt.PyJWTError:
        return None


def hash_token(token: str) -> str:
    """SHA-256 hash of a token string for DB storage/lookup."""
    return hashlib.sha256(token.encode()).hexdigest()
