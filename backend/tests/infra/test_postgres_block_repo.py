from uuid import uuid7

import pytest
from domain.block.model import Block
from infra.postgres.block_repo import PostgresBlockRepository
from infra.postgres.tables import blocks_table
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.postgres


def make_block(**overrides) -> Block:
    defaults = {"id": uuid7(), "name": "B1", "group": 1, "traversal_time_seconds": 30}
    return Block(**{**defaults, **overrides})


async def insert_block(session: AsyncSession, block: Block) -> None:
    await session.execute(
        blocks_table.insert().values(
            id=block.id,
            name=block.name,
            group=block.group,
            traversal_time_seconds=block.traversal_time_seconds,
        )
    )
    await session.commit()


class TestPostgresBlockRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresBlockRepository(pg_session)

    async def test_update_and_find_by_id(self, repo, pg_session):
        block = make_block()
        await insert_block(pg_session, block)
        block.update_traversal_time(60)
        await repo.update(block)
        found = await repo.find_by_id(block.id)
        assert found is not None
        assert found.id == block.id
        assert found.name == block.name
        assert found.group == block.group
        assert found.traversal_time_seconds == 60

    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(uuid7()) is None

    async def test_find_all(self, repo, pg_session):
        b1 = make_block(name="B1")
        b2 = make_block(name="B2")
        await insert_block(pg_session, b1)
        await insert_block(pg_session, b2)
        result = await repo.find_all()
        assert len(result) == 2

    async def test_find_by_ids(self, repo, pg_session):
        b1 = make_block(name="B1")
        b2 = make_block(name="B2")
        b3 = make_block(name="B3")
        await insert_block(pg_session, b1)
        await insert_block(pg_session, b2)
        await insert_block(pg_session, b3)
        result = await repo.find_by_ids({b1.id, b3.id})
        assert len(result) == 2
        found_ids = {b.id for b in result}
        assert found_ids == {b1.id, b3.id}

    async def test_find_by_ids_empty_set(self, repo):
        result = await repo.find_by_ids(set())
        assert result == []

    async def test_update_existing_block(self, repo, pg_session):
        block = make_block()
        await insert_block(pg_session, block)
        block.update_traversal_time(60)
        await repo.update(block)
        found = await repo.find_by_id(block.id)
        assert found is not None
        assert found.traversal_time_seconds == 60

    async def test_update_nonexistent_block_raises(self, repo):
        block = make_block()
        with pytest.raises(ValueError, match="update affected 0 rows"):
            await repo.update(block)
