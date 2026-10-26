"""
User service — CRUD operations for the User model.

All database queries live here, keeping route handlers thin.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_user_by_id(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Optional[User]:
    """Fetch a single user by primary key."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> Optional[User]:
    """Fetch a single user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    payload: UserCreate,
) -> User:
    """Register a new user (hashes the password before storing).

    Args:
        db: Active async session.
        payload: Validated registration data.

    Returns:
        The newly created ``User`` instance.
    """
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    payload: UserUpdate,
) -> User:
    """Apply partial updates to an existing user.

    Only fields explicitly set in *payload* are updated.
    """
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> Optional[User]:
    """Validate credentials and return the user, or ``None``.

    Args:
        db: Active async session.
        email: Claimed email address.
        password: Plain-text password to verify.

    Returns:
        The ``User`` if credentials are valid, ``None`` otherwise.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
