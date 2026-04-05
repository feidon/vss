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
    message: str
    context: dict[str, Any]


class ErrorResponse(BaseModel):
    detail: ErrorDetail


class VehicleConflictSchema(BaseModel):
    vehicle_id: str
    service_a_id: int
    service_b_id: int
    reason: str


class BlockConflictSchema(BaseModel):
    block_id: str
    service_a_id: int
    service_b_id: int
    overlap_start: int
    overlap_end: int


class InterlockingConflictSchema(BaseModel):
    group: int
    block_a_id: str
    block_b_id: str
    service_a_id: int
    service_b_id: int
    overlap_start: int
    overlap_end: int


class ConflictBatterySchema(BaseModel):
    type: str
    service_id: int


class ConflictDetail(BaseModel):
    message: str
    vehicle_conflicts: list[VehicleConflictSchema]
    block_conflicts: list[BlockConflictSchema]
    interlocking_conflicts: list[InterlockingConflictSchema]
    battery_conflicts: list[ConflictBatterySchema]


class ConflictDetailResponse(BaseModel):
    detail: ConflictDetail


NOT_FOUND_RESPONSE = {
    404: {"model": ErrorResponse, "description": "Resource not found"},
}
VALIDATION_RESPONSE = {
    400: {"model": ErrorResponse, "description": "Validation error"},
}
CONFLICT_RESPONSE = {
    409: {
        "model": ConflictDetailResponse,
        "description": "Scheduling conflicts detected",
    },
}
NO_ROUTE_RESPONSE = {
    422: {"model": ErrorResponse, "description": "No route between stops"},
}
