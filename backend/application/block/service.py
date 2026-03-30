from uuid import UUID

from backend.domain.block.model import Block
from backend.infra.block.repository import BlockRepository


class BlockApplicationService:
    def __init__(self, block_repo: BlockRepository) -> None:
        self._block_repo = block_repo
        
    async def updateTraversalTime(self, id: UUID, traversal_time_seconds: int) -> None:
        block: Block = self._block_repo.find_by_id(id=id)
        if block is None:
            raise ValueError(f"Block {id} not found")
        
        block.update_traversal_time(traversal_time_seconds=traversal_time_seconds)
        self._block_repo.save(block=block)
