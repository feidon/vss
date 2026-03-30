from abc import ABC, abstractmethod
from uuid import UUID

from backend.domain.block.model import Block


class BlockRepository(ABC):
    @abstractmethod
    async def find_all(self) -> list[Block]: ...
    
    @abstractmethod
    async def find_by_id(self, id: UUID) -> Block: ...
    
    @abstractmethod
    async def save(self, block: Block) -> None: ...