from __future__ import annotations

from uuid import UUID

from domain.service.model import Service
from domain.service.repository import ServiceRepository


class InMemoryServiceRepository(ServiceRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Service] = {}

    async def find_all(self) -> list[Service]:
        return list(self._store.values())

    async def find_by_id(self, id: UUID) -> Service | None:
        return self._store.get(id)

    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]:
        return [s for s in self._store.values() if s.vehicle_id == vehicle_id]

    async def save(self, service: Service) -> None:
        self._store[service.id] = service

    async def delete(self, id: UUID) -> None:
        self._store.pop(id, None)
