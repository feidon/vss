from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.block.model import Block
from domain.network.model import NodeConnection
from domain.read_model.layout import LayoutData
from domain.station.model import Platform, Station
from domain.vehicle.model import Vehicle


@dataclass(frozen=True)
class Edge:
    id: UUID
    name: str
    from_id: UUID
    to_id: UUID


@dataclass(frozen=True)
class Junction:
    id: UUID
    x: float
    y: float


@dataclass(frozen=True)
class GraphData:
    stations: list[Station]
    blocks: list[Block]
    connections: frozenset[NodeConnection]
    vehicles: list[Vehicle]
    layout: LayoutData
    edges: list[Edge]
    junctions: list[Junction]

    @property
    def platform_to_station_dict(self) -> dict[UUID, Station]:
        return {p.id: s for s in self.stations for p in s.platforms}

    @property
    def platforms(self) -> list[Platform]:
        return [p for s in self.stations for p in s.platforms]

    @property
    def yards(self) -> list[Station]:
        return [s for s in self.stations if s.is_yard]
