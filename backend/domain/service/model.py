from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.error import DomainError, ErrorCode
from domain.network.model import Node, NodeConnection
from domain.shared.types import EpochSeconds


@dataclass(eq=False, kw_only=True)
class Service:
    id: int | None = None
    name: str
    vehicle_id: UUID
    route: list[Node]
    timetable: list[TimetableEntry]

    def __post_init__(self) -> None:
        self._validate_entry_ordering(self.timetable)
        self._validate_entries_in_route(self.timetable, self.route)

    def update_route(
        self,
        route: list[Node],
        timetable: list[TimetableEntry],
        connections: frozenset[NodeConnection],
    ) -> None:
        self._validate_entry_ordering(timetable)
        self._validate_entries_in_route(timetable, route)
        self._validate_connectivity(route, connections)
        self.route = list(route)
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
            raise DomainError(
                ErrorCode.DUPLICATE_ENTRY_ORDERS, "Duplicate entry orders"
            )
        if orders != sorted(orders):
            raise DomainError(
                ErrorCode.ENTRIES_NOT_ASCENDING, "Entries must be in ascending order"
            )
        for i in range(1, len(entries)):
            if entries[i].arrival != entries[i - 1].departure:
                raise DomainError(
                    ErrorCode.ENTRIES_NOT_CONTINUOUS,
                    "Entries must be continuous: departure must equal next arrival",
                )

    @staticmethod
    def _validate_entries_in_route(
        entries: list[TimetableEntry], route: list[Node]
    ) -> None:
        node_ids = {n.id for n in route}
        for entry in entries:
            if entry.node_id not in node_ids:
                raise DomainError(
                    ErrorCode.ENTRY_NODE_NOT_IN_ROUTE,
                    f"Entry references node {entry.node_id} not in route",
                    {"node_id": str(entry.node_id)},
                )

    @staticmethod
    def _validate_connectivity(
        route: list[Node], connections: frozenset[NodeConnection]
    ) -> None:
        if not route:
            raise DomainError(
                ErrorCode.EMPTY_ROUTE, "Route must contain at least one node"
            )
        for i in range(len(route) - 1):
            link = NodeConnection(from_id=route[i].id, to_id=route[i + 1].id)
            if link not in connections:
                raise DomainError(
                    ErrorCode.ROUTE_NOT_CONNECTED,
                    f"No connection: {route[i].id} -> {route[i + 1].id}",
                )


@dataclass(frozen=True)
class TimetableEntry:
    order: int
    node_id: UUID
    arrival: EpochSeconds
    departure: EpochSeconds

    def __post_init__(self) -> None:
        if self.arrival > self.departure:
            raise DomainError(
                ErrorCode.ARRIVAL_AFTER_DEPARTURE,
                f"Arrival ({self.arrival}) must be <= departure ({self.departure})",
            )
