from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.service.model import Service


class ServiceRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Service]: ...

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Service | None: ...

    @abstractmethod
    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]: ...

    @abstractmethod
    async def save(self, service: Service) -> None: ...

    @abstractmethod
    async def delete(self, id: UUID) -> None: ...
