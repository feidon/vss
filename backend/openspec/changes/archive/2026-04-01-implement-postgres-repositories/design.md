## Context

The VSS backend uses Hexagonal Architecture with repository interfaces (ports) in the domain layer and implementations (adapters) in the infra layer. Five in-memory repositories exist and are fully functional. The PostgreSQL infrastructure is already set up: Docker Compose, SQLAlchemy async engine/session, Alembic migrations, and table definitions in `infra/postgres/tables.py`. The API layer's `dependencies.py` already switches between in-memory and PostgreSQL repos based on `DB=postgres` env var.

What's missing: all five PostgreSQL repository implementations are empty stubs (or broken, in `station_repo.py`'s case).

## Goals / Non-Goals

**Goals:**
- Implement all five PostgreSQL repositories using SQLAlchemy Core + manual mapper pattern
- Each repository has `_to_entity()` and `_to_table()` methods for domain ↔ row translation
- `save()` uses upsert (`INSERT ... ON CONFLICT DO UPDATE`) for all repositories that support writes
- Station repository loads platforms eagerly via JOIN (station is the aggregate root)
- Service repository serializes/deserializes `path` and `timetable` as JSONB
- Database seeding script populates the fixed track network
- Remove unused `mapping.py`

**Non-Goals:**
- Read-side query optimization (direct SQL joins for list endpoints) — future CQRS-lite work
- Alembic migration changes
- Transaction management beyond per-request session scope
- Connection pooling tuning

## Decisions

### 1. SQLAlchemy Core queries, not ORM

**Decision**: Use `select(table)`, `insert(table)`, `update(table)` with Table objects. No `map_imperatively()`, no declarative base.

**Rationale**: Domain dataclasses must remain pure Python with zero SQLAlchemy imports. Manual `_to_entity()` / `_to_table()` mappers at the repository boundary give complete control over the translation.

**Alternatives considered**:
- Declarative mapping: couples domain models to SQLAlchemy base class
- Imperative mapping: runtime instrumentation of domain classes, global mutable state via `start_mappers()`

### 2. Upsert for save()

**Decision**: `INSERT ... ON CONFLICT DO UPDATE SET all_columns` for every `save()` call.

**Rationale**: No need to track whether an entity is new or existing. Matches explicit persistence — caller doesn't need to know if it's an insert or update. Service uses autoincrement ID, so its save() uses plain INSERT for new entities and UPDATE by ID for existing ones.

**Alternatives considered**:
- Separate `create()` / `update()` methods: leaks persistence details into application layer
- Change tracking: explicitly rejected (see CLAUDE.md persistence strategy)

### 3. Station loads platforms via LEFT JOIN

**Decision**: `StationRepository.find_all()` and `find_by_id()` execute a single query joining `stations_table` and `platforms_table`, then group rows into Station aggregates in Python.

**Rationale**: Station is the aggregate root that owns Platform. Loading them separately would require N+1 queries or a second bulk query. A single LEFT JOIN is simpler and more efficient.

### 4. Service path/timetable as JSONB

**Decision**: `path` (list of Node) and `timetable` (list of TimetableEntry) are stored as JSONB columns. `_to_table()` serializes to dicts, `_to_entity()` deserializes back to domain value objects.

**Rationale**: These are value object collections owned by the Service aggregate. Normalizing them into separate tables adds complexity without benefit — they're always loaded/saved as a unit with the service. JSONB supports indexing if needed later.

### 5. Service ID: autoincrement handled by database

**Decision**: Service has `id: int | None`. On INSERT, let PostgreSQL assign the ID via `SERIAL`/autoincrement. After insert, read back the generated ID using `RETURNING id`. For updates, match by ID.

**Rationale**: Matches the existing in-memory pattern where `_counter` auto-assigns IDs. The domain expects `id=None` for new services.

### 6. Session injection via constructor

**Decision**: Each repository takes `AsyncSession` in its constructor. The DI container provides the session per-request.

**Rationale**: Keeps repositories stateless (aside from the session reference). Matches the existing `get_session()` dependency in `api/dependencies.py`.

### 7. Seed data as async function

**Decision**: Create `infra/postgres/seed.py` with an `async seed_database(session)` function that inserts the fixed track network (reusing data from `infra/seed.py`) if the database is empty.

**Rationale**: The track network is fixed reference data. Seeding on startup (when tables are empty) avoids requiring manual setup.

## Risks / Trade-offs

- **JSONB query limitations** → Path/timetable fields can't be efficiently queried via SQL. Mitigation: for read-side queries, use direct SQL with joins in future CQRS work, not repository methods.
- **No optimistic locking** → Concurrent updates to the same entity will silently overwrite. Mitigation: acceptable for an interview assignment with single-user expected usage. Add version column later if needed.
- **Station aggregate loading** → LEFT JOIN returns duplicate station columns for each platform row. Mitigation: grouping logic in `_to_entity()` is straightforward; station has at most 2 platforms.
- **Seed data idempotency** → INSERT on non-empty tables could fail. Mitigation: check row count before seeding; use `ON CONFLICT DO NOTHING` for safety.
