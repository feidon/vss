from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from infra.postgres.session import get_session
from main import API_PREFIX, app
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import tests.pg_config as pg_config


@pytest.fixture
async def client(_pg_tables):
    engine = create_async_engine(pg_config.TEST_DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def test_get_session():
        async with session_factory() as session:
            yield session

    # Production repo dependencies already build repos from get_session,
    # so overriding get_session is enough — all repos automatically use
    # the test session factory.
    app.dependency_overrides[get_session] = test_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f"http://test{API_PREFIX}/",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE services CASCADE"))
    await engine.dispose()
