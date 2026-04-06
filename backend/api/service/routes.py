from __future__ import annotations

from application.graph.service import GraphAppService
from application.service.service import ServiceAppService
from application.vehicle.service import VehicleAppService
from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from api.dependencies import (
    get_graph_service,
    get_service_app_service,
    get_vehicle_service,
)
from api.service.schemas import (
    CreateServiceRequest,
    ServiceDetailResponse,
    ServiceIdResponse,
    ServiceResponse,
    UpdateRouteRequest,
)
from api.shared.schemas import (
    CONFLICT_RESPONSE,
    NO_ROUTE_RESPONSE,
    NOT_FOUND_RESPONSE,
    VALIDATION_RESPONSE,
)

router = APIRouter(prefix="/services", tags=["services"])


@router.post(
    "",
    response_model=ServiceIdResponse,
    status_code=HTTP_201_CREATED,
    responses={**VALIDATION_RESPONSE},
)
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
    vehicle_app_service: VehicleAppService = Depends(get_vehicle_service),
    graph_service: GraphAppService = Depends(get_graph_service),
):
    services = await service_app_service.list_services()
    vehicles = await vehicle_app_service.list_vehicles()
    node_names = await graph_service.get_node_names()

    vehicles_map = {v.id: v for v in vehicles}

    return [
        ServiceResponse.from_domain(s, vehicles_map[s.vehicle_id], node_names)
        for s in services
    ]


@router.get(
    "/{service_id}",
    response_model=ServiceDetailResponse,
    responses={**NOT_FOUND_RESPONSE},
)
async def get_service(
    service_id: int,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
    graph_service: GraphAppService = Depends(get_graph_service),
):
    service = await service_app_service.get_service(service_id)
    graph_data = await graph_service.get_graph()
    return ServiceDetailResponse.from_domain(service, graph_data)


@router.patch(
    "/{service_id}/route",
    response_model=ServiceIdResponse,
    responses={
        **NOT_FOUND_RESPONSE,
        **VALIDATION_RESPONSE,
        **CONFLICT_RESPONSE,
        **NO_ROUTE_RESPONSE,
    },
)
async def update_route(
    service_id: int,
    request: UpdateRouteRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    stops = [s.to_route_stop() for s in request.stops]
    service = await service_app_service.update_service_route(
        service_id, stops, request.start_time
    )
    return ServiceIdResponse(id=service.id)


@router.delete(
    "/{service_id}", status_code=HTTP_204_NO_CONTENT, responses={**NOT_FOUND_RESPONSE}
)
async def delete_service(
    service_id: int,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    await service_app_service.delete_service(service_id)
