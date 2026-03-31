from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.network.model import Node, NodeConnection
from domain.shared.types import EpochSeconds


@dataclass(eq=False, kw_only=True)
class Service:
    id: int | None = None
    name: str
    vehicle_id: UUID
    path: list[Node]
    timetable: list[TimetableEntry]

    def __post_init__(self) -> None:
        self._validate_entry_ordering(self.timetable)
        self._validate_entries_in_path(self.timetable, self.path)

    def update_route(
        self,
        path: list[Node],
        timetable: list[TimetableEntry],
        connections: frozenset[NodeConnection],
    ) -> None:
        self._validate_entry_ordering(timetable)
        self._validate_entries_in_path(timetable, path)
        self._validate_connectivity(path, connections)
        self.path = list(path)
        self.timetable = list(timetable)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Service):
            return False
        if self.id is None or other.id is None:
            return self is other
        return self.id == other.id

    def __hash__(self) -> int:
        return id(self) if self.id is None else hash(self.id)

    @staticmethod
    def _validate_entry_ordering(entries: list[TimetableEntry]) -> None:
        orders = [e.order for e in entries]
        if len(orders) != len(set(orders)):
            raise ValueError("Duplicate entry orders")
        if orders != sorted(orders):
            raise ValueError("Entries must be in ascending order")
        for i in range(1, len(entries)):
            if entries[i].arrival < entries[i - 1].departure:
                raise ValueError("Entries must be chronologically non-overlapping")

    @staticmethod
    def _validate_entries_in_path(entries: list[TimetableEntry], path: list[Node]) -> None:
        node_ids = {n.id for n in path}
        for entry in entries:
            if entry.node_id not in node_ids:
                raise ValueError(f"Entry references node {entry.node_id} not in path")

    @staticmethod
    def _validate_connectivity(path: list[Node], connections: frozenset[NodeConnection]) -> None:
        if not path:
            raise ValueError("Path must contain at least one node")
        for i in range(len(path) - 1):
            link = NodeConnection(from_id=path[i].id, to_id=path[i + 1].id)
            if link not in connections:
                raise ValueError(f"No connection: {path[i].id} -> {path[i + 1].id}")


@dataclass(frozen=True)
class TimetableEntry:
    order: int
    node_id: UUID
    arrival: EpochSeconds
    departure: EpochSeconds

    def __post_init__(self) -> None:
        if self.arrival > self.departure:
            raise ValueError(f"Arrival ({self.arrival}) must be <= departure ({self.departure})")
