"""Authentication dependencies."""

from fastapi import Header, HTTPException, status

from app.auth.jwt import decode_token


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    """Extract the user from the JWT in the Authorization header.

    Returns a dict with id, email, tenant_id, email_verified, role.
    Raises 401 on missing, malformed, or expired tokens.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    payload = decode_token(authorization.split(" ", 1)[1])
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return {
        "id": int(payload["sub"]),
        "email": payload.get("email"),
        "tenant_id": payload.get("tenant_id", 1),
        "email_verified": payload.get("email_verified", False),
        "role": payload.get("role", "user"),
    }
