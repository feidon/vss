from __future__ import annotations

from uuid import UUID, uuid7

from domain.network.model import Node
from domain.service.model import Service, TimetableEntry
from domain.service.repository import ServiceRepository


class ServiceApplicationService:
    def __init__(self, service_repo: ServiceRepository) -> None:
        self._service_repo = service_repo

    async def create_service(self, name: str, vehicle_id: UUID) -> Service:
        if not name or not name.strip():
            raise ValueError("Service name must not be empty")
        service = Service(
            id=uuid7(),
            name=name,
            vehicle_id=vehicle_id,
            path=[],
            timetable=[],
        )
        await self._service_repo.save(service)
        return service

    async def get_service(self, id: UUID) -> Service:
        service = await self._service_repo.find_by_id(id)
        if service is None:
            raise ValueError(f"Service {id} not found")
        return service

    async def list_services(self) -> list[Service]:
        return await self._service_repo.find_all()

    async def update_service_path(self, id: UUID, path: list[Node]) -> Service:
        service = await self.get_service(id)
        service.update_path(path)
        await self._service_repo.save(service)
        return service

    async def update_service_timetable(
        self, id: UUID, timetable: list[TimetableEntry]
    ) -> Service:
        service = await self.get_service(id)
        service.update_timetable(timetable)
        await self._service_repo.save(service)
        return service

    async def delete_service(self, id: UUID) -> None:
        await self._service_repo.delete(id)