from __future__ import annotations

import pytest
from api.dependencies import (
    get_block_repo,
    get_connection_repo,
    get_service_repo,
    get_station_repo,
    get_vehicle_repo,
)
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from infra.postgres.block_repo import PostgresBlockRepository
from infra.postgres.connection_repo import PostgresConnectionRepository
from infra.postgres.service_repo import PostgresServiceRepository
from infra.postgres.session import get_session
from infra.postgres.station_repo import PostgresStationRepository
from infra.postgres.tables import metadata
from infra.postgres.vehicle_repo import PostgresVehicleRepository
from main import API_PREFIX, app
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.helpers.seed import seed_test_database
from tests.pg_config import TEST_DATABASE_URL

_TABLE_NAMES = ", ".join(t.name for t in metadata.sorted_tables)


@pytest.fixture
async def client(_pg_tables):
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await seed_test_database(session)

    async def test_get_session():
        async with session_factory() as session:
            yield session

    def override_block_repo(session: AsyncSession = Depends(get_session)):
        return PostgresBlockRepository(session)

    def override_service_repo(session: AsyncSession = Depends(get_session)):
        return PostgresServiceRepository(session)

    def override_connection_repo(session: AsyncSession = Depends(get_session)):
        return PostgresConnectionRepository(session)

    def override_station_repo(session: AsyncSession = Depends(get_session)):
        return PostgresStationRepository(session)

    def override_vehicle_repo(session: AsyncSession = Depends(get_session)):
        return PostgresVehicleRepository(session)

    app.dependency_overrides[get_session] = test_get_session
    app.dependency_overrides[get_block_repo] = override_block_repo
    app.dependency_overrides[get_service_repo] = override_service_repo
    app.dependency_overrides[get_connection_repo] = override_connection_repo
    app.dependency_overrides[get_station_repo] = override_station_repo
    app.dependency_overrides[get_vehicle_repo] = override_vehicle_repo

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f"http://test{API_PREFIX}/",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {_TABLE_NAMES} CASCADE"))
    await engine.dispose()
