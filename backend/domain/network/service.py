from abc import ABC, abstractmethod
from uuid import UUID

from domain.network.model import Node, NodeConnection


class PathValidator(ABC):
    @abstractmethod
    async def get_connections(self) -> frozenset[NodeConnection]: ...

    @abstractmethod
    async def get_reachable_nodes(self, from_id: UUID) -> list[Node]: ...
