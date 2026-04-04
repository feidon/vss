## Why

The current `node_layouts` seed data uses placeholder coordinates that don't match the intended track map geometry. The frontend needs accurate x/y positions to render the network diagram correctly — platforms at station boundaries, blocks along routes, and the yard at the far end.

## What Changes

- Update the `create_node_layouts()` function in `infra/seed.py` with corrected x/y coordinates for all 21 nodes (6 platforms, 14 blocks, 1 yard)
- Create an Alembic migration to update the `node_layouts` rows in the database with the new coordinates

## Capabilities

### New Capabilities

_(none — this is a data correction, not a new capability)_

### Modified Capabilities

_(none — no spec-level behavior changes, only seed data values)_

## Impact

- **`infra/seed.py`**: `create_node_layouts()` return values change
- **`infra/postgres/alembic/`**: New migration to UPDATE existing `node_layouts` rows
- **`tests/`**: Any snapshot/assertion tests that hardcode layout coordinates will need updating
- **Frontend**: Track map rendering will shift to the new geometry (desired outcome)
