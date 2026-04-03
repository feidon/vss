from __future__ import annotations

from uuid import UUID

from application.service.dto import RouteStop, RouteValidationResult
from domain.domain_service.conflict.model import BatteryConflictType
from pydantic import BaseModel, Field

from api.service.schemas import RouteStopInput


class ValidateRouteRequest(BaseModel):
    vehicle_id: UUID
    stops: list[RouteStopInput] = Field(min_length=2)
    start_time: int

    def to_route_stop(self) -> list[RouteStop]:
        return [s.to_route_stop() for s in self.stops]


class BatteryConflictSchema(BaseModel):
    type: BatteryConflictType
    service_id: int

    @classmethod
    def from_validation_result(
        cls, result: RouteValidationResult
    ) -> list[BatteryConflictSchema]:
        return [
            BatteryConflictSchema(type=conflict.type, service_id=conflict.service_id)
            for conflict in result.battery_conflicts
        ]


class ValidateRouteResponse(BaseModel):
    route: list[UUID]
    battery_conflicts: list[BatteryConflictSchema]
