from __future__ import annotations

from application.service.dto import RouteStop
from application.service.service import ServiceAppService
from domain.domain_service.conflict.model import (
    InsufficientChargeConflict,
    LowBatteryConflict,
)
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
    stops = [
        RouteStop(node_id=s.node_id, dwell_time=s.dwell_time) for s in request.stops
    ]
    result = await service_app_service.validate_route(
        request.vehicle_id,
        stops,
        request.start_time,
    )

    battery_conflicts: list[BatteryConflictSchema] = []
    for c in result.battery_conflicts:
        match c:
            case LowBatteryConflict():
                battery_conflicts.append(
                    BatteryConflictSchema(type="low_battery", service_id=c.service_id)
                )
            case InsufficientChargeConflict():
                battery_conflicts.append(
                    BatteryConflictSchema(
                        type="insufficient_charge", service_id=c.service_id
                    )
                )

    return ValidateRouteResponse(
        route=[n.id for n in result.route],
        battery_conflicts=battery_conflicts,
    )
