from uuid import uuid7

import pytest
from domain.domain_service.route_finder import RouteFinder
from domain.error import DomainError
from infra.seed import BLOCK_ID_BY_NAME, PLATFORM_ID_BY_NAME, create_connections


@pytest.fixture
def connections():
    return create_connections()


@pytest.fixture
def block_ids():
    return set(BLOCK_ID_BY_NAME.values())


class TestFindBlockChain:
    def test_p1a_to_p2a(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_ID_BY_NAME["P1A"],
            PLATFORM_ID_BY_NAME["P2A"],
            connections,
            block_ids,
        )
        assert result == [BLOCK_ID_BY_NAME["B3"], BLOCK_ID_BY_NAME["B5"]]

    def test_p1b_to_p2a(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_ID_BY_NAME["P1B"],
            PLATFORM_ID_BY_NAME["P2A"],
            connections,
            block_ids,
        )
        assert result == [BLOCK_ID_BY_NAME["B4"], BLOCK_ID_BY_NAME["B5"]]

    def test_p2a_to_p3a(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_ID_BY_NAME["P2A"],
            PLATFORM_ID_BY_NAME["P3A"],
            connections,
            block_ids,
        )
        assert result == [BLOCK_ID_BY_NAME["B6"], BLOCK_ID_BY_NAME["B7"]]

    def test_p2a_to_p3b(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_ID_BY_NAME["P2A"],
            PLATFORM_ID_BY_NAME["P3B"],
            connections,
            block_ids,
        )
        assert result == [BLOCK_ID_BY_NAME["B6"], BLOCK_ID_BY_NAME["B8"]]

    def test_p3a_to_p2b(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_ID_BY_NAME["P3A"],
            PLATFORM_ID_BY_NAME["P2B"],
            connections,
            block_ids,
        )
        assert result == [BLOCK_ID_BY_NAME["B10"], BLOCK_ID_BY_NAME["B11"]]

    def test_p2b_to_p1a(self, connections, block_ids):
        result = RouteFinder.find_block_chain(
            PLATFORM_ID_BY_NAME["P2B"],
            PLATFORM_ID_BY_NAME["P1A"],
            connections,
            block_ids,
        )
        assert result == [BLOCK_ID_BY_NAME["B12"], BLOCK_ID_BY_NAME["B13"]]

    def test_no_route_raises(self, connections, block_ids):
        # P2A has no direct path to P1A (wrong direction)
        with pytest.raises(DomainError, match="No route"):
            RouteFinder.find_block_chain(
                PLATFORM_ID_BY_NAME["P2A"],
                PLATFORM_ID_BY_NAME["P1A"],
                connections,
                block_ids,
            )

    def test_no_route_unknown_node(self, connections, block_ids):
        with pytest.raises(DomainError, match="No route"):
            RouteFinder.find_block_chain(
                uuid7(), PLATFORM_ID_BY_NAME["P2A"], connections, block_ids
            )


class TestBuildFullPath:
    def test_two_stops(self, connections, block_ids):
        result = RouteFinder.build_full_path(
            [PLATFORM_ID_BY_NAME["P1A"], PLATFORM_ID_BY_NAME["P2A"]],
            connections,
            block_ids,
        )
        assert result == [
            PLATFORM_ID_BY_NAME["P1A"],
            BLOCK_ID_BY_NAME["B3"],
            BLOCK_ID_BY_NAME["B5"],
            PLATFORM_ID_BY_NAME["P2A"],
        ]

    def test_three_stops(self, connections, block_ids):
        result = RouteFinder.build_full_path(
            [
                PLATFORM_ID_BY_NAME["P1A"],
                PLATFORM_ID_BY_NAME["P2A"],
                PLATFORM_ID_BY_NAME["P3A"],
            ],
            connections,
            block_ids,
        )
        assert result == [
            PLATFORM_ID_BY_NAME["P1A"],
            BLOCK_ID_BY_NAME["B3"],
            BLOCK_ID_BY_NAME["B5"],
            PLATFORM_ID_BY_NAME["P2A"],
            BLOCK_ID_BY_NAME["B6"],
            BLOCK_ID_BY_NAME["B7"],
            PLATFORM_ID_BY_NAME["P3A"],
        ]

    def test_full_loop(self, connections, block_ids):
        # P1A -> P2A -> P3A -> P2B -> P1A
        result = RouteFinder.build_full_path(
            [
                PLATFORM_ID_BY_NAME["P1A"],
                PLATFORM_ID_BY_NAME["P2A"],
                PLATFORM_ID_BY_NAME["P3A"],
                PLATFORM_ID_BY_NAME["P2B"],
                PLATFORM_ID_BY_NAME["P1A"],
            ],
            connections,
            block_ids,
        )
        assert result == [
            PLATFORM_ID_BY_NAME["P1A"],
            BLOCK_ID_BY_NAME["B3"],
            BLOCK_ID_BY_NAME["B5"],
            PLATFORM_ID_BY_NAME["P2A"],
            BLOCK_ID_BY_NAME["B6"],
            BLOCK_ID_BY_NAME["B7"],
            PLATFORM_ID_BY_NAME["P3A"],
            BLOCK_ID_BY_NAME["B10"],
            BLOCK_ID_BY_NAME["B11"],
            PLATFORM_ID_BY_NAME["P2B"],
            BLOCK_ID_BY_NAME["B12"],
            BLOCK_ID_BY_NAME["B13"],
            PLATFORM_ID_BY_NAME["P1A"],
        ]

    def test_single_stop_raises(self, connections, block_ids):
        with pytest.raises(DomainError, match="At least two stops"):
            RouteFinder.build_full_path(
                [PLATFORM_ID_BY_NAME["P1A"]], connections, block_ids
            )
