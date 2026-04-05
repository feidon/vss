from __future__ import annotations

from uuid import UUID, uuid7

from domain.vehicle.model import Vehicle
from domain.vehicle.repository import VehicleRepository


class InMemoryVehicleRepository(VehicleRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Vehicle] = {}

    async def find_all(self) -> list[Vehicle]:
        return list(self._store.values())

    async def find_by_id(self, id: UUID) -> Vehicle | None:
        return self._store.get(id)

    async def add_by_number(self, number: int) -> None:
        current_number = len(self._store.items())
        for i in range(number):
            new_vehicle = Vehicle(id=uuid7(), name=f"V{current_number + i}")
            self._store[new_vehicle.id] = new_vehicle

    async def save(self, vehicle: Vehicle) -> None:
        self._store[vehicle.id] = vehicle
