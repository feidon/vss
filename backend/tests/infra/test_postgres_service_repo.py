from uuid import uuid7

import pytest

from domain.network.model import Node, NodeType
from domain.service.model import Service, TimetableEntry
from infra.postgres.service_repo import PostgresServiceRepository
from tests.infra.conftest import insert_vehicle

pytestmark = pytest.mark.postgres


def make_service(vehicle_id=None, with_route=False) -> Service:
    vid = vehicle_id or uuid7()
    if with_route:
        node_id = uuid7()
        path = [Node(id=node_id, type=NodeType.PLATFORM)]
        timetable = [TimetableEntry(order=0, node_id=node_id, arrival=1000, departure=1060)]
    else:
        path = []
        timetable = []
    return Service(name="S1", vehicle_id=vid, path=path, timetable=timetable)


class TestPostgresServiceRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresServiceRepository(pg_session)

    async def test_save_new_assigns_id(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        service = make_service(vehicle_id=vid)
        assert service.id is None
        await repo.save(service)
        assert service.id is not None
        assert isinstance(service.id, int)

    async def test_save_and_find_by_id(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        service = make_service(vehicle_id=vid, with_route=True)
        await repo.save(service)

        found = await repo.find_by_id(service.id)
        assert found is not None
        assert found.id == service.id
        assert found.name == "S1"
        assert found.vehicle_id == vid
        assert len(found.path) == 1
        assert found.path[0].type == NodeType.PLATFORM
        assert len(found.timetable) == 1
        assert found.timetable[0].arrival == 1000

    async def test_save_existing_updates(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        service = make_service(vehicle_id=vid)
        await repo.save(service)

        # Update with a route
        node_id = uuid7()
        service.path = [Node(id=node_id, type=NodeType.BLOCK)]
        service.timetable = [TimetableEntry(order=0, node_id=node_id, arrival=2000, departure=2030)]
        await repo.save(service)

        found = await repo.find_by_id(service.id)
        assert found is not None
        assert len(found.path) == 1
        assert found.path[0].type == NodeType.BLOCK
        assert found.timetable[0].arrival == 2000

    async def test_find_by_vehicle_id(self, repo, pg_session):
        vid = uuid7()
        other_vid = uuid7()
        await insert_vehicle(pg_session, vid)
        await insert_vehicle(pg_session, other_vid)

        s1 = make_service(vehicle_id=vid)
        s2 = make_service(vehicle_id=vid)
        s3 = make_service(vehicle_id=other_vid)
        await repo.save(s1)
        await repo.save(s2)
        await repo.save(s3)

        result = await repo.find_by_vehicle_id(vid)
        assert len(result) == 2

    async def test_find_all(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        s1 = make_service(vehicle_id=vid)
        s2 = make_service(vehicle_id=vid)
        await repo.save(s1)
        await repo.save(s2)
        result = await repo.find_all()
        assert len(result) == 2

    async def test_delete(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        service = make_service(vehicle_id=vid)
        await repo.save(service)
        await repo.delete(service.id)
        assert await repo.find_by_id(service.id) is None

    async def test_delete_nonexistent_is_idempotent(self, repo):
        await repo.delete(999)  # should not raise

    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(999) is None
