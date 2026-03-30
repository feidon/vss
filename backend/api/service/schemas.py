from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from domain.service.model import Service


class CreateServiceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    vehicle_id: UUID


class NodeSchema(BaseModel):
    id: UUID
    type: Literal["block", "platform"]


class UpdatePathRequest(BaseModel):
    path: list[NodeSchema]


class TimetableEntrySchema(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int


class UpdateTimetableRequest(BaseModel):
    timetable: list[TimetableEntrySchema]


class ServiceResponse(BaseModel):
    id: UUID
    name: str
    vehicle_id: UUID
    path: list[NodeSchema]
    timetable: list[TimetableEntrySchema]

    @classmethod
    def from_domain(cls, service: Service) -> ServiceResponse:
        return cls(
            id=service.id,
            name=service.name,
            vehicle_id=service.vehicle_id,
            path=[NodeSchema(id=n.id, type=n.type.value) for n in service.path],
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
