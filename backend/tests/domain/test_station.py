from uuid import uuid7

import pytest

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

    def test_frozen(self):
        p = Platform(id=uuid7(), name="P1")
        with pytest.raises(AttributeError):
            p.name = "P2"


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
        with pytest.raises(ValueError, match="already exists"):
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
        with pytest.raises(ValueError, match="not found"):
            s.remove_platform(uuid7())

    def test_equality_by_id(self):
        sid = uuid7()
        s1 = Station(id=sid, name="A", is_yard=False, platforms=[])
        s2 = Station(id=sid, name="B", is_yard=True, platforms=[])
        assert s1 == s2

    def test_hashable(self):
        sid = uuid7()
        s1 = Station(id=sid, name="A", is_yard=False, platforms=[])
        s2 = Station(id=sid, name="B", is_yard=True, platforms=[])
        assert {s1, s2} == {s1}
