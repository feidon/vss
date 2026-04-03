from __future__ import annotations

from application.vehicle.service import VehicleAppService
from fastapi import APIRouter, Depends

from api.dependencies import get_vehicle_service
from api.vehicle.schemas import VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleResponse])
async def list_vehicles(
    vehicle_app_service: VehicleAppService = Depends(get_vehicle_service),
):
    vehicles = await vehicle_app_service.list_vehicles()
    return [VehicleResponse(id=v.id, name=v.name) for v in vehicles]
