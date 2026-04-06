from __future__ import annotations

from uuid import UUID

from domain.block.model import Block
from domain.block.repository import BlockRepository
from domain.network.model import NodeConnection
from domain.network.repository import ConnectionRepository
from domain.read_model.layout import LayoutData, LayoutRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository

from application.graph.dto import Edge, GraphData, Junction


class GraphAppService:
    def __init__(
        self,
        station_repo: StationRepository,
        block_repo: BlockRepository,
        connection_repo: ConnectionRepository,
        vehicle_repo: VehicleRepository,
        layout_repo: LayoutRepository,
    ) -> None:
        self._station_repo = station_repo
        self._block_repo = block_repo
        self._connection_repo = connection_repo
        self._vehicle_repo = vehicle_repo
        self._layout_repo = layout_repo

    async def get_graph(self) -> GraphData:
        stations = await self._station_repo.find_all()
        blocks = await self._block_repo.find_all()
        connections = await self._connection_repo.find_all()
        vehicles = await self._vehicle_repo.find_all()
        layout = await self._layout_repo.find_all()
        edges, junctions = _build_edges_and_junctions(blocks, connections, layout)
        return GraphData(
            stations=stations,
            blocks=blocks,
            connections=connections,
            vehicles=vehicles,
            layout=layout,
            edges=edges,
            junctions=junctions,
        )

    async def get_node_names(self) -> dict[UUID, str]:
        """Return a map of node ID → display name for all stations, platforms, and blocks.

        Lighter-weight than ``get_graph()`` — skips connections, vehicles, layout,
        and edge/junction computation.
        """
        stations = await self._station_repo.find_all()
        blocks = await self._block_repo.find_all()
        names: dict[UUID, str] = {}
        for station in stations:
            names[station.id] = station.name
            for platform in station.platforms:
                names[platform.id] = platform.name
        for block in blocks:
            names[block.id] = block.name
        return names


def _build_edges_and_junctions(
    blocks: list[Block],
    connections: frozenset[NodeConnection],
    layout: LayoutData,
) -> tuple[list[Edge], list[Junction]]:
    block_junction: dict[UUID, UUID] = {}
    for (from_b, to_b), jid in layout.junction_blocks.items():
        block_junction[from_b] = jid
        block_junction[to_b] = jid

    block_ids = {b.id for b in blocks}
    who_connect_to_block: dict[UUID, set[UUID]] = {b.id: set() for b in blocks}
    block_connect_to_who: dict[UUID, set[UUID]] = {b.id: set() for b in blocks}
    for conn in connections:
        if conn.to_id in block_ids:
            from_id = block_junction.get(conn.from_id, conn.from_id)
            who_connect_to_block[conn.to_id].add(from_id)
        if conn.from_id in block_ids:
            to_id = block_junction.get(conn.to_id, conn.to_id)
            block_connect_to_who[conn.from_id].add(to_id)

    edges: list[Edge] = []
    for block in blocks:
        from_ids = who_connect_to_block.get(block.id, set())
        to_ids = block_connect_to_who.get(block.id, set())
        if not from_ids or not to_ids:
            continue
        for from_id in from_ids:
            for to_id in to_ids:
                if from_id != to_id:
                    edges.append(
                        Edge(
                            id=block.id,
                            name=block.name,
                            from_id=from_id,
                            to_id=to_id,
                        )
                    )

    junction_ids = set(block_junction.values())
    junctions = [
        Junction(id=jid, x=layout.positions[jid][0], y=layout.positions[jid][1])
        for jid in junction_ids
        if jid in layout.positions
    ]

    return edges, junctions
