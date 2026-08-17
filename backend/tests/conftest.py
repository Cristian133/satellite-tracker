"""Shared pytest fixtures for the backend test suite.

Tests run against a throwaway SQLite database instead of the real Postgres
instance. The DATABASE_URL env var must be set *before* `app.database` is
first imported (it builds the SQLAlchemy engine at import time), so this
module does that as its very first action.
"""

import os

os.environ.setdefault(
    "DATABASE_URL", "sqlite+aiosqlite:///./.pytest_satellite_tracker.db"
)

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import Base, async_session, engine  # noqa: E402 (env var must be set first)
from app.main import app  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _clean_database():
    """Gives every test a fresh, empty schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def db_session():
    """A raw DB session for arranging test data / asserting on stored rows."""
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """An HTTP client wired directly to the ASGI app (no network, no lifespan:
    startup would hit the real Celestrak API and start the background
    scheduler, which we don't want in tests)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
