from uuid import uuid7

import pytest

from domain.block.model import Block
from domain.block.repository import BlockRepository
from domain.network.model import Node, NodeType
from domain.service.conflict import (
    BlockConflict,
    ConflictDetectionService,
    VehicleConflict,
)
from domain.service.model import Service, TimetableEntry
from domain.service.repository import ServiceRepository


def make_block_node(block_id=None) -> Node:
    return Node(id=block_id or uuid7(), type=NodeType.BLOCK)


def make_service_with_window(
    vehicle_id,
    node: Node,
    arrival: int,
    departure: int,
) -> Service:
    entry = TimetableEntry(order=0, node_id=node.id, arrival=arrival, departure=departure)
    return Service(
        id=uuid7(),
        name="S",
        vehicle_id=vehicle_id,
        path=[node],
        timetable=[entry],
    )


class FakeServiceRepo(ServiceRepository):
    def __init__(self, services: list[Service]):
        self._services = {s.id: s for s in services}

    async def find_by_vehicle_id(self, vehicle_id) -> list[Service]:
        return [s for s in self._services.values() if s.vehicle_id == vehicle_id]

    async def find_all(self) -> list[Service]:
        return list(self._services.values())

    async def find_by_id(self, id) -> Service | None:
        return self._services.get(id)

    async def save(self, service) -> None:
        self._services[service.id] = service

    async def delete(self, id) -> None:
        self._services.pop(id, None)


class FakeBlockRepo(BlockRepository):
    def __init__(self, blocks: list[Block]):
        self._blocks = {b.id: b for b in blocks}

    async def find_all(self) -> list[Block]:
        return list(self._blocks.values())

    async def find_by_id(self, id) -> Block | None:
        return self._blocks.get(id)

    async def save(self, block) -> None:
        self._blocks[block.id] = block


class TestVehicleConflicts:
    @pytest.mark.asyncio
    async def test_no_conflicts(self):
        vid = uuid7()
        node = make_block_node()
        s1 = make_service_with_window(vid, node, arrival=0, departure=10)
        s2 = make_service_with_window(vid, node, arrival=10, departure=20)

        svc = ConflictDetectionService(
            FakeServiceRepo([s1, s2]),
            FakeBlockRepo([]),
        )
        conflicts = await svc.detect_vehicle_conflicts(vid)
        assert conflicts == []

    @pytest.mark.asyncio
    async def test_overlapping_time_windows(self):
        vid = uuid7()
        node = make_block_node()
        s1 = make_service_with_window(vid, node, arrival=0, departure=15)
        s2 = make_service_with_window(vid, node, arrival=10, departure=20)

        svc = ConflictDetectionService(
            FakeServiceRepo([s1, s2]),
            FakeBlockRepo([]),
        )
        conflicts = await svc.detect_vehicle_conflicts(vid)
        assert len(conflicts) == 1
        assert conflicts[0].reason == "Overlapping time windows"

    @pytest.mark.asyncio
    async def test_location_discontinuity(self):
        vid = uuid7()
        n1, n2 = make_block_node(), make_block_node()
        s1 = make_service_with_window(vid, n1, arrival=0, departure=10)
        s2 = make_service_with_window(vid, n2, arrival=10, departure=20)

        svc = ConflictDetectionService(
            FakeServiceRepo([s1, s2]),
            FakeBlockRepo([]),
        )
        conflicts = await svc.detect_vehicle_conflicts(vid)
        assert len(conflicts) == 1
        assert conflicts[0].reason == "Location discontinuity"

    @pytest.mark.asyncio
    async def test_empty_timetable_skipped(self):
        vid = uuid7()
        node = make_block_node()
        s1 = make_service_with_window(vid, node, arrival=0, departure=10)
        s2 = Service(id=uuid7(), name="S", vehicle_id=vid, path=[], timetable=[])

        svc = ConflictDetectionService(
            FakeServiceRepo([s1, s2]),
            FakeBlockRepo([]),
        )
        conflicts = await svc.detect_vehicle_conflicts(vid)
        assert conflicts == []


class TestBlockConflicts:
    @pytest.mark.asyncio
    async def test_no_conflicts(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        node = make_block_node(block.id)
        s1 = make_service_with_window(uuid7(), node, arrival=0, departure=10)
        s2 = make_service_with_window(uuid7(), node, arrival=10, departure=20)

        svc = ConflictDetectionService(
            FakeServiceRepo([s1, s2]),
            FakeBlockRepo([block]),
        )
        conflicts = await svc.detect_block_conflicts()
        assert conflicts == []

    @pytest.mark.asyncio
    async def test_overlapping_on_same_block(self):
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        node = make_block_node(block.id)
        s1 = make_service_with_window(uuid7(), node, arrival=0, departure=15)
        s2 = make_service_with_window(uuid7(), node, arrival=10, departure=20)

        svc = ConflictDetectionService(
            FakeServiceRepo([s1, s2]),
            FakeBlockRepo([block]),
        )
        conflicts = await svc.detect_block_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0].block_id == block.id

    @pytest.mark.asyncio
    async def test_finds_all_overlapping_pairs(self):
        """A:[0,10], B:[1,2], C:[3,9] — should find A-B, A-C, B-C is not overlap (3 >= 2)."""
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        node = make_block_node(block.id)
        sa = make_service_with_window(uuid7(), node, arrival=0, departure=10)
        sb = make_service_with_window(uuid7(), node, arrival=1, departure=2)
        sc = make_service_with_window(uuid7(), node, arrival=3, departure=9)

        svc = ConflictDetectionService(
            FakeServiceRepo([sa, sb, sc]),
            FakeBlockRepo([block]),
        )
        conflicts = await svc.detect_block_conflicts()
        pairs = {(c.service_a_id, c.service_b_id) for c in conflicts}
        assert (sa.id, sb.id) in pairs
        assert (sa.id, sc.id) in pairs
        assert len(conflicts) == 2

    @pytest.mark.asyncio
    async def test_platform_nodes_ignored(self):
        """Entries on platform nodes should not be checked for block conflicts."""
        block = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        platform_node = Node(id=uuid7(), type=NodeType.PLATFORM)
        s1 = make_service_with_window(uuid7(), platform_node, arrival=0, departure=15)
        s2 = make_service_with_window(uuid7(), platform_node, arrival=10, departure=20)

        svc = ConflictDetectionService(
            FakeServiceRepo([s1, s2]),
            FakeBlockRepo([block]),
        )
        conflicts = await svc.detect_block_conflicts()
        assert conflicts == []
