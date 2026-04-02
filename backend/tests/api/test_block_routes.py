from uuid import uuid7

import pytest
from infra.seed import BLOCK_ID_BY_NAME

pytestmark = pytest.mark.postgres


class TestBlockRoutes:
    async def test_list_blocks(self, client):
        resp = await client.get("/blocks")
        assert resp.status_code == 200
        assert len(resp.json()) == 14

    async def test_update_block(self, client):
        block_id = BLOCK_ID_BY_NAME["B1"]
        resp = await client.patch(
            f"/blocks/{block_id}", json={"traversal_time_seconds": 60}
        )
        assert resp.status_code == 200
        assert resp.json() == {"id": str(block_id)}

    async def test_update_block_invalid_time(self, client):
        block_id = BLOCK_ID_BY_NAME["B1"]
        resp = await client.patch(
            f"/blocks/{block_id}", json={"traversal_time_seconds": 0}
        )
        assert resp.status_code == 422

    async def test_update_block_not_found(self, client):
        resp = await client.patch(
            f"/blocks/{uuid7()}", json={"traversal_time_seconds": 60}
        )
        assert resp.status_code == 404
