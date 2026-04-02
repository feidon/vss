from __future__ import annotations

from application.graph.service import GraphAppService
from application.service.dto import RouteStop
from application.service.service import ServiceAppService
from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from api.dependencies import get_graph_service, get_service_app_service
from api.service.schemas import (
    CreateServiceRequest,
    ServiceDetailResponse,
    ServiceIdResponse,
    ServiceResponse,
    UpdateRouteRequest,
)

router = APIRouter(prefix="/services", tags=["services"])


@router.post("", response_model=ServiceIdResponse, status_code=HTTP_201_CREATED)
async def create_service(
    request: CreateServiceRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    service = await service_app_service.create_service(
        name=request.name, vehicle_id=request.vehicle_id
    )
    return ServiceIdResponse(id=service.id)


@router.get("", response_model=list[ServiceResponse])
async def list_services(
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    services = await service_app_service.list_services()
    return [
        ServiceResponse(id=s.id, name=s.name, vehicle_id=s.vehicle_id) for s in services
    ]


@router.get("/{service_id}", response_model=ServiceDetailResponse)
async def get_service(
    service_id: int,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
    graph_service: GraphAppService = Depends(get_graph_service),
):
    service = await service_app_service.get_service(service_id)
    graph_data = await graph_service.get_graph()
    return ServiceDetailResponse.from_domain(service, graph_data)


@router.patch("/{service_id}/route", response_model=ServiceIdResponse)
async def update_route(
    service_id: int,
    request: UpdateRouteRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    stops = [
        RouteStop(node_id=s.node_id, dwell_time=s.dwell_time) for s in request.stops
    ]
    service = await service_app_service.update_service_route(
        service_id, stops, request.start_time
    )
    return ServiceIdResponse(id=service.id)


@router.delete("/{service_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    await service_app_service.delete_service(service_id)
