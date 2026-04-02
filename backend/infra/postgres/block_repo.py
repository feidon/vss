from __future__ import annotations

from uuid import UUID

from domain.block.model import Block
from domain.block.repository import BlockRepository
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from infra.postgres.tables import blocks_table


class PostgresBlockRepository(BlockRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[Block]:
        result = await self._session.execute(select(blocks_table))
        return [self._to_entity(row) for row in result.mappings()]

    async def find_by_id(self, id: UUID) -> Block | None:
        result = await self._session.execute(
            select(blocks_table).where(blocks_table.c.id == id)
        )
        row = result.mappings().first()
        return self._to_entity(row) if row else None

    async def find_by_ids(self, ids: set[UUID]) -> list[Block]:
        if not ids:
            return []
        result = await self._session.execute(
            select(blocks_table).where(blocks_table.c.id.in_(ids))
        )
        return [self._to_entity(row) for row in result.mappings()]

    async def save(self, block: Block) -> None:
        values = self._to_table(block)
        update_values = {k: v for k, v in values.items() if k != "id"}
        stmt = (
            insert(blocks_table)
            .values(**values)
            .on_conflict_do_update(index_elements=["id"], set_=update_values)
        )
        await self._session.execute(stmt)
        await self._session.commit()

    @staticmethod
    def _to_entity(row) -> Block:
        return Block(
            id=row["id"],
            name=row["name"],
            group=row["group"],
            traversal_time_seconds=row["traversal_time_seconds"],
        )

    @staticmethod
    def _to_table(block: Block) -> dict:
        return {
            "id": block.id,
            "name": block.name,
            "group": block.group,
            "traversal_time_seconds": block.traversal_time_seconds,
        }
