from __future__ import annotations

from domain.network.model import NodeConnection
from domain.network.repository import ConnectionRepository


class InMemoryConnectionRepository(ConnectionRepository):
    def __init__(self, connections: frozenset[NodeConnection] | None = None) -> None:
        self._connections: frozenset[NodeConnection] = connections or frozenset()

    async def find_all(self) -> frozenset[NodeConnection]:
        return self._connections
