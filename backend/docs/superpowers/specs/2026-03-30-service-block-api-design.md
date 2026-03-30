# Service CRUD & Block Read/Update API Design

## Context

The VSS backend has a well-structured domain layer (Block, Service, Vehicle, Station, Network) but no API, application, or infrastructure layers yet. This design adds REST APIs for:
- **Service**: Full CRUD (create with basic info, path/timetable via separate endpoints)
- **Block**: Read (single + list) and update (traversal_time_seconds only)

## Decisions

- **IDs**: Server-generated UUID7
- **Persistence**: In-memory repositories (swap to SQLAlchemy later)
- **Structure**: Layer-based with domain subfolders (e.g., `api/service/`, `api/block/`)
- **Repository ports**: Single unified interface per entity (merging existing query ports)
- **Validation**: No vehicle_id existence check at this stage (deferred to DB-level referential integrity)
- **Concurrency**: In-memory repos are not thread-safe; acceptable for initial implementation

## File Structure

```
api/
├── service/
│   ├── routes.py          # FastAPI router for /services
│   └── schemas.py         # Pydantic request/response models
└── block/
    ├── routes.py          # FastAPI router for /blocks
    └── schemas.py         # Pydantic request/response models

application/
├── service/
│   └── service.py         # ServiceApplicationService
└── block/
    └── service.py         # BlockApplicationService

domain/
├── service/
│   ├── repository.py      # ServiceRepository (ABC) — replaces ServiceQueryPort
│   └── ...existing files
└── block/
    ├── repository.py      # BlockRepository (ABC) — replaces BlockQueryPort
    └── model.py           # Add with_traversal_time() method

infra/
└── memory/
    ├── service_repo.py    # InMemoryServiceRepository
    └── block_repo.py      # InMemoryBlockRepository
```

## Repository Ports

### ServiceRepository (`domain/service/repository.py`)

```python
class ServiceRepository(ABC):
    async def find_all(self) -> list[Service]: ...
    async def find_by_id(self, id: UUID) -> Service | None: ...
    async def find_by_vehicle_id(self, vehicle_id: UUID) -> list[Service]: ...
    async def save(self, service: Service) -> None: ...
    async def delete(self, id: UUID) -> None: ...
```

Merges existing `ServiceQueryPort` methods (`find_all`, `find_by_vehicle_id`) with write operations. `ConflictDetectionService` will depend on `ServiceRepository` instead of `ServiceQueryPort`.

- `delete` is idempotent: silently succeeds if the ID does not exist.

### BlockRepository (`domain/block/repository.py`)

```python
class BlockRepository(ABC):
    async def find_all(self) -> list[Block]: ...
    async def find_by_id(self, id: UUID) -> Block | None: ...
    async def save(self, block: Block) -> None: ...
```

Merges existing `BlockQueryPort` with new `find_by_id` (needed for `GET /blocks/{id}`) and `save`. No delete — blocks are managed externally.

## Domain Model Changes

### Block — add `with_traversal_time()` method

Add to `domain/block/model.py`:

```python
def with_traversal_time(self, traversal_time_seconds: int) -> Block:
    return Block(
        id=self.id,
        name=self.name,
        group=self.group,
        traversal_time_seconds=traversal_time_seconds,
    )
```

This keeps the domain responsible for its own invariants (`__post_init__` validates > 0) and avoids the application layer reaching into Block fields.

## Request/Response Schemas

### Service Schemas (`api/service/schemas.py`)

```python
class CreateServiceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    vehicle_id: UUID

class NodeSchema(BaseModel):
    id: UUID
    type: str  # "block" or "platform"

class UpdatePathRequest(BaseModel):
    path: list[NodeSchema]

class TimetableEntrySchema(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int

class UpdateTimetableRequest(BaseModel):
    timetable: list[TimetableEntrySchema]

class TimetableEntryResponse(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int

class ServiceResponse(BaseModel):
    id: UUID
    name: str
    vehicle_id: UUID
    path: list[NodeSchema]
    timetable: list[TimetableEntryResponse]
```

### Block Schemas (`api/block/schemas.py`)

```python
class UpdateBlockRequest(BaseModel):
    traversal_time_seconds: int = Field(gt=0)

class BlockResponse(BaseModel):
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int
```

## API Endpoints

### Service (`/services`)

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/services` | `CreateServiceRequest` | `201` + `ServiceResponse` |
| GET | `/services` | — | `200` + `list[ServiceResponse]` |
| GET | `/services/{id}` | — | `200` + `ServiceResponse` |
| PATCH | `/services/{id}/path` | `UpdatePathRequest` | `200` + `ServiceResponse` |
| PATCH | `/services/{id}/timetable` | `UpdateTimetableRequest` | `200` + `ServiceResponse` |
| DELETE | `/services/{id}` | — | `204` |

**Ordering constraint**: Path must be set before timetable entries can reference nodes. Calling `PATCH /services/{id}/timetable` with node_ids not in the current path returns `400` with a message indicating which nodes are missing.

### Block (`/blocks`)

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/blocks` | — | `200` + `list[BlockResponse]` |
| GET | `/blocks/{id}` | — | `200` + `BlockResponse` |
| PATCH | `/blocks/{id}` | `UpdateBlockRequest` | `200` + `BlockResponse` |

## Application Services

### ServiceApplicationService (`application/service/service.py`)

- `create_service(name, vehicle_id)` — validates name non-empty, generates UUID7, creates Service with empty path/timetable, saves
- `get_service(id)` — returns Service or raises not-found error
- `list_services()` — returns all services
- `update_service_path(id, path)` — loads service, calls `service.update_path()`, saves
- `update_service_timetable(id, timetable)` — loads service, calls `service.update_timetable()`, saves. Returns 400 if path is empty and timetable references nodes.
- `delete_service(id)` — removes service from repository (idempotent)

### BlockApplicationService (`application/block/service.py`)

- `get_block(id)` — returns Block or raises not-found error
- `list_blocks()` — returns all blocks
- `update_block(id, traversal_time_seconds)` — loads block, calls `block.with_traversal_time(seconds)`, saves new instance

## In-Memory Repositories

Both use `dict[UUID, Entity]` internally:
- `InMemoryServiceRepository` in `infra/memory/service_repo.py`
- `InMemoryBlockRepository` in `infra/memory/block_repo.py`

## Dependency Injection

In `main.py`:
1. Instantiate in-memory repositories
2. Instantiate application services with repositories
3. Use FastAPI `Depends()` to inject app services into route handlers
4. Include routers via `app.include_router()`

## Error Handling

- Domain `ValueError` → HTTP 400 (Bad Request) with error message in response body
- Entity not found → HTTP 404 (Not Found)
- Pydantic validation failure → HTTP 422 (automatic from FastAPI)
- Use FastAPI exception handlers to map domain exceptions to HTTP responses

## Migration Notes

- `ConflictDetectionService` constructor changes: accepts `ServiceRepository` and `BlockRepository` instead of `ServiceQueryPort` and `BlockQueryPort`
- Remove `ServiceQueryPort` and `BlockQueryPort` from `conflict.py`
- Update `conflict.py` tests to use the new repository interfaces (fakes now implement `ServiceRepository` / `BlockRepository`)
- `BlockRepository` adds new `find_by_id` and `save` methods not present in the old `BlockQueryPort`
- `ServiceRepository` adds new `find_by_id`, `save`, and `delete` methods not present in the old `ServiceQueryPort`
