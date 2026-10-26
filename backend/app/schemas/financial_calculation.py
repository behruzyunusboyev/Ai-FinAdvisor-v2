"""Request and response schemas for deterministic financial calculations."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.domain.financial import LoanRepaymentMethod, TaxRegime
from app.schemas.financial_input import MenuItemInput


class FinancialCalculationRequest(BaseModel):
    """Validated inputs needed by the deterministic financial engine."""

    menu_items: list[MenuItemInput] = Field(default_factory=list)
    employee_count: int | None = Field(None, ge=0)
    average_salary: Decimal | None = Field(None, ge=0)
    equipment_list: list[dict[str, Any]] = Field(default_factory=list)
    rent_monthly: Decimal | None = Field(None, ge=0)
    utilities_monthly: Decimal | None = Field(None, ge=0)
    initial_investment: Decimal | None = Field(None, ge=0)
    loan_amount: Decimal | None = Field(None, ge=0)
    loan_term_months: int | None = Field(None, ge=1)
    loan_interest_rate: Decimal | None = Field(None, ge=0, le=100)
    loan_repayment_method: LoanRepaymentMethod | None = None
    annual_revenue_excluding_vat: Decimal | None = Field(None, ge=0)
    annual_input_vat: Decimal | None = Field(None, ge=0)
    annual_taxable_profit: Decimal | None = None
    annual_net_income_after_tax: Decimal | None = None
    tax_regime: TaxRegime | None = None


class FinancialCalculationResponse(BaseModel):
    """Calculation sections; unavailable sections remain null."""

    capex: dict[str, Any]
    monthly_opex: dict[str, Any]
    annual_taxes: dict[str, Any] | None
    loan_schedule: dict[str, Any] | None
    break_even: dict[str, Any] | None
    roi: dict[str, Any] | None
