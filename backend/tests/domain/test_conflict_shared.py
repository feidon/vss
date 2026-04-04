from uuid import uuid7

from domain.block.model import Block
from domain.domain_service.conflict.shared import (
    BlockOccupancy,
    build_occupancies,
    build_vehicle_schedule,
    find_time_overlaps,
)
from domain.network.model import Node, NodeType
from domain.service.model import Service, TimetableEntry


class TestFindTimeOverlaps:
    def test_empty_input(self):
        assert find_time_overlaps([]) == []

    def test_single_entry(self):
        assert find_time_overlaps([BlockOccupancy(1, 0, 10)]) == []

    def test_overlapping_pair(self):
        pairs = find_time_overlaps(
            [BlockOccupancy(1, 0, 15), BlockOccupancy(2, 10, 20)]
        )
        assert len(pairs) == 1

    def test_touching_boundaries_no_overlap(self):
        assert (
            find_time_overlaps([BlockOccupancy(1, 0, 10), BlockOccupancy(2, 10, 20)])
            == []
        )

    def test_unsorted_input(self):
        pairs = find_time_overlaps(
            [BlockOccupancy(2, 10, 20), BlockOccupancy(1, 0, 15)]
        )
        assert len(pairs) == 1

    def test_three_mutually_overlapping(self):
        pairs = find_time_overlaps(
            [
                BlockOccupancy(1, 0, 20),
                BlockOccupancy(2, 5, 15),
                BlockOccupancy(3, 10, 25),
            ]
        )
        assert len(pairs) == 3


def _make_service(sid, vehicle_id, node, arrival, departure):
    entry = TimetableEntry(
        order=0, node_id=node.id, arrival=arrival, departure=departure
    )
    return Service(
        id=sid, name="S", vehicle_id=vehicle_id, route=[node], timetable=[entry]
    )


class TestBuildVehicleSchedule:
    def test_no_matching_vehicle(self):
        v1 = uuid7()
        v2 = uuid7()
        node = Node(id=uuid7(), type=NodeType.PLATFORM)
        svc = _make_service(1, v1, node, arrival=0, departure=100)

        schedule = build_vehicle_schedule(v2, [svc])

        assert schedule.windows == []
        assert schedule.endpoints == []

    def test_sorted_by_start_time(self):
        vid = uuid7()
        n1 = Node(id=uuid7(), type=NodeType.PLATFORM)
        n2 = Node(id=uuid7(), type=NodeType.PLATFORM)
        svc_late = _make_service(1, vid, n1, arrival=100, departure=200)
        svc_early = _make_service(2, vid, n2, arrival=50, departure=150)

        schedule = build_vehicle_schedule(vid, [svc_late, svc_early])

        assert schedule.windows[0].start == 50
        assert schedule.windows[1].start == 100
        assert schedule.endpoints[0].start == 50
        assert schedule.endpoints[1].start == 100


class TestBuildOccupancies:
    def test_empty_services(self):
        by_block, by_group = build_occupancies([], [])
        assert dict(by_block) == {}
        assert dict(by_group) == {}

    def test_skips_platform_entries(self):
        block_node = Node(id=uuid7(), type=NodeType.BLOCK)
        platform_node = Node(id=uuid7(), type=NodeType.PLATFORM)
        block = Block(id=block_node.id, name="B", group=1, traversal_time_seconds=30)

        svc = Service(
            id=1,
            name="S",
            vehicle_id=uuid7(),
            route=[block_node, platform_node],
            timetable=[
                TimetableEntry(order=0, node_id=block_node.id, arrival=0, departure=30),
                TimetableEntry(
                    order=1, node_id=platform_node.id, arrival=30, departure=60
                ),
            ],
        )

        by_block, by_group = build_occupancies([svc], [block])

        assert block_node.id in by_block
        assert platform_node.id not in by_block
        assert len(by_block[block_node.id]) == 1

    def test_groups_by_interlocking_group(self):
        node_g1 = Node(id=uuid7(), type=NodeType.BLOCK)
        node_g2 = Node(id=uuid7(), type=NodeType.BLOCK)
        block_g1 = Block(id=node_g1.id, name="B1", group=1, traversal_time_seconds=30)
        block_g2 = Block(id=node_g2.id, name="B2", group=2, traversal_time_seconds=30)

        svc = Service(
            id=1,
            name="S",
            vehicle_id=uuid7(),
            route=[node_g1, node_g2],
            timetable=[
                TimetableEntry(order=0, node_id=node_g1.id, arrival=0, departure=30),
                TimetableEntry(order=1, node_id=node_g2.id, arrival=30, departure=60),
            ],
        )

        by_block, by_group = build_occupancies([svc], [block_g1, block_g2])

        assert len(by_group[1]) == 1
        assert by_group[1][0].block_id == node_g1.id
        assert len(by_group[2]) == 1
        assert by_group[2][0].block_id == node_g2.id
