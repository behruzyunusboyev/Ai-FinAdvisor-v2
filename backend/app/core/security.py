"""
Security utilities — password hashing and JWT token management.

All secrets are read from ``app.core.config.settings``; nothing is hardcoded.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return the bcrypt hash of *password*."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify *plain_password* against *hashed_password*."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT tokens ───────────────────────────────────────────────────

def _create_token(
    data: dict[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> str:
    """Internal helper to build a signed JWT."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a short-lived access token.

    Args:
        subject: The token subject — typically the user's UUID string.
        expires_delta: Custom expiry; falls back to config default.
    """
    delta = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return _create_token({"sub": subject}, delta, token_type="access")


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a long-lived refresh token.

    Args:
        subject: The token subject — typically the user's UUID string.
        expires_delta: Custom expiry; falls back to config default.
    """
    delta = expires_delta or timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    return _create_token({"sub": subject}, delta, token_type="refresh")


def verify_token(token: str, expected_type: str = "access") -> Optional[str]:
    """Decode and verify a JWT token.

    Args:
        token: The raw JWT string.
        expected_type: ``"access"`` or ``"refresh"``.

    Returns:
        The ``sub`` claim (user id) on success, ``None`` on any failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        token_type: str | None = payload.get("type")
        subject: str | None = payload.get("sub")
        if token_type != expected_type or subject is None:
            return None
        return subject
    except JWTError:
        return None
