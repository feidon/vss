from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_graph_service
from api.graph.schemas import GraphResponse
from application.graph.service import GraphAppService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
async def get_graph(
    graph_service: GraphAppService = Depends(get_graph_service),
):
    data = await graph_service.get_graph()
    return GraphResponse.from_graph_data(data)
