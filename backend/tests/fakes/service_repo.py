from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from domain.service.model import Service
from domain.service.repository import ServiceRepository


class InMemoryServiceRepository(ServiceRepository):
    def __init__(self) -> None:
        self._store: dict[int, Service] = {}
        self._counter: int = 0

    async def find_all(self) -> list[Service]:
        return list(self._store.values())

    async def find_by_id(self, id: int) -> Service | None:
        return self._store.get(id)

    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]:
        return [s for s in self._store.values() if s.vehicle_id == vehicle_id]

    async def create(self, service: Service) -> Service:
        self._counter += 1
        created = replace(service, id=self._counter)
        self._store[created.id] = created
        return created

    async def update(self, service: Service) -> None:
        self._store[service.id] = service

    async def delete(self, id: int) -> None:
        self._store.pop(id, None)
