"""Pure contract tests for Payme checkout and callback authentication."""

import base64
import json
import uuid

import pytest
from starlette.requests import Request

from app.api.v1.payments import (
    build_checkout_url,
    payme_auth_matches,
    payme_callback,
)
from app.core.config import Settings, settings
from app.models.payment import Payment, PaymentStatus
from app.models.business_profile import BusinessProfile  # noqa: F401
from app.models.financial_input import FinancialInput  # noqa: F401
from app.models.generated_plan import GeneratedPlan  # noqa: F401


class FakeResult:
    def __init__(self, value=None) -> None:
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeDb:
    def __init__(self, payment: Payment) -> None:
        self.payment = payment
        self.subscription = None
        self.added = []

    async def execute(self, statement):
        sql = str(statement)
        if "WHERE payments.payme_transaction_id" in sql:
            return FakeResult(self.payment if self.payment.payme_transaction_id else None)
        if "WHERE payments.id" in sql:
            return FakeResult(self.payment)
        if "FROM subscriptions" in sql:
            return FakeResult(self.subscription)
        return FakeResult()

    def add(self, value) -> None:
        self.added.append(value)
        if value.__class__.__name__ == "Subscription":
            self.subscription = value


def _request(payload: dict, login: str, key: str) -> Request:
    encoded = base64.b64encode(f"{login}:{key}".encode()).decode()
    body = json.dumps(payload).encode()
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/payments/payme",
            "headers": [(b"authorization", f"Basic {encoded}".encode())],
        },
        receive,
    )


def test_checkout_link_encodes_server_order_and_amount(monkeypatch) -> None:
    monkeypatch.setattr(settings, "PAYME_CHECKOUT_URL", "https://checkout.test.paycom.uz/")
    monkeypatch.setattr(settings, "PAYME_RETURN_URL", None)
    order_id = uuid.uuid4()

    url = build_checkout_url("merchant-id", order_id, 123400)

    encoded = url.rsplit("/", maxsplit=1)[1]
    params = base64.b64decode(encoded).decode()
    assert url.startswith("https://checkout.test.paycom.uz/")
    assert params == f"m=merchant-id;ac.order_id={order_id};a=123400;l=uz"


def test_checkout_link_can_add_configured_return_url(monkeypatch) -> None:
    monkeypatch.setattr(settings, "PAYME_CHECKOUT_URL", "https://checkout.test.paycom.uz")
    monkeypatch.setattr(settings, "PAYME_RETURN_URL", "https://app.example/payment-result")
    params = base64.b64decode(
        build_checkout_url("merchant", uuid.uuid4(), 500).rsplit("/", 1)[1]
    ).decode()
    assert params.endswith(";c=https://app.example/payment-result")


def test_payme_basic_auth_matches_configured_credentials() -> None:
    credentials = base64.b64encode(b"merchant-login:secret-key").decode()
    assert payme_auth_matches(f"Basic {credentials}", "merchant-login", "secret-key")
    assert not payme_auth_matches(f"Basic {credentials}", "merchant-login", "wrong-key")
    assert not payme_auth_matches("Bearer token", "merchant-login", "secret-key")
    assert not payme_auth_matches(f"Basic {credentials}", None, "secret-key")


def test_blank_payme_environment_placeholders_are_unset() -> None:
    config = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db",
        SECRET_KEY="test-secret-key-at-least-thirty-two-characters-long",
        UZB_VAT_RATE=12,
        UZB_INCOME_TAX_RATE=12,
        UZB_SOCIAL_TAX_RATE=12,
        UZB_TURNOVER_TAX_RATE=4,
        UZB_PROFIT_TAX_RATE=15,
        UZB_SIMPLIFIED_VAT_RATE=6,
        UZB_BASE_CALCULATION_AMOUNT=440000,
        UZB_TURNOVER_TAX_LIMIT_BHM=12000,
        PAYME_SUBSCRIPTION_PRICE_TIYIN="",
        PAYME_SUBSCRIPTION_PERIOD_DAYS="",
    )

    assert config.PAYME_SUBSCRIPTION_PRICE_TIYIN is None
    assert config.PAYME_SUBSCRIPTION_PERIOD_DAYS is None


@pytest.mark.asyncio
async def test_check_perform_transaction_checks_server_amount(monkeypatch) -> None:
    monkeypatch.setattr(settings, "PAYME_MERCHANT_LOGIN", "login")
    monkeypatch.setattr(settings, "PAYME_MERCHANT_KEY", "secret")
    payment = Payment(
        id=uuid.uuid4(), user_id=uuid.uuid4(), amount_tiyin=50000,
        plan_code="test", status=PaymentStatus.CREATED,
    )
    db = FakeDb(payment)
    request = _request(
        {
            "id": 19,
            "method": "CheckPerformTransaction",
            "params": {
                "amount": 49999,
                "account": {"order_id": str(payment.id)},
            },
        },
        "login",
        "secret",
    )

    response = await payme_callback(request, db)

    assert response["id"] == 19
    assert response["error"]["code"] == -31001
    assert payment.status == PaymentStatus.CREATED


@pytest.mark.asyncio
async def test_create_transaction_is_idempotent(monkeypatch) -> None:
    monkeypatch.setattr(settings, "PAYME_MERCHANT_LOGIN", "login")
    monkeypatch.setattr(settings, "PAYME_MERCHANT_KEY", "secret")
    payment = Payment(
        id=uuid.uuid4(), user_id=uuid.uuid4(), amount_tiyin=50000,
        plan_code="test", status=PaymentStatus.CREATED,
    )
    db = FakeDb(payment)
    body = {
        "id": 20,
        "method": "CreateTransaction",
        "params": {
            "id": "payme-transaction-1",
            "time": 1730000000000,
            "amount": 50000,
            "account": {"order_id": str(payment.id)},
        },
    }

    first = await payme_callback(_request(body, "login", "secret"), db)
    second = await payme_callback(_request(body, "login", "secret"), db)

    assert first["result"]["state"] == 1
    assert second["result"] == first["result"]


@pytest.mark.asyncio
async def test_perform_transaction_grants_subscription_once(monkeypatch) -> None:
    monkeypatch.setattr(settings, "PAYME_MERCHANT_LOGIN", "login")
    monkeypatch.setattr(settings, "PAYME_MERCHANT_KEY", "secret")
    monkeypatch.setattr(settings, "PAYME_SUBSCRIPTION_PERIOD_DAYS", 30)
    payment = Payment(
        id=uuid.uuid4(), user_id=uuid.uuid4(), amount_tiyin=50000,
        plan_code="test", status=PaymentStatus.CREATED,
        payme_transaction_id="payme-transaction-1",
    )
    db = FakeDb(payment)
    body = {
        "id": 21,
        "method": "PerformTransaction",
        "params": {"id": "payme-transaction-1"},
    }

    first = await payme_callback(_request(body, "login", "secret"), db)
    subscription_end = db.subscription.current_period_end_ms
    second = await payme_callback(_request(body, "login", "secret"), db)

    assert first["result"]["state"] == 2
    assert second["result"] == first["result"]
    assert db.subscription.current_period_end_ms == subscription_end
    assert len(db.added) == 1


@pytest.mark.asyncio
async def test_cancel_and_check_transaction_keep_payme_state(monkeypatch) -> None:
    monkeypatch.setattr(settings, "PAYME_MERCHANT_LOGIN", "login")
    monkeypatch.setattr(settings, "PAYME_MERCHANT_KEY", "secret")
    payment = Payment(
        id=uuid.uuid4(), user_id=uuid.uuid4(), amount_tiyin=50000,
        plan_code="test", status=PaymentStatus.PERFORMED,
        payme_transaction_id="payme-transaction-1",
        payme_create_time=1730000000000,
        payme_perform_time=1730000001000,
    )
    db = FakeDb(payment)
    cancel = {
        "id": 22,
        "method": "CancelTransaction",
        "params": {"id": "payme-transaction-1", "reason": 5},
    }
    check = {
        "id": 23,
        "method": "CheckTransaction",
        "params": {"id": "payme-transaction-1"},
    }

    cancelled = await payme_callback(_request(cancel, "login", "secret"), db)
    checked = await payme_callback(_request(check, "login", "secret"), db)

    assert cancelled["result"]["state"] == -2
    assert checked["result"]["state"] == -2
    assert checked["result"]["reason"] == 5
    assert payment.status == PaymentStatus.CANCELLED
