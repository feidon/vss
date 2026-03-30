from abc import ABC, abstractmethod
from uuid import UUID

from backend.domain.block.model import Block
from backend.infra.block.repository import BlockRepository


class InMemoryBlockRepositoryImpl(BlockRepository):
    def __init__(self, blocks: list[Block]):
        self._blocks = {b.id: b for b in blocks}

    async def find_all(self) -> list[Block]:
        return list(self._blocks.values)
    
    async def find_by_id(self, id: UUID) -> Block:
        return self._blocks.get(id)
    
    async def save(self, block: Block) -> None:
        self._blocks[block.id] = block