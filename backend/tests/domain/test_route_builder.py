from uuid import uuid7

import pytest
from domain.domain_service.route_builder import build_full_route
from domain.error import DomainError
from domain.network.model import NodeType
from infra.seed import (
    BLOCK_ID_BY_NAME,
    PLATFORM_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
)


@pytest.fixture
def connections():
    return create_connections()


@pytest.fixture
def stations():
    return create_stations()


@pytest.fixture
def blocks():
    return create_blocks()


class TestBuildFullRoute:
    def test_two_stop_route_returns_correct_nodes(self, connections, stations, blocks):
        p1a = PLATFORM_ID_BY_NAME["P1A"]
        p2a = PLATFORM_ID_BY_NAME["P2A"]
        stop_ids = [p1a, p2a]
        dwell_by_stop = {p1a: 60, p2a: 90}
        start_time = 1_000

        route, timetable = build_full_route(
            stop_ids, dwell_by_stop, start_time, connections, stations, blocks
        )

        # Expected full path: P1A -> B3 -> B5 -> P2A
        assert len(route) == 4
        assert route[0].id == p1a
        assert route[0].type == NodeType.PLATFORM
        assert route[1].id == BLOCK_ID_BY_NAME["B3"]
        assert route[1].type == NodeType.BLOCK
        assert route[2].id == BLOCK_ID_BY_NAME["B5"]
        assert route[2].type == NodeType.BLOCK
        assert route[3].id == p2a
        assert route[3].type == NodeType.PLATFORM

    def test_two_stop_route_timetable_timing(self, connections, stations, blocks):
        p1a = PLATFORM_ID_BY_NAME["P1A"]
        p2a = PLATFORM_ID_BY_NAME["P2A"]
        stop_ids = [p1a, p2a]
        dwell_p1a = 60
        dwell_p2a = 90
        dwell_by_stop = {p1a: dwell_p1a, p2a: dwell_p2a}
        traversal_time = 30  # default from seed
        start_time = 1_000

        _, timetable = build_full_route(
            stop_ids, dwell_by_stop, start_time, connections, stations, blocks
        )

        # P1A: arrival=1000, departure=1000+60=1060
        assert timetable[0].node_id == p1a
        assert timetable[0].arrival == start_time
        assert timetable[0].departure == start_time + dwell_p1a

        # B3: arrival=1060, departure=1060+30=1090
        b3_arrival = start_time + dwell_p1a
        assert timetable[1].node_id == BLOCK_ID_BY_NAME["B3"]
        assert timetable[1].arrival == b3_arrival
        assert timetable[1].departure == b3_arrival + traversal_time

        # B5: arrival=1090, departure=1090+30=1120
        b5_arrival = b3_arrival + traversal_time
        assert timetable[2].node_id == BLOCK_ID_BY_NAME["B5"]
        assert timetable[2].arrival == b5_arrival
        assert timetable[2].departure == b5_arrival + traversal_time

        # P2A: arrival=1120, departure=1120+90=1210
        p2a_arrival = b5_arrival + traversal_time
        assert timetable[3].node_id == p2a
        assert timetable[3].arrival == p2a_arrival
        assert timetable[3].departure == p2a_arrival + dwell_p2a

    def test_timetable_order_indices(self, connections, stations, blocks):
        p1a = PLATFORM_ID_BY_NAME["P1A"]
        p2a = PLATFORM_ID_BY_NAME["P2A"]

        _, timetable = build_full_route(
            [p1a, p2a], {}, 0, connections, stations, blocks
        )

        for expected_order, entry in enumerate(timetable):
            assert entry.order == expected_order

    def test_unknown_stop_raises_domain_error(self, connections, stations, blocks):
        unknown_id = uuid7()
        p2a = PLATFORM_ID_BY_NAME["P2A"]

        with pytest.raises(DomainError, match="not found"):
            build_full_route([unknown_id, p2a], {}, 0, connections, stations, blocks)

    def test_second_unknown_stop_raises_domain_error(
        self, connections, stations, blocks
    ):
        p1a = PLATFORM_ID_BY_NAME["P1A"]
        unknown_id = uuid7()

        with pytest.raises(DomainError, match="not found"):
            build_full_route([p1a, unknown_id], {}, 0, connections, stations, blocks)

    def test_missing_dwell_defaults_to_zero(self, connections, stations, blocks):
        p1a = PLATFORM_ID_BY_NAME["P1A"]
        p2a = PLATFORM_ID_BY_NAME["P2A"]

        _, timetable = build_full_route(
            [p1a, p2a], {}, 1_000, connections, stations, blocks
        )

        # P1A with no dwell: departure == arrival
        assert timetable[0].departure == timetable[0].arrival

    def test_three_stop_route_node_count(self, connections, stations, blocks):
        p1a = PLATFORM_ID_BY_NAME["P1A"]
        p2a = PLATFORM_ID_BY_NAME["P2A"]
        p3a = PLATFORM_ID_BY_NAME["P3A"]

        # P1A -> B3 -> B5 -> P2A -> B6 -> B7 -> P3A  (7 nodes)
        route, timetable = build_full_route(
            [p1a, p2a, p3a], {}, 0, connections, stations, blocks
        )

        assert len(route) == 7
        assert len(timetable) == 7
