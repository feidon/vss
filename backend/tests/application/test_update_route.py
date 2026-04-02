from uuid import uuid7

import pytest

from application.service.errors import ConflictError
from application.service.dto import RouteStop
from application.service.service import ServiceAppService
from domain.network.model import NodeType
from domain.vehicle.model import Vehicle
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.connection_repo import InMemoryConnectionRepository
from infra.memory.service_repo import InMemoryServiceRepository
from infra.memory.station_repo import InMemoryStationRepository
from infra.memory.vehicle_repo import InMemoryVehicleRepository
from infra.seed import (
    BLOCK_ID_BY_NAME,
    PLATFORM_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
)


def _make_app():
    block_repo = InMemoryBlockRepository()
    for b in create_blocks():
        block_repo._store[b.id] = b

    station_repo = InMemoryStationRepository()
    for s in create_stations():
        station_repo._store[s.id] = s

    connection_repo = InMemoryConnectionRepository(create_connections())
    vehicle_repo = InMemoryVehicleRepository()
    service_repo = InMemoryServiceRepository()

    return ServiceAppService(
        service_repo=service_repo,
        block_repo=block_repo,
        connection_repo=connection_repo,
        vehicle_repo=vehicle_repo,
        station_repo=station_repo,
    ), vehicle_repo


def seed_vehicle(vehicle_repo, vid=None, battery=100):
    v = Vehicle(id=vid or uuid7(), name="V1", battery=battery)
    vehicle_repo._store[v.id] = v
    return v


class TestUpdateServiceRoute:
    async def test_two_stop_route(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)
        svc = await app.create_service(name="S1", vehicle_id=v.id)

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=90),
        ]
        result = await app.update_service_route(svc.id, stops, start_time=1000)

        # Path: P1A -> B3 -> B5 -> P2A
        assert len(result.path) == 4
        assert result.path[0].id == PLATFORM_ID_BY_NAME["P1A"]
        assert result.path[1].id == BLOCK_ID_BY_NAME["B3"]
        assert result.path[2].id == BLOCK_ID_BY_NAME["B5"]
        assert result.path[3].id == PLATFORM_ID_BY_NAME["P2A"]

        # Timetable: P1A dwell=60, B3 traverse=30, B5 traverse=30, P2A dwell=90
        tt = result.timetable
        assert len(tt) == 4
        assert tt[0].arrival == 1000 and tt[0].departure == 1060  # P1A
        assert tt[1].arrival == 1060 and tt[1].departure == 1090  # B3
        assert tt[2].arrival == 1090 and tt[2].departure == 1120  # B5
        assert tt[3].arrival == 1120 and tt[3].departure == 1210  # P2A

    async def test_three_stop_route(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)
        svc = await app.create_service(name="S1", vehicle_id=v.id)

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=30),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P3A"], dwell_time=60),
        ]
        result = await app.update_service_route(svc.id, stops, start_time=0)

        # Path: P1A, B3, B5, P2A, B6, B7, P3A
        assert len(result.path) == 7
        assert [n.id for n in result.path] == [
            PLATFORM_ID_BY_NAME["P1A"], BLOCK_ID_BY_NAME["B3"], BLOCK_ID_BY_NAME["B5"],
            PLATFORM_ID_BY_NAME["P2A"], BLOCK_ID_BY_NAME["B6"], BLOCK_ID_BY_NAME["B7"],
            PLATFORM_ID_BY_NAME["P3A"],
        ]

        # Verify all block nodes
        block_nodes = [n for n in result.path if n.type == NodeType.BLOCK]
        assert len(block_nodes) == 4

    async def test_unknown_platform_rejected(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)
        svc = await app.create_service(name="S1", vehicle_id=v.id)

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=uuid7(), dwell_time=60),
        ]
        with pytest.raises(ValueError, match="Stop.*not found"):
            await app.update_service_route(svc.id, stops, start_time=0)

    async def test_service_not_found(self):
        app, _ = _make_app()
        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=60),
        ]
        with pytest.raises(ValueError, match="not found"):
            await app.update_service_route(999, stops, start_time=0)

    async def test_single_stop_rejected(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)
        svc = await app.create_service(name="S1", vehicle_id=v.id)

        stops = [RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60)]
        with pytest.raises(ValueError, match="At least two stops"):
            await app.update_service_route(svc.id, stops, start_time=0)

    async def test_no_route_between_platforms_rejected(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)
        svc = await app.create_service(name="S1", vehicle_id=v.id)

        # P2A -> P1A has no route (wrong direction)
        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
        ]
        with pytest.raises(ValueError, match="No route"):
            await app.update_service_route(svc.id, stops, start_time=0)

    async def test_route_update_replaces_previous(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)
        svc = await app.create_service(name="S1", vehicle_id=v.id)

        # First route
        stops1 = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=60),
        ]
        await app.update_service_route(svc.id, stops1, start_time=0)

        # Second route replaces first
        stops2 = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=30),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P3B"], dwell_time=30),
        ]
        result = await app.update_service_route(svc.id, stops2, start_time=500)
        assert result.path[0].id == PLATFORM_ID_BY_NAME["P2A"]
        assert result.timetable[0].arrival == 500


class TestRouteConflicts:
    async def test_vehicle_conflict(self):
        app, vehicle_repo = _make_app()
        vid = uuid7()
        seed_vehicle(vehicle_repo, vid)

        s1 = await app.create_service(name="S1", vehicle_id=vid)
        s2 = await app.create_service(name="S2", vehicle_id=vid)

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=60),
        ]
        await app.update_service_route(s1.id, stops, start_time=0)

        # Overlapping time with same vehicle
        with pytest.raises(ConflictError) as exc_info:
            await app.update_service_route(s2.id, stops, start_time=10)
        assert exc_info.value.conflicts.has_conflicts

    async def test_block_conflict(self):
        app, vehicle_repo = _make_app()
        v1 = seed_vehicle(vehicle_repo)
        v2 = seed_vehicle(vehicle_repo)

        s1 = await app.create_service(name="S1", vehicle_id=v1.id)
        s2 = await app.create_service(name="S2", vehicle_id=v2.id)

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
        ]
        await app.update_service_route(s1.id, stops, start_time=0)

        # Same route, overlapping block times, different vehicles
        with pytest.raises(ConflictError) as exc_info:
            await app.update_service_route(s2.id, stops, start_time=10)
        assert len(exc_info.value.conflicts.block_conflicts) > 0

    async def test_interlocking_conflict(self):
        app, vehicle_repo = _make_app()
        v1 = seed_vehicle(vehicle_repo)
        v2 = seed_vehicle(vehicle_repo)

        s1 = await app.create_service(name="S1", vehicle_id=v1.id)
        s2 = await app.create_service(name="S2", vehicle_id=v2.id)

        # S1: P1A -> P2A (uses B3 in group 2)
        stops1 = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
        ]
        await app.update_service_route(s1.id, stops1, start_time=0)

        # S2: P1B -> P2A (uses B4 in group 2, interlocks with B3)
        stops2 = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1B"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
        ]
        with pytest.raises(ConflictError) as exc_info:
            await app.update_service_route(s2.id, stops2, start_time=0)
        assert len(exc_info.value.conflicts.interlocking_conflicts) > 0

    async def test_block_conflict_checks_all_existing_services(self):
        """S3 should detect block conflicts against both S1 and S2 (different vehicles)."""
        app, vehicle_repo = _make_app()
        v1 = seed_vehicle(vehicle_repo)
        v2 = seed_vehicle(vehicle_repo)
        v3 = seed_vehicle(vehicle_repo)

        s1 = await app.create_service(name="S1", vehicle_id=v1.id)
        s2 = await app.create_service(name="S2", vehicle_id=v2.id)
        s3 = await app.create_service(name="S3", vehicle_id=v3.id)

        # S1: P1A -> P2A at time 0 (B3: 0-30, B5: 30-60)
        stops_s1 = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
        ]
        await app.update_service_route(s1.id, stops_s1, start_time=0)

        # S2: P2A -> P3A at time 60 (B6: 60-90, B7: 90-120)
        # B5 (group 0) ends at 60, B6 (group 0) starts at 60 → no interlocking overlap
        stops_s2 = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P3A"], dwell_time=0),
        ]
        await app.update_service_route(s2.id, stops_s2, start_time=60)

        # S3: P1A -> P2A -> P3A at time 0
        # B3: 0-30, B5: 30-60, B6: 60-90, B7: 90-120
        # Overlaps S1 on B3 and B5, overlaps S2 on B6 and B7
        stops_s3 = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P3A"], dwell_time=0),
        ]
        with pytest.raises(ConflictError) as exc_info:
            await app.update_service_route(s3.id, stops_s3, start_time=0)

        conflicts = exc_info.value.conflicts.block_conflicts
        conflicting_service_ids = {c.service_a_id for c in conflicts} | {c.service_b_id for c in conflicts}
        assert s1.id in conflicting_service_ids, "Should detect conflict with S1"
        assert s2.id in conflicting_service_ids, "Should detect conflict with S2"


