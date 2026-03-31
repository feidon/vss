from itertools import count
from uuid import uuid7

import pytest

from domain.block.model import Block
from domain.network.model import Node, NodeType
from domain.service.conflict import ConflictDetector
from domain.service.model import Service, TimetableEntry

_id_counter = count(1)


def make_block(block_id=None, group=1) -> Block:
    bid = block_id or uuid7()
    return Block(id=bid, name="B", group=group, traversal_time_seconds=30)


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
        id=next(_id_counter),
        name="S",
        vehicle_id=vehicle_id,
        path=[node],
        timetable=[entry],
    )


def validate(candidate: Service, others: list[Service], blocks: list[Block] | None = None):
    return ConflictDetector.validate_service(candidate, others, blocks or [])


class TestVehicleConflicts:
    def test_no_conflicts(self):
        vid = uuid7()
        node = make_block_node()
        s1 = make_service_with_window(vid, node, arrival=0, departure=10)
        s2 = make_service_with_window(vid, node, arrival=10, departure=20)

        result = validate(s2, [s1])
        assert result.vehicle_conflicts == []

    def test_overlapping_time_windows(self):
        vid = uuid7()
        node = make_block_node()
        s1 = make_service_with_window(vid, node, arrival=0, departure=15)
        s2 = make_service_with_window(vid, node, arrival=10, departure=20)

        result = validate(s2, [s1])
        assert len(result.vehicle_conflicts) == 1
        assert result.vehicle_conflicts[0].reason == "Overlapping time windows"

    def test_location_discontinuity(self):
        vid = uuid7()
        n1, n2 = make_block_node(), make_block_node()
        s1 = make_service_with_window(vid, n1, arrival=0, departure=10)
        s2 = make_service_with_window(vid, n2, arrival=10, departure=20)

        result = validate(s2, [s1])
        assert len(result.vehicle_conflicts) == 1
        assert result.vehicle_conflicts[0].reason == "Location discontinuity"

    def test_empty_timetable_skipped(self):
        vid = uuid7()
        node = make_block_node()
        s1 = make_service_with_window(vid, node, arrival=0, departure=10)
        s2 = Service(id=next(_id_counter), name="S", vehicle_id=vid, path=[], timetable=[])

        result = validate(s2, [s1])
        assert result.vehicle_conflicts == []

    def test_non_consecutive_overlap_detected(self):
        vid = uuid7()
        node = make_block_node()
        sa = make_service_with_window(vid, node, arrival=0, departure=20)
        sb = make_service_with_window(vid, node, arrival=5, departure=10)
        sc = make_service_with_window(vid, node, arrival=15, departure=25)

        result = validate(sc, [sa, sb])
        pairs = {(c.service_a_id, c.service_b_id) for c in result.vehicle_conflicts}
        assert (sa.id, sb.id) in pairs
        assert (sa.id, sc.id) in pairs


class TestBlockConflicts:
    def test_no_conflicts(self):
        block = make_block()
        node = make_block_node(block.id)
        s1 = make_service_with_window(uuid7(), node, arrival=0, departure=10)
        s2 = make_service_with_window(uuid7(), node, arrival=10, departure=20)

        result = validate(s2, [s1], [block])
        assert result.block_conflicts == []

    def test_overlapping_on_same_block(self):
        block = make_block()
        node = make_block_node(block.id)
        s1 = make_service_with_window(uuid7(), node, arrival=0, departure=15)
        s2 = make_service_with_window(uuid7(), node, arrival=10, departure=20)

        result = validate(s2, [s1], [block])
        assert len(result.block_conflicts) == 1
        assert result.block_conflicts[0].block_id == block.id

    def test_finds_all_overlapping_pairs(self):
        """A:[0,10], B:[1,2], C:[3,9] — should find A-B, A-C, B-C is not overlap (3 >= 2)."""
        block = make_block()
        node = make_block_node(block.id)
        sa = make_service_with_window(uuid7(), node, arrival=0, departure=10)
        sb = make_service_with_window(uuid7(), node, arrival=1, departure=2)
        sc = make_service_with_window(uuid7(), node, arrival=3, departure=9)

        result = validate(sc, [sa, sb], [block])
        pairs = {(c.service_a_id, c.service_b_id) for c in result.block_conflicts}
        assert (sa.id, sb.id) in pairs
        assert (sa.id, sc.id) in pairs
        assert len(result.block_conflicts) == 2

    def test_platform_nodes_ignored(self):
        """Entries on platform nodes should not be checked for block conflicts."""
        block = make_block()
        platform_node = Node(id=uuid7(), type=NodeType.PLATFORM)
        s1 = make_service_with_window(uuid7(), platform_node, arrival=0, departure=15)
        s2 = make_service_with_window(uuid7(), platform_node, arrival=10, departure=20)

        result = validate(s2, [s1], [block])
        assert result.block_conflicts == []
