from __future__ import annotations

from uuid import UUID

from domain.block.model import Block
from domain.block.repository import BlockRepository


class BlockAppService:
    def __init__(self, block_repo: BlockRepository) -> None:
        self._block_repo = block_repo

    async def get_block(self, id: UUID) -> Block:
        block = await self._block_repo.find_by_id(id)
        if block is None:
            raise ValueError(f"Block {id} not found")
        return block

    async def list_blocks(self) -> list[Block]:
        return await self._block_repo.find_all()

    async def update_block(self, id: UUID, traversal_time_seconds: int) -> Block:
        block = await self._block_repo.find_by_id(id)
        if block is None:
            raise ValueError(f"Block {id} not found")
        block.update_traversal_time(traversal_time_seconds)
        await self._block_repo.save(block)
        return block
