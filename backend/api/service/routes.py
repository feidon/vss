from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from api.dependencies import get_service_app_service
from api.service.schemas import (
    CreateServiceRequest,
    ServiceResponse,
    UpdatePathRequest,
    UpdateTimetableRequest,
)
from application.service.errors import ConflictError
from application.service.service import ServiceAppService

router = APIRouter(prefix="/services", tags=["services"])


def _conflict_response(e: ConflictError) -> HTTPException:
    c = e.conflicts
    detail = {
        "message": str(e),
        "vehicle_conflicts": [
            {"vehicle_id": str(vc.vehicle_id), "service_a_id": str(vc.service_a_id),
             "service_b_id": str(vc.service_b_id), "reason": vc.reason}
            for vc in c.vehicle_conflicts
        ],
        "block_conflicts": [
            {"block_id": str(bc.block_id), "service_a_id": str(bc.service_a_id),
             "service_b_id": str(bc.service_b_id),
             "overlap_start": bc.overlap_start, "overlap_end": bc.overlap_end}
            for bc in c.block_conflicts
        ],
        "interlocking_conflicts": [
            {"group": ic.group, "block_a_id": str(ic.block_a_id),
             "block_b_id": str(ic.block_b_id), "service_a_id": str(ic.service_a_id),
             "service_b_id": str(ic.service_b_id),
             "overlap_start": ic.overlap_start, "overlap_end": ic.overlap_end}
            for ic in c.interlocking_conflicts
        ],
    }
    return HTTPException(status_code=409, detail=detail)


@router.post("", response_model=ServiceResponse, status_code=HTTP_201_CREATED)
async def create_service(
    request: CreateServiceRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    try:
        service = await service_app_service.create_service(
            name=request.name, vehicle_id=request.vehicle_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    blocks = await service_app_service.resolve_blocks([service])
    return ServiceResponse.from_domain(service, blocks)


@router.get("", response_model=list[ServiceResponse])
async def list_services(
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    services = await service_app_service.list_services()
    blocks = await service_app_service.resolve_blocks(services)
    return [ServiceResponse.from_domain(s, blocks) for s in services]


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: UUID,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    try:
        service = await service_app_service.get_service(service_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    blocks = await service_app_service.resolve_blocks([service])
    return ServiceResponse.from_domain(service, blocks)


@router.patch("/{service_id}/path", response_model=ServiceResponse)
async def update_path(
    service_id: UUID,
    request: UpdatePathRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    try:
        service = await service_app_service.update_service_path(service_id, request.to_nodes())
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    blocks = await service_app_service.resolve_blocks([service])
    return ServiceResponse.from_domain(service, blocks)


@router.patch("/{service_id}/timetable", response_model=ServiceResponse)
async def update_timetable(
    service_id: UUID,
    request: UpdateTimetableRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    entries = request.to_domains()
    try:
        service = await service_app_service.update_service_timetable(service_id, entries)
    except ConflictError as e:
        raise _conflict_response(e)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    blocks = await service_app_service.resolve_blocks([service])
    return ServiceResponse.from_domain(service, blocks)


@router.delete("/{service_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: UUID,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    await service_app_service.delete_service(service_id)
