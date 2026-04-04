from uuid import uuid7

import pytest
from infra.postgres.layout_repo import PostgresLayoutRepository
from infra.postgres.tables import junction_blocks_table, node_layouts_table
from sqlalchemy.dialects.postgresql import insert

pytestmark = pytest.mark.postgres


class TestPostgresLayoutRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresLayoutRepository(pg_session)

    async def test_find_all_empty(self, repo):
        result = await repo.find_all()
        assert result.positions == {}
        assert result.junction_blocks == {}

    async def test_find_all_returns_positions(self, repo, pg_session):
        node_id = uuid7()
        await pg_session.execute(
            insert(node_layouts_table).values(node_id=node_id, x=100.0, y=200.0)
        )
        await pg_session.commit()

        result = await repo.find_all()
        assert result.positions[node_id] == (100.0, 200.0)

    async def test_find_all_returns_junction_blocks(self, repo, pg_session):
        junction_id = uuid7()
        block_a = uuid7()
        block_b = uuid7()

        await pg_session.execute(
            insert(node_layouts_table).values(node_id=junction_id, x=1.0, y=2.0)
        )
        await pg_session.execute(
            insert(junction_blocks_table).values(
                from_block_id=block_a, to_block_id=block_b, junction_id=junction_id
            )
        )
        await pg_session.commit()

        result = await repo.find_all()
        assert result.junction_blocks[(block_a, block_b)] == junction_id
