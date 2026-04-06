from __future__ import annotations

from uuid import UUID

from application.schedule.dto import GenerateScheduleResponse
from pydantic import BaseModel, Field


class GenerateScheduleRequestSchema(BaseModel):
    interval_seconds: int = Field(gt=0)
    start_time: int
    end_time: int
    dwell_time_seconds: int = Field(gt=0)


class GenerateScheduleResponseSchema(BaseModel):
    services_created: int
    vehicles_used: list[UUID]
    cycle_time_seconds: int

    @classmethod
    def from_dto(cls, dto: GenerateScheduleResponse) -> GenerateScheduleResponseSchema:
        return cls(
            services_created=dto.services_created,
            vehicles_used=dto.vehicles_used,
            cycle_time_seconds=dto.cycle_time_seconds,
        )
