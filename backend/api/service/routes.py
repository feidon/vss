from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from api.service.schemas import (
    CreateServiceRequest,
    ServiceResponse,
    UpdatePathRequest,
    UpdateTimetableRequest,
)
from application.service.service import ServiceApplicationService
from domain.network.model import Node, NodeType
from domain.service.model import TimetableEntry


def create_service_router(service_service: ServiceApplicationService) -> APIRouter:
    router = APIRouter(prefix="/services", tags=["services"])

    @router.post("", response_model=ServiceResponse, status_code=HTTP_201_CREATED)
    async def create_service(request: CreateServiceRequest):
        try:
            service = await service_service.create_service(
                name=request.name, vehicle_id=request.vehicle_id
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return ServiceResponse.from_domain(service)

    @router.get("", response_model=list[ServiceResponse])
    async def list_services():
        services = await service_service.list_services()
        return [ServiceResponse.from_domain(s) for s in services]

    @router.get("/{service_id}", response_model=ServiceResponse)
    async def get_service(service_id: UUID):
        try:
            service = await service_service.get_service(service_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        return ServiceResponse.from_domain(service)

    @router.patch("/{service_id}/path", response_model=ServiceResponse)
    async def update_path(service_id: UUID, request: UpdatePathRequest):
        path = [
            Node(id=n.id, type=NodeType(n.type)) for n in request.path
        ]
        try:
            service = await service_service.update_service_path(service_id, path)
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        return ServiceResponse.from_domain(service)

    @router.patch("/{service_id}/timetable", response_model=ServiceResponse)
    async def update_timetable(service_id: UUID, request: UpdateTimetableRequest):
        entries = [
            TimetableEntry(
                order=e.order,
                node_id=e.node_id,
                arrival=e.arrival,
                departure=e.departure,
            )
            for e in request.timetable
        ]
        try:
            service = await service_service.update_service_timetable(service_id, entries)
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        return ServiceResponse.from_domain(service)

    @router.delete("/{service_id}", status_code=HTTP_204_NO_CONTENT)
    async def delete_service(service_id: UUID):
        await service_service.delete_service(service_id)

    return router
