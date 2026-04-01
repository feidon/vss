from uuid import uuid7

import pytest

from domain.vehicle.model import Vehicle
from infra.postgres.vehicle_repo import PostgresVehicleRepository
from tests.infra.conftest import insert_vehicle

pytestmark = pytest.mark.postgres


class TestPostgresVehicleRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresVehicleRepository(pg_session)

    async def test_find_all(self, repo, pg_session):
        v1 = Vehicle(id=uuid7(), name="V1")
        v2 = Vehicle(id=uuid7(), name="V2")
        await insert_vehicle(pg_session, v1.id, v1.name)
        await insert_vehicle(pg_session, v2.id, v2.name)
        result = await repo.find_all()
        assert len(result) == 2

    async def test_find_by_id(self, repo, pg_session):
        v = Vehicle(id=uuid7(), name="V1")
        await insert_vehicle(pg_session, v.id, v.name)
        found = await repo.find_by_id(v.id)
        assert found is not None
        assert found.id == v.id
        assert found.name == v.name

    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(uuid7()) is None
