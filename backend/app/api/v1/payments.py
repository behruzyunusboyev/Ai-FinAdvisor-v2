"""Payme Merchant API callbacks and authenticated subscription checkout."""

import base64
import hmac
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.payment import Payment, PaymentStatus, Subscription
from app.models.user import User

router = APIRouter(tags=["Payments"])


def _payme_error(request_id: Any, code: int, message: str, data: str | None = None) -> dict:
    error: dict[str, Any] = {
        "code": code,
        "message": {"uz": message, "ru": message, "en": message},
    }
    if data:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _checkout_is_configured() -> bool:
    return bool(
        settings.PAYME_MERCHANT_ID
        and settings.PAYME_MERCHANT_KEY
        and settings.PAYME_SUBSCRIPTION_PRICE_TIYIN
        and settings.PAYME_SUBSCRIPTION_PRICE_TIYIN > 0
        and settings.PAYME_SUBSCRIPTION_PERIOD_DAYS
        and settings.PAYME_SUBSCRIPTION_PERIOD_DAYS > 0
    )


def build_checkout_url(merchant_id: str, order_id: uuid.UUID, amount_tiyin: int) -> str:
    params = f"m={merchant_id};ac.order_id={order_id};a={amount_tiyin};l=uz"
    if settings.PAYME_RETURN_URL:
        params += f";c={settings.PAYME_RETURN_URL}"
    payload = base64.b64encode(params.encode("utf-8")).decode("ascii")
    return f"{settings.PAYME_CHECKOUT_URL.rstrip('/')}/{payload}"


@router.post("/payments/payme/checkout", summary="Create Payme subscription checkout")
async def create_payme_checkout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    """Create a server-priced subscription renewal. Client cannot set amount."""
    if not _checkout_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payme subscription price, period, and merchant credentials are not configured",
        )

    payment = Payment(
        user_id=current_user.id,
        amount_tiyin=settings.PAYME_SUBSCRIPTION_PRICE_TIYIN,
        plan_code=settings.PAYME_SUBSCRIPTION_PLAN_CODE,
        status=PaymentStatus.CREATED,
    )
    db.add(payment)
    await db.flush()

    return {
        "payment_id": str(payment.id),
        "amount_tiyin": payment.amount_tiyin,
        "checkout_url": build_checkout_url(
            settings.PAYME_MERCHANT_ID,
            payment.id,
            payment.amount_tiyin,
        ),
    }


@router.get("/payments/subscription", summary="Get current subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()
    now_ms = int(time.time() * 1000)
    return {
        "active": bool(subscription and subscription.current_period_end_ms > now_ms),
        "plan_code": subscription.plan_code if subscription else None,
        "current_period_end_ms": subscription.current_period_end_ms if subscription else None,
        "renewal": "manual",
    }


def _check_payme_auth(request: Request) -> bool:
    return payme_auth_matches(
        request.headers.get("authorization", ""),
        settings.PAYME_MERCHANT_LOGIN,
        settings.PAYME_MERCHANT_KEY,
    )


def payme_auth_matches(auth_header: str, login: str | None, key: str | None) -> bool:
    if not login or not key:
        return False
    auth = auth_header
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth[6:], validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    expected = f"{login}:{key}"
    return hmac.compare_digest(decoded, expected)


@router.post("/payments/payme", summary="Payme Merchant API callback")
async def payme_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle Payme JSON-RPC callbacks; callbacks are authenticated with Basic auth."""
    if not _check_payme_auth(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Payme credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    try:
        body = await request.json()
    except ValueError:
        return _payme_error(None, -32700, "JSON parse error")

    request_id = body.get("id") if isinstance(body, dict) else None
    if not isinstance(body, dict) or not isinstance(body.get("method"), str):
        return _payme_error(request_id, -32600, "Invalid request")
    method = body["method"]
    params = body.get("params") or {}
    if not isinstance(params, dict):
        return _payme_error(request_id, -32602, "Invalid params")

    if method == "CheckPerformTransaction":
        payment = await _payment_for_order(db, params.get("account"))
        if payment is None:
            return _payme_error(request_id, -31050, "Order not found", "account")
        if params.get("amount") != payment.amount_tiyin:
            return _payme_error(request_id, -31001, "Incorrect payment amount", "amount")
        if payment.status != PaymentStatus.CREATED:
            return _payme_error(request_id, -31008, "Order cannot be paid")
        return {"jsonrpc": "2.0", "id": request_id, "result": {"allow": True}}

    if method == "CreateTransaction":
        order = await _payment_for_order(db, params.get("account"), lock=True)
        if order is None:
            return _payme_error(request_id, -31050, "Order not found", "account")
        if params.get("amount") != order.amount_tiyin:
            return _payme_error(request_id, -31001, "Incorrect payment amount", "amount")
        transaction_id = params.get("id")
        if not isinstance(transaction_id, str) or not transaction_id:
            return _payme_error(request_id, -32602, "Invalid transaction id")
        existing = await db.execute(
            select(Payment).where(Payment.payme_transaction_id == transaction_id)
        )
        other = existing.scalar_one_or_none()
        if other is not None and other.id != order.id:
            return _payme_error(request_id, -31008, "Transaction already exists")
        if order.payme_transaction_id == transaction_id:
            return {"jsonrpc": "2.0", "id": request_id, "result": {
                "create_time": order.payme_create_time,
                "transaction": str(order.id), "state": 1,
            }}
        if order.status != PaymentStatus.CREATED or order.payme_transaction_id:
            return _payme_error(request_id, -31008, "Order cannot be paid")
        order.payme_transaction_id = transaction_id
        order.payme_create_time = int(time.time() * 1000)
        return {"jsonrpc": "2.0", "id": request_id, "result": {
            "create_time": order.payme_create_time,
            "transaction": str(order.id), "state": 1,
        }}

    if method in {"PerformTransaction", "CancelTransaction", "CheckTransaction"}:
        transaction_id = params.get("id")
        result = await db.execute(
            select(Payment)
            .where(Payment.payme_transaction_id == transaction_id)
            .with_for_update()
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            return _payme_error(request_id, -31003, "Transaction not found", "id")
        if method == "PerformTransaction":
            if payment.status == PaymentStatus.CANCELLED:
                return _payme_error(request_id, -31008, "Transaction is cancelled")
            if payment.status == PaymentStatus.CREATED:
                now_ms = int(time.time() * 1000)
                payment.status = PaymentStatus.PERFORMED
                payment.payme_perform_time = now_ms
                await _extend_subscription(db, payment, now_ms)
            result_data = {
                "transaction": str(payment.id),
                "perform_time": payment.payme_perform_time or 0,
                "state": 2,
            }
            return {"jsonrpc": "2.0", "id": request_id, "result": result_data}
        if method == "CancelTransaction":
            reason = params.get("reason")
            if payment.status != PaymentStatus.CANCELLED:
                now_ms = int(time.time() * 1000)
                payment.status = PaymentStatus.CANCELLED
                payment.cancel_reason = reason if isinstance(reason, int) else None
                payment.payme_cancel_time = now_ms
            return {"jsonrpc": "2.0", "id": request_id, "result": {
                "transaction": str(payment.id),
                "cancel_time": payment.payme_cancel_time or 0,
                "state": -2 if payment.payme_perform_time else -1,
            }}
        state = {
            PaymentStatus.CREATED: 1,
            PaymentStatus.PERFORMED: 2,
            PaymentStatus.CANCELLED: -2 if payment.payme_perform_time else -1,
        }[payment.status]
        return {"jsonrpc": "2.0", "id": request_id, "result": {
            "create_time": payment.payme_create_time or 0,
            "perform_time": payment.payme_perform_time or 0,
            "cancel_time": payment.payme_cancel_time or 0,
            "transaction": str(payment.id),
            "state": state,
            "reason": payment.cancel_reason,
        }}

    return _payme_error(request_id, -32601, "Method not found")


async def _payment_for_order(
    db: AsyncSession,
    account: Any,
    lock: bool = False,
) -> Payment | None:
    if not isinstance(account, dict) or not isinstance(account.get("order_id"), str):
        return None
    try:
        payment_id = uuid.UUID(account["order_id"])
    except ValueError:
        return None
    query = select(Payment).where(Payment.id == payment_id)
    if lock:
        query = query.with_for_update()
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _extend_subscription(
    db: AsyncSession,
    payment: Payment,
    now_ms: int,
) -> None:
    period_days = settings.PAYME_SUBSCRIPTION_PERIOD_DAYS
    if not period_days:
        raise RuntimeError("Payme subscription period is not configured")
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == payment.user_id)
        .with_for_update()
    )
    subscription = result.scalar_one_or_none()
    starts_ms = max(now_ms, subscription.current_period_end_ms) if subscription else now_ms
    end_ms = int(
        (datetime.fromtimestamp(starts_ms / 1000, tz=timezone.utc)
         + timedelta(days=period_days)).timestamp() * 1000
    )
    if subscription is None:
        db.add(Subscription(
            user_id=payment.user_id,
            plan_code=payment.plan_code,
            current_period_end_ms=end_ms,
            last_payment_id=payment.id,
        ))
    else:
        subscription.plan_code = payment.plan_code
        subscription.current_period_end_ms = end_ms
        subscription.last_payment_id = payment.id
