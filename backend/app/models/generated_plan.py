"""
Generated Plan SQLAlchemy model.

Stores the output of the financial calculation engine and AI narrative.
"""

import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PlanStatus(str, enum.Enum):
    """Lifecycle status of a generated plan."""

    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class GeneratedPlan(Base):
    """Computed business / financial plan linked to a business profile."""

    __tablename__ = "generated_plans"

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Calculation results ──────────────────────────────────────
    financial_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Deterministic engine output: revenue, costs, projections, etc.",
    )

    # ── AI narrative ─────────────────────────────────────────────
    ai_narrative: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="LLM-generated narrative summary (not used for calculations)",
    )

    # ── Scores ───────────────────────────────────────────────────
    bank_readiness_score: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="0–100 score indicating bank-readiness of the plan",
    )

    # ── Exports ──────────────────────────────────────────────────
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    excel_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Status ───────────────────────────────────────────────────
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="plan_status", create_constraint=True),
        default=PlanStatus.DRAFT,
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    business_profile = relationship(
        "BusinessProfile", back_populates="generated_plans",
    )
