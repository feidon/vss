from __future__ import annotations

from uuid import UUID

from application.service.dto import RouteStop
from application.service.errors import ConflictError
from domain.block.repository import BlockRepository
from domain.network.model import Node, NodeType
from domain.network.pathfinder import RouteFinder
from domain.network.repository import ConnectionRepository
from domain.service.conflict import ConflictDetectionService
from domain.service.model import Service, TimetableEntry
from domain.shared.types import EpochSeconds
from domain.service.repository import ServiceRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository


class ServiceAppService:
    def __init__(
        self,
        service_repo: ServiceRepository,
        block_repo: BlockRepository,
        connection_repo: ConnectionRepository,
        vehicle_repo: VehicleRepository,
        station_repo: StationRepository,
    ) -> None:
        self._service_repo = service_repo
        self._block_repo = block_repo
        self._connection_repo = connection_repo
        self._vehicle_repo = vehicle_repo
        self._station_repo = station_repo

    async def create_service(self, name: str, vehicle_id: UUID) -> Service:
        if not name or not name.strip():
            raise ValueError("Service name must not be empty")
        
        vehicle = await self._vehicle_repo.find_by_id(vehicle_id)
        if vehicle is None:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        service = Service(
            name=name,
            vehicle_id=vehicle_id,
            path=[],
            timetable=[],
        )
        
        await self._service_repo.save(service)
        
        return service

    async def get_service(self, id: int) -> Service:
        service = await self._service_repo.find_by_id(id)
        
        if service is None:
            raise ValueError(f"Service {id} not found")
        
        return service

    async def list_services(self) -> list[Service]:
        return await self._service_repo.find_all()

    async def update_service_route(
        self, id: int, stops: list[RouteStop], start_time: EpochSeconds
    ) -> Service:
        service = await self.get_service(id)

        # Validate platforms exist
        stations = await self._station_repo.find_all()
        all_platforms = {p.id: p for s in stations for p in s.platforms}
        for stop in stops:
            if stop.platform_id not in all_platforms:
                raise ValueError(f"Platform {stop.platform_id} not found")

        # Build full path via pathfinding
        connections = await self._connection_repo.find_all()
        all_blocks = await self._block_repo.find_all()
        block_ids = {b.id for b in all_blocks}

        stop_ids = [s.platform_id for s in stops]
        full_path_ids = RouteFinder.build_full_path(stop_ids, connections, block_ids)

        # Map IDs to Nodes
        node_types: dict[UUID, NodeType] = {}
        for b in all_blocks:
            node_types[b.id] = NodeType.BLOCK
        for pid in all_platforms:
            node_types[pid] = NodeType.PLATFORM
        full_path = [Node(id=nid, type=node_types[nid]) for nid in full_path_ids]

        # Compute timetable
        blocks_by_id = {b.id: b for b in all_blocks}
        dwell_by_platform = {s.platform_id: s.dwell_time for s in stops}
        timetable = _compute_timetable(full_path, blocks_by_id, dwell_by_platform, start_time)

        # Atomic update
        service.update_route(full_path, timetable)
        service.validate_connectivity(connections)

        # Conflict detection
        all_services = await self._service_repo.find_all()
        conflicts = ConflictDetectionService.validate_service(service, all_services, all_blocks)
        if conflicts.has_conflicts:
            raise ConflictError(conflicts)

        await self._service_repo.save(service)
        return service

    async def delete_service(self, id: int) -> None:
        await self._service_repo.delete(id)


def _compute_timetable(
    full_path: list[Node],
    blocks_by_id: dict[UUID, object],
    dwell_by_platform: dict[UUID, int],
    start_time: EpochSeconds,
) -> list[TimetableEntry]:
    entries: list[TimetableEntry] = []
    current_time = start_time

    for order, node in enumerate(full_path):
        if node.type == NodeType.BLOCK:
            block = blocks_by_id[node.id]
            departure = current_time + block.traversal_time_seconds
        else:
            dwell = dwell_by_platform.get(node.id, 0)
            departure = current_time + dwell

        entries.append(TimetableEntry(
            order=order,
            node_id=node.id,
            arrival=current_time,
            departure=departure,
        ))
        current_time = departure

    return entries
