"""
Financial Input SQLAlchemy model.

Stores raw financial data entered by the user for a specific business.
All monetary values are stored as floats; currency is UZS unless noted.
"""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import Enum, Float, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.financial import LoanRepaymentMethod, TaxRegime
from app.db.base import Base


class FinancialInput(Base):
    """Raw financial inputs associated with a business profile."""

    __tablename__ = "financial_inputs"

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Revenue / Menu ───────────────────────────────────────────
    menu_items: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of menu items with name, price, cost, category",
    )

    # ── Staff ────────────────────────────────────────────────────
    employee_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    average_salary: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Monthly average salary in UZS",
    )

    # ── Equipment ────────────────────────────────────────────────
    equipment_list: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of equipment items with name, cost, lifespan_years",
    )

    # ── Operating costs ──────────────────────────────────────────
    rent_monthly: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Monthly rent in UZS",
    )
    utilities_monthly: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Monthly utilities in UZS",
    )

    # ── Capital / Loans ──────────────────────────────────────────
    initial_investment: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Total initial investment in UZS",
    )
    loan_amount: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Requested loan amount in UZS",
    )
    loan_term_months: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    loan_interest_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Annual interest rate in %",
    )
    loan_repayment_method: Mapped[LoanRepaymentMethod | None] = mapped_column(
        Enum(
            LoanRepaymentMethod,
            name="loan_repayment_method",
            create_constraint=True,
        ),
        nullable=True,
    )

    annual_revenue_excluding_vat: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="Annual turnover before output VAT, in UZS",
    )
    annual_input_vat: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="Input VAT available for offset in the same period, in UZS",
    )
    annual_taxable_profit: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="Annual taxable profit base for profit tax, in UZS",
    )
    annual_net_income_after_tax: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True,
        comment="Annual net income after taxes, in UZS",
    )

    # ── Tax ──────────────────────────────────────────────────────
    tax_regime: Mapped[TaxRegime | None] = mapped_column(
        Enum(TaxRegime, name="tax_regime", create_constraint=True),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────
    business_profile = relationship(
        "BusinessProfile", back_populates="financial_inputs",
    )
