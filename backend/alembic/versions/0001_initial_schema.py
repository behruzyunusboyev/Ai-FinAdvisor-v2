"""Create the initial FinAdvisor schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role = postgresql.ENUM(
    "user", "admin", name="user_role", create_type=False,
)
business_type = postgresql.ENUM(
    "restaurant", "cafe", "bakery", "fast_food", "other",
    name="business_type", create_type=False,
)
tax_regime = postgresql.ENUM(
    "general", "simplified", "vat_payer", "turnover_tax",
    name="tax_regime", create_type=False,
)
plan_status = postgresql.ENUM(
    "draft", "generating", "completed", "failed", name="plan_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    business_type.create(bind, checkfirst=True)
    tax_regime.create(bind, checkfirst=True)
    plan_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    op.create_table(
        "business_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_name", sa.String(length=255), nullable=False),
        sa.Column("business_type", business_type, nullable=False),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("seating_capacity", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_business_profiles_id", "business_profiles", ["id"], unique=False,
    )
    op.create_index(
        "ix_business_profiles_user_id", "business_profiles", ["user_id"],
        unique=False,
    )

    op.create_table(
        "financial_inputs",
        sa.Column("business_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("menu_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("average_salary", sa.Float(), nullable=True),
        sa.Column("equipment_list", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rent_monthly", sa.Float(), nullable=True),
        sa.Column("utilities_monthly", sa.Float(), nullable=True),
        sa.Column("initial_investment", sa.Float(), nullable=True),
        sa.Column("loan_amount", sa.Float(), nullable=True),
        sa.Column("loan_term_months", sa.Integer(), nullable=True),
        sa.Column("loan_interest_rate", sa.Float(), nullable=True),
        sa.Column("tax_regime", tax_regime, nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["business_profile_id"], ["business_profiles.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_financial_inputs_business_profile_id", "financial_inputs",
        ["business_profile_id"], unique=False,
    )
    op.create_index(
        "ix_financial_inputs_id", "financial_inputs", ["id"], unique=False,
    )

    op.create_table(
        "generated_plans",
        sa.Column("business_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("financial_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_narrative", sa.Text(), nullable=True),
        sa.Column("bank_readiness_score", sa.Float(), nullable=True),
        sa.Column("pdf_url", sa.String(length=500), nullable=True),
        sa.Column("excel_url", sa.String(length=500), nullable=True),
        sa.Column("status", plan_status, nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["business_profile_id"], ["business_profiles.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_generated_plans_business_profile_id", "generated_plans",
        ["business_profile_id"], unique=False,
    )
    op.create_index(
        "ix_generated_plans_id", "generated_plans", ["id"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_generated_plans_id", table_name="generated_plans")
    op.drop_index(
        "ix_generated_plans_business_profile_id", table_name="generated_plans",
    )
    op.drop_table("generated_plans")
    op.drop_index("ix_financial_inputs_id", table_name="financial_inputs")
    op.drop_index(
        "ix_financial_inputs_business_profile_id", table_name="financial_inputs",
    )
    op.drop_table("financial_inputs")
    op.drop_index("ix_business_profiles_user_id", table_name="business_profiles")
    op.drop_index("ix_business_profiles_id", table_name="business_profiles")
    op.drop_table("business_profiles")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    plan_status.drop(bind, checkfirst=True)
    tax_regime.drop(bind, checkfirst=True)
    business_type.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
