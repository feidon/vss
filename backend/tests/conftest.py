"""Shared fixtures for PostgreSQL integration tests.

Requires a running PostgreSQL instance at localhost:5432 with database 'vss_test'.
Tests are marked with @pytest.mark.postgres and skipped if the database is unavailable.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from infra.postgres.tables import metadata, vehicles_table
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.pg_config import TEST_DATABASE_URL, TEST_DATABASE_URL_SYNC

_TABLE_NAMES = ", ".join(t.name for t in metadata.sorted_tables)


@pytest.fixture(scope="session")
def _pg_tables():
    """Create all tables once per test session using a sync engine."""
    sync_engine = create_engine(TEST_DATABASE_URL_SYNC)
    metadata.create_all(sync_engine)
    yield
    metadata.drop_all(sync_engine)
    sync_engine.dispose()


@pytest.fixture
async def pg_session(_pg_tables):
    """Provide a clean database session for each test.

    Uses NullPool so connections aren't reused across event loops.
    Tables are truncated after each test.
    """
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {_TABLE_NAMES} CASCADE"))
    await engine.dispose()


async def insert_vehicle(
    session: AsyncSession, vehicle_id: UUID, name: str = "V1"
) -> None:
    """Insert a vehicle row (shared helper for FK setup)."""
    await session.execute(insert(vehicles_table).values(id=vehicle_id, name=name))
    await session.commit()
