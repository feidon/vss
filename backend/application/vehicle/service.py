from __future__ import annotations

from domain.vehicle.model import Vehicle
from domain.vehicle.repository import VehicleRepository


class VehicleAppService:
    def __init__(self, vehicle_repo: VehicleRepository) -> None:
        self._repo = vehicle_repo

    async def list_vehicles(self) -> list[Vehicle]:
        return await self._repo.find_all()
