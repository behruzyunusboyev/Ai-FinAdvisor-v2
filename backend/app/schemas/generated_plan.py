"""
Generated Plan Pydantic schemas — Create, Read, Update.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.generated_plan import PlanStatus


# ── Create ───────────────────────────────────────────────────────

class GeneratedPlanCreate(BaseModel):
    """Payload to kick off plan generation."""

    business_profile_id: uuid.UUID
    status: PlanStatus = PlanStatus.DRAFT


# ── Read ─────────────────────────────────────────────────────────

class GeneratedPlanRead(BaseModel):
    """Full generated plan response."""

    id: uuid.UUID
    business_profile_id: uuid.UUID
    financial_data: Optional[dict[str, Any]] = None
    ai_narrative: Optional[str] = None
    bank_readiness_score: Optional[float] = None
    pdf_url: Optional[str] = None
    excel_url: Optional[str] = None
    status: PlanStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Update ───────────────────────────────────────────────────────

class GeneratedPlanUpdate(BaseModel):
    """Partial update — typically set by the engine/service layer."""

    financial_data: Optional[dict[str, Any]] = None
    ai_narrative: Optional[str] = None
    bank_readiness_score: Optional[float] = Field(None, ge=0, le=100)
    pdf_url: Optional[str] = None
    excel_url: Optional[str] = None
    status: Optional[PlanStatus] = None
