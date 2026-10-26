"""
FastAPI application entry point.

Creates the app, wires CORS middleware, and includes all routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "FinAdvisor — AI-powered financial planning platform for "
        "restaurants and cafés in Uzbekistan."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(v1_router)


# ── Health check ─────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "healthy", "version": settings.APP_VERSION}
