from __future__ import annotations

import pytest
from infra.seed import VEHICLE_ID_BY_NAME

pytestmark = pytest.mark.postgres


class TestGenerateSchedule:
    async def test_generate_returns_200(self, client):
        resp = await client.post(
            "schedules/generate",
            json={
                "interval_seconds": 360,
                "start_time": 0,
                "end_time": 3600,
                "dwell_time_seconds": 30,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["services_created"] > 0
        assert len(data["vehicles_used"]) > 0
        assert data["cycle_time_seconds"] > 0

    async def test_generated_services_are_persisted(self, client):
        await client.post(
            "schedules/generate",
            json={
                "interval_seconds": 360,
                "start_time": 0,
                "end_time": 3600,
                "dwell_time_seconds": 30,
            },
        )
        resp = await client.get("services")
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    async def test_clears_existing_services(self, client):
        vid = str(list(VEHICLE_ID_BY_NAME.values())[0])
        await client.post("services", json={"name": "Manual", "vehicle_id": vid})

        resp = await client.post(
            "schedules/generate",
            json={
                "interval_seconds": 360,
                "start_time": 0,
                "end_time": 3600,
                "dwell_time_seconds": 30,
            },
        )
        assert resp.status_code == 200
        services = (await client.get("services")).json()
        assert all(s["name"].startswith("Auto-") for s in services)

    async def test_invalid_interval_returns_422(self, client):
        resp = await client.post(
            "schedules/generate",
            json={
                "interval_seconds": 0,
                "start_time": 0,
                "end_time": 3600,
                "dwell_time_seconds": 30,
            },
        )
        assert resp.status_code == 422
