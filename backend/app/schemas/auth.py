from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import VersionStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    client_version: str = Field(min_length=1, max_length=64)
    client_content_version_key: str = Field(default="unknown", min_length=1, max_length=64)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=255)
    client_version: str = Field(min_length=1, max_length=64)
    client_content_version_key: str = Field(default="unknown", min_length=1, max_length=64)


class SessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    session_id: str
    user_id: int
    email: EmailStr
    display_name: str
    is_admin: bool
    expires_at: datetime
    version_status: VersionStatus
