import pytest

from infra.seed import PLATFORM_ID_BY_NAME, VEHICLE_ID_BY_NAME, YARD_ID

pytestmark = pytest.mark.postgres


class TestValidateRoute:
    async def test_valid_route(self, client):
        resp = await client.post(
            "/routes/validate",
            json={
                "vehicle_id": str(VEHICLE_ID_BY_NAME["V1"]),
                "stops": [
                    {"node_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                    {"node_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 90},
                ],
                "start_time": 1000,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["path"]) == 4
        assert data["battery_conflicts"] == []

    async def test_unreachable_returns_422(self, client):
        resp = await client.post(
            "/routes/validate",
            json={
                "vehicle_id": str(VEHICLE_ID_BY_NAME["V1"]),
                "stops": [
                    {"node_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 60},
                    {"node_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                ],
                "start_time": 0,
            },
        )
        assert resp.status_code == 422

    async def test_yard_as_stop(self, client):
        resp = await client.post(
            "/routes/validate",
            json={
                "vehicle_id": str(VEHICLE_ID_BY_NAME["V1"]),
                "stops": [
                    {"node_id": str(YARD_ID), "dwell_time": 0},
                    {"node_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                ],
                "start_time": 0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["path"]) >= 2

    async def test_single_stop_rejected(self, client):
        resp = await client.post(
            "/routes/validate",
            json={
                "vehicle_id": str(VEHICLE_ID_BY_NAME["V1"]),
                "stops": [
                    {"node_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                ],
                "start_time": 0,
            },
        )
        assert resp.status_code == 422
