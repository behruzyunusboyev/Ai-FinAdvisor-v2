"""Configurable annual tax calculations for the supported business regimes."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.domain.financial import TaxRegime
from app.services.financial_engine.capex import MoneyInput, _non_negative_money


@dataclass(frozen=True)
class TaxPolicy:
    """Tax rates and thresholds supplied by application configuration."""

    vat_rate: Decimal
    profit_tax_rate: Decimal
    personal_income_tax_rate: Decimal
    social_tax_rate: Decimal
    turnover_tax_rate: Decimal
    simplified_vat_rate: Decimal
    turnover_tax_limit_uzs: Decimal


def tax_policy_from_settings(settings: object) -> TaxPolicy:
    """Build the calculation policy from validated application settings."""
    base_calculation_amount = Decimal(str(settings.UZB_BASE_CALCULATION_AMOUNT))
    turnover_limit_bhm = Decimal(str(settings.UZB_TURNOVER_TAX_LIMIT_BHM))
    return TaxPolicy(
        vat_rate=Decimal(str(settings.UZB_VAT_RATE)),
        profit_tax_rate=Decimal(str(settings.UZB_PROFIT_TAX_RATE)),
        personal_income_tax_rate=Decimal(str(settings.UZB_INCOME_TAX_RATE)),
        social_tax_rate=Decimal(str(settings.UZB_SOCIAL_TAX_RATE)),
        turnover_tax_rate=Decimal(str(settings.UZB_TURNOVER_TAX_RATE)),
        simplified_vat_rate=Decimal(str(settings.UZB_SIMPLIFIED_VAT_RATE)),
        turnover_tax_limit_uzs=base_calculation_amount * turnover_limit_bhm,
    )


@dataclass(frozen=True)
class AnnualTaxBreakdown:
    """Tax values and calculation bases for one annual forecast."""

    regime: TaxRegime
    revenue_excluding_vat: Decimal
    vat_rate_applied: Decimal | None
    output_vat: Decimal | None
    input_vat_credit: Decimal | None
    unused_input_vat_credit: Decimal | None
    vat_payable: Decimal | None
    taxable_profit: Decimal | None
    profit_tax_rate_applied: Decimal | None
    profit_tax: Decimal | None
    turnover_tax_rate_applied: Decimal | None
    turnover_tax: Decimal | None
    annual_gross_payroll: Decimal | None
    personal_income_tax_rate_applied: Decimal
    personal_income_tax_withheld: Decimal | None
    social_tax_rate_applied: Decimal
    employer_social_tax: Decimal | None


def _percentage(value: Decimal, field_name: str) -> Decimal:
    if not value.is_finite() or value < 0 or value > 100:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return value / Decimal(100)


def calculate_annual_taxes(
    *,
    regime: TaxRegime,
    annual_revenue_excluding_vat: MoneyInput,
    annual_input_vat: MoneyInput | None,
    annual_taxable_profit: MoneyInput | None,
    employee_count: int | None,
    average_salary_monthly: MoneyInput | None,
    policy: TaxPolicy,
) -> AnnualTaxBreakdown:
    """Calculate annual turnover/VAT/profit/payroll tax components.

    ``annual_revenue_excluding_vat`` is the tax base before output VAT.
    ``annual_taxable_profit`` must be supplied by the caller for the standard
    profit-tax regimes because accounting inputs alone do not establish the
    legal taxable-profit base.
    """
    try:
        regime = TaxRegime(regime)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unsupported tax regime: {regime}") from exc

    revenue = _non_negative_money(
        annual_revenue_excluding_vat, "annual_revenue_excluding_vat",
    )
    input_vat = (
        None
        if annual_input_vat is None
        else _non_negative_money(annual_input_vat, "annual_input_vat")
    )
    if annual_taxable_profit is None:
        taxable_profit = None
    else:
        try:
            taxable_profit = Decimal(str(annual_taxable_profit))
        except InvalidOperation as exc:
            raise ValueError("annual_taxable_profit must be a number") from exc
        if not taxable_profit.is_finite():
            raise ValueError("annual_taxable_profit must be a finite number")

    if employee_count is not None and (
        isinstance(employee_count, bool)
        or not isinstance(employee_count, int)
        or employee_count < 0
    ):
        raise ValueError("employee_count must be a non-negative integer")
    salary = (
        None
        if average_salary_monthly is None
        else _non_negative_money(average_salary_monthly, "average_salary_monthly")
    )
    if employee_count == 0:
        annual_payroll = Decimal(0)
    elif employee_count is not None and salary is not None:
        annual_payroll = Decimal(employee_count) * salary * Decimal(12)
    else:
        annual_payroll = None

    vat_rate = _percentage(policy.vat_rate, "vat_rate")
    profit_tax_rate = _percentage(policy.profit_tax_rate, "profit_tax_rate")
    personal_income_tax_rate = _percentage(
        policy.personal_income_tax_rate, "personal_income_tax_rate",
    )
    social_tax_rate = _percentage(policy.social_tax_rate, "social_tax_rate")
    turnover_tax_rate = _percentage(policy.turnover_tax_rate, "turnover_tax_rate")
    simplified_vat_rate = _percentage(
        policy.simplified_vat_rate, "simplified_vat_rate",
    )
    turnover_limit = _non_negative_money(
        policy.turnover_tax_limit_uzs, "turnover_tax_limit_uzs",
    )

    output_vat: Decimal | None = None
    input_vat_credit: Decimal | None = None
    unused_input_vat_credit: Decimal | None = None
    vat_payable: Decimal | None = None
    profit_tax: Decimal | None = None
    turnover_tax: Decimal | None = None

    if regime in (TaxRegime.GENERAL, TaxRegime.VAT_PAYER):
        applied_vat_rate = vat_rate
        applied_profit_tax_rate = profit_tax_rate
        output_vat = revenue * vat_rate
        if input_vat is not None:
            input_vat_credit = min(input_vat, output_vat)
            unused_input_vat_credit = max(Decimal(0), input_vat - output_vat)
            vat_payable = max(Decimal(0), output_vat - input_vat)
        if taxable_profit is not None:
            profit_tax = max(Decimal(0), taxable_profit) * profit_tax_rate
        turnover_tax = Decimal(0)
    elif regime == TaxRegime.SIMPLIFIED:
        applied_vat_rate = simplified_vat_rate
        applied_profit_tax_rate = Decimal(0)
        output_vat = revenue * simplified_vat_rate
        input_vat_credit = Decimal(0)
        unused_input_vat_credit = Decimal(0)
        vat_payable = output_vat
        profit_tax = Decimal(0)
        turnover_tax = Decimal(0)
    elif regime == TaxRegime.TURNOVER_TAX:
        if revenue > turnover_limit:
            raise ValueError(
                "annual_revenue_excluding_vat exceeds the configured "
                "turnover-tax limit"
            )
        applied_vat_rate = None
        applied_profit_tax_rate = Decimal(0)
        profit_tax = Decimal(0)
        turnover_tax = revenue * turnover_tax_rate
    else:
        raise ValueError(f"Unsupported tax regime: {regime}")

    personal_income_tax = (
        None
        if annual_payroll is None
        else annual_payroll * personal_income_tax_rate
    )
    employer_social_tax = (
        None if annual_payroll is None else annual_payroll * social_tax_rate
    )
    return AnnualTaxBreakdown(
        regime=regime,
        revenue_excluding_vat=revenue,
        vat_rate_applied=applied_vat_rate,
        output_vat=output_vat,
        input_vat_credit=input_vat_credit,
        unused_input_vat_credit=unused_input_vat_credit,
        vat_payable=vat_payable,
        taxable_profit=taxable_profit,
        profit_tax_rate_applied=applied_profit_tax_rate,
        profit_tax=profit_tax,
        turnover_tax_rate_applied=(
            turnover_tax_rate if regime == TaxRegime.TURNOVER_TAX else None
        ),
        turnover_tax=turnover_tax,
        annual_gross_payroll=annual_payroll,
        personal_income_tax_rate_applied=personal_income_tax_rate,
        personal_income_tax_withheld=personal_income_tax,
        social_tax_rate_applied=social_tax_rate,
        employer_social_tax=employer_social_tax,
    )
