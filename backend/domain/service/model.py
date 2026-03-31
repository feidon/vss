from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.network.model import Node, NodeConnection

EpochSeconds = int


@dataclass(eq=False)
class Service:
    id: int
    name: str
    vehicle_id: UUID
    path: list[Node]
    timetable: list[TimetableEntry]

    def __post_init__(self) -> None:
        _validate_entry_ordering(self.timetable)
        _validate_entries_in_path(self.timetable, self.path)

    def update_path(self, path: list[Node]) -> None:
        _validate_entries_in_path(self.timetable, path)
        self.path = list(path)

    def update_timetable(self, entries: list[TimetableEntry]) -> None:
        _validate_entry_ordering(entries)
        _validate_entries_in_path(entries, self.path)
        self.timetable = list(entries)

    def validate_connectivity(self, connections: frozenset[NodeConnection]) -> None:
        if not self.path:
            raise ValueError("Path must contain at least one node")
        for i in range(len(self.path) - 1):
            link = NodeConnection(from_id=self.path[i].id, to_id=self.path[i + 1].id)
            if link not in connections:
                raise ValueError(f"No connection: {self.path[i].id} -> {self.path[i + 1].id}")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Service) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(frozen=True)
class TimetableEntry:
    order: int
    node_id: UUID
    arrival: EpochSeconds
    departure: EpochSeconds

    def __post_init__(self) -> None:
        if self.arrival > self.departure:
            raise ValueError(f"Arrival ({self.arrival}) must be <= departure ({self.departure})")


def _validate_entry_ordering(entries: list[TimetableEntry]) -> None:
    orders = [e.order for e in entries]
    if len(orders) != len(set(orders)):
        raise ValueError("Duplicate entry orders")
    if orders != sorted(orders):
        raise ValueError("Entries must be in ascending order")
    for i in range(1, len(entries)):
        if entries[i].arrival < entries[i - 1].departure:
            raise ValueError("Entries must be chronologically non-overlapping")


def _validate_entries_in_path(entries: list[TimetableEntry], path: list[Node]) -> None:
    node_ids = {n.id for n in path}
    for entry in entries:
        if entry.node_id not in node_ids:
            raise ValueError(f"Entry references node {entry.node_id} not in path")
