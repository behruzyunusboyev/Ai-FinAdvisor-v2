"""
Business Profile SQLAlchemy model.
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BusinessType(str, enum.Enum):
    """Supported business types."""

    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAKERY = "bakery"
    FAST_FOOD = "fast_food"
    OTHER = "other"


class BusinessProfile(Base):
    """A single business entity owned by a user."""

    __tablename__ = "business_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    business_type: Mapped[BusinessType] = mapped_column(
        Enum(BusinessType, name="business_type", create_constraint=True),
        nullable=False,
    )
    location: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )
    seating_capacity: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────
    owner = relationship("User", back_populates="business_profiles")

    financial_inputs = relationship(
        "FinancialInput",
        back_populates="business_profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    generated_plans = relationship(
        "GeneratedPlan",
        back_populates="business_profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
