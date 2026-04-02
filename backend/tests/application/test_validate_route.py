from uuid import uuid7

import pytest

from application.service.dto import RouteStop
from application.service.service import ServiceAppService
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.connection_repo import InMemoryConnectionRepository
from infra.memory.service_repo import InMemoryServiceRepository
from infra.memory.station_repo import InMemoryStationRepository
from infra.memory.vehicle_repo import InMemoryVehicleRepository
from domain.vehicle.model import Vehicle
from infra.seed import (
    PLATFORM_ID_BY_NAME,
    VEHICLE_ID_BY_NAME,
    YARD_ID,
    create_blocks,
    create_connections,
    create_stations,
    create_vehicles,
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

    for v in create_vehicles():
        vehicle_repo._store[v.id] = v

    return ServiceAppService(
        service_repo=service_repo,
        block_repo=block_repo,
        connection_repo=connection_repo,
        vehicle_repo=vehicle_repo,
        station_repo=station_repo,
    ), vehicle_repo


class TestValidateRoute:
    async def test_valid_two_stop_route(self):
        app, _ = _make_app()

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=90),
        ]
        result = await app.validate_route(
            VEHICLE_ID_BY_NAME["V1"], stops, start_time=1000,
        )

        # Path: P1A -> B3 -> B5 -> P2A
        assert len(result.path) == 4
        assert result.path[0].id == PLATFORM_ID_BY_NAME["P1A"]
        assert result.path[3].id == PLATFORM_ID_BY_NAME["P2A"]
        assert result.battery_conflicts == []

    async def test_yard_as_stop(self):
        app, _ = _make_app()

        stops = [
            RouteStop(node_id=YARD_ID, dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
        ]
        result = await app.validate_route(
            VEHICLE_ID_BY_NAME["V1"], stops, start_time=0,
        )

        assert result.path[0].id == YARD_ID
        assert len(result.path) >= 2

    async def test_unreachable_route_raises(self):
        app, _ = _make_app()

        # P2A -> P1A has no route (wrong direction)
        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
        ]
        with pytest.raises(ValueError, match="No route"):
            await app.validate_route(
                VEHICLE_ID_BY_NAME["V1"], stops, start_time=0,
            )

    async def test_low_battery_detected(self):
        app, vehicle_repo = _make_app()

        # Replace V1 with a low-battery vehicle
        vid = VEHICLE_ID_BY_NAME["V1"]
        vehicle_repo._store[vid] = Vehicle(id=vid, name="V1", battery=30)

        # P1A -> P2A -> P3A uses 4 blocks, battery starts at 30 which is already critical threshold
        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P3A"], dwell_time=0),
        ]
        result = await app.validate_route(vid, stops, start_time=0)

        assert len(result.battery_conflicts) > 0

    async def test_unknown_stop_rejected(self):
        app, _ = _make_app()

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=uuid7(), dwell_time=60),
        ]
        with pytest.raises(ValueError, match="Stop.*not found"):
            await app.validate_route(
                VEHICLE_ID_BY_NAME["V1"], stops, start_time=0,
            )

    async def test_vehicle_not_found_rejected(self):
        app, _ = _make_app()

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=60),
        ]
        with pytest.raises(ValueError, match="Vehicle.*not found"):
            await app.validate_route(uuid7(), stops, start_time=0)
