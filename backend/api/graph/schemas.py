from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from api.shared.schemas import BlockNodeSchema, NodeSchema, PlatformNodeSchema, YardNodeSchema
from application.graph.dto import GraphData


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


class GraphResponse(BaseModel):
    nodes: list[NodeSchema]
    connections: list[ConnectionSchema]
    stations: list[StationSchema]
    vehicles: list[VehicleSchema]

    @classmethod
    def from_graph_data(cls, data: GraphData) -> GraphResponse:
        nodes: list[BlockNodeSchema | PlatformNodeSchema | YardNodeSchema] = []
        layouts = data.layouts

        yard = data.yard
        if yard is not None:
            x, y = layouts.get(yard.id, (0.0, 0.0))
            nodes.append(YardNodeSchema(id=yard.id, name=yard.name, x=x, y=y))

        for platform in data.all_platforms:
            x, y = layouts.get(platform.id, (0.0, 0.0))
            nodes.append(PlatformNodeSchema(id=platform.id, name=platform.name, x=x, y=y))

        for block in data.blocks:
            x, y = layouts.get(block.id, (0.0, 0.0))
            nodes.append(BlockNodeSchema(
                id=block.id,
                name=block.name,
                group=block.group,
                traversal_time_seconds=block.traversal_time_seconds,
                x=x,
                y=y,
            ))

        connections = [
            ConnectionSchema(from_id=c.from_id, to_id=c.to_id)
            for c in data.connections
        ]

        stations = [
            StationSchema(
                id=s.id,
                name=s.name,
                is_yard=s.is_yard,
                platform_ids=[p.id for p in s.platforms],
            )
            for s in data.stations
        ]

        vehicles = [
            VehicleSchema(id=v.id, name=v.name)
            for v in data.vehicles
        ]

        return cls(
            nodes=nodes,
            connections=connections,
            stations=stations,
            vehicles=vehicles,
        )
