from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.block.model import Block
from domain.block.repository import BlockRepository
from domain.network.model import NodeConnection
from domain.network.repository import ConnectionRepository
from domain.station.model import Platform, Station
from domain.station.repository import StationRepository
from domain.vehicle.model import Vehicle
from domain.vehicle.repository import VehicleRepository


@dataclass(frozen=True)
class GraphData:
    stations: list[Station]
    blocks: list[Block]
    connections: frozenset[NodeConnection]
    vehicles: list[Vehicle]

    @property
    def platform_to_station(self) -> dict[UUID, Station]:
        return {
            p.id: s
            for s in self.stations
            for p in s.platforms
        }

    @property
    def all_platforms(self) -> list[Platform]:
        return [p for s in self.stations for p in s.platforms]

    @property
    def yard(self) -> Station | None:
        return next((s for s in self.stations if s.is_yard), None)


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
