## 1. Update seed data

- [x] 1.1 Update `create_node_layouts()` in `infra/seed.py` with the new x/y coordinates for all 21 nodes
- [x] 1.2 Verify `tests/helpers/seed.py` uses `create_node_layouts()` (no hardcoded coordinates to update)

## 2. Alembic migration

- [x] 2.1 Create a new Alembic data migration that UPDATEs `node_layouts` rows with the new coordinates (lookup node IDs by name via blocks/platforms/stations tables)

## 3. Verify

- [x] 3.1 Run unit tests (`uv run pytest`) to confirm nothing breaks
- [x] 3.2 Run PostgreSQL integration tests (`uv run pytest -m postgres`) to confirm migration applies correctly
