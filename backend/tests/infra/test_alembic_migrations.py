"""Verify Alembic migrations upgrade and downgrade cleanly."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from tests.pg_config import TEST_DATABASE_URL_SYNC

pytestmark = pytest.mark.postgres

ALEMBIC_INI = "alembic.ini"


def _alembic_config() -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL_SYNC)
    return cfg


@pytest.fixture(autouse=True)
def _clean_alembic():
    """Downgrade to base before and after each test."""
    cfg = _alembic_config()
    command.downgrade(cfg, "base")
    yield
    command.downgrade(cfg, "base")


class TestAlembicMigrations:
    def test_upgrade_to_head_creates_all_tables(self):
        cfg = _alembic_config()
        command.upgrade(cfg, "head")

        engine = create_engine(TEST_DATABASE_URL_SYNC)
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        engine.dispose()

        expected = {
            "stations",
            "platforms",
            "blocks",
            "vehicles",
            "services",
            "node_connections",
            "node_layouts",
            "alembic_version",
        }
        assert expected.issubset(table_names)

    def test_upgrade_seeds_data(self):
        cfg = _alembic_config()
        command.upgrade(cfg, "head")

        engine = create_engine(TEST_DATABASE_URL_SYNC)
        with engine.connect() as conn:
            stations = conn.execute(text("SELECT count(*) FROM stations")).scalar()
            blocks = conn.execute(text("SELECT count(*) FROM blocks")).scalar()
            vehicles = conn.execute(text("SELECT count(*) FROM vehicles")).scalar()
        engine.dispose()

        assert stations == 4
        assert blocks == 14
        assert vehicles == 3

    def test_downgrade_to_base_removes_tables(self):
        cfg = _alembic_config()
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")

        engine = create_engine(TEST_DATABASE_URL_SYNC)
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        engine.dispose()

        schema_tables = {
            "stations",
            "platforms",
            "blocks",
            "vehicles",
            "services",
            "node_connections",
            "node_layouts",
        }
        assert schema_tables.isdisjoint(table_names)
