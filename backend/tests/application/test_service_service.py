from uuid import uuid7

import pytest

from application.service.service import ServiceApplicationService
from domain.network.model import Node, NodeType
from domain.service.model import TimetableEntry
from infra.memory.service_repo import InMemoryServiceRepository


class TestServiceApplicationService:
    @pytest.fixture
    def repo(self):
        return InMemoryServiceRepository()

    @pytest.fixture
    def service(self, repo):
        return ServiceApplicationService(repo)

    @pytest.mark.asyncio
    async def test_create_service(self, service):
        vid = uuid7()
        result = await service.create_service(name="Express", vehicle_id=vid)
        assert result.name == "Express"
        assert result.vehicle_id == vid
        assert result.path == []
        assert result.timetable == []

    @pytest.mark.asyncio
    async def test_create_service_rejects_empty_name(self, service):
        with pytest.raises(ValueError, match="name"):
            await service.create_service(name="", vehicle_id=uuid7())

    @pytest.mark.asyncio
    async def test_get_service(self, service):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        result = await service.get_service(created.id)
        assert result == created

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, service):
        with pytest.raises(ValueError, match="not found"):
            await service.get_service(uuid7())

    @pytest.mark.asyncio
    async def test_list_services(self, service):
        await service.create_service(name="S1", vehicle_id=uuid7())
        await service.create_service(name="S2", vehicle_id=uuid7())
        result = await service.list_services()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_path(self, service):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        n1 = Node(id=uuid7(), type=NodeType.BLOCK)
        n2 = Node(id=uuid7(), type=NodeType.PLATFORM)
        result = await service.update_service_path(created.id, [n1, n2])
        assert len(result.path) == 2

    @pytest.mark.asyncio
    async def test_update_timetable(self, service):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        node = Node(id=uuid7(), type=NodeType.BLOCK)
        await service.update_service_path(created.id, [node])
        entries = [TimetableEntry(order=0, node_id=node.id, arrival=0, departure=10)]
        result = await service.update_service_timetable(created.id, entries)
        assert len(result.timetable) == 1

    @pytest.mark.asyncio
    async def test_update_timetable_rejects_unknown_node(self, service):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        entries = [TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10)]
        with pytest.raises(ValueError, match="not in path"):
            await service.update_service_timetable(created.id, entries)

    @pytest.mark.asyncio
    async def test_delete_service(self, service, repo):
        created = await service.create_service(name="S1", vehicle_id=uuid7())
        await service.delete_service(created.id)
        assert await repo.find_by_id(created.id) is None

    @pytest.mark.asyncio
    async def test_delete_service_idempotent(self, service):
        await service.delete_service(uuid7())  # should not raise
