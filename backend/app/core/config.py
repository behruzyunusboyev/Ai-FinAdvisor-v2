"""
Application configuration loaded from environment variables.

Uses pydantic-settings to validate and type-check all config values.
No secrets are hardcoded — everything comes from .env or the OS environment.
"""

from decimal import Decimal
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "FinAdvisor API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pw@host/db

    # ── Security / JWT ───────────────────────────────────────────
    SECRET_KEY: str  # Must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── CORS ─────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | List[str]) -> List[str]:
        """Accept a JSON-encoded list *or* a plain Python list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # ── Uzbekistan-specific configurable parameters ──────────────
    # Tax parameters are supplied through environment configuration.
    UZB_VAT_RATE: Decimal
    UZB_INCOME_TAX_RATE: Decimal
    UZB_SOCIAL_TAX_RATE: Decimal
    UZB_TURNOVER_TAX_RATE: Decimal
    UZB_PROFIT_TAX_RATE: Decimal
    UZB_SIMPLIFIED_VAT_RATE: Decimal
    UZB_BASE_CALCULATION_AMOUNT: Decimal
    UZB_TURNOVER_TAX_LIMIT_BHM: int

    # Optional Responses API configuration. No model is selected by default.
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None

    # Payme Merchant API. Price and billing period are intentionally unset
    # until the product owner configures the approved SaaS offer.
    PAYME_MERCHANT_ID: str | None = None
    PAYME_MERCHANT_LOGIN: str | None = None
    PAYME_MERCHANT_KEY: str | None = None
    PAYME_SUBSCRIPTION_PRICE_TIYIN: int | None = None
    PAYME_SUBSCRIPTION_PERIOD_DAYS: int | None = None
    PAYME_SUBSCRIPTION_PLAN_CODE: str = "configured"
    PAYME_CHECKOUT_URL: str = "https://checkout.paycom.uz"
    PAYME_RETURN_URL: str | None = None

    @field_validator(
        "PAYME_SUBSCRIPTION_PRICE_TIYIN",
        "PAYME_SUBSCRIPTION_PERIOD_DAYS",
        mode="before",
    )
    @classmethod
    def blank_payme_numbers_are_unset(cls, value: object) -> object:
        """Treat empty .env placeholders as unset instead of invalid integers."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    # Internal completeness rubric; these weights describe product policy,
    # not lender approval criteria, and must total 100 points.
    READINESS_WEIGHT_CAPEX: int = 10
    READINESS_WEIGHT_OPEX: int = 20
    READINESS_WEIGHT_SALES_TAX: int = 20
    READINESS_WEIGHT_INVESTMENT_ROI: int = 20
    READINESS_WEIGHT_LOAN: int = 20
    READINESS_WEIGHT_TAX_OUTPUT: int = 10

    @model_validator(mode="after")
    def validate_readiness_weights(self) -> "Settings":
        weights = (
            self.READINESS_WEIGHT_CAPEX,
            self.READINESS_WEIGHT_OPEX,
            self.READINESS_WEIGHT_SALES_TAX,
            self.READINESS_WEIGHT_INVESTMENT_ROI,
            self.READINESS_WEIGHT_LOAN,
            self.READINESS_WEIGHT_TAX_OUTPUT,
        )
        if any(weight < 0 for weight in weights) or sum(weights) != 100:
            raise ValueError("readiness rubric weights must be non-negative and total 100")
        return self


settings = Settings()  # type: ignore[call-arg]
