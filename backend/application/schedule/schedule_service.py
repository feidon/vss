from __future__ import annotations

import logging
import math
from collections import defaultdict

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

logger = logging.getLogger(__name__)


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

        # 4. Check feasibility — the minimum departure gap is set by the
        #    widest interlocking group occupancy window in a single trip.
        effective_interval = req.interval_seconds + req.dwell_time_seconds
        min_departure_gap = _compute_min_departure_gap(variants, blocks)
        if effective_interval < min_departure_gap:
            min_passenger_wait = min_departure_gap - req.dwell_time_seconds
            raise DomainError(
                ErrorCode.INTERVAL_BELOW_MINIMUM,
                f"Requested interval {req.interval_seconds}s is not achievable. "
                f"Minimum passenger wait is {min_passenger_wait}s "
                f"due to interlocking constraints.",
                context={
                    "requested_interval": req.interval_seconds,
                    "minimum_interval": min_passenger_wait,
                    "dwell_time": req.dwell_time_seconds,
                    "min_departure_gap": min_departure_gap,
                },
            )

        # 5. Compute num_vehicles
        cycle_times = [v.cycle_time for v in variants]
        min_yard_dwells = [v.num_blocks * 12 for v in variants]
        max_turnaround = max(c + y for c, y in zip(cycle_times, min_yard_dwells))
        num_vehicles = math.ceil(max_turnaround / effective_interval) + 1

        if num_vehicles > len(vehicles):
            await self._vehicle_repo.add_by_number(num_vehicles - len(vehicles))
            vehicles = await self._vehicle_repo.find_all()

        used_vehicles = vehicles[:num_vehicles]

        # 6. Build interlocking groups
        interlocking_groups: dict[int, list] = {}
        for b in blocks:
            if b.group != 0:
                interlocking_groups.setdefault(b.group, []).append(b.id)

        # 7. Solve
        solver_input = SolverInput(
            variants=variants,
            num_vehicles=num_vehicles,
            vehicle_ids=[v.id for v in used_vehicles],
            start_time=req.start_time,
            end_time=req.end_time,
            departure_gap_seconds=effective_interval,
            interlocking_groups=interlocking_groups,
        )

        result = solve_schedule(solver_input)

        if not result.assignments:
            raise DomainError(
                ErrorCode.SCHEDULE_INFEASIBLE,
                "Could not place any trips in the given time window.",
            )

        # 8. Delete all existing services
        await self._service_repo.delete_all()

        # 9. Create services from solver output
        yard = next(s for s in stations if s.is_yard)
        services: list[Service] = []
        trip_counter: dict[int, int] = defaultdict(int)
        for assignment in result.assignments:
            variant = variants[assignment.variant_index]
            vehicle = used_vehicles[assignment.vehicle_index]

            dwell_by_stop = {sid: req.dwell_time_seconds for sid in variant.stop_ids}
            dwell_by_stop[yard.id] = 0

            route, timetable = build_full_route(
                variant.stop_ids,
                dwell_by_stop,
                assignment.depart_time,
                connections,
                stations,
                blocks,
            )

            trip_counter[assignment.vehicle_index] += 1
            service = Service(
                name=f"Auto-V{assignment.vehicle_index + 1}-T{trip_counter[assignment.vehicle_index]}",
                vehicle_id=vehicle.id,
                route=route,
                timetable=timetable,
            )
            created = await self._service_repo.create(service)
            services.append(created)

        # 10. Sanity check — conflicts in generated schedule indicate a solver bug
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

        # 11. Station frequency assertion
        platform_to_station = {p.id: s.name for s in stations for p in s.platforms}
        arrivals_by_station: dict[str, list[int]] = defaultdict(list)
        for svc in services:
            for entry in svc.timetable:
                sname = platform_to_station.get(entry.node_id)
                if sname:
                    arrivals_by_station[sname].append(entry.arrival)
        for sname, times in arrivals_by_station.items():
            times.sort()
            for i in range(len(times) - 1):
                gap = times[i + 1] - times[i]
                if gap > effective_interval:
                    logger.warning(
                        "Station %s: gap %ds > effective interval %ds (at t=%d)",
                        sname,
                        gap,
                        effective_interval,
                        times[i],
                    )

        # 12. Return response
        return GenerateScheduleResponse(
            services_created=len(services),
            vehicles_used=[v.id for v in used_vehicles],
            cycle_time_seconds=max(cycle_times),
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


def _compute_min_departure_gap(variants, blocks) -> int:
    """Minimum seconds between consecutive departures.

    For each pair of variants, compute the set of gap values that would
    cause an interlocking conflict (forbidden intervals).  The minimum
    feasible gap is the smallest positive integer outside all forbidden
    intervals.  Return the best (smallest) across all variant pairs.
    """
    block_group = {b.id: b.group for b in blocks}

    def _group_intervals(variant):
        gi: dict[int, list[tuple[int, int]]] = {}
        for bt in variant.block_timings:
            g = block_group.get(bt.block_id, 0)
            if g != 0:
                gi.setdefault(g, []).append((bt.enter_offset, bt.exit_offset))
        return gi

    all_gi = [_group_intervals(v) for v in variants]
    all_groups: set[int] = set()
    for gi in all_gi:
        all_groups.update(gi.keys())

    if not all_groups:
        return 0

    best_gap: int | None = None
    for gi1 in all_gi:
        for gi2 in all_gi:
            forbidden: list[tuple[int, int]] = []
            for g_id in all_groups:
                for a, b in gi1.get(g_id, []):
                    for c, d in gi2.get(g_id, []):
                        lo = a - d + 1
                        hi = b - c - 1
                        if lo <= hi:
                            forbidden.append((lo, hi))

            pair_min = _min_positive_outside(forbidden)
            if best_gap is None or pair_min < best_gap:
                best_gap = pair_min

    return best_gap if best_gap is not None else 0


def _min_positive_outside(intervals: list[tuple[int, int]]) -> int:
    """Smallest positive integer not covered by any interval."""
    pos = [(max(lo, 1), hi) for lo, hi in intervals if hi >= 1]
    if not pos:
        return 1
    pos.sort()
    merged = [list(pos[0])]
    for lo, hi in pos[1:]:
        if lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    if merged[0][0] > 1:
        return 1
    return merged[0][1] + 1
