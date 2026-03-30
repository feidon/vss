from abc import ABC, abstractmethod
from uuid import UUID

from backend.domain.service.model import Service
from backend.domain.service.repository import ServiceRepository


class InMemoryServiceRepositoryImpl(ServiceRepository):
    def __init__(self, services: list[Service]):
        self._services = {s.id: s for s in services}
        
    async def find_all(self) -> list[Service]:
        return list(self._services.values())

    async def find_by_id(self, id: UUID) -> Service | None:
        return self._services.get(id)

    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]:
        return [s for s in self._services.values() if s.vehicle_id == vehicle_id]

    async def save(self, service: Service) -> None:
        self._services[service.id] = service

    async def delete(self, id: UUID) -> None:
        self._services.pop(id, None)