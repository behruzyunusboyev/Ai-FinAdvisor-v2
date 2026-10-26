"""Store annual after-tax income used by the ROI calculation.

Revision ID: 0004_net_income_for_roi
Revises: 0003_loan_repayment_method
Create Date: 2026-10-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_net_income_for_roi"
down_revision: Union[str, None] = "0003_loan_repayment_method"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "financial_inputs",
        sa.Column("annual_net_income_after_tax", sa.Numeric(18, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_inputs", "annual_net_income_after_tax")
