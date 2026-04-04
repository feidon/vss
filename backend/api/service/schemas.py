from __future__ import annotations

from uuid import UUID

from application.graph.dto import GraphData
from application.service.dto import RouteStop
from domain.block.model import Block
from domain.network.model import NodeType
from domain.service.model import Service
from domain.station.model import Platform
from domain.vehicle.model import Vehicle
from pydantic import BaseModel, Field

from api.shared.schemas import (
    BlockNodeSchema,
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

        return cls(
            nodes=nodes,
            edges=[
                EdgeSchema(id=e.id, name=e.name, from_id=e.from_id, to_id=e.to_id)
                for e in data.edges
            ],
            junctions=[JunctionSchema(id=j.id, x=j.x, y=j.y) for j in data.junctions],
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
        block_dict = {b.id: b for b in graph_data.blocks}
        platform_dict = {p.id: p for p in graph_data.platforms}
        yard_name_dict = {y.id: y.name for y in graph_data.yards}
        route_nodes = cls._get_route_nodes(
            service, block_dict, platform_dict, yard_name_dict
        )

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
        block_dict: dict[UUID, Block],
        platform_dict: dict[UUID, Platform],
        yard_name_dict: dict[UUID, str],
    ) -> list[PlatformNodeSchema | YardNodeSchema]:
        route_nodes: list[PlatformNodeSchema | YardNodeSchema] = []
        for node in service.route:
            if node.type == NodeType.BLOCK and node.id in block_dict:
                b = block_dict[node.id]
                route_nodes.append(
                    BlockNodeSchema(
                        id=b.id,
                        name=b.name,
                        group=b.group,
                        traversal_time_seconds=b.traversal_time_seconds,
                    )
                )
            elif node.type == NodeType.PLATFORM and node.id in platform_dict:
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
