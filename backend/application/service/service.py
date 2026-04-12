from __future__ import annotations

from uuid import UUID

from domain.block.repository import BlockRepository
from domain.domain_service.conflict import detect_conflicts
from domain.domain_service.route_builder import build_full_route
from domain.error import DomainError, ErrorCode
from domain.network.repository import ConnectionRepository
from domain.service.model import Service
from domain.service.repository import ServiceRepository
from domain.shared.types import EpochSeconds
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository

from application.service.dto import RouteStop
from application.service.errors import ConflictError


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
            raise DomainError(
                ErrorCode.EMPTY_SERVICE_NAME, "Service name must not be empty"
            )

        vehicle = await self._vehicle_repo.find_by_id(vehicle_id)
        if vehicle is None:
            raise DomainError(
                ErrorCode.VEHICLE_NOT_FOUND,
                f"Vehicle {vehicle_id} not found",
                {"vehicle_id": str(vehicle_id)},
            )

        service = Service(
            name=name,
            vehicle_id=vehicle_id,
            route=[],
            timetable=[],
        )

        return await self._service_repo.create(service)

    async def get_service(self, id: int) -> Service:
        service = await self._service_repo.find_by_id(id)

        if service is None:
            raise DomainError(
                ErrorCode.SERVICE_NOT_FOUND,
                f"Service {id} not found",
                {"service_id": id},
            )

        return service

    async def list_services(self) -> list[Service]:
        return await self._service_repo.find_all()

    async def update_service_route(
        self, id: int, stops: list[RouteStop], start_time: EpochSeconds
    ) -> Service:
        service = await self.get_service(id)
        connections = await self._connection_repo.find_all()
        all_stations = await self._station_repo.find_all()
        all_blocks = await self._block_repo.find_all()

        stop_ids = [s.node_id for s in stops]
        dwell_by_stop = {s.node_id: s.dwell_time for s in stops}
        full_route, timetable = build_full_route(
            stop_ids, dwell_by_stop, start_time, connections, all_stations, all_blocks
        )
        service.update_route(full_route, timetable, connections)

        all_services = await self._service_repo.find_all()
        all_vehicles = await self._vehicle_repo.find_all()
        conflicts = detect_conflicts(
            service,
            all_services,
            all_blocks,
            all_vehicles,
        )

        if conflicts.has_conflicts:
            service_names = {s.id: s.name for s in all_services if s.id is not None}
            raise ConflictError(conflicts, service_names)

        await self._service_repo.update(service)
        return service

    async def delete_service(self, id: int) -> None:
        await self._service_repo.delete(id)
