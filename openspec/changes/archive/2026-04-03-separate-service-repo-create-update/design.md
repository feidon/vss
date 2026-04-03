## Context

The `ServiceRepository` currently exposes a single `save(service)` method that handles both creation and update. It checks `service.id is None` internally to decide which SQL operation to run. The create path mutates the entity by assigning the generated ID back to `service.id`, violating the project's immutability principle. Call sites in `ServiceAppService` don't communicate intent — both `create_service()` and `update_service_route()` call the same `save()`.

## Goals / Non-Goals

**Goals:**
- Separate `save()` into `create()` and `update()` with distinct signatures
- `create()` returns a new `Service` with the assigned ID instead of mutating the input
- Make call-site intent explicit
- Maintain all existing behavior — no API or schema changes

**Non-Goals:**
- Changing the database schema or migration strategy
- Modifying the `Service` domain entity itself
- Introducing a Unit of Work pattern or transaction changes
- Changing other repositories (block, vehicle) — those can follow later if desired

## Decisions

### 1. `create()` returns `Service`, `update()` returns `None`

`create(service: Service) -> Service` — returns a new entity with the DB-assigned ID. This avoids mutating the input and makes the ID assignment explicit at the call site.

`update(service: Service) -> None` — the service already has an ID; the caller doesn't need a return value.

**Alternative considered**: Both return `Service`. Rejected — `update()` returning the same entity adds no information and suggests a reload that doesn't happen.

### 2. `create()` constructs a new Service via `Service.create()` or dataclass replacement

Rather than mutating `service.id = generated_id`, `create()` will construct a new `Service` instance with the generated ID and the same field values. This uses the existing `Service` constructor or a factory method.

**Alternative considered**: Add a `with_id()` method to `Service`. Acceptable but unnecessary — the repository can construct the entity directly since it already knows all fields.

### 3. No guard clauses for ID state

`create()` won't assert `service.id is None` and `update()` won't assert `service.id is not None`. The database constraints (auto-generated ID for insert, WHERE clause for update) naturally enforce correctness. Adding guards would be defensive code for scenarios that can't happen given current call sites.

## Risks / Trade-offs

- **Low risk**: This is a straightforward refactoring with comprehensive test coverage. All call sites are in a single application service.
- **Breaking internal interface**: All implementations (Postgres, InMemory) and tests must be updated together. Mitigated by doing it in a single commit.
