"""
User profile endpoints — view and update the authenticated user.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import update_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Return the profile of the authenticated user."""
    return UserRead.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserRead,
    summary="Update current user profile",
)
async def update_current_user(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Update the authenticated user's mutable profile fields."""
    updated = await update_user(db, current_user, payload)
    return UserRead.model_validate(updated)
