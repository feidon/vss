from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from domain.block.model import Block
from domain.network.model import Node, NodeType
from domain.service.model import Service, TimetableEntry


class CreateServiceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    vehicle_id: UUID


class NodeInput(BaseModel):
    id: UUID
    type: Literal["block", "platform"]

    def to_domain(self) -> Node:
        return Node(id=self.id, type=NodeType(self.type))


class UpdatePathRequest(BaseModel):
    path: list[NodeInput]

    def to_nodes(self) -> list[Node]:
        return [n.to_domain() for n in self.path]


class TimetableEntrySchema(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int


class UpdateTimetableRequest(BaseModel):
    timetable: list[TimetableEntrySchema]

    def to_domains(self) -> list[TimetableEntry]:
        return [
            TimetableEntry(
                order=e.order,
                node_id=e.node_id,
                arrival=e.arrival,
                departure=e.departure,
            )
            for e in self.timetable
        ]


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


PathNodeResponse = Annotated[
    BlockNodeResponse | PlatformNodeResponse,
    Field(discriminator="type"),
]


class ServiceResponse(BaseModel):
    id: UUID
    name: str
    vehicle_id: UUID
    path: list[PathNodeResponse]
    timetable: list[TimetableEntrySchema]

    @classmethod
    def from_domain(cls, service: Service, blocks: dict[UUID, Block]) -> ServiceResponse:
        path_nodes: list[BlockNodeResponse | PlatformNodeResponse] = []
        for node in service.path:
            if node.id in blocks:
                b = blocks[node.id]
                path_nodes.append(BlockNodeResponse(
                    id=b.id, name=b.name, group=b.group,
                    traversal_time_seconds=b.traversal_time_seconds,
                ))
            # TODO: add platform branch when available

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
