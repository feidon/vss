from __future__ import annotations

from application.graph.dto import GraphData
from domain.block.repository import BlockRepository
from domain.network.repository import ConnectionRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository


class GraphAppService:
    def __init__(
        self,
        station_repo: StationRepository,
        block_repo: BlockRepository,
        connection_repo: ConnectionRepository,
        vehicle_repo: VehicleRepository,
    ) -> None:
        self._station_repo = station_repo
        self._block_repo = block_repo
        self._connection_repo = connection_repo
        self._vehicle_repo = vehicle_repo

    async def get_graph(self) -> GraphData:
        stations = await self._station_repo.find_all()
        blocks = await self._block_repo.find_all()
        connections = await self._connection_repo.find_all()
        vehicles = await self._vehicle_repo.find_all()
        return GraphData(
            stations=stations,
            blocks=blocks,
            connections=connections,
            vehicles=vehicles,
        )
