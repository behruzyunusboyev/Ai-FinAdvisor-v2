"""Add explicit annual tax calculation bases to financial inputs.

Revision ID: 0002_financial_tax_inputs
Revises: 0001_initial_schema
Create Date: 2026-10-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_financial_tax_inputs"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "financial_inputs",
        sa.Column("annual_revenue_excluding_vat", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "financial_inputs",
        sa.Column("annual_input_vat", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "financial_inputs",
        sa.Column("annual_taxable_profit", sa.Numeric(18, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_inputs", "annual_taxable_profit")
    op.drop_column("financial_inputs", "annual_input_vat")
    op.drop_column("financial_inputs", "annual_revenue_excluding_vat")
