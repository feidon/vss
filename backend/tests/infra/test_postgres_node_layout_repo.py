from uuid import uuid7

import pytest
from infra.postgres.node_layout_repo import PostgresNodeLayoutRepository
from infra.postgres.tables import node_layouts_table
from sqlalchemy.dialects.postgresql import insert

pytestmark = pytest.mark.postgres


class TestPostgresNodeLayoutRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresNodeLayoutRepository(pg_session)

    async def test_find_all_empty(self, repo):
        result = await repo.find_all()
        assert result == {}

    async def test_find_all_returns_seeded_data(self, repo, pg_session):
        node_id = uuid7()
        await pg_session.execute(
            insert(node_layouts_table).values(node_id=node_id, x=100.0, y=200.0)
        )
        await pg_session.commit()

        result = await repo.find_all()
        assert len(result) == 1
        assert result[node_id] == (100.0, 200.0)
