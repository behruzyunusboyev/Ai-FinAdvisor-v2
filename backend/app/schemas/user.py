"""
User Pydantic schemas — Create, Read, Update.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


# ── Create ───────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


# ── Read ─────────────────────────────────────────────────────────

class UserRead(BaseModel):
    """Public user representation (no password)."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Update ───────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    """Fields a user may update on their own profile."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


# ── Login ────────────────────────────────────────────────────────

class UserLogin(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str
