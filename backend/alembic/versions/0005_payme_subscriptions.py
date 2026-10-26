"""Add Payme payments and SaaS subscription entitlements.

Revision ID: 0005_payme_subscriptions
Revises: 0004_net_income_for_roi
Create Date: 2026-10-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0005_payme_subscriptions"
down_revision: Union[str, None] = "0004_net_income_for_roi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


payment_status = postgresql.ENUM(
    "created", "performed", "cancelled", name="payment_status", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    payment_status.create(bind, checkfirst=True)
    op.create_table(
        "payments",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_tiyin", sa.BigInteger(), nullable=False),
        sa.Column("plan_code", sa.String(length=40), nullable=False),
        sa.Column("payme_transaction_id", sa.String(length=100), nullable=True),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("payme_create_time", sa.BigInteger(), nullable=True),
        sa.Column("payme_perform_time", sa.BigInteger(), nullable=True),
        sa.Column("payme_cancel_time", sa.BigInteger(), nullable=True),
        sa.Column("cancel_reason", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payme_transaction_id"),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_table(
        "subscriptions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_code", sa.String(length=40), nullable=False),
        sa.Column("current_period_end_ms", sa.BigInteger(), nullable=False),
        sa.Column("last_payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["last_payment_id"], ["payments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")
    payment_status.drop(op.get_bind(), checkfirst=True)
