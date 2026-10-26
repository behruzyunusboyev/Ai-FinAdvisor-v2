"""
Shared pytest fixtures for the FinAdvisor backend test suite.

Provides:
- An async test client (``client``)
- An isolated async database session (``db_session``)
- A pre-created test user (``test_user``)
"""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole

# ── Use an event loop that persists across the session ───────────
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Async test engine (uses the same DATABASE_URL) ───────────────
TEST_ENGINE = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)
TestSessionFactory = async_sessionmaker(
    bind=TEST_ENGINE,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session that rolls back after each test."""
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionFactory() as session:
        async with session.begin():
            yield session
            await session.rollback()

    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client with the DB dependency overridden."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def test_user(db_session: AsyncSession) -> User:
    """Create and return a test user in the database."""
    user = User(
        id=uuid.uuid4(),
        email="test@finadvisor.uz",
        hashed_password=hash_password("TestPassword123"),
        full_name="Test User",
        phone="+998901234567",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user
