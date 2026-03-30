from uuid import uuid7

import pytest

from domain.block.model import Block
from infra.memory.block_repo import InMemoryBlockRepository


def make_block() -> Block:
    return Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)


class TestInMemoryBlockRepository:
    @pytest.fixture
    def repo(self):
        return InMemoryBlockRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repo):
        block = make_block()
        await repo.save(block)
        found = await repo.find_by_id(block.id)
        assert found == block

    @pytest.mark.asyncio
    async def test_find_by_id_returns_none(self, repo):
        assert await repo.find_by_id(uuid7()) is None

    @pytest.mark.asyncio
    async def test_find_all(self, repo):
        b1, b2 = make_block(), make_block()
        await repo.save(b1)
        await repo.save(b2)
        result = await repo.find_all()
        assert len(result) == 2
