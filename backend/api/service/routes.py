from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from api.dependencies import get_graph_service, get_service_app_service
from api.service.schemas import (
    CreateServiceRequest,
    ServiceResponse,
    UpdateRouteRequest,
)
from application.graph.service import GraphAppService, GraphData
from application.service.errors import ConflictError
from application.service.service import RouteStop, ServiceAppService
from domain.service.model import Service

router = APIRouter(prefix="/services", tags=["services"])


def _to_response(
    graph: GraphData, services: list[Service]
) -> list[ServiceResponse]:
    blocks = {b.id: b for b in graph.blocks}
    platforms = {p.id: p for p in graph.all_platforms}
    yard = graph.yard
    return [
        ServiceResponse.from_domain(
            s,
            blocks,
            platforms,
            yard.id if yard else None,
            yard.name if yard else "Y",
        )
        for s in services
    ]


def _conflict_response(e: ConflictError) -> HTTPException:
    c = e.conflicts
    detail = {
        "message": str(e),
        "vehicle_conflicts": [
            {"vehicle_id": str(vc.vehicle_id), "service_a_id": vc.service_a_id,
             "service_b_id": vc.service_b_id, "reason": vc.reason}
            for vc in c.vehicle_conflicts
        ],
        "block_conflicts": [
            {"block_id": str(bc.block_id), "service_a_id": bc.service_a_id,
             "service_b_id": bc.service_b_id,
             "overlap_start": bc.overlap_start, "overlap_end": bc.overlap_end}
            for bc in c.block_conflicts
        ],
        "interlocking_conflicts": [
            {"group": ic.group, "block_a_id": str(ic.block_a_id),
             "block_b_id": str(ic.block_b_id), "service_a_id": ic.service_a_id,
             "service_b_id": ic.service_b_id,
             "overlap_start": ic.overlap_start, "overlap_end": ic.overlap_end}
            for ic in c.interlocking_conflicts
        ],
    }
    return HTTPException(status_code=409, detail=detail)


@router.post("", response_model=ServiceResponse, status_code=HTTP_201_CREATED)
async def create_service(
    request: CreateServiceRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
    graph_service: GraphAppService = Depends(get_graph_service),
):
    try:
        service = await service_app_service.create_service(
            name=request.name, vehicle_id=request.vehicle_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    graph = await graph_service.get_graph()
    return _to_response(graph, [service])[0]


@router.get("", response_model=list[ServiceResponse])
async def list_services(
    service_app_service: ServiceAppService = Depends(get_service_app_service),
    graph_service: GraphAppService = Depends(get_graph_service),
):
    services = await service_app_service.list_services()
    graph = await graph_service.get_graph()
    return _to_response(graph, services)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
    graph_service: GraphAppService = Depends(get_graph_service),
):
    try:
        service = await service_app_service.get_service(service_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    graph = await graph_service.get_graph()
    return _to_response(graph, [service])[0]


@router.patch("/{service_id}/route", response_model=ServiceResponse)
async def update_route(
    service_id: int,
    request: UpdateRouteRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
    graph_service: GraphAppService = Depends(get_graph_service),
):
    stops = [
        RouteStop(platform_id=s.platform_id, dwell_time=s.dwell_time)
        for s in request.stops
    ]
    try:
        service = await service_app_service.update_service_route(
            service_id, stops, request.start_time
        )
    except ConflictError as e:
        raise _conflict_response(e)
    except ValueError as e:
        if str(e).startswith(f"Service {service_id}"):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    graph = await graph_service.get_graph()
    return _to_response(graph, [service])[0]


@router.delete("/{service_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    await service_app_service.delete_service(service_id)
