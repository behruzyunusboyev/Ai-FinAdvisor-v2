from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.domain.financial import TaxRegime
from app.services.financial_engine import (
    TaxPolicy,
    calculate_annual_taxes,
    calculate_break_even,
    calculate_capex,
    calculate_loan_schedule,
    calculate_monthly_opex,
    calculate_roi,
    tax_policy_from_settings,
)


def _tax_policy() -> TaxPolicy:
    return TaxPolicy(
        vat_rate=Decimal("12"),
        profit_tax_rate=Decimal("15"),
        personal_income_tax_rate=Decimal("12"),
        social_tax_rate=Decimal("12"),
        turnover_tax_rate=Decimal("4"),
        simplified_vat_rate=Decimal("6"),
        turnover_tax_limit_uzs=Decimal("5280000000"),
    )


def test_capex_preserves_initial_investment_separately_from_equipment() -> None:
    result = calculate_capex(
        equipment_list=[
            {"name": "Oven", "cost": 12_500_000},
            {"name": "Refrigerator", "cost": "8300000.50"},
        ],
        initial_investment=50_000_000,
    )

    assert result.equipment_total == Decimal("20800000.50")
    assert result.initial_investment == Decimal("50000000")
    assert [item.name for item in result.equipment_items] == ["Oven", "Refrigerator"]


def test_capex_rejects_an_equipment_item_without_a_cost() -> None:
    with pytest.raises(ValueError, match=r"equipment_list\[0\]\.cost"):
        calculate_capex([{"name": "Oven"}], None)


def test_monthly_opex_reports_traceable_components_and_total() -> None:
    result = calculate_monthly_opex(
        employee_count=4,
        average_salary="3500000",
        rent_monthly=12_000_000,
        utilities_monthly=2_500_000,
    )

    assert result.payroll == Decimal("14000000")
    assert result.rent == Decimal("12000000")
    assert result.utilities == Decimal("2500000")
    assert result.total == Decimal("28500000")


def test_monthly_opex_keeps_total_unknown_when_inputs_are_missing() -> None:
    result = calculate_monthly_opex(
        employee_count=3,
        average_salary=None,
        rent_monthly=12_000_000,
        utilities_monthly=None,
    )

    assert result.payroll is None
    assert result.rent == Decimal("12000000")
    assert result.utilities is None
    assert result.total is None


def test_monthly_opex_zero_staff_has_zero_payroll_without_salary() -> None:
    result = calculate_monthly_opex(
        employee_count=0,
        average_salary=None,
        rent_monthly=0,
        utilities_monthly=0,
    )

    assert result.payroll == Decimal(0)
    assert result.total == Decimal(0)


def test_standard_tax_regime_returns_traceable_vat_profit_and_payroll_tax() -> None:
    result = calculate_annual_taxes(
        regime=TaxRegime.GENERAL,
        annual_revenue_excluding_vat=100_000_000,
        annual_input_vat=5_000_000,
        annual_taxable_profit=20_000_000,
        employee_count=2,
        average_salary_monthly=4_000_000,
        policy=_tax_policy(),
    )

    assert result.output_vat == Decimal("12000000")
    assert result.input_vat_credit == Decimal("5000000")
    assert result.vat_payable == Decimal("7000000")
    assert result.profit_tax == Decimal("3000000")
    assert result.annual_gross_payroll == Decimal("96000000")
    assert result.personal_income_tax_withheld == Decimal("11520000")
    assert result.employer_social_tax == Decimal("11520000")


def test_standard_tax_regime_preserves_unused_input_vat_credit() -> None:
    result = calculate_annual_taxes(
        regime=TaxRegime.VAT_PAYER,
        annual_revenue_excluding_vat=10_000_000,
        annual_input_vat=2_000_000,
        annual_taxable_profit=None,
        employee_count=0,
        average_salary_monthly=None,
        policy=_tax_policy(),
    )

    assert result.vat_payable == Decimal(0)
    assert result.input_vat_credit == Decimal("1200000")
    assert result.unused_input_vat_credit == Decimal("800000")
    assert result.profit_tax is None


def test_simplified_regime_uses_configured_rate_without_input_credit() -> None:
    result = calculate_annual_taxes(
        regime=TaxRegime.SIMPLIFIED,
        annual_revenue_excluding_vat=100_000_000,
        annual_input_vat=5_000_000,
        annual_taxable_profit=20_000_000,
        employee_count=0,
        average_salary_monthly=None,
        policy=_tax_policy(),
    )

    assert result.vat_rate_applied == Decimal("0.06")
    assert result.vat_payable == Decimal("6000000")
    assert result.input_vat_credit == Decimal(0)
    assert result.profit_tax == Decimal(0)


def test_turnover_tax_uses_configured_limit_and_rate() -> None:
    result = calculate_annual_taxes(
        regime=TaxRegime.TURNOVER_TAX,
        annual_revenue_excluding_vat=100_000_000,
        annual_input_vat=None,
        annual_taxable_profit=None,
        employee_count=0,
        average_salary_monthly=None,
        policy=_tax_policy(),
    )

    assert result.turnover_tax == Decimal("4000000")
    assert result.output_vat is None
    assert result.profit_tax == Decimal(0)


def test_turnover_tax_rejects_revenue_over_configured_limit() -> None:
    with pytest.raises(ValueError, match="turnover-tax limit"):
        calculate_annual_taxes(
            regime=TaxRegime.TURNOVER_TAX,
            annual_revenue_excluding_vat=5_280_000_001,
            annual_input_vat=None,
            annual_taxable_profit=None,
            employee_count=0,
            average_salary_monthly=None,
            policy=_tax_policy(),
        )


def test_tax_policy_reads_dynamic_rates_and_limit_from_settings() -> None:
    settings = SimpleNamespace(
        UZB_VAT_RATE=12,
        UZB_PROFIT_TAX_RATE=15,
        UZB_INCOME_TAX_RATE=12,
        UZB_SOCIAL_TAX_RATE=12,
        UZB_TURNOVER_TAX_RATE=4,
        UZB_SIMPLIFIED_VAT_RATE=6,
        UZB_BASE_CALCULATION_AMOUNT=440_000,
        UZB_TURNOVER_TAX_LIMIT_BHM=12_000,
    )

    policy = tax_policy_from_settings(settings)

    assert policy.vat_rate == Decimal("12")
    assert policy.turnover_tax_limit_uzs == Decimal("5280000000")


def test_annuity_schedule_reduces_balance_and_reconciles_totals() -> None:
    result = calculate_loan_schedule(
        principal=1_200_000,
        annual_interest_rate=12,
        term_months=12,
        method="annuity",
    )

    assert len(result.installments) == 12
    assert result.installments[0].interest_payment == Decimal("12000")
    assert result.installments[-1].closing_balance == Decimal(0)
    assert result.total_principal == Decimal("1200000")
    assert result.total_payment == result.total_principal + result.total_interest


def test_differentiated_schedule_has_equal_principal_and_falling_payments() -> None:
    result = calculate_loan_schedule(
        principal=1_200_000,
        annual_interest_rate=12,
        term_months=12,
        method="differentiated",
    )

    assert result.installments[0].principal_payment == Decimal("100000")
    assert result.installments[-1].principal_payment == Decimal("100000")
    assert result.installments[0].total_payment == Decimal("112000")
    assert result.installments[-1].total_payment == Decimal("101000")
    assert result.installments[-1].closing_balance == Decimal(0)


def test_zero_interest_schedule_splits_principal_evenly() -> None:
    result = calculate_loan_schedule(
        principal=1_200_000,
        annual_interest_rate=0,
        term_months=12,
        method="annuity",
    )

    assert result.total_interest == Decimal(0)
    assert all(row.total_payment == Decimal("100000") for row in result.installments)


def test_loan_schedule_rejects_unknown_method() -> None:
    with pytest.raises(ValueError, match="method must be"):
        calculate_loan_schedule(
            principal=1_200_000,
            annual_interest_rate=12,
            term_months=12,
            method="flat",
        )


def test_break_even_uses_forecast_menu_mix_and_fixed_costs() -> None:
    result = calculate_break_even(
        monthly_fixed_costs=30_000_000,
        menu_items=[
            {"name": "Meal A", "price": 50_000, "cost": 20_000, "expected_monthly_units": 600},
            {"name": "Meal B", "price": 100_000, "cost": 60_000, "expected_monthly_units": 400},
        ],
    )

    assert result.expected_monthly_units == 1000
    assert result.expected_monthly_revenue == Decimal("70000000")
    expected_break_even_revenue = (
        Decimal("30000000") * Decimal("70") / Decimal("34")
    )
    assert abs(result.break_even_revenue - expected_break_even_revenue) < Decimal("0.000001")
    assert (
        result.item_break_even_units["Meal A"]
        + result.item_break_even_units["Meal B"]
        == result.break_even_total_units
    )


def test_break_even_requires_sales_volume_and_positive_contribution_margin() -> None:
    with pytest.raises(ValueError, match="expected monthly sales"):
        calculate_break_even(
            monthly_fixed_costs=1_000,
            menu_items=[{"name": "Meal", "price": 10, "cost": 5}],
        )
    with pytest.raises(ValueError, match="positive contribution margin"):
        calculate_break_even(
            monthly_fixed_costs=1_000,
            menu_items=[
                {
                    "name": "Meal",
                    "price": 10,
                    "cost": 10,
                    "expected_monthly_units": 1,
                }
            ],
        )


def test_roi_uses_after_tax_annual_income_and_initial_investment() -> None:
    result = calculate_roi(
        annual_net_income_after_tax=20_000_000,
        initial_investment=100_000_000,
    )

    assert result.roi_percent == Decimal("20")


def test_roi_allows_loss_but_requires_nonzero_investment() -> None:
    result = calculate_roi(
        annual_net_income_after_tax=-5_000_000,
        initial_investment=100_000_000,
    )

    assert result.roi_percent == Decimal("-5")
    with pytest.raises(ValueError, match="greater than zero"):
        calculate_roi(annual_net_income_after_tax=1, initial_investment=0)
