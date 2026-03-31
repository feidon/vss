from __future__ import annotations

from uuid import UUID

from domain.vehicle.model import Vehicle
from domain.vehicle.repository import VehicleRepository


class InMemoryVehicleRepository(VehicleRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Vehicle] = {}

    async def find_all(self) -> list[Vehicle]:
        return list(self._store.values())

    async def find_by_id(self, id: UUID) -> Vehicle | None:
        return self._store.get(id)

    async def save(self, vehicle: Vehicle) -> None:
        self._store[vehicle.id] = vehicle
