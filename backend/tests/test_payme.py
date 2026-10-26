"""Pure contract tests for Payme checkout and callback authentication."""

import base64
import uuid

from app.api.v1.payments import build_checkout_url, payme_auth_matches
from app.core.config import settings


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
