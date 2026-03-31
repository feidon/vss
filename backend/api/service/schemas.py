from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from domain.block.model import Block
from domain.network.model import NodeType
from domain.service.model import Service
from domain.station.model import Platform


class CreateServiceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    vehicle_id: UUID


class RouteStopInput(BaseModel):
    platform_id: UUID
    dwell_time: int = Field(ge=0)


class UpdateRouteRequest(BaseModel):
    stops: list[RouteStopInput] = Field(min_length=1)
    start_time: int


# ── Response schemas ─────────────────────────────────────────


class BlockNodeResponse(BaseModel):
    type: Literal["block"] = "block"
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int


class PlatformNodeResponse(BaseModel):
    type: Literal["platform"] = "platform"
    id: UUID
    name: str


class YardNodeResponse(BaseModel):
    type: Literal["yard"] = "yard"
    id: UUID
    name: str


PathNodeResponse = Annotated[
    BlockNodeResponse | PlatformNodeResponse | YardNodeResponse,
    Field(discriminator="type"),
]


class TimetableEntrySchema(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int


class ServiceResponse(BaseModel):
    id: int
    name: str
    vehicle_id: UUID
    path: list[PathNodeResponse]
    timetable: list[TimetableEntrySchema]

    @classmethod
    def from_domain(
        cls,
        service: Service,
        blocks: dict[UUID, Block],
        platforms: dict[UUID, Platform],
        yard_id: UUID | None = None,
        yard_name: str = "Y",
    ) -> ServiceResponse:
        path_nodes: list[BlockNodeResponse | PlatformNodeResponse | YardNodeResponse] = []
        for node in service.path:
            if node.type == NodeType.BLOCK and node.id in blocks:
                b = blocks[node.id]
                path_nodes.append(BlockNodeResponse(
                    id=b.id, name=b.name, group=b.group,
                    traversal_time_seconds=b.traversal_time_seconds,
                ))
            elif node.type == NodeType.PLATFORM and node.id in platforms:
                p = platforms[node.id]
                path_nodes.append(PlatformNodeResponse(id=p.id, name=p.name))
            elif node.type == NodeType.YARD:
                path_nodes.append(YardNodeResponse(
                    id=node.id, name=yard_name,
                ))

        return cls(
            id=service.id,
            name=service.name,
            vehicle_id=service.vehicle_id,
            path=path_nodes,
            timetable=[
                TimetableEntrySchema(
                    order=e.order,
                    node_id=e.node_id,
                    arrival=e.arrival,
                    departure=e.departure,
                )
                for e in service.timetable
            ],
        )
