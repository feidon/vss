from uuid import uuid7

import pytest

from application.service.errors import ConflictError
from application.service.service import ServiceAppService
from domain.block.model import Block
from domain.network.model import Node, NodeConnection, NodeType
from domain.service.model import TimetableEntry
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.connection_repo import InMemoryConnectionRepository
from infra.memory.service_repo import InMemoryServiceRepository


def _make_app(service_repo=None, block_repo=None, connection_repo=None):
    service_repo = service_repo or InMemoryServiceRepository()
    block_repo = block_repo or InMemoryBlockRepository()
    connection_repo = connection_repo or InMemoryConnectionRepository()
    return ServiceAppService(service_repo, block_repo, connection_repo)


class TestServiceAppService:
    @pytest.fixture
    def app(self):
        return _make_app()

    @pytest.mark.asyncio
    async def test_create_service(self, app):
        vid = uuid7()
        result = await app.create_service(name="Express", vehicle_id=vid)
        assert result.name == "Express"
        assert result.vehicle_id == vid
        assert result.path == []
        assert result.timetable == []

    @pytest.mark.asyncio
    async def test_create_service_rejects_empty_name(self, app):
        with pytest.raises(ValueError, match="name"):
            await app.create_service(name="", vehicle_id=uuid7())

    @pytest.mark.asyncio
    async def test_get_service(self, app):
        created = await app.create_service(name="S1", vehicle_id=uuid7())
        result = await app.get_service(created.id)
        assert result == created

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, app):
        with pytest.raises(ValueError, match="not found"):
            await app.get_service(uuid7())

    @pytest.mark.asyncio
    async def test_list_services(self, app):
        await app.create_service(name="S1", vehicle_id=uuid7())
        await app.create_service(name="S2", vehicle_id=uuid7())
        result = await app.list_services()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_path_single_node(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        block_repo = InMemoryBlockRepository()
        await block_repo.save(block)
        app = _make_app(block_repo=block_repo)

        created = await app.create_service(name="S1", vehicle_id=uuid7())
        result = await app.update_service_path(created.id, [Node(id=block.id, type=NodeType.BLOCK)])
        assert len(result.path) == 1
        assert result.path[0].id == block.id

    @pytest.mark.asyncio
    async def test_update_path_rejects_unknown_block(self):
        app = _make_app()
        created = await app.create_service(name="S1", vehicle_id=uuid7())
        with pytest.raises(ValueError, match="not found"):
            await app.update_service_path(created.id, [Node(id=uuid7(), type=NodeType.BLOCK)])

    @pytest.mark.asyncio
    async def test_update_timetable(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        block_repo = InMemoryBlockRepository()
        await block_repo.save(block)
        app = _make_app(block_repo=block_repo)

        created = await app.create_service(name="S1", vehicle_id=uuid7())
        await app.update_service_path(created.id, [Node(id=block.id, type=NodeType.BLOCK)])
        entries = [TimetableEntry(order=0, node_id=block.id, arrival=0, departure=10)]
        result = await app.update_service_timetable(created.id, entries)
        assert len(result.timetable) == 1

    @pytest.mark.asyncio
    async def test_update_timetable_rejects_unknown_node(self, app):
        created = await app.create_service(name="S1", vehicle_id=uuid7())
        entries = [TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10)]
        with pytest.raises(ValueError, match="not in path"):
            await app.update_service_timetable(created.id, entries)

    @pytest.mark.asyncio
    async def test_delete_service(self):
        service_repo = InMemoryServiceRepository()
        app = _make_app(service_repo=service_repo)
        created = await app.create_service(name="S1", vehicle_id=uuid7())
        await app.delete_service(created.id)
        assert await service_repo.find_by_id(created.id) is None

    @pytest.mark.asyncio
    async def test_delete_service_idempotent(self, app):
        await app.delete_service(uuid7())


class TestPathValidation:
    @pytest.mark.asyncio
    async def test_update_path_validates_connectivity(self):
        b1 = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        b2 = Block(id=uuid7(), name="B2", group=1, traversal_time_seconds=30)
        block_repo = InMemoryBlockRepository()
        await block_repo.save(b1)
        await block_repo.save(b2)
        connections = frozenset({NodeConnection(from_id=b1.id, to_id=b2.id)})
        connection_repo = InMemoryConnectionRepository(connections)
        app = _make_app(block_repo=block_repo, connection_repo=connection_repo)

        created = await app.create_service(name="S1", vehicle_id=uuid7())
        result = await app.update_service_path(
            created.id, [Node(id=b1.id, type=NodeType.BLOCK), Node(id=b2.id, type=NodeType.BLOCK)]
        )
        assert len(result.path) == 2

    @pytest.mark.asyncio
    async def test_update_path_rejects_disconnected(self):
        b1 = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        b2 = Block(id=uuid7(), name="B2", group=1, traversal_time_seconds=30)
        block_repo = InMemoryBlockRepository()
        await block_repo.save(b1)
        await block_repo.save(b2)
        connection_repo = InMemoryConnectionRepository()  # no connections
        app = _make_app(block_repo=block_repo, connection_repo=connection_repo)

        created = await app.create_service(name="S1", vehicle_id=uuid7())
        with pytest.raises(ValueError, match="No connection"):
            await app.update_service_path(
                created.id, [Node(id=b1.id, type=NodeType.BLOCK), Node(id=b2.id, type=NodeType.BLOCK)]
            )


class TestConflictOnSave:
    @pytest.mark.asyncio
    async def test_timetable_update_rejects_vehicle_conflict(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        block_repo = InMemoryBlockRepository()
        await block_repo.save(block)
        app = _make_app(block_repo=block_repo)
        node = Node(id=block.id, type=NodeType.BLOCK)
        vid = uuid7()

        s1 = await app.create_service(name="S1", vehicle_id=vid)
        await app.update_service_path(s1.id, [node])
        await app.update_service_timetable(
            s1.id, [TimetableEntry(order=0, node_id=block.id, arrival=0, departure=100)]
        )

        s2 = await app.create_service(name="S2", vehicle_id=vid)
        await app.update_service_path(s2.id, [node])

        with pytest.raises(ConflictError) as exc_info:
            await app.update_service_timetable(
                s2.id, [TimetableEntry(order=0, node_id=block.id, arrival=50, departure=150)]
            )
        assert len(exc_info.value.conflicts.vehicle_conflicts) > 0

    @pytest.mark.asyncio
    async def test_timetable_update_rejects_block_conflict(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        block_repo = InMemoryBlockRepository()
        await block_repo.save(block)
        app = _make_app(block_repo=block_repo)
        node = Node(id=block.id, type=NodeType.BLOCK)

        s1 = await app.create_service(name="S1", vehicle_id=uuid7())
        await app.update_service_path(s1.id, [node])
        await app.update_service_timetable(
            s1.id, [TimetableEntry(order=0, node_id=block.id, arrival=0, departure=100)]
        )

        s2 = await app.create_service(name="S2", vehicle_id=uuid7())
        await app.update_service_path(s2.id, [node])

        with pytest.raises(ConflictError) as exc_info:
            await app.update_service_timetable(
                s2.id, [TimetableEntry(order=0, node_id=block.id, arrival=50, departure=150)]
            )
        assert len(exc_info.value.conflicts.block_conflicts) > 0

    @pytest.mark.asyncio
    async def test_timetable_update_rejects_interlocking_conflict(self):
        b1 = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        b2 = Block(id=uuid7(), name="B2", group=1, traversal_time_seconds=30)
        block_repo = InMemoryBlockRepository()
        await block_repo.save(b1)
        await block_repo.save(b2)
        app = _make_app(block_repo=block_repo)

        s1 = await app.create_service(name="S1", vehicle_id=uuid7())
        await app.update_service_path(s1.id, [Node(id=b1.id, type=NodeType.BLOCK)])
        await app.update_service_timetable(
            s1.id, [TimetableEntry(order=0, node_id=b1.id, arrival=0, departure=100)]
        )

        s2 = await app.create_service(name="S2", vehicle_id=uuid7())
        await app.update_service_path(s2.id, [Node(id=b2.id, type=NodeType.BLOCK)])

        with pytest.raises(ConflictError) as exc_info:
            await app.update_service_timetable(
                s2.id, [TimetableEntry(order=0, node_id=b2.id, arrival=50, departure=150)]
            )
        assert len(exc_info.value.conflicts.interlocking_conflicts) > 0
