"""
Token Pydantic schemas.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """Response returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    type: str
    exp: int


class RefreshTokenRequest(BaseModel):
    """Body for the token-refresh endpoint."""

    refresh_token: str
