from uuid import uuid7

import pytest

from domain.network.model import NodeConnection
from infra.postgres.connection_repo import PostgresConnectionRepository
from infra.postgres.tables import node_connections_table
from sqlalchemy.dialects.postgresql import insert

pytestmark = pytest.mark.postgres


class TestPostgresConnectionRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresConnectionRepository(pg_session)

    async def test_find_all_returns_frozenset(self, repo, pg_session):
        id_a, id_b, id_c = uuid7(), uuid7(), uuid7()
        await pg_session.execute(
            insert(node_connections_table).values([
                {"from_id": id_a, "to_id": id_b},
                {"from_id": id_b, "to_id": id_c},
            ])
        )
        await pg_session.commit()

        result = await repo.find_all()
        assert isinstance(result, frozenset)
        assert len(result) == 2
        assert NodeConnection(from_id=id_a, to_id=id_b) in result
        assert NodeConnection(from_id=id_b, to_id=id_c) in result

    async def test_find_all_empty(self, repo):
        result = await repo.find_all()
        assert result == frozenset()
