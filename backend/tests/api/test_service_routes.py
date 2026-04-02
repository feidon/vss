from uuid import uuid7

import pytest

from infra.seed import PLATFORM_ID_BY_NAME, VEHICLE_ID_BY_NAME

pytestmark = pytest.mark.postgres


async def create_service(client, vehicle_name="V1"):
    vid = str(VEHICLE_ID_BY_NAME[vehicle_name])
    resp = await client.post("/services", json={"name": "S1", "vehicle_id": vid})
    assert resp.status_code == 201
    return resp.json()["id"]


class TestServiceCRUD:
    async def test_create_service(self, client):
        vid = str(VEHICLE_ID_BY_NAME["V1"])
        resp = await client.post(
            "/services", json={"name": "Express", "vehicle_id": vid}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert set(data.keys()) == {"id"}

    async def test_create_service_empty_name_rejected(self, client):
        vid = str(VEHICLE_ID_BY_NAME["V1"])
        resp = await client.post("/services", json={"name": "", "vehicle_id": vid})
        assert resp.status_code == 422

    async def test_create_service_unknown_vehicle_rejected(self, client):
        resp = await client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        assert resp.status_code == 400

    async def test_list_services_empty(self, client):
        resp = await client.get("/services")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_services(self, client):
        vid1 = str(VEHICLE_ID_BY_NAME["V1"])
        vid2 = str(VEHICLE_ID_BY_NAME["V2"])
        await client.post("/services", json={"name": "S1", "vehicle_id": vid1})
        await client.post("/services", json={"name": "S2", "vehicle_id": vid2})
        resp = await client.get("/services")
        assert len(resp.json()) == 2

    async def test_get_service(self, client):
        sid = await create_service(client)
        resp = await client.get(f"/services/{sid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "S1"

    async def test_get_service_not_found(self, client):
        resp = await client.get("/services/999")
        assert resp.status_code == 404

    async def test_delete_service(self, client):
        sid = await create_service(client)
        resp = await client.delete(f"/services/{sid}")
        assert resp.status_code == 204
        assert (await client.get(f"/services/{sid}")).status_code == 404

    async def test_delete_service_idempotent(self, client):
        resp = await client.delete("/services/999")
        assert resp.status_code == 204


class TestServiceRouteUpdate:
    async def test_update_route(self, client):
        sid = await create_service(client)
        resp = await client.patch(
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
        get_resp = await client.get(f"/services/{sid}")
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

    async def test_update_route_unknown_platform(self, client):
        sid = await create_service(client)
        resp = await client.patch(
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

    async def test_update_route_service_not_found(self, client):
        resp = await client.patch(
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

    async def test_update_route_no_route_returns_400(self, client):
        sid = await create_service(client)
        # P2A -> P1A has no route
        resp = await client.patch(
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

    async def test_update_route_conflict_returns_409(self, client):
        vid = str(VEHICLE_ID_BY_NAME["V1"])

        r1 = await client.post("/services", json={"name": "S1", "vehicle_id": vid})
        r2 = await client.post("/services", json={"name": "S2", "vehicle_id": vid})
        s1_id, s2_id = r1.json()["id"], r2.json()["id"]

        route = {
            "stops": [
                {"platform_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 0},
                {"platform_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 0},
            ],
            "start_time": 0,
        }
        await client.patch(f"/services/{s1_id}/route", json=route)

        # Overlapping route with same vehicle
        resp = await client.patch(
            f"/services/{s2_id}/route",
            json={**route, "start_time": 10},
        )
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert (
            len(detail["vehicle_conflicts"]) > 0
            or len(detail["block_conflicts"]) > 0
        )
        # Battery conflict fields present in response
        assert "low_battery_conflicts" in detail
        assert "insufficient_charge_conflicts" in detail
