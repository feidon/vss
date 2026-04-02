from uuid import uuid7

import pytest
from domain.error import DomainError
from domain.network.model import NodeType
from domain.station.model import Platform, Station


class TestPlatform:
    def test_create_platform(self):
        p = Platform(id=uuid7(), name="P1")
        assert p.name == "P1"

    def test_to_node(self):
        p = Platform(id=uuid7(), name="P1")
        node = p.to_node()
        assert node.id == p.id
        assert node.type == NodeType.PLATFORM

    def test_to_timetable_entry(self):
        p = Platform(id=uuid7(), name="P1")
        entry = p.to_timetable_entry(order=0, arrival=100, dwell_time=100)
        assert entry.node_id == p.id
        assert entry.order == 0
        assert entry.arrival == 100
        assert entry.departure == 200

    def test_equality_by_id(self):
        pid = uuid7()
        p1 = Platform(id=pid, name="P1")
        p2 = Platform(id=pid, name="P2")
        assert p1 == p2

    def test_inequality_by_id(self):
        p1 = Platform(id=uuid7(), name="P1")
        p2 = Platform(id=uuid7(), name="P1")
        assert p1 != p2

    def test_hashable(self):
        pid = uuid7()
        p1 = Platform(id=pid, name="P1")
        p2 = Platform(id=pid, name="P2")
        assert {p1, p2} == {p1}


class TestStation:
    def test_create_station(self):
        p = Platform(id=uuid7(), name="P1")
        s = Station(id=uuid7(), name="S1", is_yard=False, platforms=[p])
        assert s.name == "S1"
        assert len(s.platforms) == 1

    def test_add_platform(self):
        s = Station(id=uuid7(), name="S1", is_yard=False, platforms=[])
        p = Platform(id=uuid7(), name="P1")
        s.add_platform(p)
        assert len(s.platforms) == 1
        assert s.platforms[0] == p

    def test_add_duplicate_platform_rejected(self):
        pid = uuid7()
        p = Platform(id=pid, name="P1")
        s = Station(id=uuid7(), name="S1", is_yard=False, platforms=[p])
        with pytest.raises(DomainError, match="already exists"):
            s.add_platform(Platform(id=pid, name="P1-dup"))

    def test_remove_platform(self):
        p1 = Platform(id=uuid7(), name="P1")
        p2 = Platform(id=uuid7(), name="P2")
        s = Station(id=uuid7(), name="S1", is_yard=False, platforms=[p1, p2])
        s.remove_platform(p1.id)
        assert len(s.platforms) == 1
        assert s.platforms[0] == p2

    def test_remove_nonexistent_platform_rejected(self):
        s = Station(id=uuid7(), name="S1", is_yard=False, platforms=[])
        with pytest.raises(DomainError, match="not found"):
            s.remove_platform(uuid7())

    def test_equality_by_id(self):
        sid = uuid7()
        s1 = Station(id=sid, name="A", is_yard=False, platforms=[])
        s2 = Station(id=sid, name="B", is_yard=True, platforms=[])
        assert s1 == s2

    def test_to_timetable_entry_yard(self):
        s = Station(id=uuid7(), name="Yard", is_yard=True, platforms=[])
        entry = s.to_timetable_entry(order=0, arrival=50, dwell_time=50)
        assert entry.node_id == s.id
        assert entry.arrival == 50
        assert entry.departure == 100

    def test_to_timetable_entry_non_yard_rejected(self):
        s = Station(id=uuid7(), name="S1", is_yard=False, platforms=[])
        with pytest.raises(DomainError, match="Only yards"):
            s.to_timetable_entry(order=0, arrival=0, dwell_time=10)

    def test_hashable(self):
        sid = uuid7()
        s1 = Station(id=sid, name="A", is_yard=False, platforms=[])
        s2 = Station(id=sid, name="B", is_yard=True, platforms=[])
        assert {s1, s2} == {s1}
