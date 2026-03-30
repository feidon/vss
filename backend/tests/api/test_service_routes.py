from uuid import uuid7

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_block_repo, get_service_repo
from domain.block.model import Block
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.service_repo import InMemoryServiceRepository
from main import app


@pytest.fixture
def service_repo():
    return InMemoryServiceRepository()


@pytest.fixture
def block_repo():
    return InMemoryBlockRepository()


@pytest.fixture
def client(service_repo, block_repo):
    app.dependency_overrides[get_service_repo] = lambda: service_repo
    app.dependency_overrides[get_block_repo] = lambda: block_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def seed_block(block_repo, **kwargs) -> Block:
    defaults = dict(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
    defaults.update(kwargs)
    block = Block(**defaults)
    block_repo._store[block.id] = block
    return block


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
    def test_update_path(self, client, block_repo):
        block = seed_block(block_repo, name="B1")
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        resp = client.patch(
            f"/services/{sid}/path",
            json={"path": [{"id": str(block.id), "type": "block"}]},
        )
        assert resp.status_code == 200
        path = resp.json()["path"]
        assert len(path) == 1
        assert path[0]["type"] == "block"
        assert path[0]["name"] == "B1"
        assert path[0]["traversal_time_seconds"] == 30

    def test_update_path_unknown_block(self, client):
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        resp = client.patch(
            f"/services/{sid}/path",
            json={"path": [{"id": str(uuid7()), "type": "block"}]},
        )
        assert resp.status_code == 404

    def test_update_path_not_found(self, client):
        resp = client.patch(
            f"/services/{uuid7()}/path",
            json={"path": []},
        )
        assert resp.status_code == 404


class TestServiceTimetableUpdate:
    def test_update_timetable(self, client, block_repo):
        block = seed_block(block_repo)
        create_resp = client.post(
            "/services", json={"name": "S1", "vehicle_id": str(uuid7())}
        )
        sid = create_resp.json()["id"]
        client.patch(
            f"/services/{sid}/path",
            json={"path": [{"id": str(block.id), "type": "block"}]},
        )
        resp = client.patch(
            f"/services/{sid}/timetable",
            json={
                "timetable": [
                    {"order": 0, "node_id": str(block.id), "arrival": 0, "departure": 10}
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

    def test_update_timetable_conflict_returns_409(self, client, block_repo):
        block = seed_block(block_repo)
        nid = str(block.id)
        vid = str(uuid7())

        r1 = client.post("/services", json={"name": "S1", "vehicle_id": vid})
        r2 = client.post("/services", json={"name": "S2", "vehicle_id": vid})
        s1_id, s2_id = r1.json()["id"], r2.json()["id"]

        client.patch(f"/services/{s1_id}/path", json={"path": [{"id": nid, "type": "block"}]})
        client.patch(f"/services/{s2_id}/path", json={"path": [{"id": nid, "type": "block"}]})

        client.patch(
            f"/services/{s1_id}/timetable",
            json={"timetable": [{"order": 0, "node_id": nid, "arrival": 0, "departure": 100}]},
        )

        resp = client.patch(
            f"/services/{s2_id}/timetable",
            json={"timetable": [{"order": 0, "node_id": nid, "arrival": 50, "departure": 150}]},
        )
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert len(detail["vehicle_conflicts"]) > 0 or len(detail["block_conflicts"]) > 0
