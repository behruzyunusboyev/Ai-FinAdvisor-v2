"""Payme payment and subscription entitlement records."""

import enum
import uuid

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    PERFORMED = "performed"
    CANCELLED = "cancelled"


class Payment(Base):
    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount_tiyin: Mapped[int] = mapped_column(BigInteger, nullable=False)
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False)
    payme_transaction_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="payment_status",
            create_constraint=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        default=PaymentStatus.CREATED, nullable=False,
    )
    payme_create_time: Mapped[int | None] = mapped_column(BigInteger)
    payme_perform_time: Mapped[int | None] = mapped_column(BigInteger)
    payme_cancel_time: Mapped[int | None] = mapped_column(BigInteger)
    cancel_reason: Mapped[int | None] = mapped_column(Integer)


class Subscription(Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False)
    current_period_end_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    last_payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False,
    )
