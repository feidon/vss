from __future__ import annotations

import math

from domain.block.repository import BlockRepository
from domain.domain_service.conflict.block import detect_block_conflicts
from domain.domain_service.conflict.interlocking import detect_interlocking_conflicts
from domain.domain_service.conflict.shared import (
    build_occupancies,
    build_vehicle_schedule,
)
from domain.domain_service.conflict.vehicle import detect_vehicle_conflicts
from domain.domain_service.route_builder import build_full_route
from domain.error import DomainError, ErrorCode
from domain.network.repository import ConnectionRepository
from domain.service.model import Service
from domain.service.repository import ServiceRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository

from application.schedule.dto import GenerateScheduleRequest, GenerateScheduleResponse
from application.schedule.model import SolverInput
from application.schedule.route_variant import compute_route_variants
from application.schedule.solver import solve_schedule


class ScheduleAppService:
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

    async def generate_schedule(
        self,
        req: GenerateScheduleRequest,
    ) -> GenerateScheduleResponse:
        # 1. Validate input
        self._validate_request(req)

        # 2. Load all data from repos
        blocks = await self._block_repo.find_all()
        stations = await self._station_repo.find_all()
        connections = await self._connection_repo.find_all()
        vehicles = await self._vehicle_repo.find_all()

        # 3. Compute route variants
        variants = compute_route_variants(
            stations, blocks, connections, req.dwell_time_seconds
        )

        # 4. Calculate num_vehicles needed
        max_cycle = max(v.cycle_time for v in variants)
        max_blocks = max(v.num_blocks for v in variants)
        worst_yard_dwell = max_blocks * 12
        effective_cycle = max_cycle + worst_yard_dwell
        num_vehicles = math.ceil(effective_cycle / req.interval_seconds) + 1

        if num_vehicles > len(vehicles):
            await self._vehicle_repo.add_by_number(num_vehicles - len(vehicles))
            vehicles = await self._vehicle_repo.find_all()

        used_vehicles = vehicles[:num_vehicles]
        trips_per_vehicle = max(
            (req.end_time - req.start_time) // (num_vehicles * req.interval_seconds), 1
        )

        # 5. Build interlocking groups
        interlocking_groups: dict[int, list] = {}
        for b in blocks:
            if b.group != 0:
                interlocking_groups.setdefault(b.group, []).append(b.id)

        # 6. Build SolverInput and call solve_schedule()
        solver_input = SolverInput(
            variants=variants,
            num_vehicles=num_vehicles,
            vehicle_ids=[v.id for v in used_vehicles],
            trips_per_vehicle=trips_per_vehicle,
            interval_seconds=req.interval_seconds,
            start_time=req.start_time,
            end_time=req.end_time,
            min_yard_dwells=[v.num_blocks * 12 for v in variants],
            cycle_times=[v.cycle_time for v in variants],
            interlocking_groups=interlocking_groups,
        )

        result = solve_schedule(solver_input)

        # 7. If infeasible
        if result is None:
            raise DomainError(
                ErrorCode.SCHEDULE_INFEASIBLE,
                "Schedule is infeasible: solver could not find a valid assignment",
            )

        # 8. Delete all existing services
        await self._service_repo.delete_all()

        # 9. For each trip assignment: build Service, persist
        services: list[Service] = []
        for assignment in result.assignments:
            variant = variants[assignment.variant_index]
            vehicle = used_vehicles[assignment.vehicle_index]

            dwell_by_stop = {sid: req.dwell_time_seconds for sid in variant.stop_ids}
            yard = next(s for s in stations if s.is_yard)
            dwell_by_stop[yard.id] = 0  # yard dwell handled by solver spacing

            route, timetable = build_full_route(
                variant.stop_ids,
                dwell_by_stop,
                assignment.depart_time,
                connections,
                stations,
                blocks,
            )

            service = Service(
                name=f"Auto-V{assignment.vehicle_index + 1}-T{assignment.trip_index + 1}",
                vehicle_id=vehicle.id,
                route=route,
                timetable=timetable,
            )
            created = await self._service_repo.create(service)
            services.append(created)

        # 10. Sanity check: run conflict detection on all generated services
        block_occ, group_occ = build_occupancies(services, blocks)
        block_conflicts = detect_block_conflicts(block_occ)
        interlocking_conflicts = detect_interlocking_conflicts(group_occ)

        vehicle_conflicts = []
        for v in used_vehicles:
            schedule = build_vehicle_schedule(v.id, services)
            vehicle_conflicts.extend(
                detect_vehicle_conflicts(v.id, schedule.windows, schedule.endpoints)
            )

        if block_conflicts or interlocking_conflicts or vehicle_conflicts:
            conflict_details = []
            if block_conflicts:
                conflict_details.append(f"{len(block_conflicts)} block conflicts")
            if interlocking_conflicts:
                conflict_details.append(
                    f"{len(interlocking_conflicts)} interlocking conflicts"
                )
            if vehicle_conflicts:
                conflict_details.append(f"{len(vehicle_conflicts)} vehicle conflicts")
            raise RuntimeError(
                f"BUG: Generated schedule has conflicts: {', '.join(conflict_details)}"
            )

        # 11. Return response
        return GenerateScheduleResponse(
            services_created=len(services),
            vehicles_used=[v.id for v in used_vehicles],
            cycle_time_seconds=max_cycle,
        )

    @staticmethod
    def _validate_request(req: GenerateScheduleRequest) -> None:
        if req.interval_seconds <= 0:
            raise DomainError(
                ErrorCode.INVALID_INTERVAL,
                "interval_seconds must be positive",
            )
        if req.dwell_time_seconds <= 0:
            raise DomainError(
                ErrorCode.INVALID_DWELL_TIME,
                "dwell_time_seconds must be positive",
            )
        if req.end_time <= req.start_time:
            raise DomainError(
                ErrorCode.INVALID_TIME_RANGE,
                "end_time must be greater than start_time",
            )
