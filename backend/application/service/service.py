from __future__ import annotations

from uuid import UUID

from application.service.dto import RouteStop
from application.service.errors import ConflictError
from domain.block.model import Block
from domain.block.repository import BlockRepository
from domain.network.model import Node, NodeType
from domain.domain_service.route_finder import RouteFinder
from domain.network.repository import ConnectionRepository
from domain.domain_service.conflict import detect_conflicts
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

        full_path, timetable = await self._build_route(stops, start_time)
        connections = await self._connection_repo.find_all()
        service.update_route(full_path, timetable, connections)

        all_services = await self._service_repo.find_all()
        all_blocks = await self._block_repo.find_all()
        all_vehicles = await self._vehicle_repo.find_all()
        conflicts = detect_conflicts(
            service, all_services, all_blocks, all_vehicles,
        )
        if conflicts.has_conflicts:
            raise ConflictError(conflicts)

        await self._service_repo.save(service)
        return service

    async def _build_route(
        self, stops: list[RouteStop], start_time: EpochSeconds
    ) -> tuple[list[Node], list[TimetableEntry]]:
        stations = await self._station_repo.find_all()
        all_platforms = {p.id: p for s in stations for p in s.platforms}
        yard_ids = {s.id for s in stations if s.is_yard}
        self._validate_stops_exist(stops, all_platforms, yard_ids)

        connections = await self._connection_repo.find_all()
        all_blocks = await self._block_repo.find_all()

        full_path = self._build_node_path(stops, connections, all_blocks, all_platforms, yard_ids)
        timetable = self._compute_timetable(
            full_path,
            {b.id: b for b in all_blocks},
            {s.node_id: s.dwell_time for s in stops},
            start_time,
        )

        return full_path, timetable

    async def delete_service(self, id: int) -> None:
        await self._service_repo.delete(id)

    @staticmethod
    def _validate_stops_exist(
        stops: list[RouteStop],
        all_platforms: dict[UUID, object],
        yard_ids: set[UUID],
    ) -> None:
        valid_ids = set(all_platforms.keys()) | yard_ids
        for stop in stops:
            if stop.node_id not in valid_ids:
                raise ValueError(f"Stop {stop.node_id} not found")

    @staticmethod
    def _build_node_path(
        stops: list[RouteStop],
        connections: frozenset,
        all_blocks: list[Block],
        all_platforms: dict[UUID, object],
        yard_ids: set[UUID],
    ) -> list[Node]:
        block_ids = {b.id for b in all_blocks}
        stop_ids = [s.node_id for s in stops]
        full_path_ids = RouteFinder.build_full_path(stop_ids, connections, block_ids)

        node_types: dict[UUID, NodeType] = {}
        for b in all_blocks:
            node_types[b.id] = NodeType.BLOCK
        for pid in all_platforms:
            node_types[pid] = NodeType.PLATFORM
        for yid in yard_ids:
            node_types[yid] = NodeType.YARD

        return [Node(id=nid, type=node_types[nid]) for nid in full_path_ids]

    @staticmethod
    def _compute_timetable(
        full_path: list[Node],
        blocks_by_id: dict[UUID, Block],
        dwell_by_stop: dict[UUID, int],
        start_time: EpochSeconds,
    ) -> list[TimetableEntry]:
        entries: list[TimetableEntry] = []
        current_time = start_time

        for order, node in enumerate(full_path):
            if node.type == NodeType.BLOCK:
                block = blocks_by_id[node.id]
                departure = current_time + block.traversal_time_seconds
            else:
                dwell = dwell_by_stop.get(node.id, 0)
                departure = current_time + dwell

            entries.append(TimetableEntry(
                order=order,
                node_id=node.id,
                arrival=current_time,
                departure=departure,
            ))
            current_time = departure

        return entries
