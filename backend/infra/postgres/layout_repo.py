from __future__ import annotations

from uuid import UUID

from domain.read_model.layout import LayoutData, LayoutRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.postgres.tables import junction_blocks_table, node_layouts_table


class PostgresLayoutRepository(LayoutRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> LayoutData:
        layout_result = await self._session.execute(select(node_layouts_table))
        positions: dict[UUID, tuple[float, float]] = {
            row["node_id"]: (row["x"], row["y"]) for row in layout_result.mappings()
        }

        jb_result = await self._session.execute(select(junction_blocks_table))
        junction_blocks: dict[tuple[UUID, UUID], UUID] = {
            (row["from_block_id"], row["to_block_id"]): row["junction_id"]
            for row in jb_result.mappings()
        }

        return LayoutData(positions=positions, junction_blocks=junction_blocks)
