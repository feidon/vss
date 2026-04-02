## Context

The Service entity stores a field named `path: list[Node]` representing the complete traversal sequence (platforms + intermediate blocks). However, the rest of the codebase consistently uses "route" for this concept: `Service.update_route()`, `ServiceAppService.update_service_route()`, `PATCH /services/{id}/route`, `POST /routes/validate`. The user input (stops) is already clearly named as `stops` / `RouteStop`. The only inconsistency is the stored field name `path` vs the operation name `route`.

The DB schema stores this as a JSONB column named `path` in the `services` table. There are no Alembic migration versions yet — the schema is managed by table definitions in `infra/postgres/tables.py`.

## Goals / Non-Goals

**Goals:**
- Rename `Service.path` to `Service.route` so the domain entity matches the ubiquitous language used in operations, DTOs, and API endpoints.
- Rename the DB column `path` to `route` in the services table definition.
- Rename all downstream references: API response fields, DTOs, repository mapper code, validation messages, local variables, and tests.

**Non-Goals:**
- Introducing a `Route` value object or entity — the `list[Node]` representation remains.
- Renaming `RouteFinder.build_full_path()` — its internal `path` variable describes a BFS traversal path, which is algorithmically correct naming for a pathfinding method. The method returns `list[UUID]` (not `list[Node]`), and the caller (`ServiceAppService`) maps UUIDs to Nodes. The "path" in RouteFinder refers to the graph traversal result, not the Service field.
- Renaming `stops` / `RouteStop` — these are already clear.
- Writing an Alembic migration — no migration versions exist yet; the table definition change is sufficient.

## Decisions

### 1. Rename field to `route` (not introduce a Route type)

**Decision:** Pure rename of `Service.path` -> `Service.route` without introducing a new value object.

**Rationale:** The `list[Node]` type is already descriptive. A `Route` wrapper would add indirection for zero behavioral benefit — it would just be a list with no domain methods.

**Alternative considered:** Create a `Route` value object wrapping `list[Node]` with potential future methods (e.g., `stops()`, `blocks()`). Rejected because YAGNI — no current use case requires route-specific behavior beyond what list operations provide.

### 2. Rename DB column alongside code

**Decision:** Rename the JSONB column from `path` to `route` in `tables.py`.

**Rationale:** No Alembic migration history exists, so there's no backward compatibility concern. The table definition is the source of truth. Keeping the DB column aligned with the domain field avoids mapper confusion.

**Alternative considered:** Keep DB column as `path` and only rename in code (aliased in mapper). Rejected because it adds unnecessary translation and the DB has no migration history to preserve.

### 3. Keep `RouteFinder.build_full_path()` name

**Decision:** Do not rename `RouteFinder.build_full_path()` or its internal variables.

**Rationale:** In `RouteFinder`, "path" refers to the BFS graph traversal result (a list of UUIDs), which is standard graph algorithm terminology. It operates on raw IDs, not domain Nodes. The name is accurate in its local context. Renaming it to `build_full_route()` would blur the distinction between graph-algorithm output and domain-level route.

## Risks / Trade-offs

- **[Breaking API change]** `path` -> `route` in `ServiceDetailResponse` and `ValidateRouteResponse` will break frontend consumers. -> Mitigation: Frontend is TBD and currently not deployed, so no real consumer impact.
- **[DB column rename]** Existing data in PostgreSQL will reference the old column name. -> Mitigation: The DB is development-only (Docker), easily recreated. No production data exists.
- **[Grep-ability]** "route" is more overloaded than "path" (FastAPI routes, API route endpoints). -> Mitigation: Field access `service.route` is distinct from module-level `routes.py` files. The domain context disambiguates.
