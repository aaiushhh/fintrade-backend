"""Auth module — Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ── Request schemas ──────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Response schemas ─────────────────────────────────────────────────
class RoleResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    roles: List[RoleResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
