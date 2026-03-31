from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.vehicle.model import Vehicle


class VehicleRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Vehicle]: ...

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Vehicle | None: ...
