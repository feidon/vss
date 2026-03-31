from uuid import uuid7

import pytest
from fastapi.testclient import TestClient

from api.dependencies import (
    get_block_repo,
    get_connection_repo,
    get_service_repo,
    get_station_repo,
    get_vehicle_repo,
)
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
from main import app


@pytest.fixture
def service_repo():
    return InMemoryServiceRepository()


@pytest.fixture
def block_repo():
    repo = InMemoryBlockRepository()
    for b in create_blocks():
        repo._store[b.id] = b
    return repo


@pytest.fixture
def station_repo():
    repo = InMemoryStationRepository()
    for s in create_stations():
        repo._store[s.id] = s
    return repo


@pytest.fixture
def connection_repo():
    return InMemoryConnectionRepository(create_connections())


@pytest.fixture
def vehicle_repo():
    return InMemoryVehicleRepository()


@pytest.fixture
def client(service_repo, block_repo, station_repo, connection_repo, vehicle_repo):
    app.dependency_overrides[get_service_repo] = lambda: service_repo
    app.dependency_overrides[get_block_repo] = lambda: block_repo
    app.dependency_overrides[get_station_repo] = lambda: station_repo
    app.dependency_overrides[get_connection_repo] = lambda: connection_repo
    app.dependency_overrides[get_vehicle_repo] = lambda: vehicle_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def seed_vehicle(vehicle_repo, vid=None):
    v = Vehicle(id=vid or uuid7(), name="V1")
    vehicle_repo._store[v.id] = v
    return v


def create_service(client, vehicle_repo):
    v = seed_vehicle(vehicle_repo)
    resp = client.post("/services", json={"name": "S1", "vehicle_id": str(v.id)})
    assert resp.status_code == 201
    return resp.json()["id"], v


class TestServiceCRUD:
    def test_create_service(self, client, vehicle_repo):
        v = seed_vehicle(vehicle_repo)
        resp = client.post("/services", json={"name": "Express", "vehicle_id": str(v.id)})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert set(data.keys()) == {"id"}

    def test_create_service_empty_name_rejected(self, client, vehicle_repo):
        v = seed_vehicle(vehicle_repo)
        resp = client.post("/services", json={"name": "", "vehicle_id": str(v.id)})
        assert resp.status_code == 422

    def test_create_service_unknown_vehicle_rejected(self, client):
        resp = client.post("/services", json={"name": "S1", "vehicle_id": str(uuid7())})
        assert resp.status_code == 400

    def test_list_services_empty(self, client):
        resp = client.get("/services")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_services(self, client, vehicle_repo):
        v1 = seed_vehicle(vehicle_repo)
        v2 = seed_vehicle(vehicle_repo)
        client.post("/services", json={"name": "S1", "vehicle_id": str(v1.id)})
        client.post("/services", json={"name": "S2", "vehicle_id": str(v2.id)})
        resp = client.get("/services")
        assert len(resp.json()) == 2

    def test_get_service(self, client, vehicle_repo):
        sid, _ = create_service(client, vehicle_repo)
        resp = client.get(f"/services/{sid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "S1"

    def test_get_service_not_found(self, client):
        resp = client.get("/services/999")
        assert resp.status_code == 404

    def test_delete_service(self, client, vehicle_repo):
        sid, _ = create_service(client, vehicle_repo)
        resp = client.delete(f"/services/{sid}")
        assert resp.status_code == 204
        assert client.get(f"/services/{sid}").status_code == 404

    def test_delete_service_idempotent(self, client):
        resp = client.delete("/services/999")
        assert resp.status_code == 204


class TestServiceRouteUpdate:
    def test_update_route(self, client, vehicle_repo):
        sid, _ = create_service(client, vehicle_repo)
        resp = client.patch(
            f"/services/{sid}/route",
            json={
                "stops": [
                    {"platform_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                    {"platform_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 90},
                ],
                "start_time": 1000,
            },
        )
        assert resp.status_code == 200
        assert resp.json() == {"id": sid}

        # Verify full state via GET
        get_resp = client.get(f"/services/{sid}")
        data = get_resp.json()

        # Path: P1A -> B3 -> B5 -> P2A
        path = data["path"]
        assert len(path) == 4
        assert path[0]["type"] == "platform"
        assert path[0]["name"] == "P1A"
        assert path[1]["type"] == "block"
        assert path[1]["name"] == "B3"
        assert path[2]["type"] == "block"
        assert path[2]["name"] == "B5"
        assert path[3]["type"] == "platform"
        assert path[3]["name"] == "P2A"

        # Timetable
        tt = data["timetable"]
        assert len(tt) == 4
        assert tt[0]["arrival"] == 1000 and tt[0]["departure"] == 1060  # P1A dwell=60
        assert tt[1]["arrival"] == 1060 and tt[1]["departure"] == 1090  # B3 traverse=30
        assert tt[2]["arrival"] == 1090 and tt[2]["departure"] == 1120  # B5 traverse=30
        assert tt[3]["arrival"] == 1120 and tt[3]["departure"] == 1210  # P2A dwell=90

    def test_update_route_unknown_platform(self, client, vehicle_repo):
        sid, _ = create_service(client, vehicle_repo)
        resp = client.patch(
            f"/services/{sid}/route",
            json={
                "stops": [
                    {"platform_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                    {"platform_id": str(uuid7()), "dwell_time": 60},
                ],
                "start_time": 0,
            },
        )
        assert resp.status_code == 400

    def test_update_route_service_not_found(self, client):
        resp = client.patch(
            "/services/999/route",
            json={
                "stops": [
                    {"platform_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                    {"platform_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 60},
                ],
                "start_time": 0,
            },
        )
        assert resp.status_code == 404

    def test_update_route_no_route_returns_400(self, client, vehicle_repo):
        sid, _ = create_service(client, vehicle_repo)
        # P2A -> P1A has no route
        resp = client.patch(
            f"/services/{sid}/route",
            json={
                "stops": [
                    {"platform_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 60},
                    {"platform_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                ],
                "start_time": 0,
            },
        )
        assert resp.status_code == 400

    def test_update_route_conflict_returns_409(self, client, vehicle_repo):
        v = seed_vehicle(vehicle_repo)
        vid = str(v.id)

        r1 = client.post("/services", json={"name": "S1", "vehicle_id": vid})
        r2 = client.post("/services", json={"name": "S2", "vehicle_id": vid})
        s1_id, s2_id = r1.json()["id"], r2.json()["id"]

        route = {
            "stops": [
                {"platform_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 0},
                {"platform_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 0},
            ],
            "start_time": 0,
        }
        client.patch(f"/services/{s1_id}/route", json=route)

        # Overlapping route with same vehicle
        resp = client.patch(
            f"/services/{s2_id}/route",
            json={**route, "start_time": 10},
        )
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert (
            len(detail["vehicle_conflicts"]) > 0
            or len(detail["block_conflicts"]) > 0
        )
