import pytest
from application.schedule.dto import GenerateScheduleRequest
from application.schedule.schedule_service import ScheduleAppService
from domain.error import DomainError
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


def _make_app():
    block_repo = InMemoryBlockRepository()
    for b in create_blocks():
        block_repo._store[b.id] = b

    station_repo = InMemoryStationRepository()
    for s in create_stations():
        station_repo._store[s.id] = s

    connection_repo = InMemoryConnectionRepository(create_connections())

    vehicle_repo = InMemoryVehicleRepository()
    for v in create_vehicles():
        vehicle_repo._store[v.id] = v

    service_repo = InMemoryServiceRepository()

    return ScheduleAppService(
        service_repo=service_repo,
        block_repo=block_repo,
        connection_repo=connection_repo,
        vehicle_repo=vehicle_repo,
        station_repo=station_repo,
    ), service_repo


class TestScheduleAppService:
    async def test_generates_services(self):
        app, service_repo = _make_app()
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
        app, service_repo = _make_app()
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
        app, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=0,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        with pytest.raises(DomainError, match="interval"):
            await app.generate_schedule(req)

    async def test_rejects_invalid_time_range(self):
        app, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=3600,
            end_time=0,
            dwell_time_seconds=30,
        )
        with pytest.raises(DomainError, match="end_time"):
            await app.generate_schedule(req)

    async def test_vehicles_used_in_response(self):
        app, _ = _make_app()
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
        app, service_repo = _make_app()
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
        app, service_repo = _make_app()
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

    async def test_station_frequency_within_interval(self):
        app, service_repo = _make_app()
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

        platform_to_station = {p.id: s.name for s in stations for p in s.platforms}

        arrivals_by_station: dict[str, list[int]] = {"S1": [], "S2": [], "S3": []}
        for svc in services:
            for entry in svc.timetable:
                sname = platform_to_station.get(entry.node_id)
                if sname:
                    arrivals_by_station[sname].append(entry.arrival)

        for sname, times in arrivals_by_station.items():
            times.sort()
            for i in range(len(times) - 1):
                gap = times[i + 1] - times[i]
                assert gap <= interval, (
                    f"Station {sname}: gap {gap}s between arrivals "
                    f"at t={times[i]} and t={times[i + 1]} exceeds interval {interval}s"
                )

    async def test_vehicle_yard_dwell_sufficient_for_recharge(self):
        app, service_repo = _make_app()
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
                min_dwell = num_blocks * 12
                assert yard_dwell >= min_dwell, (
                    f"Yard dwell {yard_dwell}s < min {min_dwell}s for {num_blocks} blocks"
                )


def _make_app_with_vehicles(num_vehicles: int):
    """Build ScheduleAppService seeding exactly `num_vehicles` vehicles."""
    block_repo = InMemoryBlockRepository()
    for b in create_blocks():
        block_repo._store[b.id] = b

    station_repo = InMemoryStationRepository()
    for s in create_stations():
        station_repo._store[s.id] = s

    connection_repo = InMemoryConnectionRepository(create_connections())

    vehicle_repo = InMemoryVehicleRepository()
    for v in create_vehicles()[:num_vehicles]:
        vehicle_repo._store[v.id] = v

    service_repo = InMemoryServiceRepository()

    app = ScheduleAppService(
        service_repo=service_repo,
        block_repo=block_repo,
        connection_repo=connection_repo,
        vehicle_repo=vehicle_repo,
        station_repo=station_repo,
    )
    return app, service_repo, vehicle_repo


class TestScheduleAutoGeneratesVehicles:
    """Tests for vehicle auto-generation when insufficient vehicles exist."""

    async def test_generates_vehicles_when_none_exist(self):
        app, service_repo, vehicle_repo = _make_app_with_vehicles(0)
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
        app, service_repo, vehicle_repo = _make_app_with_vehicles(1)
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
        app, service_repo, vehicle_repo = _make_app_with_vehicles(3)
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
