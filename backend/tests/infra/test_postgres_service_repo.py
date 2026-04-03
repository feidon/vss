from uuid import uuid7

import pytest
from domain.network.model import Node, NodeType
from domain.service.model import Service, TimetableEntry
from infra.postgres.service_repo import PostgresServiceRepository

from tests.conftest import insert_vehicle

pytestmark = pytest.mark.postgres


def make_service(vehicle_id=None, with_route=False) -> Service:
    vid = vehicle_id or uuid7()
    if with_route:
        node_id = uuid7()
        route = [Node(id=node_id, type=NodeType.PLATFORM)]
        timetable = [
            TimetableEntry(order=0, node_id=node_id, arrival=1000, departure=1060)
        ]
    else:
        route = []
        timetable = []
    return Service(name="S1", vehicle_id=vid, route=route, timetable=timetable)


class TestPostgresServiceRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresServiceRepository(pg_session)

    async def test_create_assigns_id(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        service = make_service(vehicle_id=vid)
        assert service.id is None
        created = await repo.create(service)
        assert created.id is not None
        assert isinstance(created.id, int)
        assert service.id is None  # original not mutated

    async def test_create_and_find_by_id(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        service = make_service(vehicle_id=vid, with_route=True)
        created = await repo.create(service)

        found = await repo.find_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.name == "S1"
        assert found.vehicle_id == vid
        assert len(found.route) == 1
        assert found.route[0].type == NodeType.PLATFORM
        assert len(found.timetable) == 1
        assert found.timetable[0].arrival == 1000

    async def test_update_existing(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        service = make_service(vehicle_id=vid)
        created = await repo.create(service)

        # Update with a route
        node_id = uuid7()
        created.route = [Node(id=node_id, type=NodeType.BLOCK)]
        created.timetable = [
            TimetableEntry(order=0, node_id=node_id, arrival=2000, departure=2030)
        ]
        await repo.update(created)

        found = await repo.find_by_id(created.id)
        assert found is not None
        assert len(found.route) == 1
        assert found.route[0].type == NodeType.BLOCK
        assert found.timetable[0].arrival == 2000

    async def test_find_by_vehicle_id(self, repo, pg_session):
        vid = uuid7()
        other_vid = uuid7()
        await insert_vehicle(pg_session, vid)
        await insert_vehicle(pg_session, other_vid)

        s1 = make_service(vehicle_id=vid)
        s2 = make_service(vehicle_id=vid)
        s3 = make_service(vehicle_id=other_vid)
        await repo.create(s1)
        await repo.create(s2)
        await repo.create(s3)

        result = await repo.find_by_vehicle_id(vid)
        assert len(result) == 2

    async def test_find_all(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        s1 = make_service(vehicle_id=vid)
        s2 = make_service(vehicle_id=vid)
        await repo.create(s1)
        await repo.create(s2)
        result = await repo.find_all()
        assert len(result) == 2

    async def test_delete(self, repo, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        service = make_service(vehicle_id=vid)
        created = await repo.create(service)
        await repo.delete(created.id)
        assert await repo.find_by_id(created.id) is None

    async def test_delete_nonexistent_is_idempotent(self, repo):
        await repo.delete(999)  # should not raise

    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(999) is None
