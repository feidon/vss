from uuid import uuid7

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_block_repo
from domain.block.model import Block
from infra.memory.block_repo import InMemoryBlockRepository
from main import app


@pytest.fixture
def block_repo():
    return InMemoryBlockRepository()


@pytest.fixture
def client(block_repo):
    app.dependency_overrides[get_block_repo] = lambda: block_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


async def seed_block(repo, **kwargs) -> Block:
    defaults = dict(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
    defaults.update(kwargs)
    block = Block(**defaults)
    await repo.save(block)
    return block


class TestBlockRoutes:
    def test_list_blocks_empty(self, client):
        resp = client.get("/blocks")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_blocks(self, client, block_repo):
        await seed_block(block_repo)
        await seed_block(block_repo, name="B2")
        resp = client.get("/blocks")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_update_block(self, client, block_repo):
        block = await seed_block(block_repo)
        resp = client.patch(f"/blocks/{block.id}", json={"traversal_time_seconds": 60})
        assert resp.status_code == 200
        assert resp.json() == {"id": str(block.id)}

    @pytest.mark.asyncio
    async def test_update_block_invalid_time(self, client, block_repo):
        block = await seed_block(block_repo)
        resp = client.patch(f"/blocks/{block.id}", json={"traversal_time_seconds": 0})
        assert resp.status_code == 422

    def test_update_block_not_found(self, client):
        resp = client.patch(f"/blocks/{uuid7()}", json={"traversal_time_seconds": 60})
        assert resp.status_code == 404
