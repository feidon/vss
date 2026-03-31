from uuid import uuid7

import pytest

from domain.network.pathfinder import RouteFinder
from infra.seed import BLOCK_IDS, PLATFORM_IDS, create_connections


@pytest.fixture
def connections():
    return create_connections()


@pytest.fixture
def block_ids():
    return set(BLOCK_IDS.values())


class TestFindBlockChain:
    def test_p1a_to_p2a(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_IDS["P1A"], PLATFORM_IDS["P2A"], connections, block_ids
        )
        assert result == [BLOCK_IDS["B3"], BLOCK_IDS["B5"]]

    def test_p1b_to_p2a(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_IDS["P1B"], PLATFORM_IDS["P2A"], connections, block_ids
        )
        assert result == [BLOCK_IDS["B4"], BLOCK_IDS["B5"]]

    def test_p2a_to_p3a(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_IDS["P2A"], PLATFORM_IDS["P3A"], connections, block_ids
        )
        assert result == [BLOCK_IDS["B6"], BLOCK_IDS["B7"]]

    def test_p2a_to_p3b(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_IDS["P2A"], PLATFORM_IDS["P3B"], connections, block_ids
        )
        assert result == [BLOCK_IDS["B6"], BLOCK_IDS["B8"]]

    def test_p3a_to_p2b(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_IDS["P3A"], PLATFORM_IDS["P2B"], connections, block_ids
        )
        assert result == [BLOCK_IDS["B10"], BLOCK_IDS["B11"]]

    def test_p2b_to_p1a(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_IDS["P2B"], PLATFORM_IDS["P1A"], connections, block_ids
        )
        assert result == [BLOCK_IDS["B12"], BLOCK_IDS["B13"]]

    def test_no_route_raises(self, connections, block_ids):
        # P2A has no direct path to P1A (wrong direction)
        with pytest.raises(ValueError, match="No route"):
            RouteFinder.find_block_chain(
                PLATFORM_IDS["P2A"], PLATFORM_IDS["P1A"], connections, block_ids
            )

    def test_no_route_unknown_node(self, connections, block_ids):
        with pytest.raises(ValueError, match="No route"):
            RouteFinder.find_block_chain(
                uuid7(), PLATFORM_IDS["P2A"], connections, block_ids
            )


class TestBuildFullPath:
    def test_two_stops(self, connections, block_ids):
        result = RouteFinder.build_full_path(
            [PLATFORM_IDS["P1A"], PLATFORM_IDS["P2A"]], connections, block_ids
        )
        assert result == [
            PLATFORM_IDS["P1A"],
            BLOCK_IDS["B3"], BLOCK_IDS["B5"],
            PLATFORM_IDS["P2A"],
        ]

    def test_three_stops(self, connections, block_ids):
        result = RouteFinder.build_full_path(
            [PLATFORM_IDS["P1A"], PLATFORM_IDS["P2A"], PLATFORM_IDS["P3A"]],
            connections, block_ids,
        )
        assert result == [
            PLATFORM_IDS["P1A"],
            BLOCK_IDS["B3"], BLOCK_IDS["B5"],
            PLATFORM_IDS["P2A"],
            BLOCK_IDS["B6"], BLOCK_IDS["B7"],
            PLATFORM_IDS["P3A"],
        ]

    def test_full_loop(self, connections, block_ids):
        # P1A -> P2A -> P3A -> P2B -> P1A
        result = RouteFinder.build_full_path(
            [
                PLATFORM_IDS["P1A"], PLATFORM_IDS["P2A"],
                PLATFORM_IDS["P3A"], PLATFORM_IDS["P2B"],
                PLATFORM_IDS["P1A"],
            ],
            connections, block_ids,
        )
        assert result == [
            PLATFORM_IDS["P1A"],
            BLOCK_IDS["B3"], BLOCK_IDS["B5"],
            PLATFORM_IDS["P2A"],
            BLOCK_IDS["B6"], BLOCK_IDS["B7"],
            PLATFORM_IDS["P3A"],
            BLOCK_IDS["B10"], BLOCK_IDS["B11"],
            PLATFORM_IDS["P2B"],
            BLOCK_IDS["B12"], BLOCK_IDS["B13"],
            PLATFORM_IDS["P1A"],
        ]

    def test_single_stop_raises(self, connections, block_ids):
        with pytest.raises(ValueError, match="At least two stops"):
            RouteFinder.build_full_path(
                [PLATFORM_IDS["P1A"]], connections, block_ids
            )
