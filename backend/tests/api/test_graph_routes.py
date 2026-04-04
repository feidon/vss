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
        assert "edges" in graph
        assert "junctions" in graph
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

    async def test_graph_node_count(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        # 1 yard + 6 platforms = 7 nodes (blocks are now edges)
        assert len(graph["nodes"]) == 7

    async def test_graph_has_edges_for_all_blocks(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        edge_names = {e["name"] for e in graph["edges"]}
        assert edge_names == {f"B{i}" for i in range(1, 15)}
        # 12 unidirectional + 2 bidirectional (B1, B2) x 2 directions = 16
        assert len(graph["edges"]) == 16

    async def test_edges_have_from_and_to(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        for edge in graph["edges"]:
            assert "from_id" in edge
            assert "to_id" in edge
            assert "id" in edge
            assert "name" in edge

    async def test_graph_has_four_junctions(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        assert len(graph["junctions"]) == 4
        for junction in graph["junctions"]:
            assert "id" in junction
            assert "x" in junction
            assert "y" in junction

    async def test_platform_station_lookup_via_stations(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        p1a = next(n for n in graph["nodes"] if n.get("name") == "P1A")
        s1 = next(s for s in graph["stations"] if s["name"] == "S1")
        assert p1a["id"] in s1["platform_ids"]

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

    async def test_every_edge_has_distinct_endpoints(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        for edge in graph["edges"]:
            assert edge["from_id"] != edge["to_id"], f"{edge['name']} has same from/to"

    async def test_junction_edges_preserve_direction(self, client):
        """Edges through junctions must reflect the directed track topology."""
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]

        nodes_by_id = {n["id"]: n for n in graph["nodes"]}
        junction_ids = {j["id"] for j in graph["junctions"]}

        def edges_for(name: str) -> list[dict]:
            return [e for e in graph["edges"] if e["name"] == name]

        def node_name(uid: str) -> str:
            return nodes_by_id[uid]["name"]

        def assert_directed_edge(
            name: str,
            from_name: str | None,
            to_name: str | None,
        ):
            """Exactly one edge with this (from, to). None = junction."""
            matches = [
                e
                for e in edges_for(name)
                if (
                    (from_name is None or node_name(e["from_id"]) == from_name)
                    and (to_name is None or node_name(e["to_id"]) == to_name)
                    and (from_name is not None or e["from_id"] in junction_ids)
                    and (to_name is not None or e["to_id"] in junction_ids)
                )
            ]
            assert len(matches) == 1, (
                f"Expected 1 edge {name} {from_name}→{to_name}, got {len(matches)}"
            )

        # Outbound: S1 → S2 via J1
        assert_directed_edge("B3", "P1A", None)
        assert_directed_edge("B4", "P1B", None)
        assert_directed_edge("B5", None, "P2A")

        # Outbound: S2 → S3 via J2
        assert_directed_edge("B6", "P2A", None)
        assert_directed_edge("B7", None, "P3A")
        assert_directed_edge("B8", None, "P3B")

        # Return: S3 → S2 via J3
        assert_directed_edge("B10", "P3A", None)
        assert_directed_edge("B9", "P3B", None)
        assert_directed_edge("B11", None, "P2B")

        # Return: S2 → S1 via J4
        assert_directed_edge("B12", "P2B", None)
        assert_directed_edge("B13", None, "P1A")
        assert_directed_edge("B14", None, "P1B")

    async def test_bidirectional_edges(self, client):
        """B1 and B2 each produce two edges (one per direction)."""
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]

        nodes_by_id = {n["id"]: n for n in graph["nodes"]}

        def edge_directions(name: str) -> set[tuple[str, str]]:
            return {
                (nodes_by_id[e["from_id"]]["name"], nodes_by_id[e["to_id"]]["name"])
                for e in graph["edges"]
                if e["name"] == name
            }

        assert edge_directions("B1") == {("Y", "P1A"), ("P1A", "Y")}
        assert edge_directions("B2") == {("Y", "P1B"), ("P1B", "Y")}
