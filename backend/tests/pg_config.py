import os

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://vss:vss@localhost:5432/vss_test"
)
TEST_DATABASE_URL_SYNC = os.getenv(
    "TEST_DATABASE_URL_SYNC", "postgresql+psycopg://vss:vss@localhost:5432/vss_test"
)
