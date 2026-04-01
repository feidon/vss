## 1. Cleanup & Simple Repositories (Block, Vehicle, Connection)

- [x] 1.1 Delete empty `infra/postgres/mapping.py` (no ORM mapping needed)
- [x] 1.2 Implement `PostgresBlockRepository` with `_to_entity()`, `_to_table()`, upsert `save()`, and all query methods
- [x] 1.3 Write infra tests for `PostgresBlockRepository` (find_all, find_by_id, find_by_ids, save insert, save update)
- [x] 1.4 Implement `PostgresVehicleRepository` with `_to_entity()` and read-only query methods
- [x] 1.5 Write infra tests for `PostgresVehicleRepository` (find_all, find_by_id, not found)
- [x] 1.6 Implement `PostgresConnectionRepository` with `_to_entity()` returning `frozenset[NodeConnection]`
- [x] 1.7 Write infra tests for `PostgresConnectionRepository` (find_all returns frozenset)

## 2. Station Repository (Aggregate with JOIN)

- [x] 2.1 Rewrite `PostgresStationRepository` using LEFT JOIN on `stations_table`/`platforms_table`, grouping rows into Station aggregates with Platform children
- [x] 2.2 Write infra tests for `PostgresStationRepository` (find_all with platforms, find_by_id with platforms, yard with no platforms, not found)

## 3. Service Repository (JSONB + Autoincrement)

- [x] 3.1 Implement `PostgresServiceRepository` with JSONB serialization for path/timetable, RETURNING for autoincrement ID, and upsert for updates
- [x] 3.2 Write infra tests for `PostgresServiceRepository` (save new with generated ID, save existing update, find_by_id with deserialized JSONB, find_by_vehicle_id, delete, delete non-existent)

## 4. Database Seeding

- [x] 4.1 Create `infra/postgres/seed.py` with `async seed_database(session)` reusing data from `infra/seed.py`, idempotent via ON CONFLICT DO NOTHING
- [x] 4.2 Wire seeding into application startup (lifespan event) when `DB=postgres`
- [x] 4.3 Write test for seed idempotency (calling twice does not duplicate data)

## 5. Integration Verification

- [x] 5.1 Update `api/dependencies.py` to import and use the new PostgreSQL repository classes
- [x] 5.2 Run full test suite (`uv run pytest`) to verify in-memory tests still pass
- [x] 5.3 Smoke test with `DB=postgres` against Docker Compose PostgreSQL (start app, hit API endpoints)
