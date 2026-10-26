"""Traceable annuity and differentiated loan repayment schedules."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.domain.financial import LoanRepaymentMethod
from app.services.financial_engine.capex import MoneyInput, _non_negative_money


@dataclass(frozen=True)
class LoanInstallment:
    """One monthly loan repayment row, in UZS."""

    period: int
    opening_balance: Decimal
    principal_payment: Decimal
    interest_payment: Decimal
    total_payment: Decimal
    closing_balance: Decimal


@dataclass(frozen=True)
class LoanSchedule:
    """Full repayment schedule and totals."""

    method: LoanRepaymentMethod
    principal: Decimal
    annual_interest_rate: Decimal
    installments: tuple[LoanInstallment, ...]
    total_principal: Decimal
    total_interest: Decimal
    total_payment: Decimal


def _annual_rate(value: MoneyInput) -> Decimal:
    try:
        rate = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("annual_interest_rate must be between 0 and 100") from exc
    if not rate.is_finite() or rate < 0 or rate > 100:
        raise ValueError("annual_interest_rate must be between 0 and 100")
    return rate


def calculate_loan_schedule(
    *,
    principal: MoneyInput,
    annual_interest_rate: MoneyInput,
    term_months: int,
    method: LoanRepaymentMethod | str,
) -> LoanSchedule:
    """Build an annuity or differentiated schedule using a nominal monthly rate."""
    loan_principal = _non_negative_money(principal, "principal")
    annual_rate = _annual_rate(annual_interest_rate)
    try:
        method = LoanRepaymentMethod(method)
    except (TypeError, ValueError) as exc:
        raise ValueError("method must be 'annuity' or 'differentiated'") from exc
    if isinstance(term_months, bool) or not isinstance(term_months, int) or term_months < 1:
        raise ValueError("term_months must be a positive integer")
    monthly_rate = annual_rate / Decimal(100) / Decimal(12)
    if method == LoanRepaymentMethod.ANNUITY and monthly_rate != 0:
        regular_payment = loan_principal * monthly_rate / (
            Decimal(1) - (Decimal(1) + monthly_rate) ** (-term_months)
        )
    else:
        regular_payment = loan_principal / Decimal(term_months)

    balance = loan_principal
    rows: list[LoanInstallment] = []
    for period in range(1, term_months + 1):
        opening_balance = balance
        interest_payment = opening_balance * monthly_rate
        if method == LoanRepaymentMethod.ANNUITY:
            principal_payment = regular_payment - interest_payment
        else:
            principal_payment = loan_principal / Decimal(term_months)
        if period == term_months:
            principal_payment = opening_balance
        total_payment = principal_payment + interest_payment
        balance = max(Decimal(0), opening_balance - principal_payment)
        rows.append(
            LoanInstallment(
                period=period,
                opening_balance=opening_balance,
                principal_payment=principal_payment,
                interest_payment=interest_payment,
                total_payment=total_payment,
                closing_balance=balance,
            )
        )

    total_interest = sum((row.interest_payment for row in rows), start=Decimal(0))
    total_principal = sum((row.principal_payment for row in rows), start=Decimal(0))
    return LoanSchedule(
        method=method,
        principal=loan_principal,
        annual_interest_rate=annual_rate,
        installments=tuple(rows),
        total_principal=total_principal,
        total_interest=total_interest,
        total_payment=total_principal + total_interest,
    )
