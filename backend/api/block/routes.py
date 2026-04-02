from __future__ import annotations

from uuid import UUID

from application.block.service import BlockAppService
from fastapi import APIRouter, Depends

from api.block.schemas import BlockIdResponse, BlockResponse, UpdateBlockRequest
from api.dependencies import get_block_service

router = APIRouter(prefix="/blocks", tags=["blocks"])


@router.get("", response_model=list[BlockResponse])
async def list_blocks(block_service: BlockAppService = Depends(get_block_service)):
    blocks = await block_service.list_blocks()
    return [BlockResponse.from_domain(b) for b in blocks]


@router.patch("/{block_id}", response_model=BlockIdResponse)
async def update_block(
    block_id: UUID,
    request: UpdateBlockRequest,
    block_service: BlockAppService = Depends(get_block_service),
):
    await block_service.update_block(block_id, request.traversal_time_seconds)
    return BlockIdResponse(id=block_id)
