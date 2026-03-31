from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BlockNodeSchema(BaseModel):
    type: Literal["block"] = "block"
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int


class PlatformNodeSchema(BaseModel):
    type: Literal["platform"] = "platform"
    id: UUID
    name: str


class YardNodeSchema(BaseModel):
    type: Literal["yard"] = "yard"
    id: UUID
    name: str


NodeSchema = Annotated[
    BlockNodeSchema | PlatformNodeSchema | YardNodeSchema,
    Field(discriminator="type"),
]


class TimetableEntrySchema(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int
