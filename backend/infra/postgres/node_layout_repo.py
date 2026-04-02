from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.network.node_layout_repository import NodeLayoutRepository
from infra.postgres.tables import node_layouts_table


class PostgresNodeLayoutRepository(NodeLayoutRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> dict[UUID, tuple[float, float]]:
        result = await self._session.execute(select(node_layouts_table))
        return {row["node_id"]: (row["x"], row["y"]) for row in result.mappings()}
