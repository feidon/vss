from __future__ import annotations

from domain.vehicle.repository import VehicleRepository
from fastapi import APIRouter, Depends

from api.dependencies import get_vehicle_repo
from api.vehicle.schemas import VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleResponse])
async def list_vehicles(
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
):
    vehicles = await vehicle_repo.find_all()
    return [VehicleResponse(id=v.id, name=v.name) for v in vehicles]
