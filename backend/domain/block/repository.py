from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.block.model import Block


class BlockRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Block]: ...

    @abstractmethod
    async def find_by_id(self, id: UUID) -> Block | None: ...

    @abstractmethod
    async def find_by_ids(self, ids: set[UUID]) -> list[Block]: ...

    @abstractmethod
    async def update(self, block: Block) -> None: ...
