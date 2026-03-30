from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from uuid import UUID

from domain.network.model import Node, NodeConnection, NodeType


@dataclass
class Service:
    id: UUID
    name: str
    vehicle_id: UUID
    path: list[Node]
    stops: list[ServiceStop]

    def __post_init__(self) -> None:
        _validate_stop_ordering(self.stops)
        _validate_stops_in_path(self.stops, self.path)

    def update_path(self, path: list[Node]) -> None:
        _validate_stops_in_path(self.stops, path)
        self.path = list(path)

    def update_stops(self, stops: list[ServiceStop]) -> None:
        _validate_stop_ordering(stops)
        _validate_stops_in_path(stops, self.path)
        self.stops = list(stops)

    def validate_connectivity(self, connections: set[NodeConnection]) -> None:
        if not self.path:
            raise ValueError("Path must contain at least one node")
        for i in range(len(self.path) - 1):
            link = NodeConnection(
                from_id=self.path[i].id, to_id=self.path[i + 1].id
            )
            if link not in connections:
                raise ValueError(
                    f"No connection: {self.path[i].id} -> {self.path[i + 1].id}"
                )


@dataclass(frozen=True)
class ServiceStop:
    order: int
    platform_id: UUID
    arrival: time | None
    departure: time | None


def _validate_stop_ordering(stops: list[ServiceStop]) -> None:
    orders = [s.order for s in stops]
    if len(orders) != len(set(orders)):
        raise ValueError("Duplicate stop orders")
    if orders != sorted(orders):
        raise ValueError("Stops must be in ascending order")


def _validate_stops_in_path(stops: list[ServiceStop], path: list[Node]) -> None:
    platform_ids = {n.id for n in path if n.type == NodeType.PLATFORM}
    for stop in stops:
        if stop.platform_id not in platform_ids:
            raise ValueError(
                f"Stop references platform {stop.platform_id} not in path"
            )
