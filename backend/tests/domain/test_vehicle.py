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


class TestVehicleCharge:
    def test_partial_charge(self):
        v = Vehicle(id=uuid7(), name="V1", battery=50)
        v.charge(120)  # 120s // 12 = 10%
        assert v.battery == 60

    def test_charge_caps_at_100(self):
        v = Vehicle(id=uuid7(), name="V1", battery=95)
        v.charge(600)  # 600s // 12 = 50%, but capped
        assert v.battery == 100

    def test_zero_idle_no_charge(self):
        v = Vehicle(id=uuid7(), name="V1", battery=70)
        v.charge(0)
        assert v.battery == 70

    def test_short_idle_truncates(self):
        v = Vehicle(id=uuid7(), name="V1", battery=70)
        v.charge(11)  # 11 // 12 = 0
        assert v.battery == 70


class TestVehicleCanDepart:
    def test_above_threshold(self):
        v = Vehicle(id=uuid7(), name="V1", battery=90)
        assert v.can_depart() is True

    def test_at_threshold(self):
        v = Vehicle(id=uuid7(), name="V1", battery=80)
        assert v.can_depart() is True

    def test_below_threshold(self):
        v = Vehicle(id=uuid7(), name="V1", battery=79)
        assert v.can_depart() is False


class TestVehicleTraverseBlock:
    def test_traversal_costs_one_percent(self):
        v = Vehicle(id=uuid7(), name="V1", battery=100)
        v.traverse_block()
        assert v.battery == 99

    def test_exactly_at_critical(self):
        v = Vehicle(id=uuid7(), name="V1", battery=31)
        v.traverse_block()  # 31 - 1 = 30, exactly at threshold
        assert v.battery == 30
        assert v.is_battery_critical() is False

    def test_below_critical(self):
        v = Vehicle(id=uuid7(), name="V1", battery=30)
        v.traverse_block()  # 30 - 1 = 29 < 30
        assert v.battery == 29
        assert v.is_battery_critical() is True
