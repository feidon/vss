from uuid import uuid7

import pytest
from application.block.service import BlockAppService
from domain.block.model import Block
from domain.error import DomainError

from tests.fakes.block_repo import InMemoryBlockRepository


class TestBlockAppService:
    @pytest.fixture
    def repo(self):
        return InMemoryBlockRepository()

    @pytest.fixture
    def service(self, repo):
        return BlockAppService(repo)

    async def _given_block(self, repo, **kwargs) -> Block:
        defaults = dict(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        defaults.update(kwargs)
        block = Block(**defaults)
        await repo.save(block)
        return block

    async def test_list_blocks(self, service, repo):
        await self._given_block(repo)
        await self._given_block(repo)
        result = await service.list_blocks()
        assert len(result) == 2

    async def test_update_block_traversal_time(self, service, repo):
        block = await self._given_block(repo, traversal_time_seconds=30)
        await service.update_block(block.id, traversal_time_seconds=60)
        updated = await repo.find_by_id(block.id)
        assert updated.traversal_time_seconds == 60

    async def test_update_block_rejects_invalid_time(self, service, repo):
        block = await self._given_block(repo)
        with pytest.raises(
            DomainError, match="traversal_time_seconds must be positive"
        ):
            await service.update_block(block.id, traversal_time_seconds=0)

    async def test_update_block_not_found(self, service):
        with pytest.raises(DomainError, match="not found"):
            await service.update_block(uuid7(), traversal_time_seconds=60)
