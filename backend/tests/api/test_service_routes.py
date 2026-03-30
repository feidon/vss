from uuid import uuid7

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_service_repo
from infra.memory.service_repo import InMemoryServiceRepository
from main import app


@pytest.fixture
def service_repo():
    return InMemoryServiceRepository()


@pytest.fixture
def client(service_repo):
    app.dependency_overrides[get_service_repo] = lambda: service_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestServiceCRUD:
    def test_create_service(self, client):
        vid = str(uuid7())
        resp = client.post("/services", json={"name": "Express", "vehicle_id": vid})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Express"
        assert data["vehicle_id"] == vid
        assert data["path"] == []
        assert data["timetable"] == []

    def test_create_service_empty_name_rejected(self, client):
        resp = client.post("/services", json={"name": "", "vehicle_id": str(uuid7())})
        assert resp.status_code == 422

    def test_list_services_empty(self, client):
        resp = client.get("/services")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_services(self, client):
        client.post("/services", json={"name": "S1", "vehicle_id": str(uuid7())})
        client.post("/services", json={"name": "S2", "vehicle_id": str(uuid7())})
        resp = client.get("/services")
        assert len(resp.json()) == 2

    def test_get_service(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        resp = client.get(f"/services/{sid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "S1"

    def test_get_service_not_found(self, client):
        resp = client.get(f"/services/{uuid7()}")
        assert resp.status_code == 404

    def test_delete_service(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        resp = client.delete(f"/services/{sid}")
        assert resp.status_code == 204
        assert client.get(f"/services/{sid}").status_code == 404

    def test_delete_service_idempotent(self, client):
        resp = client.delete(f"/services/{uuid7()}")
        assert resp.status_code == 204


class TestServicePathUpdate:
    def test_update_path(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        nid = str(uuid7())
        resp = client.patch(
            f"/services/{sid}/path",
            json={"path": [{"id": nid, "type": "block"}]},
        )
        assert resp.status_code == 200
        assert len(resp.json()["path"]) == 1

    def test_update_path_not_found(self, client):
        resp = client.patch(
            f"/services/{uuid7()}/path",
            json={"path": []},
        )
        assert resp.status_code == 404


class TestServiceTimetableUpdate:
    def test_update_timetable(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        nid = str(uuid7())
        client.patch(
            f"/services/{sid}/path",
            json={"path": [{"id": nid, "type": "block"}]},
        )
        resp = client.patch(
            f"/services/{sid}/timetable",
            json={
                "timetable": [
                    {"order": 0, "node_id": nid, "arrival": 0, "departure": 10}
                ]
            },
        )
        assert resp.status_code == 200
        assert len(resp.json()["timetable"]) == 1

    def test_update_timetable_node_not_in_path(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        resp = client.patch(
            f"/services/{sid}/timetable",
            json={
                "timetable": [
                    {"order": 0, "node_id": str(uuid7()), "arrival": 0, "departure": 10}
                ]
            },
        )
        assert resp.status_code == 400

    def test_update_timetable_not_found(self, client):
        resp = client.patch(
            f"/services/{uuid7()}/timetable",
            json={"timetable": []},
        )
        assert resp.status_code == 404
