"""Store the selected loan repayment method.

Revision ID: 0003_loan_repayment_method
Revises: 0002_financial_tax_inputs
Create Date: 2026-10-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0003_loan_repayment_method"
down_revision: Union[str, None] = "0002_financial_tax_inputs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


loan_repayment_method = postgresql.ENUM(
    "annuity", "differentiated",
    name="loan_repayment_method",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    loan_repayment_method.create(bind, checkfirst=True)
    op.add_column(
        "financial_inputs",
        sa.Column("loan_repayment_method", loan_repayment_method, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_inputs", "loan_repayment_method")
    loan_repayment_method.drop(op.get_bind(), checkfirst=True)
