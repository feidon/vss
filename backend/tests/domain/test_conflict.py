from itertools import count
from uuid import uuid7

import pytest

from domain.block.model import Block
from domain.network.model import Node, NodeType
from domain.service.conflict import ConflictDetector
from domain.service.model import Service, TimetableEntry
from domain.vehicle.model import Vehicle

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


def validate(
    candidate: Service,
    others: list[Service],
    blocks: list[Block] | None = None,
    vehicles: list[Vehicle] | None = None,
):
    return ConflictDetector.validate_service(candidate, others, blocks or [], vehicles)


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


def make_multi_block_service(
    vehicle_id,
    num_blocks: int,
    arrival: int,
    block_time: int = 30,
) -> Service:
    """Create a service traversing `num_blocks` block nodes sequentially."""
    path = []
    timetable = []
    t = arrival
    for i in range(num_blocks):
        node = Node(id=uuid7(), type=NodeType.BLOCK)
        path.append(node)
        timetable.append(TimetableEntry(order=i, node_id=node.id, arrival=t, departure=t + block_time))
        t += block_time
    return Service(
        id=next(_id_counter),
        name="S",
        vehicle_id=vehicle_id,
        path=path,
        timetable=timetable,
    )


class TestBatteryConflicts:
    def test_no_conflict_sufficient_battery(self):
        """5 blocks: 100 - 5 = 95% — well above 30%."""
        v = Vehicle(id=uuid7(), name="V1")
        s = make_multi_block_service(v.id, num_blocks=5, arrival=0)

        result = validate(s, [], vehicles=[v])
        assert result.low_battery_conflicts == []
        assert result.insufficient_charge_conflicts == []

    def test_low_battery_conflict_detected(self):
        """75 blocks: 100 - 75 = 25% < 30% — should trigger LowBatteryConflict."""
        v = Vehicle(id=uuid7(), name="V1")
        s = make_multi_block_service(v.id, num_blocks=75, arrival=0)

        result = validate(s, [], vehicles=[v])
        assert len(result.low_battery_conflicts) == 1
        assert result.low_battery_conflicts[0].service_id == s.id
        assert result.has_conflicts

    def test_insufficient_charge_conflict_detected(self):
        """First service drains to 30%, short idle, second service can't depart at 80%."""
        v = Vehicle(id=uuid7(), name="V1")
        # Service 1: 70 blocks → 100 - 70 = 30%
        s1 = make_multi_block_service(v.id, num_blocks=70, arrival=0, block_time=10)
        # s1 ends at 70 * 10 = 700
        # Service 2 starts at 800 → 100s idle → 100 // 12 = 8% → 30 + 8 = 38% < 80%
        s2 = make_multi_block_service(v.id, num_blocks=5, arrival=800, block_time=10)

        result = validate(s2, [s1], vehicles=[v])
        assert len(result.insufficient_charge_conflicts) == 1
        assert result.insufficient_charge_conflicts[0].service_a_id == s1.id
        assert result.insufficient_charge_conflicts[0].service_b_id == s2.id
        assert result.has_conflicts

    def test_charging_prevents_conflict(self):
        """Enough idle time to charge above 80% — no conflict."""
        v = Vehicle(id=uuid7(), name="V1")
        # Service 1: 70 blocks → 100 - 70 = 30%
        s1 = make_multi_block_service(v.id, num_blocks=70, arrival=0, block_time=10)
        # s1 ends at 700
        # Service 2 starts at 1300 → 600s idle → 600 // 12 = 50% → 30 + 50 = 80% ≥ 80%
        s2 = make_multi_block_service(v.id, num_blocks=5, arrival=1300, block_time=10)

        result = validate(s2, [s1], vehicles=[v])
        assert result.low_battery_conflicts == []
        assert result.insufficient_charge_conflicts == []

    def test_cumulative_drain_across_services(self):
        """Three services that cumulatively drain the battery below threshold."""
        v = Vehicle(id=uuid7(), name="V1")
        # S1: 30 blocks → 100 - 30 = 70%, ends at 300
        s1 = make_multi_block_service(v.id, num_blocks=30, arrival=0, block_time=10)
        # Gap: 300 → 1500 = 1200s → 1200 // 12 = 100% → 70 + 100 = 170 → capped at 100
        # S2: 30 blocks → 100 - 30 = 70%, ends at 1800
        s2 = make_multi_block_service(v.id, num_blocks=30, arrival=1500, block_time=10)
        # Gap: 1800 → 1900 = 100s → 100 // 12 = 8% → 70 + 8 = 78% < 80%
        s3 = make_multi_block_service(v.id, num_blocks=5, arrival=1900, block_time=10)

        result = validate(s3, [s1, s2], vehicles=[v])
        assert len(result.insufficient_charge_conflicts) == 1
        assert result.insufficient_charge_conflicts[0].service_a_id == s2.id
        assert result.insufficient_charge_conflicts[0].service_b_id == s3.id
