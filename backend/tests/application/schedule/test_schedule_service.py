import pytest
from application.schedule.dto import GenerateScheduleRequest
from application.schedule.network_layout import SECONDS_TO_RECHARGE_PER_BLOCK
from application.schedule.schedule_service import ScheduleAppService
from domain.error import DomainError, ErrorCode
from domain.network.model import NodeType
from infra.seed import (
    VEHICLE_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
    create_vehicles,
)

from tests.fakes.block_repo import InMemoryBlockRepository
from tests.fakes.connection_repo import InMemoryConnectionRepository
from tests.fakes.service_repo import InMemoryServiceRepository
from tests.fakes.station_repo import InMemoryStationRepository
from tests.fakes.vehicle_repo import InMemoryVehicleRepository


def _make_app(num_vehicles: int | None = None):
    """Build ScheduleAppService with in-memory repos.

    num_vehicles=None seeds all vehicles; an int seeds that many.
    """
    block_repo = InMemoryBlockRepository()
    for b in create_blocks():
        block_repo.seed(b)

    station_repo = InMemoryStationRepository()
    for s in create_stations():
        station_repo.seed(s)

    connection_repo = InMemoryConnectionRepository(create_connections())

    vehicle_repo = InMemoryVehicleRepository()
    seed = (
        create_vehicles() if num_vehicles is None else create_vehicles()[:num_vehicles]
    )
    for v in seed:
        vehicle_repo.seed(v)

    service_repo = InMemoryServiceRepository()

    app = ScheduleAppService(
        service_repo=service_repo,
        block_repo=block_repo,
        connection_repo=connection_repo,
        vehicle_repo=vehicle_repo,
        station_repo=station_repo,
    )
    return app, service_repo, vehicle_repo


class TestScheduleAppService:
    async def test_generates_services(self):
        app, service_repo, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        result = await app.generate_schedule(req)
        assert result.services_created > 0
        assert len(await service_repo.find_all()) == result.services_created

    async def test_clears_existing_services_first(self):
        app, service_repo, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        second = await app.generate_schedule(req)
        assert len(await service_repo.find_all()) == second.services_created

    async def test_rejects_invalid_interval(self):
        app, _, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=0,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        with pytest.raises(DomainError, match="interval"):
            await app.generate_schedule(req)

    async def test_rejects_interval_below_minimum(self):
        """With dwell=15, min departure gap is 75s, so min passenger wait is 60s.
        interval=59 should be rejected."""
        app, _, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=59,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=15,
        )
        with pytest.raises(DomainError, match="not achievable") as exc_info:
            await app.generate_schedule(req)
        assert exc_info.value.code == ErrorCode.INTERVAL_BELOW_MINIMUM
        assert exc_info.value.context["minimum_interval"] == 60

    async def test_accepts_exact_minimum_interval(self):
        """interval=60 with dwell=15 is exactly achievable (effective=75=min gap)."""
        app, service_repo, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=60,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=15,
        )
        result = await app.generate_schedule(req)
        assert result.services_created > 0

    async def test_rejects_invalid_time_range(self):
        app, _, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=3600,
            end_time=0,
            dwell_time_seconds=30,
        )
        with pytest.raises(DomainError, match="end_time"):
            await app.generate_schedule(req)

    async def test_vehicles_used_in_response(self):
        app, _, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        result = await app.generate_schedule(req)
        assert len(result.vehicles_used) > 0
        for vid in result.vehicles_used:
            assert vid in VEHICLE_ID_BY_NAME.values()

    async def test_service_names_follow_convention(self):
        app, service_repo, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()
        for svc in services:
            assert svc.name.startswith("Auto-V")

    async def test_no_conflicts_in_generated_schedule(self):
        app, service_repo, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()
        blocks = create_blocks()

        from domain.domain_service.conflict import detect_conflicts

        for svc in services:
            others = [s for s in services if s.id != svc.id]
            conflicts = detect_conflicts(svc, others, blocks)
            assert not conflicts.has_conflicts, f"Service {svc.name} has conflicts"

    async def test_passenger_wait_within_interval(self):
        """Worst case: passenger arrives at a station just as the last vehicle
        departs. The next vehicle arriving at *any* platform of that station
        must come within the requested interval."""
        app, service_repo, _ = _make_app()
        interval = 360
        req = GenerateScheduleRequest(
            interval_seconds=interval,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()
        stations = create_stations()

        platform_to_station = {
            p.id: s.name for s in stations if not s.is_yard for p in s.platforms
        }

        # Collect (arrival, departure) per station across all platforms
        visits_by_station: dict[str, list[tuple[int, int]]] = {}
        for svc in services:
            for entry in svc.timetable:
                sname = platform_to_station.get(entry.node_id)
                if sname:
                    visits_by_station.setdefault(sname, []).append(
                        (entry.arrival, entry.departure)
                    )

        for sname, visits in visits_by_station.items():
            visits.sort(key=lambda v: v[1])  # sort by departure
            for i in range(len(visits) - 1):
                wait = visits[i + 1][0] - visits[i][1]
                assert wait <= interval, (
                    f"Station {sname}: passenger wait {wait}s "
                    f"(depart t={visits[i][1]}, next arrive t={visits[i + 1][0]}) "
                    f"exceeds interval {interval}s"
                )

    async def test_vehicle_yard_dwell_sufficient_for_recharge(self):
        app, service_repo, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=7200,
            dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()

        by_vehicle: dict[str, list] = {}
        for svc in services:
            by_vehicle.setdefault(str(svc.vehicle_id), []).append(svc)
        for trips in by_vehicle.values():
            trips.sort(key=lambda s: s.timetable[0].arrival)
            for i in range(len(trips) - 1):
                prev_end = trips[i].timetable[-1].departure
                next_start = trips[i + 1].timetable[0].arrival
                yard_dwell = next_start - prev_end
                num_blocks = sum(1 for n in trips[i].route if n.type == NodeType.BLOCK)
                min_dwell = num_blocks * SECONDS_TO_RECHARGE_PER_BLOCK
                assert yard_dwell >= min_dwell, (
                    f"Yard dwell {yard_dwell}s < min {min_dwell}s for {num_blocks} blocks"
                )

    async def test_tiling_produces_multiple_trips_per_vehicle(self):
        """With a 2-hour window, each vehicle should serve multiple trips."""
        app, service_repo, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=7200,
            dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()

        by_vehicle: dict[str, list] = {}
        for svc in services:
            by_vehicle.setdefault(str(svc.vehicle_id), []).append(svc)

        for vid, trips in by_vehicle.items():
            assert len(trips) > 1, f"Vehicle {vid} has only {len(trips)} trip(s)"


class TestScheduleAutoGeneratesVehicles:
    """Tests for vehicle auto-generation when insufficient vehicles exist."""

    async def test_generates_vehicles_when_none_exist(self):
        app, service_repo, vehicle_repo = _make_app(0)
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        result = await app.generate_schedule(req)
        assert result.services_created > 0
        vehicles_after = await vehicle_repo.find_all()
        assert len(vehicles_after) == len(result.vehicles_used)

    async def test_generates_deficit_when_not_enough(self):
        app, service_repo, vehicle_repo = _make_app(1)
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        vehicles_before = await vehicle_repo.find_all()
        result = await app.generate_schedule(req)
        vehicles_after = await vehicle_repo.find_all()
        assert len(vehicles_after) > len(vehicles_before)
        assert len(vehicles_after) >= len(result.vehicles_used)

    async def test_no_new_vehicles_when_sufficient(self):
        app, service_repo, vehicle_repo = _make_app(3)
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        vehicles_before = await vehicle_repo.find_all()
        await app.generate_schedule(req)
        vehicles_after = await vehicle_repo.find_all()
        assert len(vehicles_after) == len(vehicles_before)
