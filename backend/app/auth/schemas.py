from pydantic import BaseModel, EmailStr, Field


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserInLoginResponse(BaseModel):
    """User info returned at login so the client never needs to decode the JWT."""

    id: int
    email: str
    tenant_id: int
    role: str = "user"
    email_verified: bool = False
    must_change_password: bool = False


class UserResponseSchema(BaseModel):
    id: int
    email: str
    tenant_id: int
    email_verified: bool = False
    role: str = "user"
    must_change_password: bool = False


class TokenSchema(BaseModel):
    accessToken: str
    refreshToken: str
    token_type: str = "bearer"
    user: UserInLoginResponse | None = None


class RefreshSchema(BaseModel):
    refresh_token: str
