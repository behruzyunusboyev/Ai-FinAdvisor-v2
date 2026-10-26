"""Orchestrate deterministic financial calculations for API consumers."""

from dataclasses import asdict
from decimal import Decimal
from typing import Any

from app.schemas.financial_calculation import FinancialCalculationRequest
from app.services.financial_engine import (
    calculate_annual_taxes,
    calculate_break_even,
    calculate_capex,
    calculate_loan_schedule,
    calculate_monthly_opex,
    calculate_roi,
    tax_policy_from_settings,
)


def calculate_financial_plan(
    payload: FinancialCalculationRequest,
    settings: object,
) -> dict[str, Any]:
    """Return only values produced by the deterministic financial engine."""
    policy = tax_policy_from_settings(settings)
    capex = calculate_capex(payload.equipment_list, payload.initial_investment)
    monthly_opex = calculate_monthly_opex(
        employee_count=payload.employee_count,
        average_salary=payload.average_salary,
        rent_monthly=payload.rent_monthly,
        utilities_monthly=payload.utilities_monthly,
    )

    annual_taxes = None
    if payload.tax_regime is not None:
        if payload.annual_revenue_excluding_vat is None:
            raise ValueError("annual_revenue_excluding_vat is required with tax_regime")
        annual_taxes = calculate_annual_taxes(
            regime=payload.tax_regime,
            annual_revenue_excluding_vat=payload.annual_revenue_excluding_vat,
            annual_input_vat=payload.annual_input_vat,
            annual_taxable_profit=payload.annual_taxable_profit,
            employee_count=payload.employee_count,
            average_salary_monthly=payload.average_salary,
            policy=policy,
        )

    loan_values = (
        payload.loan_amount,
        payload.loan_term_months,
        payload.loan_interest_rate,
        payload.loan_repayment_method,
    )
    loan_schedule = None
    if any(value is not None for value in loan_values):
        if any(value is None for value in loan_values):
            raise ValueError(
                "loan_amount, loan_term_months, loan_interest_rate, and "
                "loan_repayment_method must be provided together"
            )
        loan_schedule = calculate_loan_schedule(
            principal=payload.loan_amount,
            annual_interest_rate=payload.loan_interest_rate,
            term_months=payload.loan_term_months,
            method=payload.loan_repayment_method,
        )

    break_even = None
    sales_mix_complete = bool(payload.menu_items) and all(
        item.expected_monthly_units is not None for item in payload.menu_items
    )
    if (
        sales_mix_complete
        and monthly_opex.total is not None
        and monthly_opex.payroll is not None
    ):
        employer_social_tax = monthly_opex.payroll * policy.social_tax_rate / Decimal(100)
        break_even = calculate_break_even(
            monthly_fixed_costs=monthly_opex.total + employer_social_tax,
            menu_items=[item.model_dump() for item in payload.menu_items],
        )

    roi = None
    roi_values = (payload.annual_net_income_after_tax, payload.initial_investment)
    if any(value is not None for value in roi_values):
        if any(value is None for value in roi_values):
            raise ValueError(
                "annual_net_income_after_tax and initial_investment "
                "must be provided together for ROI"
            )
        roi = calculate_roi(
            annual_net_income_after_tax=payload.annual_net_income_after_tax,
            initial_investment=payload.initial_investment,
        )

    return {
        "capex": asdict(capex),
        "monthly_opex": asdict(monthly_opex),
        "annual_taxes": None if annual_taxes is None else asdict(annual_taxes),
        "loan_schedule": None if loan_schedule is None else asdict(loan_schedule),
        "break_even": None if break_even is None else asdict(break_even),
        "roi": None if roi is None else asdict(roi),
    }
