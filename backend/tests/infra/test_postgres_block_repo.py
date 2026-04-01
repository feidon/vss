from uuid import uuid7

import pytest

from domain.block.model import Block
from infra.postgres.block_repo import PostgresBlockRepository

pytestmark = pytest.mark.postgres


def make_block(**overrides) -> Block:
    defaults = {"id": uuid7(), "name": "B1", "group": 1, "traversal_time_seconds": 30}
    return Block(**{**defaults, **overrides})


class TestPostgresBlockRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresBlockRepository(pg_session)

    async def test_save_and_find_by_id(self, repo):
        block = make_block()
        await repo.save(block)
        found = await repo.find_by_id(block.id)
        assert found is not None
        assert found.id == block.id
        assert found.name == block.name
        assert found.group == block.group
        assert found.traversal_time_seconds == block.traversal_time_seconds

    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(uuid7()) is None

    async def test_find_all(self, repo):
        b1 = make_block(name="B1")
        b2 = make_block(name="B2")
        await repo.save(b1)
        await repo.save(b2)
        result = await repo.find_all()
        assert len(result) == 2

    async def test_find_by_ids(self, repo):
        b1 = make_block(name="B1")
        b2 = make_block(name="B2")
        b3 = make_block(name="B3")
        await repo.save(b1)
        await repo.save(b2)
        await repo.save(b3)
        result = await repo.find_by_ids({b1.id, b3.id})
        assert len(result) == 2
        found_ids = {b.id for b in result}
        assert found_ids == {b1.id, b3.id}

    async def test_find_by_ids_empty_set(self, repo):
        result = await repo.find_by_ids(set())
        assert result == []

    async def test_save_upsert_updates_existing(self, repo):
        block = make_block()
        await repo.save(block)
        block.update_traversal_time(60)
        await repo.save(block)
        found = await repo.find_by_id(block.id)
        assert found is not None
        assert found.traversal_time_seconds == 60
