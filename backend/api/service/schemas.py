from __future__ import annotations

from uuid import UUID

from application.graph.dto import GraphData
from application.service.dto import RouteStop
from domain.network.model import NodeType
from domain.service.model import Service
from domain.station.model import Platform
from domain.vehicle.model import Vehicle
from pydantic import BaseModel, Field

from api.shared.schemas import (
    EdgeSchema,
    JunctionSchema,
    NodeSchema,
    PlatformNodeSchema,
    TimetableEntrySchema,
    YardNodeSchema,
)


class CreateServiceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    vehicle_id: UUID


class RouteStopInput(BaseModel):
    node_id: UUID
    dwell_time: int = Field(ge=0)

    def to_route_stop(self) -> RouteStop:
        return RouteStop(node_id=self.node_id, dwell_time=self.dwell_time)


class UpdateRouteRequest(BaseModel):
    stops: list[RouteStopInput] = Field(min_length=1)
    start_time: int


class ServiceIdResponse(BaseModel):
    id: int


# ── List response (GET /services) ─────────────────────────────


class ServiceResponse(BaseModel):
    id: int
    name: str
    vehicle_id: UUID
    vehicle_name: str
    start_time: int | None = None
    origin_name: str | None = None
    destination_name: str | None = None

    @classmethod
    def from_domain(
        cls,
        service: Service,
        vehicle: Vehicle,
        node_names: dict[UUID, str],
    ) -> ServiceResponse:
        start_time = service.timetable[0].arrival if service.timetable else None

        origin_name = node_names.get(service.route[0].id) if service.route else None

        destination_name: str | None = None
        if service.route:
            for node in reversed(service.route):
                if node.type != NodeType.BLOCK:
                    destination_name = node_names.get(node.id)
                    break

        return cls(
            id=service.id,
            name=service.name,
            vehicle_id=service.vehicle_id,
            vehicle_name=vehicle.name,
            start_time=start_time,
            origin_name=origin_name,
            destination_name=destination_name,
        )


# ── Graph sub-schemas (for service detail) ────────────────────


class VehicleSchema(BaseModel):
    id: UUID
    name: str


class StationSchema(BaseModel):
    id: UUID
    name: str
    is_yard: bool
    platform_ids: list[UUID]


class GraphSchema(BaseModel):
    nodes: list[NodeSchema]
    edges: list[EdgeSchema]
    junctions: list[JunctionSchema]
    stations: list[StationSchema]
    vehicles: list[VehicleSchema]

    @classmethod
    def from_graph_data(cls, data: GraphData) -> GraphSchema:
        nodes: list[PlatformNodeSchema | YardNodeSchema] = []
        positions = data.layout.positions

        for yard in data.yards:
            x, y = positions.get(yard.id, (0.0, 0.0))
            nodes.append(YardNodeSchema(id=yard.id, name=yard.name, x=x, y=y))

        for platform in data.platforms:
            x, y = positions.get(platform.id, (0.0, 0.0))
            nodes.append(
                PlatformNodeSchema(id=platform.id, name=platform.name, x=x, y=y)
            )

        # Build block_junction index: block_id -> junction_id
        block_junction: dict[UUID, UUID] = {}
        for (from_b, to_b), jid in data.layout.junction_blocks.items():
            block_junction[from_b] = jid
            block_junction[to_b] = jid

        # Build adjacency: for each block, find its non-block neighbors
        block_ids = {b.id for b in data.blocks}
        adjacency: dict[UUID, set[UUID]] = {b.id: set() for b in data.blocks}
        for conn in data.connections:
            if conn.from_id in block_ids and conn.to_id not in block_ids:
                adjacency[conn.from_id].add(conn.to_id)
            if conn.to_id in block_ids and conn.from_id not in block_ids:
                adjacency[conn.to_id].add(conn.from_id)

        # Compute edges
        edges: list[EdgeSchema] = []
        for block in data.blocks:
            non_block_neighbors = adjacency.get(block.id, set())
            junction_id = block_junction.get(block.id)

            if junction_id is not None and len(non_block_neighbors) == 1:
                # Block connects a platform/yard to a junction
                neighbor = next(iter(non_block_neighbors))
                edges.append(
                    EdgeSchema(
                        id=block.id,
                        name=block.name,
                        from_id=neighbor,
                        to_id=junction_id,
                    )
                )
            elif junction_id is None and len(non_block_neighbors) == 2:
                # Bidirectional block (B1, B2): connects two platforms/yards directly
                neighbors = list(non_block_neighbors)
                edges.append(
                    EdgeSchema(
                        id=block.id,
                        name=block.name,
                        from_id=neighbors[0],
                        to_id=neighbors[1],
                    )
                )

        # Build junctions list
        junction_ids = set(block_junction.values())
        junctions = [
            JunctionSchema(id=jid, x=positions[jid][0], y=positions[jid][1])
            for jid in junction_ids
            if jid in positions
        ]

        return cls(
            nodes=nodes,
            edges=edges,
            junctions=junctions,
            stations=[
                StationSchema(
                    id=s.id,
                    name=s.name,
                    is_yard=s.is_yard,
                    platform_ids=[p.id for p in s.platforms],
                )
                for s in data.stations
            ],
            vehicles=[VehicleSchema(id=v.id, name=v.name) for v in data.vehicles],
        )


# ── Detail response (GET /services/{id}) ──────────────────────


class ServiceDetailResponse(BaseModel):
    id: int
    name: str
    vehicle_id: UUID
    route: list[NodeSchema]
    timetable: list[TimetableEntrySchema]
    graph: GraphSchema

    @classmethod
    def from_domain(
        cls,
        service: Service,
        graph_data: GraphData,
    ) -> ServiceDetailResponse:
        platform_dict = {p.id: p for p in graph_data.platforms}
        yard_name_dict = {y.id: y.name for y in graph_data.yards}
        route_nodes = cls._get_route_nodes(service, platform_dict, yard_name_dict)

        return cls(
            id=service.id,
            name=service.name,
            vehicle_id=service.vehicle_id,
            route=route_nodes,
            timetable=[
                TimetableEntrySchema(
                    order=e.order,
                    node_id=e.node_id,
                    arrival=e.arrival,
                    departure=e.departure,
                )
                for e in service.timetable
            ],
            graph=GraphSchema.from_graph_data(graph_data),
        )

    @classmethod
    def _get_route_nodes(
        cls,
        service: Service,
        platform_dict: dict[UUID, Platform],
        yard_name_dict: dict[UUID, str],
    ) -> list[PlatformNodeSchema | YardNodeSchema]:
        route_nodes: list[PlatformNodeSchema | YardNodeSchema] = []
        for node in service.route:
            if node.type == NodeType.PLATFORM and node.id in platform_dict:
                p = platform_dict[node.id]
                route_nodes.append(PlatformNodeSchema(id=p.id, name=p.name))
            elif node.type == NodeType.YARD:
                route_nodes.append(
                    YardNodeSchema(
                        id=node.id,
                        name=yard_name_dict.get(node.id, "Y"),
                    )
                )

        return route_nodes
