from __future__ import annotations

from uuid import UUID

from application.graph.dto import GraphData
from application.service.dto import RouteStop
from domain.network.model import NodeType
from domain.service.model import Service
from domain.vehicle.model import Vehicle
from pydantic import BaseModel, Field

from api.shared.schemas import (
    BlockNodeSchema,
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

    @classmethod
    def from_domain(cls, service: Service, vehicle: Vehicle) -> ServiceResponse:
        return cls(
            id=service.id,
            name=service.name,
            vehicle_id=service.vehicle_id,
            vehicle_name=vehicle.name,
        )


# ── Graph sub-schemas (for service detail) ────────────────────


class ConnectionSchema(BaseModel):
    from_id: UUID
    to_id: UUID


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
    connections: list[ConnectionSchema]
    stations: list[StationSchema]
    vehicles: list[VehicleSchema]

    @classmethod
    def from_graph_data(cls, data: GraphData) -> GraphSchema:
        nodes: list[BlockNodeSchema | PlatformNodeSchema | YardNodeSchema] = []
        layouts = data.layouts

        for yard in data.yards:
            x, y = layouts.get(yard.id, (0.0, 0.0))
            nodes.append(YardNodeSchema(id=yard.id, name=yard.name, x=x, y=y))

        for platform in data.all_platforms:
            x, y = layouts.get(platform.id, (0.0, 0.0))
            nodes.append(
                PlatformNodeSchema(id=platform.id, name=platform.name, x=x, y=y)
            )

        for block in data.blocks:
            x, y = layouts.get(block.id, (0.0, 0.0))
            nodes.append(
                BlockNodeSchema(
                    id=block.id,
                    name=block.name,
                    group=block.group,
                    traversal_time_seconds=block.traversal_time_seconds,
                    x=x,
                    y=y,
                )
            )

        return cls(
            nodes=nodes,
            connections=[
                ConnectionSchema(from_id=c.from_id, to_id=c.to_id)
                for c in data.connections
            ],
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
        blocks = {b.id: b for b in graph_data.blocks}
        platforms = {p.id: p for p in graph_data.all_platforms}
        yards = {y.id: y.name for y in graph_data.yards}

        route_nodes: list[BlockNodeSchema | PlatformNodeSchema | YardNodeSchema] = []
        for node in service.route:
            if node.type == NodeType.BLOCK and node.id in blocks:
                b = blocks[node.id]
                route_nodes.append(
                    BlockNodeSchema(
                        id=b.id,
                        name=b.name,
                        group=b.group,
                        traversal_time_seconds=b.traversal_time_seconds,
                    )
                )
            elif node.type == NodeType.PLATFORM and node.id in platforms:
                p = platforms[node.id]
                route_nodes.append(PlatformNodeSchema(id=p.id, name=p.name))
            elif node.type == NodeType.YARD:
                route_nodes.append(
                    YardNodeSchema(
                        id=node.id,
                        name=yards.get(node.id, "Y"),
                    )
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
