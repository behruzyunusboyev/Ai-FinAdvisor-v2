"""
V1 API router — aggregates all sub-routers for the ``/api/v1`` prefix.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.financial_plans import router as financial_plans_router
from app.api.v1.users import router as users_router
from app.api.v1.payments import router as payments_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(financial_plans_router)
router.include_router(payments_router)
