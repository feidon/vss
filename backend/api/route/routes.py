from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_service_app_service
from api.route.schemas import BatteryConflictSchema, ValidateRouteRequest, ValidateRouteResponse
from application.service.dto import RouteStop
from application.service.service import ServiceAppService
from domain.domain_service.conflict.model import InsufficientChargeConflict, LowBatteryConflict

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/validate", response_model=ValidateRouteResponse)
async def validate_route(
    request: ValidateRouteRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    stops = [RouteStop(node_id=s.node_id, dwell_time=s.dwell_time) for s in request.stops]
    try:
        result = await service_app_service.validate_route(
            request.vehicle_id, stops, request.start_time,
        )
    except ValueError as e:
        if "No route" in str(e):
            raise HTTPException(status_code=422, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    battery_conflicts: list[BatteryConflictSchema] = []
    for c in result.battery_conflicts:
        match c:
            case LowBatteryConflict():
                battery_conflicts.append(BatteryConflictSchema(type="low_battery", service_id=c.service_id))
            case InsufficientChargeConflict():
                battery_conflicts.append(BatteryConflictSchema(type="insufficient_charge", service_id=c.service_id))

    return ValidateRouteResponse(
        path=[n.id for n in result.path],
        battery_conflicts=battery_conflicts,
    )
