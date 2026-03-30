from uuid import uuid7

from domain.vehicle.model import Vehicle


class TestVehicle:
    def test_create_vehicle(self):
        v = Vehicle(id=uuid7(), name="V1")
        assert v.name == "V1"

    def test_equality_by_id(self):
        vid = uuid7()
        v1 = Vehicle(id=vid, name="A")
        v2 = Vehicle(id=vid, name="B")
        assert v1 == v2

    def test_inequality_by_id(self):
        v1 = Vehicle(id=uuid7(), name="V1")
        v2 = Vehicle(id=uuid7(), name="V1")
        assert v1 != v2

    def test_hashable(self):
        vid = uuid7()
        v1 = Vehicle(id=vid, name="A")
        v2 = Vehicle(id=vid, name="B")
        assert {v1, v2} == {v1}
