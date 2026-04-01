from uuid import uuid7

import pytest

from infra.postgres.station_repo import PostgresStationRepository
from infra.postgres.tables import stations_table, platforms_table
from sqlalchemy.dialects.postgresql import insert

pytestmark = pytest.mark.postgres


async def _insert_station(session, *, id, name, is_yard):
    await session.execute(
        insert(stations_table).values(id=id, name=name, is_yard=is_yard)
    )
    await session.commit()


async def _insert_platform(session, *, id, name, station_id):
    await session.execute(
        insert(platforms_table).values(id=id, name=name, station_id=station_id)
    )
    await session.commit()


class TestPostgresStationRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresStationRepository(pg_session)

    async def test_find_all_with_platforms(self, repo, pg_session):
        s1_id, p1a_id, p1b_id = uuid7(), uuid7(), uuid7()
        await _insert_station(pg_session, id=s1_id, name="S1", is_yard=False)
        await _insert_platform(pg_session, id=p1a_id, name="P1A", station_id=s1_id)
        await _insert_platform(pg_session, id=p1b_id, name="P1B", station_id=s1_id)

        result = await repo.find_all()
        assert len(result) == 1
        station = result[0]
        assert station.name == "S1"
        assert not station.is_yard
        assert len(station.platforms) == 2
        platform_names = {p.name for p in station.platforms}
        assert platform_names == {"P1A", "P1B"}

    async def test_find_by_id_with_platforms(self, repo, pg_session):
        s_id, p_id = uuid7(), uuid7()
        await _insert_station(pg_session, id=s_id, name="S2", is_yard=False)
        await _insert_platform(pg_session, id=p_id, name="P2A", station_id=s_id)

        station = await repo.find_by_id(s_id)
        assert station is not None
        assert station.id == s_id
        assert len(station.platforms) == 1
        assert station.platforms[0].id == p_id

    async def test_yard_with_no_platforms(self, repo, pg_session):
        yard_id = uuid7()
        await _insert_station(pg_session, id=yard_id, name="Y", is_yard=True)

        station = await repo.find_by_id(yard_id)
        assert station is not None
        assert station.is_yard is True
        assert station.platforms == []

    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(uuid7()) is None
