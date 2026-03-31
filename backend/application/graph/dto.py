from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.block.model import Block
from domain.network.model import NodeConnection
from domain.station.model import Platform, Station
from domain.vehicle.model import Vehicle


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
