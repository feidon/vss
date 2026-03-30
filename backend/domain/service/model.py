from dataclasses import dataclass
from datetime import time
from uuid import UUID

from domain.network.model import Node, NodeConnection


@dataclass
class Service:
    id: UUID
    name: str
    vehicle_id: UUID
    path: ServicePath
    times: list[ServiceStop]


@dataclass(frozen=True)
class ServicePath:
    nodes: list[Node]

    def validate_connectivity(self, connections: frozenset[NodeConnection]) -> None:
        for i in range(len(self.nodes) - 1):
            link = NodeConnection(from_id=self.nodes[i].id, to_id=self.nodes[i + 1].id)
            if link not in connections:
                raise ValueError(
                    f"No connection: {self.nodes[i].id} -> {self.nodes[i + 1].id}"
                )


@dataclass(frozen=True)
class ServiceStop:
    order: int
    platform_id: UUID
    arrival: time | None
    departure: time | None
