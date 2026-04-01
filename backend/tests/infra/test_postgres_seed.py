import pytest

from sqlalchemy import select, func

from infra.postgres.seed import seed_database
from infra.postgres.tables import (
    blocks_table,
    node_connections_table,
    platforms_table,
    stations_table,
    vehicles_table,
)

pytestmark = pytest.mark.postgres


class TestSeedDatabase:
    async def test_seed_populates_all_tables(self, pg_session):
        await seed_database(pg_session)

        stations = (await pg_session.execute(select(func.count()).select_from(stations_table))).scalar()
        platforms = (await pg_session.execute(select(func.count()).select_from(platforms_table))).scalar()
        blocks = (await pg_session.execute(select(func.count()).select_from(blocks_table))).scalar()
        vehicles = (await pg_session.execute(select(func.count()).select_from(vehicles_table))).scalar()
        connections = (await pg_session.execute(select(func.count()).select_from(node_connections_table))).scalar()

        assert stations == 4
        assert platforms == 6
        assert blocks == 14
        assert vehicles == 3
        assert connections > 0

    async def test_seed_is_idempotent(self, pg_session):
        await seed_database(pg_session)
        await seed_database(pg_session)  # second call should not fail or duplicate

        stations = (await pg_session.execute(select(func.count()).select_from(stations_table))).scalar()
        blocks = (await pg_session.execute(select(func.count()).select_from(blocks_table))).scalar()

        assert stations == 4
        assert blocks == 14
