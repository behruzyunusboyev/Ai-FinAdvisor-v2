"""
User SQLAlchemy model.
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    """Allowed user roles."""

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """Registered platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    business_profiles = relationship(
        "BusinessProfile",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
