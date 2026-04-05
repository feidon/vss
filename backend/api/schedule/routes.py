from __future__ import annotations

from application.schedule.dto import GenerateScheduleRequest
from application.schedule.schedule_service import ScheduleAppService
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from api.dependencies import get_schedule_app_service
from api.schedule.schemas import (
    GenerateScheduleRequestSchema,
    GenerateScheduleResponseSchema,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post(
    "/generate",
    response_model=GenerateScheduleResponseSchema,
    status_code=HTTP_200_OK,
)
async def generate_schedule(
    body: GenerateScheduleRequestSchema,
    service: ScheduleAppService = Depends(get_schedule_app_service),
) -> GenerateScheduleResponseSchema:
    dto = GenerateScheduleRequest(
        interval_seconds=body.interval_seconds,
        start_time=body.start_time,
        end_time=body.end_time,
        dwell_time_seconds=body.dwell_time_seconds,
    )
    result = await service.generate_schedule(dto)
    return GenerateScheduleResponseSchema.from_dto(result)
