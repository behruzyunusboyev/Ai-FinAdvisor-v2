"""Financial domain enums independent of persistence details."""

import enum


class TaxRegime(str, enum.Enum):
    """Supported tax regimes selected for a business forecast."""

    GENERAL = "general"
    SIMPLIFIED = "simplified"
    VAT_PAYER = "vat_payer"
    TURNOVER_TAX = "turnover_tax"


class LoanRepaymentMethod(str, enum.Enum):
    """Supported loan repayment schedule methods."""

    ANNUITY = "annuity"
    DIFFERENTIATED = "differentiated"
