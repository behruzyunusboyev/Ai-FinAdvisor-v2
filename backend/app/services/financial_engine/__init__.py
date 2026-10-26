"""Deterministic financial calculations, separated by calculation domain."""

from app.services.financial_engine.capex import CapexBreakdown, EquipmentCost, calculate_capex
from app.services.financial_engine.opex import MonthlyOpex, calculate_monthly_opex
from app.services.financial_engine.returns import (
    BreakEvenResult,
    MenuSalesMixItem,
    RoiResult,
    calculate_break_even,
    calculate_roi,
)
from app.services.financial_engine.loans import (
    LoanInstallment,
    LoanSchedule,
    calculate_loan_schedule,
)
from app.services.financial_engine.taxes import (
    AnnualTaxBreakdown,
    TaxPolicy,
    calculate_annual_taxes,
    tax_policy_from_settings,
)

__all__ = [
    "CapexBreakdown",
    "EquipmentCost",
    "MonthlyOpex",
    "BreakEvenResult",
    "MenuSalesMixItem",
    "RoiResult",
    "LoanInstallment",
    "LoanSchedule",
    "AnnualTaxBreakdown",
    "TaxPolicy",
    "calculate_capex",
    "calculate_monthly_opex",
    "calculate_break_even",
    "calculate_roi",
    "calculate_loan_schedule",
    "calculate_annual_taxes",
    "tax_policy_from_settings",
]
