from __future__ import annotations

from abc import ABC, abstractmethod

from domain.network.model import NodeConnection


class ConnectionRepository(ABC):
    @abstractmethod
    async def find_all(self) -> frozenset[NodeConnection]: ...
