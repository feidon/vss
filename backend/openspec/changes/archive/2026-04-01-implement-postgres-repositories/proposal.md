## Why

The infra layer currently has empty PostgreSQL repository stubs while the application runs entirely on in-memory repositories. To persist data across restarts and enable the `DB=postgres` mode already wired in `api/dependencies.py`, all five repositories need working PostgreSQL implementations using the SQLAlchemy Core + manual mapper pattern.

## What Changes

- Implement `PostgresBlockRepository` using SQLAlchemy Core queries against `blocks_table` with `_to_entity()` / `_to_table()` mappers
- Implement `PostgresVehicleRepository` against `vehicles_table`
- Rewrite `PostgresStationRepository` (currently broken — uses ORM-style `select(Station)`) against `stations_table` + `platforms_table` with join-based loading
- Implement `PostgresServiceRepository` against `services_table` with JSONB serialization for `path` and `timetable`
- Implement `PostgresConnectionRepository` against `node_connections_table`
- Remove empty `mapping.py` (no ORM mapping needed)
- Add database seeding for the fixed track network (stations, blocks, connections, vehicles)

## Non-goals

- Alembic migration changes (already exist)
- API layer changes (dependency wiring already supports `DB=postgres`)
- Domain model changes
- Read-side query optimization (CQRS-lite) — repositories cover write-side first

## Capabilities

### New Capabilities

- `postgres-repositories`: SQLAlchemy Core repository implementations with manual entity-to-row mapping for all five domain repositories
- `database-seeding`: Seed script to populate the fixed track network into PostgreSQL

### Modified Capabilities

_(none — no existing spec-level requirements change)_

## Impact

- **Code**: `infra/postgres/` — all `*_repo.py` files rewritten, `mapping.py` removed
- **Dependencies**: No new packages (SQLAlchemy + asyncpg already installed)
- **Testing**: Existing in-memory tests unaffected; new infra tests needed for repository contract verification against real PostgreSQL
- **Deployment**: `DB=postgres` mode becomes functional with Docker Compose PostgreSQL
