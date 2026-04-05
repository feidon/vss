from uuid import uuid7

import pytest
from domain.service.model import Service
from infra.postgres.service_repo import PostgresServiceRepository

from tests.conftest import insert_vehicle


@pytest.mark.postgres
class TestDeleteAll:
    async def test_delete_all_removes_all_services(self, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        repo = PostgresServiceRepository(pg_session)

        for name in ["S1", "S2", "S3"]:
            await repo.create(
                Service(name=name, vehicle_id=vid, route=[], timetable=[])
            )

        assert len(await repo.find_all()) == 3
        await repo.delete_all()
        assert len(await repo.find_all()) == 0

    async def test_delete_all_on_empty_is_noop(self, pg_session):
        repo = PostgresServiceRepository(pg_session)
        await repo.delete_all()
        assert len(await repo.find_all()) == 0
