from uuid import uuid7

import pytest

from domain.network.model import Node, NodeConnection, NodeType
from domain.service.model import Service, TimetableEntry


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
        id=uuid7(),
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
        with pytest.raises(ValueError, match="chronologically non-overlapping"):
            make_service(path=[n1, n2], timetable=entries)

    def test_entry_referencing_unknown_node_rejected(self):
        n = make_node()
        entries = [
            TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10),
        ]
        with pytest.raises(ValueError, match="not in path"):
            make_service(path=[n], timetable=entries)

    def test_equality_by_id(self):
        sid = uuid7()
        s1 = Service(id=sid, name="A", vehicle_id=uuid7(), path=[], timetable=[])
        s2 = Service(id=sid, name="B", vehicle_id=uuid7(), path=[], timetable=[])
        assert s1 == s2

    def test_hashable(self):
        sid = uuid7()
        s1 = Service(id=sid, name="A", vehicle_id=uuid7(), path=[], timetable=[])
        s2 = Service(id=sid, name="B", vehicle_id=uuid7(), path=[], timetable=[])
        assert {s1, s2} == {s1}


class TestServiceUpdatePath:
    def test_update_path(self):
        n1, n2 = make_node(), make_node()
        service = make_service(path=[n1])
        service.update_path([n1, n2])
        assert len(service.path) == 2

    def test_update_path_rejects_if_entries_reference_missing_node(self):
        n1, n2 = make_node(), make_node()
        entries = [TimetableEntry(order=0, node_id=n1.id, arrival=0, departure=10)]
        service = make_service(path=[n1, n2], timetable=entries)
        with pytest.raises(ValueError, match="not in path"):
            service.update_path([n2])


class TestServiceUpdateTimetable:
    def test_update_timetable(self):
        n = make_node()
        service = make_service(path=[n])
        new_entries = [TimetableEntry(order=0, node_id=n.id, arrival=0, departure=10)]
        service.update_timetable(new_entries)
        assert len(service.timetable) == 1

    def test_update_timetable_rejects_invalid_ordering(self):
        n = make_node()
        service = make_service(path=[n])
        entries = [
            TimetableEntry(order=1, node_id=n.id, arrival=0, departure=5),
            TimetableEntry(order=0, node_id=n.id, arrival=10, departure=15),
        ]
        with pytest.raises(ValueError, match="ascending order"):
            service.update_timetable(entries)

    def test_update_timetable_rejects_unknown_node(self):
        n = make_node()
        service = make_service(path=[n])
        entries = [TimetableEntry(order=0, node_id=uuid7(), arrival=0, departure=10)]
        with pytest.raises(ValueError, match="not in path"):
            service.update_timetable(entries)


class TestServiceConnectivity:
    def test_valid_connectivity(self):
        n1, n2 = make_node(), make_node()
        service = make_service(path=[n1, n2])
        connections = frozenset({NodeConnection(from_id=n1.id, to_id=n2.id)})
        service.validate_connectivity(connections)

    def test_missing_connection_rejected(self):
        n1, n2 = make_node(), make_node()
        service = make_service(path=[n1, n2])
        with pytest.raises(ValueError, match="No connection"):
            service.validate_connectivity(frozenset())

    def test_empty_path_rejected(self):
        service = make_service(path=[])
        with pytest.raises(ValueError, match="at least one node"):
            service.validate_connectivity(frozenset())

    def test_single_node_path_always_valid(self):
        service = make_service(path=[make_node()])
        service.validate_connectivity(frozenset())
