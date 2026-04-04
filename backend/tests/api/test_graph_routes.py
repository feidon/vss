import pytest
from infra.seed import VEHICLE_ID_BY_NAME
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

pytestmark = pytest.mark.postgres


async def _create_service(client):
    vid = str(VEHICLE_ID_BY_NAME["V1"])
    resp = await client.post("services", json={"name": "S1", "vehicle_id": vid})
    assert resp.status_code == HTTP_201_CREATED
    return resp.json()["id"]


class TestServiceDetailGraph:
    async def test_service_detail_includes_graph(self, client):
        sid = await _create_service(client)
        resp = await client.get(f"services/{sid}")
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert "graph" in data
        graph = data["graph"]
        assert "nodes" in graph
        assert "connections" in graph
        assert "stations" in graph
        assert "vehicles" in graph

    async def test_graph_has_yard_node(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        yard_nodes = [n for n in graph["nodes"] if n["type"] == "yard"]
        assert len(yard_nodes) == 1
        assert yard_nodes[0]["name"] == "Y"

    async def test_graph_has_all_platform_nodes(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        platform_nodes = [n for n in graph["nodes"] if n["type"] == "platform"]
        names = {p["name"] for p in platform_nodes}
        assert names == {"P1A", "P1B", "P2A", "P2B", "P3A", "P3B"}

    async def test_graph_has_all_block_nodes(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        block_nodes = [n for n in graph["nodes"] if n["type"] == "block"]
        names = {b["name"] for b in block_nodes}
        assert names == {f"B{i}" for i in range(1, 15)}

    async def test_block_nodes_have_traversal_time(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        for block in graph["nodes"]:
            if block["type"] == "block":
                assert "traversal_time_seconds" in block
                assert block["traversal_time_seconds"] > 0

    async def test_block_nodes_have_group(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        b1 = next(n for n in graph["nodes"] if n.get("name") == "B1")
        assert b1["group"] == 1

    async def test_platform_station_lookup_via_stations(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        p1a = next(n for n in graph["nodes"] if n.get("name") == "P1A")
        s1 = next(s for s in graph["stations"] if s["name"] == "S1")
        assert p1a["id"] in s1["platform_ids"]

    async def test_graph_has_connections(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        assert len(graph["connections"]) > 0
        conn = graph["connections"][0]
        assert "from_id" in conn
        assert "to_id" in conn

    async def test_graph_has_stations(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        station_names = {s["name"] for s in graph["stations"]}
        assert station_names == {"Y", "S1", "S2", "S3"}

    async def test_graph_has_vehicles(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        vehicle_names = {v["name"] for v in graph["vehicles"]}
        assert vehicle_names == {"V1", "V2", "V3"}

    async def test_graph_node_count(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        # 1 yard + 6 platforms + 14 blocks = 21 nodes
        assert len(graph["nodes"]) == 21
