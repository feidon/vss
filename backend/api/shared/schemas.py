from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BlockNodeSchema(BaseModel):
    type: Literal["block"] = "block"
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int
    x: float = 0.0
    y: float = 0.0


class PlatformNodeSchema(BaseModel):
    type: Literal["platform"] = "platform"
    id: UUID
    name: str
    x: float = 0.0
    y: float = 0.0


class YardNodeSchema(BaseModel):
    type: Literal["yard"] = "yard"
    id: UUID
    name: str
    x: float = 0.0
    y: float = 0.0


NodeSchema = Annotated[
    BlockNodeSchema | PlatformNodeSchema | YardNodeSchema,
    Field(discriminator="type"),
]


class JunctionSchema(BaseModel):
    id: UUID
    x: float
    y: float


class EdgeSchema(BaseModel):
    id: UUID
    name: str
    from_id: UUID
    to_id: UUID


class TimetableEntrySchema(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int


# --- Error response schemas (for OpenAPI documentation) ---


class ErrorDetail(BaseModel):
    error_code: str
    context: dict[str, Any]


class ErrorResponse(BaseModel):
    detail: ErrorDetail


NOT_FOUND_RESPONSE = {
    404: {"model": ErrorResponse, "description": "Resource not found"},
}
VALIDATION_RESPONSE = {
    400: {"model": ErrorResponse, "description": "Validation error"},
}
CONFLICT_RESPONSE = {
    409: {"model": ErrorResponse, "description": "Scheduling conflicts detected"},
}
NO_ROUTE_RESPONSE = {
    422: {"model": ErrorResponse, "description": "No route between stops"},
}
