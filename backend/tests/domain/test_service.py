from itertools import count
from uuid import uuid7

import pytest

from domain.network.model import Node, NodeConnection, NodeType
from domain.service.model import Service, TimetableEntry

_id_counter = count(1)


def make_node() -> Node:
    return Node(id=uuid7(), type=NodeType.BLOCK)


def make_service(
    path: list[Node] | None = None,
    timetable: list[TimetableEntry] | None = None,
) -> Service:
    if path is None:
        path = [make_node()]
    if timetable is None:
        timetable = []
    return Service(
        id=next(_id_counter),
        name="S1",
        vehicle_id=uuid7(),
        path=path,
        timetable=timetable,
    )


class TestTimetableEntry:
    def test_create_entry(self):
        entry = TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10)
        assert entry.arrival == 0
        assert entry.departure == 10

    def test_arrival_equals_departure_allowed(self):
        entry = TimetableEntry(order=0, node_id=uuid7(), arrival=5, departure=5)
        assert entry.arrival == entry.departure

    def test_arrival_after_departure_rejected(self):
        with pytest.raises(ValueError, match="must be <="):
            TimetableEntry(order=0, node_id=uuid7(), arrival=10, departure=5)

    def test_frozen(self):
        entry = TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10)
        with pytest.raises(AttributeError):
            entry.order = 1


class TestServiceCreation:
    def test_create_with_empty_timetable(self):
        service = make_service()
        assert service.timetable == []

    def test_create_with_valid_timetable(self):
        n1, n2 = make_node(), make_node()
        entries = [
            TimetableEntry(order=0, node_id=n1.id, arrival=0, departure=10),
            TimetableEntry(order=1, node_id=n2.id, arrival=10, departure=20),
        ]
        service = make_service(path=[n1, n2], timetable=entries)
        assert len(service.timetable) == 2

    def test_duplicate_order_rejected(self):
        n = make_node()
        entries = [
            TimetableEntry(order=0, node_id=n.id, arrival=0, departure=5),
            TimetableEntry(order=0, node_id=n.id, arrival=10, departure=15),
        ]
        with pytest.raises(ValueError, match="Duplicate entry orders"):
            make_service(path=[n], timetable=entries)

    def test_unordered_entries_rejected(self):
        n1, n2 = make_node(), make_node()
        entries = [
            TimetableEntry(order=1, node_id=n1.id, arrival=0, departure=5),
            TimetableEntry(order=0, node_id=n2.id, arrival=10, departure=15),
        ]
        with pytest.raises(ValueError, match="ascending order"):
            make_service(path=[n1, n2], timetable=entries)

    def test_overlapping_time_windows_rejected(self):
        n1, n2 = make_node(), make_node()
        entries = [
            TimetableEntry(order=0, node_id=n1.id, arrival=0, departure=15),
            TimetableEntry(order=1, node_id=n2.id, arrival=10, departure=20),
        ]
        with pytest.raises(ValueError, match="continuous"):
            make_service(path=[n1, n2], timetable=entries)

    def test_gap_between_entries_rejected(self):
        n1, n2 = make_node(), make_node()
        entries = [
            TimetableEntry(order=0, node_id=n1.id, arrival=0, departure=10),
            TimetableEntry(order=1, node_id=n2.id, arrival=15, departure=20),
        ]
        with pytest.raises(ValueError, match="continuous"):
            make_service(path=[n1, n2], timetable=entries)

    def test_entry_referencing_unknown_node_rejected(self):
        n = make_node()
        entries = [
            TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10),
        ]
        with pytest.raises(ValueError, match="not in path"):
            make_service(path=[n], timetable=entries)

    def test_equality_by_id(self):
        s1 = Service(id=1, name="A", vehicle_id=uuid7(), path=[], timetable=[])
        s2 = Service(id=1, name="B", vehicle_id=uuid7(), path=[], timetable=[])
        assert s1 == s2

    def test_hashable(self):
        s1 = Service(id=1, name="A", vehicle_id=uuid7(), path=[], timetable=[])
        s2 = Service(id=1, name="B", vehicle_id=uuid7(), path=[], timetable=[])
        assert {s1, s2} == {s1}


class TestServiceUpdateRoute:
    def test_update_route(self):
        n1, n2 = make_node(), make_node()
        entries = [
            TimetableEntry(order=0, node_id=n1.id, arrival=0, departure=10),
            TimetableEntry(order=1, node_id=n2.id, arrival=10, departure=20),
        ]
        connections = frozenset({NodeConnection(from_id=n1.id, to_id=n2.id)})
        service = make_service(path=[make_node()])
        service.update_route([n1, n2], entries, connections)
        assert len(service.path) == 2
        assert len(service.timetable) == 2

    def test_update_route_rejects_invalid_ordering(self):
        n = make_node()
        entries = [
            TimetableEntry(order=1, node_id=n.id, arrival=0, departure=5),
            TimetableEntry(order=0, node_id=n.id, arrival=100, departure=105),
        ]
        service = make_service(path=[n])
        with pytest.raises(ValueError, match="ascending order"):
            service.update_route([n], entries, frozenset())

    def test_update_route_rejects_entry_not_in_path(self):
        n = make_node()
        entries = [TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10)]
        service = make_service(path=[n])
        with pytest.raises(ValueError, match="not in path"):
            service.update_route([n], entries, frozenset())

    def test_update_route_rejects_disconnected_path(self):
        n1, n2 = make_node(), make_node()
        entries = [
            TimetableEntry(order=0, node_id=n1.id, arrival=0, departure=10),
            TimetableEntry(order=1, node_id=n2.id, arrival=10, departure=20),
        ]
        service = make_service(path=[make_node()])
        with pytest.raises(ValueError, match="No connection"):
            service.update_route([n1, n2], entries, frozenset())


