from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from api.service.schemas import RouteStopInput


class ValidateRouteRequest(BaseModel):
    vehicle_id: UUID
    stops: list[RouteStopInput] = Field(min_length=2)
    start_time: int


class BatteryConflictSchema(BaseModel):
    type: str  # "low_battery" or "insufficient_charge"
    service_id: int


class ValidateRouteResponse(BaseModel):
    route: list[UUID]
    battery_conflicts: list[BatteryConflictSchema]
