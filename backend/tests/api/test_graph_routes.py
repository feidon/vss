import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    yield TestClient(app)


class TestGraphEndpoint:
    def test_get_graph(self, client):
        resp = client.get("/graph")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "connections" in data
        assert "stations" in data
        assert "vehicles" in data

    def test_graph_has_yard_node(self, client):
        data = client.get("/graph").json()
        yard_nodes = [n for n in data["nodes"] if n["type"] == "yard"]
        assert len(yard_nodes) == 1
        assert yard_nodes[0]["name"] == "Y"

    def test_graph_has_all_platform_nodes(self, client):
        data = client.get("/graph").json()
        platform_nodes = [n for n in data["nodes"] if n["type"] == "platform"]
        names = {p["name"] for p in platform_nodes}
        assert names == {"P1A", "P1B", "P2A", "P2B", "P3A", "P3B"}

    def test_graph_has_all_block_nodes(self, client):
        data = client.get("/graph").json()
        block_nodes = [n for n in data["nodes"] if n["type"] == "block"]
        names = {b["name"] for b in block_nodes}
        assert names == {f"B{i}" for i in range(1, 15)}

    def test_block_nodes_have_traversal_time(self, client):
        data = client.get("/graph").json()
        for block in data["nodes"]:
            if block["type"] == "block":
                assert "traversal_time_seconds" in block
                assert block["traversal_time_seconds"] > 0

    def test_block_nodes_have_group(self, client):
        data = client.get("/graph").json()
        b1 = next(n for n in data["nodes"] if n.get("name") == "B1")
        assert b1["group"] == 1

    def test_platform_nodes_have_station_name(self, client):
        data = client.get("/graph").json()
        p1a = next(n for n in data["nodes"] if n.get("name") == "P1A")
        assert p1a["station_name"] == "S1"

    def test_graph_has_connections(self, client):
        data = client.get("/graph").json()
        assert len(data["connections"]) > 0
        conn = data["connections"][0]
        assert "from_id" in conn
        assert "to_id" in conn

    def test_graph_has_stations(self, client):
        data = client.get("/graph").json()
        station_names = {s["name"] for s in data["stations"]}
        assert station_names == {"Y", "S1", "S2", "S3"}

    def test_graph_has_vehicles(self, client):
        data = client.get("/graph").json()
        vehicle_names = {v["name"] for v in data["vehicles"]}
        assert vehicle_names == {"V1", "V2", "V3"}

    def test_graph_node_count(self, client):
        data = client.get("/graph").json()
        # 1 yard + 6 platforms + 14 blocks = 21 nodes
        assert len(data["nodes"]) == 21
