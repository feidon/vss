from uuid import uuid7

import pytest
from application.graph.service import GraphAppService
from domain.block.model import Block
from domain.network.model import NodeConnection
from domain.station.model import Platform, Station
from domain.vehicle.model import Vehicle

from tests.fakes.block_repo import InMemoryBlockRepository
from tests.fakes.connection_repo import InMemoryConnectionRepository
from tests.fakes.node_layout_repo import InMemoryNodeLayoutRepository
from tests.fakes.station_repo import InMemoryStationRepository
from tests.fakes.vehicle_repo import InMemoryVehicleRepository


class TestGraphAppService:
    @pytest.fixture
    def station_repo(self):
        repo = InMemoryStationRepository()
        s = Station(
            id=uuid7(),
            name="S1",
            is_yard=False,
            platforms=[
                Platform(id=uuid7(), name="P1A"),
            ],
        )
        repo._store[s.id] = s
        return repo

    @pytest.fixture
    def block_repo(self):
        repo = InMemoryBlockRepository()
        b = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        repo._store[b.id] = b
        return repo

    @pytest.fixture
    def connection_repo(self):
        return InMemoryConnectionRepository(
            frozenset(
                {
                    NodeConnection(from_id=uuid7(), to_id=uuid7()),
                }
            )
        )

    @pytest.fixture
    def vehicle_repo(self):
        repo = InMemoryVehicleRepository()
        v = Vehicle(id=uuid7(), name="V1")
        repo._store[v.id] = v
        return repo

    @pytest.fixture
    def node_layout_repo(self):
        return InMemoryNodeLayoutRepository()

    @pytest.fixture
    def service(
        self, station_repo, block_repo, connection_repo, vehicle_repo, node_layout_repo
    ):
        return GraphAppService(
            station_repo=station_repo,
            block_repo=block_repo,
            connection_repo=connection_repo,
            vehicle_repo=vehicle_repo,
            node_layout_repo=node_layout_repo,
        )

    async def test_get_graph_assembles_all_data(
        self, service, station_repo, block_repo, vehicle_repo
    ):
        graph = await service.get_graph()
        assert len(graph.stations) == 1
        assert len(graph.blocks) == 1
        assert len(graph.connections) == 1
        assert len(graph.vehicles) == 1

    async def test_get_graph_empty_repos(self):
        svc = GraphAppService(
            station_repo=InMemoryStationRepository(),
            block_repo=InMemoryBlockRepository(),
            connection_repo=InMemoryConnectionRepository(),
            vehicle_repo=InMemoryVehicleRepository(),
            node_layout_repo=InMemoryNodeLayoutRepository(),
        )
        graph = await svc.get_graph()
        assert graph.stations == []
        assert graph.blocks == []
        assert graph.connections == frozenset()
        assert graph.vehicles == []

    async def test_platform_to_station_mapping(self, service):
        graph = await service.get_graph()
        station = graph.stations[0]
        platform = station.platforms[0]
        assert graph.platform_to_station[platform.id] == station

    async def test_yard_property(self):
        repo = InMemoryStationRepository()
        yard = Station(id=uuid7(), name="Y", is_yard=True, platforms=[])
        non_yard = Station(id=uuid7(), name="S1", is_yard=False, platforms=[])
        repo._store[yard.id] = yard
        repo._store[non_yard.id] = non_yard

        svc = GraphAppService(
            station_repo=repo,
            block_repo=InMemoryBlockRepository(),
            connection_repo=InMemoryConnectionRepository(),
            vehicle_repo=InMemoryVehicleRepository(),
            node_layout_repo=InMemoryNodeLayoutRepository(),
        )
        graph = await svc.get_graph()
        assert graph.yards == [yard]
