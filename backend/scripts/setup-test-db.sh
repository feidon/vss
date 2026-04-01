#!/bin/bash
# Run with: sudo bash scripts/setup-test-db.sh
# Starts PostgreSQL and creates the test database.
set -e

cd "$(dirname "$0")/../.."

# Start PostgreSQL container
docker compose up -d postgres

# Wait for PostgreSQL to be fully ready (database initialized, not just process up)
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker compose exec -T postgres psql -U vss -d vss -c "SELECT 1" > /dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: PostgreSQL did not become ready in 30 seconds."
        exit 1
    fi
    sleep 1
done

# Create test database if it doesn't exist
docker compose exec -T postgres \
    psql -U vss -d vss -tc "SELECT 1 FROM pg_database WHERE datname = 'vss_test'" | grep -q 1 || \
    docker compose exec -T postgres \
    psql -U vss -d vss -c "CREATE DATABASE vss_test OWNER vss"

echo "Test database 'vss_test' is ready."
echo ""
echo "Run postgres tests with:"
echo "  uv run pytest -m postgres -v"
echo ""
echo "Smoke test with:"
echo "  DB=postgres uv run uvicorn main:app --reload"
