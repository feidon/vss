from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.network.model import NodeConnection
from domain.network.repository import ConnectionRepository
from infra.postgres.tables import node_connections_table


class PostgresConnectionRepository(ConnectionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> frozenset[NodeConnection]:
        result = await self._session.execute(select(node_connections_table))
        return frozenset(self._to_entity(row) for row in result.mappings())

    @staticmethod
    def _to_entity(row) -> NodeConnection:
        return NodeConnection(
            from_id=row["from_id"],
            to_id=row["to_id"],
        )
