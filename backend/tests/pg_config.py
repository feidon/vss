"""Connection URLs for postgres integration tests.

Populated at runtime by the testcontainers session fixture in conftest.py.
"""

# Set by conftest._pg_container fixture
TEST_DATABASE_URL: str = ""
TEST_DATABASE_URL_SYNC: str = ""
