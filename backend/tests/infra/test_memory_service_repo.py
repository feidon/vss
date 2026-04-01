from uuid import uuid7

import pytest

from domain.service.model import Service
from infra.memory.service_repo import InMemoryServiceRepository


def make_service(vehicle_id=None) -> Service:
    return Service(
        name="S1",
        vehicle_id=vehicle_id or uuid7(),
        path=[],
        timetable=[],
    )


class TestInMemoryServiceRepository:
    @pytest.fixture
    def repo(self):
        return InMemoryServiceRepository()

    async def test_save_assigns_id(self, repo):
        service = make_service()
        await repo.save(service)
        assert service.id == 1

    async def test_save_and_find_by_id(self, repo):
        service = make_service()
        await repo.save(service)
        found = await repo.find_by_id(service.id)
        assert found == service

    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(999) is None

    async def test_find_all(self, repo):
        s1, s2 = make_service(), make_service()
        await repo.save(s1)
        await repo.save(s2)
        result = await repo.find_all()
        assert len(result) == 2

    async def test_find_by_vehicle_id(self, repo):
        vid = uuid7()
        s1 = make_service(vehicle_id=vid)
        s2 = make_service(vehicle_id=vid)
        s3 = make_service()
        await repo.save(s1)
        await repo.save(s2)
        await repo.save(s3)
        result = await repo.find_by_vehicle_id(vid)
        assert len(result) == 2

    async def test_delete(self, repo):
        service = make_service()
        await repo.save(service)
        await repo.delete(service.id)
        assert await repo.find_by_id(service.id) is None

    async def test_delete_nonexistent_is_idempotent(self, repo):
        await repo.delete(999)  # should not raise
