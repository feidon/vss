from __future__ import annotations

from dataclasses import dataclass, field
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
    layouts: dict[UUID, tuple[float, float]] = field(default_factory=dict)

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
    def yards(self) -> list[Station]:
        return [s for s in self.stations if s.is_yard]
