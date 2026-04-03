"""Shared fixtures for PostgreSQL integration tests.

Uses testcontainers to spin up a throwaway Postgres 17 container per session.
No external database required.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from infra.postgres.tables import metadata, vehicles_table
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

import tests.pg_config as pg_config

_TABLE_NAMES = ", ".join(t.name for t in metadata.sorted_tables)


@pytest.fixture(scope="session")
def _pg_container():
    """Start a Postgres 17 container for the entire test session."""
    with PostgresContainer("postgres:17", driver="psycopg") as pg:
        sync_url = pg.get_connection_url()  # postgresql+psycopg://...
        async_url = sync_url.replace("+psycopg", "+asyncpg")

        # Populate the shared config so other modules can read URLs
        pg_config.TEST_DATABASE_URL = async_url
        pg_config.TEST_DATABASE_URL_SYNC = sync_url

        yield pg


@pytest.fixture(scope="session")
def _pg_tables(_pg_container):
    """Create all tables once per test session."""
    sync_engine = create_engine(pg_config.TEST_DATABASE_URL_SYNC)
    metadata.create_all(sync_engine)
    sync_engine.dispose()
    yield


@pytest.fixture
async def pg_session(_pg_tables):
    """Provide a clean database session for each test.

    Uses NullPool so connections aren't reused across event loops.
    Tables are truncated after each test.
    """
    engine = create_async_engine(pg_config.TEST_DATABASE_URL, poolclass=NullPool)
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
