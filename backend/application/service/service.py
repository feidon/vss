from __future__ import annotations

from uuid import UUID, uuid7

from application.service.errors import ConflictError
from domain.block.model import Block
from domain.block.repository import BlockRepository
from domain.network.model import Node, NodeType
from domain.network.repository import ConnectionRepository
from domain.service.conflict import ConflictDetectionService
from domain.service.model import Service, TimetableEntry
from domain.service.repository import ServiceRepository


class ServiceAppService:
    def __init__(
        self,
        service_repo: ServiceRepository,
        block_repo: BlockRepository,
        connection_repo: ConnectionRepository,
    ) -> None:
        self._service_repo = service_repo
        self._block_repo = block_repo
        self._connection_repo = connection_repo

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
        await self._validate_nodes_exist(path)
        service.update_path(path)
        connections = await self._connection_repo.find_all()
        if path:
            service.validate_connectivity(connections)
        await self._service_repo.save(service)
        return service

    async def update_service_timetable(
        self, id: UUID, timetable: list[TimetableEntry]
    ) -> Service:
        service = await self.get_service(id)
        service.update_timetable(timetable)

        all_services = await self._service_repo.find_all()
        services = [s for s in all_services if s.id != service.id] + [service]
        blocks = await self._block_repo.find_all()

        conflicts = ConflictDetectionService.validate_service(service, services, blocks)
        if conflicts.has_conflicts:
            raise ConflictError(conflicts)

        await self._service_repo.save(service)
        return service

    async def delete_service(self, id: UUID) -> None:
        await self._service_repo.delete(id)

    async def resolve_blocks(self, services: list[Service]) -> dict[UUID, Block]:
        """Batch-fetch all blocks referenced by the given services' paths."""
        block_ids = {
            n.id for s in services for n in s.path if n.type == NodeType.BLOCK
        }
        if not block_ids:
            return {}
        blocks = await self._block_repo.find_by_ids(block_ids)
        return {b.id: b for b in blocks}

    async def _validate_nodes_exist(self, path: list[Node]) -> None:
        """Validate that all nodes in the path exist in their respective repositories."""
        block_ids = {n.id for n in path if n.type == NodeType.BLOCK}
        if block_ids:
            found = await self._block_repo.find_by_ids(block_ids)
            found_ids = {b.id for b in found}
            missing = block_ids - found_ids
            if missing:
                raise ValueError(f"Block {next(iter(missing))} not found")
