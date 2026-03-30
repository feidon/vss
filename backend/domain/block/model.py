from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.network.model import Node, NodeType


@dataclass
class Block:
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int

    def __post_init__(self) -> None:
        if self.traversal_time_seconds <= 0:
            raise ValueError("traversal_time_seconds must be positive")

    def to_node(self) -> Node:
        return Node(id=self.id, type=NodeType.BLOCK)
