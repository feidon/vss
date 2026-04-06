from itertools import count
from uuid import uuid7

import pytest
from domain.block.model import Block
from domain.domain_service.conflict import detect_conflicts
from domain.domain_service.conflict.model import (
    BatteryConflictType,
    BlockConflict,
    InterlockingConflict,
    ServiceConflicts,
)
from domain.network.model import Node, NodeType
from domain.service.model import Service, TimetableEntry
from domain.vehicle.model import Vehicle

_id_counter = count(1)


@pytest.fixture(autouse=True)
def _reset_id_counter():
    global _id_counter
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
    entry = TimetableEntry(
        order=0, node_id=node.id, arrival=arrival, departure=departure
    )
    return Service(
        id=next(_id_counter),
        name="S",
        vehicle_id=vehicle_id,
        route=[node],
        timetable=[entry],
    )


def validate(
    candidate: Service,
    others: list[Service],
    blocks: list[Block] | None = None,
    vehicles: list[Vehicle] | None = None,
):
    return detect_conflicts(candidate, others, blocks or [], vehicles)


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
        s2 = Service(
            id=next(_id_counter), name="S", vehicle_id=vid, route=[], timetable=[]
        )

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
        """A:[0,10], B:[1,2], C:[3,9] - should find A-B, A-C, B-C is not overlap (3 >= 2)."""
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


class TestInterlockingConflicts:
    def test_same_group_different_blocks_conflict(self):
        """Two services on different blocks in the same group with overlapping times."""
        b1 = make_block(group=1)
        b2 = make_block(group=1)
        n1 = make_block_node(b1.id)
        n2 = make_block_node(b2.id)
        s1 = make_service_with_window(uuid7(), n1, arrival=0, departure=15)
        s2 = make_service_with_window(uuid7(), n2, arrival=10, departure=20)

        result = validate(s2, [s1], [b1, b2])
        assert len(result.interlocking_conflicts) == 1
        assert result.interlocking_conflicts[0].group == 1

    def test_group_zero_excluded(self):
        """Blocks in group 0 (no interlocking group) should not trigger conflicts."""
        b1 = make_block(group=0)
        b2 = make_block(group=0)
        n1 = make_block_node(b1.id)
        n2 = make_block_node(b2.id)
        s1 = make_service_with_window(uuid7(), n1, arrival=0, departure=15)
        s2 = make_service_with_window(uuid7(), n2, arrival=10, departure=20)

        result = validate(s2, [s1], [b1, b2])
        assert result.interlocking_conflicts == []


def _build_block_segment(path, timetable, num_blocks, t, order, block_time):
    for _ in range(num_blocks):
        node = Node(id=uuid7(), type=NodeType.BLOCK)
        path.append(node)
        timetable.append(
            TimetableEntry(
                order=order, node_id=node.id, arrival=t, departure=t + block_time
            )
        )
        t += block_time
        order += 1
    return t, order


def make_multi_block_service(
    vehicle_id,
    num_blocks: int,
    arrival: int,
    block_time: int = 30,
    starts_at_yard: bool = False,
    ends_at_yard: bool = False,
) -> Service:
    """Create a service traversing `num_blocks` block nodes sequentially.

    If ``starts_at_yard`` is True, a Yard node with a zero-duration entry is
    prepended (the vehicle departs from a Yard).
    If ``ends_at_yard`` is True, a Yard node with a zero-duration entry is
    appended (the vehicle returns to a Yard).
    """
    path = []
    timetable = []
    t = arrival
    order = 0
    if starts_at_yard:
        yard_node = Node(id=uuid7(), type=NodeType.YARD)
        path.append(yard_node)
        timetable.append(
            TimetableEntry(order=order, node_id=yard_node.id, arrival=t, departure=t)
        )
        order += 1
    t, order = _build_block_segment(path, timetable, num_blocks, t, order, block_time)
    if ends_at_yard:
        yard_node = Node(id=uuid7(), type=NodeType.YARD)
        path.append(yard_node)
        timetable.append(
            TimetableEntry(order=order, node_id=yard_node.id, arrival=t, departure=t)
        )
    return Service(
        id=next(_id_counter),
        name="S",
        vehicle_id=vehicle_id,
        route=path,
        timetable=timetable,
    )


def make_service_with_mid_yard(
    vehicle_id,
    blocks_before: int,
    yard_dwell: int,
    blocks_after: int,
    arrival: int = 0,
    block_time: int = 10,
) -> Service:
    """Create a service: N blocks -> yard (dwell) -> M blocks."""
    path = []
    timetable = []
    t = arrival
    order = 0
    t, order = _build_block_segment(
        path, timetable, blocks_before, t, order, block_time
    )
    yard = Node(id=uuid7(), type=NodeType.YARD)
    path.append(yard)
    timetable.append(
        TimetableEntry(
            order=order, node_id=yard.id, arrival=t, departure=t + yard_dwell
        )
    )
    t += yard_dwell
    order += 1
    t, order = _build_block_segment(path, timetable, blocks_after, t, order, block_time)
    return Service(
        id=next(_id_counter),
        name="S",
        vehicle_id=vehicle_id,
        route=path,
        timetable=timetable,
    )


class TestBatteryConflicts:
    def test_no_conflict_sufficient_battery(self):
        """5 blocks: 80 - 5 = 75% - well above 30%."""
        v = Vehicle(id=uuid7(), name="V1")
        s = make_multi_block_service(v.id, num_blocks=5, arrival=0)

        result = validate(s, [], vehicles=[v])
        assert result.battery_conflicts == []

    def test_low_battery_conflict_detected(self):
        """75 blocks: 80 - 75 = 5% < 30% - should trigger LowBatteryConflict."""
        v = Vehicle(id=uuid7(), name="V1")
        s = make_multi_block_service(v.id, num_blocks=75, arrival=0)

        result = validate(s, [], vehicles=[v])
        assert len(result.battery_conflicts) == 1
        assert result.battery_conflicts[0].type == BatteryConflictType.LOWBATTERY
        assert result.battery_conflicts[0].service_id == s.id
        assert result.has_conflicts

    def test_insufficient_charge_conflict_detected(self):
        """First service drains to 30%, second departs from yard with 0 charge time → can't depart."""
        v = Vehicle(id=uuid7(), name="V1")
        # Service 1: 50 blocks → 80 - 50 = 30% (not critical, exactly at threshold)
        s1 = make_multi_block_service(v.id, num_blocks=50, arrival=0, block_time=10)
        # s1 ends at 500
        # Service 2 starts at yard (zero-duration) → charge 0 → 30% < 80% → can't depart
        s2 = make_multi_block_service(
            v.id, num_blocks=5, arrival=600, block_time=10, starts_at_yard=True
        )

        result = validate(s2, [s1], vehicles=[v])
        assert len(result.battery_conflicts) == 1
        assert result.battery_conflicts[0].type == BatteryConflictType.INSUFCHARGE
        assert result.battery_conflicts[0].service_id == s2.id
        assert result.has_conflicts

    def test_charging_prevents_conflict(self):
        """Enough idle time at the Yard to charge above 80% - no conflict."""
        v = Vehicle(id=uuid7(), name="V1")
        # Service 1: 50 blocks → 80 - 50 = 30%, returns to Yard
        s1 = make_multi_block_service(
            v.id, num_blocks=50, arrival=0, block_time=10, ends_at_yard=True
        )
        # s1 ends at 500
        # Service 2 starts at 1100 → 600s idle at Yard → 600 // 12 = 50% → 30 + 50 = 80% ≥ 80%
        s2 = make_multi_block_service(v.id, num_blocks=5, arrival=1100, block_time=10)

        result = validate(s2, [s1], vehicles=[v])
        assert result.battery_conflicts == []

    def test_no_charging_when_not_at_yard(self):
        """Vehicle doesn't return to Yard between services - battery drops to critical."""
        v = Vehicle(id=uuid7(), name="V1")
        # Service 1: 50 blocks → 80 - 50 = 30%, does NOT return to Yard
        s1 = make_multi_block_service(v.id, num_blocks=50, arrival=0, block_time=10)
        # s1 ends at 500
        # No yard anywhere → no charging, no can_depart check → battery hits <30 on next block
        s2 = make_multi_block_service(v.id, num_blocks=5, arrival=1100, block_time=10)

        result = validate(s2, [s1], vehicles=[v])
        assert len(result.battery_conflicts) == 1

    def test_cumulative_drain_across_services(self):
        """Three services that cumulatively drain the battery below threshold."""
        v = Vehicle(id=uuid7(), name="V1")
        # S1: 30 blocks → 80 - 30 = 50%, returns to Yard, ends at 300
        s1 = make_multi_block_service(
            v.id, num_blocks=30, arrival=0, block_time=10, ends_at_yard=True
        )
        # Gap at Yard: 300 → 1500 = 1200s → 1200 // 12 = 100% → 50 + 100 = 150 → capped at 100
        # S2: 30 blocks → 100 - 30 = 70%, returns to Yard, ends at 1800
        s2 = make_multi_block_service(
            v.id, num_blocks=30, arrival=1500, block_time=10, ends_at_yard=True
        )
        # S2 yard charges: 1900 - 1800 = 100s → 100 // 12 = 8% → 70 + 8 = 78% < 80% → can't depart
        s3 = make_multi_block_service(v.id, num_blocks=5, arrival=1900, block_time=10)

        result = validate(s3, [s1, s2], vehicles=[v])
        assert len(result.battery_conflicts) == 1
        assert result.battery_conflicts[0].service_id == s2.id
        assert result.battery_conflicts[0].type == BatteryConflictType.INSUFCHARGE
        assert result.has_conflicts

    def test_mid_service_yard_provides_charging(self):
        """A yard in the middle of a service charges the vehicle, preventing low battery."""
        v = Vehicle(id=uuid7(), name="V1")
        # 45 blocks → yard (960s dwell) → 10 blocks
        # Without yard: 80 - 55 = 25 < 30 → low battery
        # With yard: 80 - 45 = 35, charge 960 // 12 = 80 → 100 (capped), can_depart OK,
        #   then 10 blocks → 90. No conflict.
        s = make_service_with_mid_yard(
            v.id, blocks_before=45, yard_dwell=960, blocks_after=10
        )

        result = validate(s, [], vehicles=[v])
        assert result.battery_conflicts == []

    def test_mid_service_yard_insufficient_charge(self):
        """Yard mid-service but dwell too short to reach 80% → can't depart."""
        v = Vehicle(id=uuid7(), name="V1")
        # 50 blocks → yard (100s dwell) → 1 block
        # 80 - 50 = 30, charge 100 // 12 = 8 → 38 < 80 → insufficient charge
        s = make_service_with_mid_yard(
            v.id, blocks_before=50, yard_dwell=100, blocks_after=1
        )

        result = validate(s, [], vehicles=[v])
        assert len(result.battery_conflicts) == 1
        assert result.battery_conflicts[0].service_id == s.id
        assert result.battery_conflicts[0].type == BatteryConflictType.INSUFCHARGE
        assert result.has_conflicts

    def test_battery_exactly_at_critical_threshold_no_conflict(self):
        """Battery at exactly 30% is NOT critical (< 30 required)."""
        v = Vehicle(id=uuid7(), name="V1")
        # 50 blocks: 80 - 50 = 30 - exactly at threshold, not below
        s = make_multi_block_service(v.id, num_blocks=50, arrival=0)

        result = validate(s, [], vehicles=[v])
        assert result.battery_conflicts == []

    def test_battery_exactly_at_depart_threshold_no_conflict(self):
        """Battery at exactly 80% can depart (>= 80 required)."""
        v = Vehicle(id=uuid7(), name="V1")
        # 50 blocks → 30%, yard charges 600s → 30 + 50 = 80% - exactly at threshold
        s1 = make_multi_block_service(
            v.id, num_blocks=50, arrival=0, block_time=10, ends_at_yard=True
        )
        s2 = make_multi_block_service(v.id, num_blocks=5, arrival=1100, block_time=10)

        result = validate(s2, [s1], vehicles=[v])
        assert result.battery_conflicts == []

    def test_no_vehicles_skips_battery_check(self):
        """When no vehicles provided, battery checks are skipped entirely."""
        s = make_multi_block_service(uuid7(), num_blocks=75, arrival=0)

        result = validate(s, [])
        assert result.battery_conflicts == []

    def test_different_vehicle_entries_ignored(self):
        """Battery simulation only considers services assigned to the candidate's vehicle."""
        v1 = Vehicle(id=uuid7(), name="V1")
        v2 = Vehicle(id=uuid7(), name="V2")
        # v2 has a heavy service - should not affect v1's battery
        heavy = make_multi_block_service(v2.id, num_blocks=75, arrival=0, block_time=10)
        light = make_multi_block_service(v1.id, num_blocks=5, arrival=0, block_time=10)

        result = validate(light, [heavy], vehicles=[v1, v2])
        assert result.battery_conflicts == []

    def test_yard_at_end_no_conflict_when_no_subsequent_service(self):
        """Trailing yard with no subsequent service → vehicle is parked, no departure check."""
        v = Vehicle(id=uuid7(), name="V1")
        # 5 blocks → 75%, yard at end → no departure needed → no conflict
        s = make_multi_block_service(
            v.id, num_blocks=5, arrival=0, block_time=10, ends_at_yard=True
        )

        result = validate(s, [], vehicles=[v])
        assert result.battery_conflicts == []

    def test_round_trip_yard_to_yard_no_false_insufficient_charge(self):
        """Yard → blocks → Yard round trip: battery drops below 80% but no conflict."""
        v = Vehicle(id=uuid7(), name="V1")
        # Yard → 10 blocks → Yard: 80 - 10 = 70%, no departure needed
        s = make_multi_block_service(
            v.id,
            num_blocks=10,
            arrival=0,
            block_time=30,
            starts_at_yard=True,
            ends_at_yard=True,
        )

        result = validate(s, [], vehicles=[v])
        assert result.battery_conflicts == []

    def test_trailing_yard_with_subsequent_service_still_triggers_insufficient_charge(
        self,
    ):
        """Yard at end of service A, service B departs shortly after → INSUFCHARGE."""
        v = Vehicle(id=uuid7(), name="V1")
        # Service 1: 50 blocks → 30%, ends at Yard at t=500
        s1 = make_multi_block_service(
            v.id, num_blocks=50, arrival=0, block_time=10, ends_at_yard=True
        )
        # Service 2: starts 100s later → charge 100//12=8 → 38% < 80% → can't depart
        s2 = make_multi_block_service(v.id, num_blocks=5, arrival=600, block_time=10)

        result = validate(s2, [s1], vehicles=[v])
        assert len(result.battery_conflicts) == 1
        assert result.battery_conflicts[0].type == BatteryConflictType.INSUFCHARGE


class TestVehicleConflictsEdgeCases:
    def test_single_service_no_conflicts(self):
        """One service, no others → no vehicle conflicts."""
        vid = uuid7()
        node = make_block_node()
        s1 = make_service_with_window(vid, node, arrival=0, departure=10)

        result = validate(s1, [])
        assert result.vehicle_conflicts == []

    def test_multiple_location_discontinuities(self):
        """3 sequential services at different locations → 2 discontinuity conflicts."""
        vid = uuid7()
        node_a, node_b, node_c = (
            make_block_node(),
            make_block_node(),
            make_block_node(),
        )
        s1 = make_service_with_window(vid, node_a, arrival=0, departure=10)
        s2 = make_service_with_window(vid, node_b, arrival=10, departure=20)
        s3 = make_service_with_window(vid, node_c, arrival=20, departure=30)

        result = validate(s3, [s1, s2])
        discontinuities = [
            c for c in result.vehicle_conflicts if c.reason == "Location discontinuity"
        ]
        assert len(discontinuities) == 2

    def test_overlap_and_discontinuity_combined(self):
        """2 services for same vehicle, overlapping in time AND at different locations."""
        vid = uuid7()
        node_a = make_block_node()
        node_b = make_block_node()
        s1 = make_service_with_window(vid, node_a, arrival=0, departure=20)
        s2 = make_service_with_window(vid, node_b, arrival=10, departure=30)

        result = validate(s2, [s1])
        reasons = {c.reason for c in result.vehicle_conflicts}
        assert len(result.vehicle_conflicts) >= 2
        assert "Overlapping time windows" in reasons
        assert "Location discontinuity" in reasons


class TestInterlockingConflictsEdgeCases:
    def test_same_block_same_group_not_interlocking(self):
        """Two services on the SAME block in group 1 → block conflict, not interlocking."""
        block = make_block(group=1)
        node = make_block_node(block.id)
        s1 = make_service_with_window(uuid7(), node, arrival=0, departure=15)
        s2 = make_service_with_window(uuid7(), node, arrival=10, departure=20)

        result = validate(s2, [s1], [block])
        assert result.interlocking_conflicts == []

    def test_different_groups_no_conflict(self):
        """Service A on block in group 1, service B on block in group 2 → no interlocking conflict."""
        b1 = make_block(group=1)
        b2 = make_block(group=2)
        n1 = make_block_node(b1.id)
        n2 = make_block_node(b2.id)
        s1 = make_service_with_window(uuid7(), n1, arrival=0, departure=15)
        s2 = make_service_with_window(uuid7(), n2, arrival=10, departure=20)

        result = validate(s2, [s1], [b1, b2])
        assert result.interlocking_conflicts == []

    def test_multi_group_conflicts(self):
        """4 blocks in 2 groups, overlapping services → 2 interlocking conflicts."""
        b1a = make_block(group=1)
        b1b = make_block(group=1)
        b2a = make_block(group=2)
        b2b = make_block(group=2)
        n1a = make_block_node(b1a.id)
        n1b = make_block_node(b1b.id)
        n2a = make_block_node(b2a.id)
        n2b = make_block_node(b2b.id)
        # Service A uses blocks from group 1 and group 2
        sa = Service(
            id=next(_id_counter),
            name="S",
            vehicle_id=uuid7(),
            route=[n1a, n2a],
            timetable=[
                TimetableEntry(order=0, node_id=n1a.id, arrival=0, departure=15),
                TimetableEntry(order=1, node_id=n2a.id, arrival=15, departure=30),
            ],
        )
        # Service B uses different blocks in same groups, overlapping with A
        sb = Service(
            id=next(_id_counter),
            name="S",
            vehicle_id=uuid7(),
            route=[n1b, n2b],
            timetable=[
                TimetableEntry(order=0, node_id=n1b.id, arrival=10, departure=20),
                TimetableEntry(order=1, node_id=n2b.id, arrival=20, departure=35),
            ],
        )

        result = validate(sb, [sa], [b1a, b1b, b2a, b2b])
        assert len(result.interlocking_conflicts) == 2
        groups = {c.group for c in result.interlocking_conflicts}
        assert groups == {1, 2}


class TestBlockConflictsEdgeCases:
    def test_multiple_blocks_with_overlaps(self):
        """Two blocks, each with overlapping services → 2 block conflicts total."""
        block_a = make_block()
        block_b = make_block()
        node_a = make_block_node(block_a.id)
        node_b = make_block_node(block_b.id)
        # Service 1 uses both blocks
        s1 = Service(
            id=next(_id_counter),
            name="S",
            vehicle_id=uuid7(),
            route=[node_a, node_b],
            timetable=[
                TimetableEntry(order=0, node_id=node_a.id, arrival=0, departure=15),
                TimetableEntry(order=1, node_id=node_b.id, arrival=15, departure=30),
            ],
        )
        # Service 2 uses same blocks, overlapping with s1 on both blocks
        s2 = Service(
            id=next(_id_counter),
            name="S",
            vehicle_id=uuid7(),
            route=[node_a, node_b],
            timetable=[
                TimetableEntry(order=0, node_id=node_a.id, arrival=10, departure=20),
                TimetableEntry(order=1, node_id=node_b.id, arrival=20, departure=35),
            ],
        )

        result = validate(s2, [s1], [block_a, block_b])
        assert len(result.block_conflicts) == 2
        conflicting_blocks = {c.block_id for c in result.block_conflicts}
        assert conflicting_blocks == {block_a.id, block_b.id}

    def test_touching_boundary_no_conflict(self):
        """Service A departs at t=100, service B arrives at t=100 → no conflict."""
        block = make_block()
        node = make_block_node(block.id)
        s1 = make_service_with_window(uuid7(), node, arrival=50, departure=100)
        s2 = make_service_with_window(uuid7(), node, arrival=100, departure=150)

        result = validate(s2, [s1], [block])
        assert result.block_conflicts == []


class TestBatteryConflictsEdgeCases:
    def test_empty_steps_no_conflict(self):
        """Service has only platform nodes (no blocks) → no battery conflict."""
        v = Vehicle(id=uuid7(), name="V1")
        platform_node = Node(id=uuid7(), type=NodeType.PLATFORM)
        s = make_service_with_window(v.id, platform_node, arrival=0, departure=100)

        result = validate(s, [], vehicles=[v])
        assert result.battery_conflicts == []

    def test_single_block_traversal_no_conflict(self):
        """1 block: 80 - 1 = 79% > 30% → no conflict."""
        v = Vehicle(id=uuid7(), name="V1")
        s = make_multi_block_service(v.id, num_blocks=1, arrival=0)

        result = validate(s, [], vehicles=[v])
        assert result.battery_conflicts == []

    def test_battery_exactly_at_critical_boundary(self):
        """50 blocks: 80 - 50 = 30%, exactly at threshold → no conflict."""
        v = Vehicle(id=uuid7(), name="V1")
        s = make_multi_block_service(v.id, num_blocks=50, arrival=0)

        result = validate(s, [], vehicles=[v])
        assert result.battery_conflicts == []


class TestServiceConflictsModel:
    def test_has_conflicts_with_only_block_conflicts(self):
        """ServiceConflicts with only block conflicts → has_conflicts is True."""
        conflicts = ServiceConflicts(
            vehicle_conflicts=[],
            block_conflicts=[
                BlockConflict(
                    block_id=uuid7(),
                    service_a_id=1,
                    service_b_id=2,
                    overlap_start=0,
                    overlap_end=10,
                )
            ],
            interlocking_conflicts=[],
            battery_conflicts=[],
        )
        assert conflicts.has_conflicts is True

    def test_has_conflicts_with_only_interlocking_conflicts(self):
        """ServiceConflicts with only interlocking conflicts → has_conflicts is True."""
        conflicts = ServiceConflicts(
            vehicle_conflicts=[],
            block_conflicts=[],
            interlocking_conflicts=[
                InterlockingConflict(
                    group=1,
                    block_a_id=uuid7(),
                    block_b_id=uuid7(),
                    service_a_id=1,
                    service_b_id=2,
                    overlap_start=0,
                    overlap_end=10,
                )
            ],
            battery_conflicts=[],
        )
        assert conflicts.has_conflicts is True

    def test_has_conflicts_all_empty(self):
        """All empty lists → has_conflicts is False."""
        conflicts = ServiceConflicts(
            vehicle_conflicts=[],
            block_conflicts=[],
            interlocking_conflicts=[],
            battery_conflicts=[],
        )
        assert conflicts.has_conflicts is False
