## Context

The `node_layouts` table stores x/y coordinates for rendering the track map in the frontend. The current seed values in `create_node_layouts()` are placeholders that don't reflect the intended visual layout. The correct geometry has been specified by the user with exact pixel positions for all 21 nodes.

## Goals / Non-Goals

**Goals:**
- Update `create_node_layouts()` in `infra/seed.py` with the correct coordinates
- Create an Alembic migration to apply the new coordinates to existing databases

**Non-Goals:**
- No schema changes (the `node_layouts` table structure is unchanged)
- No domain model changes
- No API changes

## Decisions

**1. Update via Alembic data migration (not schema migration)**

The table structure doesn't change — only the row values. Use `op.execute()` with UPDATE statements in a new Alembic revision. This keeps existing databases in sync without requiring a full re-seed.

Alternative considered: DROP + re-INSERT all rows. Rejected because UPDATE is simpler and avoids FK issues if any future table references `node_layouts.node_id`.

**2. Keep `create_node_layouts()` as the source of truth for fresh installs**

Update the function in `infra/seed.py` so that `create_node_layouts()` returns the new coordinates. Fresh databases (and test seeding) will get the correct values automatically.

**3. Match node IDs via name lookup in migration**

The migration must map node names to UUIDs. Use a subquery against `blocks`, `platforms`, and `stations` tables to resolve names to IDs, then update `node_layouts` accordingly.

## Risks / Trade-offs

**[Risk] UUID lookup in migration** → The migration needs to join against blocks/platforms/stations to find IDs by name. This is safe because seed data names are stable and unique.

**[Risk] Test seed data divergence** → `tests/helpers/seed.py` also seeds node layouts. Ensure it calls the same `create_node_layouts()` function so values stay consistent.
