from __future__ import annotations

from uuid import UUID

from domain.block.model import Block
from domain.block.repository import BlockRepository


class InMemoryBlockRepository(BlockRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Block] = {}

    async def find_all(self) -> list[Block]:
        return list(self._store.values())

    async def find_by_id(self, id: UUID) -> Block | None:
        return self._store.get(id)

    async def save(self, block: Block) -> None:
        self._store[block.id] = block
