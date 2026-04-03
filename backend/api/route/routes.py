from __future__ import annotations

from application.service.service import ServiceAppService
from fastapi import APIRouter, Depends

from api.dependencies import get_service_app_service
from api.route.schemas import (
    BatteryConflictSchema,
    ValidateRouteRequest,
    ValidateRouteResponse,
)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/validate", response_model=ValidateRouteResponse)
async def validate_route(
    request: ValidateRouteRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    stops = request.to_route_stop()
    result = await service_app_service.validate_route(
        request.vehicle_id,
        stops,
        request.start_time,
    )

    return ValidateRouteResponse(
        route=[n.id for n in result.route],
        battery_conflicts=BatteryConflictSchema.from_validation_result(result),
    )
