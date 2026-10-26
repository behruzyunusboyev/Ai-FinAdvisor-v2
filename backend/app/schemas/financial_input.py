"""
Financial Input Pydantic schemas — Create, Read, Update.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.financial import LoanRepaymentMethod
from app.models.financial_input import TaxRegime


class MenuItemInput(BaseModel):
    """Menu price, unit cost, and forecast sales mix input."""

    name: str = Field(min_length=1)
    price: Decimal = Field(ge=0)
    cost: Decimal = Field(ge=0)
    category: Optional[str] = None
    expected_monthly_units: Optional[int] = Field(None, ge=0)

    model_config = ConfigDict(extra="allow")


# ── Create ───────────────────────────────────────────────────────

class FinancialInputCreate(BaseModel):
    """Payload for creating a financial input set."""

    business_profile_id: uuid.UUID
    menu_items: Optional[list[MenuItemInput]] = None
    employee_count: Optional[int] = Field(None, ge=0)
    average_salary: Optional[float] = Field(None, ge=0)
    equipment_list: Optional[list[dict[str, Any]]] = None
    rent_monthly: Optional[float] = Field(None, ge=0)
    utilities_monthly: Optional[float] = Field(None, ge=0)
    initial_investment: Optional[float] = Field(None, ge=0)
    loan_amount: Optional[float] = Field(None, ge=0)
    loan_term_months: Optional[int] = Field(None, ge=1)
    loan_interest_rate: Optional[float] = Field(None, ge=0, le=100)
    loan_repayment_method: Optional[LoanRepaymentMethod] = None
    annual_revenue_excluding_vat: Optional[Decimal] = Field(None, ge=0)
    annual_input_vat: Optional[Decimal] = Field(None, ge=0)
    annual_taxable_profit: Optional[Decimal] = None
    annual_net_income_after_tax: Optional[Decimal] = None
    tax_regime: Optional[TaxRegime] = None


# ── Read ─────────────────────────────────────────────────────────

class FinancialInputRead(BaseModel):
    """Full financial input response."""

    id: uuid.UUID
    business_profile_id: uuid.UUID
    menu_items: Optional[list[dict[str, Any]]] = None
    employee_count: Optional[int] = None
    average_salary: Optional[float] = None
    equipment_list: Optional[list[dict[str, Any]]] = None
    rent_monthly: Optional[float] = None
    utilities_monthly: Optional[float] = None
    initial_investment: Optional[float] = None
    loan_amount: Optional[float] = None
    loan_term_months: Optional[int] = None
    loan_interest_rate: Optional[float] = None
    loan_repayment_method: Optional[LoanRepaymentMethod] = None
    annual_revenue_excluding_vat: Optional[Decimal] = None
    annual_input_vat: Optional[Decimal] = None
    annual_taxable_profit: Optional[Decimal] = None
    annual_net_income_after_tax: Optional[Decimal] = None
    tax_regime: Optional[TaxRegime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Update ───────────────────────────────────────────────────────

class FinancialInputUpdate(BaseModel):
    """Partial update for financial inputs."""

    menu_items: Optional[list[MenuItemInput]] = None
    employee_count: Optional[int] = Field(None, ge=0)
    average_salary: Optional[float] = Field(None, ge=0)
    equipment_list: Optional[list[dict[str, Any]]] = None
    rent_monthly: Optional[float] = Field(None, ge=0)
    utilities_monthly: Optional[float] = Field(None, ge=0)
    initial_investment: Optional[float] = Field(None, ge=0)
    loan_amount: Optional[float] = Field(None, ge=0)
    loan_term_months: Optional[int] = Field(None, ge=1)
    loan_interest_rate: Optional[float] = Field(None, ge=0, le=100)
    loan_repayment_method: Optional[LoanRepaymentMethod] = None
    annual_revenue_excluding_vat: Optional[Decimal] = Field(None, ge=0)
    annual_input_vat: Optional[Decimal] = Field(None, ge=0)
    annual_taxable_profit: Optional[Decimal] = None
    annual_net_income_after_tax: Optional[Decimal] = None
    tax_regime: Optional[TaxRegime] = None
