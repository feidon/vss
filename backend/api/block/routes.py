from uuid import UUID

from fastapi import APIRouter, HTTPException

from backend.api.block.schemas import BlockResponse, UpdateBlockRequest
from backend.application.block.service import BlockApplicationService


def create_block_router(block_service: BlockApplicationService) -> APIRouter:
    router = APIRouter(prefix="/blocks", tags=["blocks"])

    @router.get("", response_model=list[BlockResponse])
    async def list_blocks():
        blocks = await block_service.list_blocks()
        return [BlockResponse._from(b) for b in blocks]

    @router.get("/{block_id}", response_model=BlockResponse)
    async def get_block(block_id: UUID):
        try:
            block = await block_service.get_block(block_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Block {block_id} not found")
        return BlockResponse._from(block)

    @router.patch("/{block_id}", response_model=BlockResponse)
    async def update_block(block_id: UUID, request: UpdateBlockRequest):
        try:
            block = await block_service.update_block(
                block_id, traversal_time_seconds=request.traversal_time_seconds
            )
        except ValueError as e:
            if "not found" in str(e):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        return BlockResponse._from(block)

    return router