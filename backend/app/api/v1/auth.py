"""
Authentication endpoints — register, login, refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Create a new user account.

    Raises:
        HTTPException 409: If the email is already taken.
    """
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    user = await create_user(db, payload)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Log in and receive tokens",
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate with email + password, receive JWT pair.

    Raises:
        HTTPException 401: Invalid credentials.
    """
    user = await authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return Token(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
)
async def refresh(payload: RefreshTokenRequest) -> Token:
    """Exchange a valid refresh token for a new access + refresh pair.

    Raises:
        HTTPException 401: If the refresh token is invalid or expired.
    """
    user_id = verify_token(payload.refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return Token(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )
