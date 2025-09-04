"""Test configuration and fixtures for Agent Workbench."""

import asyncio
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from agent_workbench.models.database import Base


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine):
    """Create a database session for testing."""
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock(spec=AsyncSession)
