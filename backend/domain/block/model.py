from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.network.model import Node, NodeType
from domain.service.model import TimetableEntry
from domain.shared.types import EpochSeconds


@dataclass(eq=False)
class Block:
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int

    def __post_init__(self) -> None:
        self._validate_traversal_time(self.traversal_time_seconds)

    def update_traversal_time(self, traversal_time_seconds: int) -> None:
        self._validate_traversal_time(traversal_time_seconds)
        self.traversal_time_seconds = traversal_time_seconds

    def to_node(self) -> Node:
        return Node(id=self.id, type=NodeType.BLOCK)

    def to_timetable_entry(self, order: int, arrival: EpochSeconds) -> TimetableEntry:
        return TimetableEntry(
            order=order,
            node_id=self.id,
            arrival=arrival,
            departure=arrival + self.traversal_time_seconds,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Block) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @staticmethod
    def _validate_traversal_time(value: int) -> None:
        if value <= 0:
            raise ValueError("traversal_time_seconds must be positive")
