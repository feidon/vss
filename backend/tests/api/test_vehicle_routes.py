import pytest
from starlette.status import HTTP_200_OK

pytestmark = pytest.mark.postgres


class TestListVehicles:
    async def test_returns_all_seeded_vehicles(self, client):
        resp = await client.get("vehicles")
        assert resp.status_code == HTTP_200_OK
        vehicles = resp.json()
        names = {v["name"] for v in vehicles}
        assert names == {"V1", "V2", "V3"}

    async def test_vehicle_has_id_and_name(self, client):
        resp = await client.get("vehicles")
        vehicle = resp.json()[0]
        assert "id" in vehicle
        assert "name" in vehicle
        assert set(vehicle.keys()) == {"id", "name"}
