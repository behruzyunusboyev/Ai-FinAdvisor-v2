"""
Business Profile Pydantic schemas — Create, Read, Update.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.business_profile import BusinessType


# ── Create ───────────────────────────────────────────────────────

class BusinessProfileCreate(BaseModel):
    """Payload for creating a new business profile."""

    business_name: str = Field(..., min_length=1, max_length=255)
    business_type: BusinessType
    location: Optional[str] = Field(None, max_length=500)
    seating_capacity: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None


# ── Read ─────────────────────────────────────────────────────────

class BusinessProfileRead(BaseModel):
    """Full business profile returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    business_name: str
    business_type: BusinessType
    location: Optional[str] = None
    seating_capacity: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Update ───────────────────────────────────────────────────────

class BusinessProfileUpdate(BaseModel):
    """Partial update for a business profile."""

    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_type: Optional[BusinessType] = None
    location: Optional[str] = Field(None, max_length=500)
    seating_capacity: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
