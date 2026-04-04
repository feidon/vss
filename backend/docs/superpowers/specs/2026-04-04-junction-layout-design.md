# Junction Layout Design

## Context

The track map frontend is transitioning from rendering blocks as nodes to rendering them as edges (lines between platforms/yards/junctions). Junctions are the points where multiple blocks meet (merge/diverge points in the track topology). They are purely for frontend rendering and must not appear in domain models.

Currently the backend returns blocks as nodes in the `GraphSchema`. After this change, blocks become edges with `from_id`/`to_id` endpoints, and junctions are returned as a separate array with positions for rendering.

## Goals

- Store junction positions in `node_layouts` alongside platform/yard positions
- Store junction-block mapping in a new `junction_blocks` table
- Serve junctions and edges in the graph API response
- Keep the domain layer untouched (RouteFinder, ConflictDetectionService, node_connections)

## Non-Goals

- Adding junction as a domain entity
- Changing RouteFinder or conflict detection logic
- Modifying `node_connections` table
- Changing route update or validation endpoints

## Database Schema

### `node_layouts` (altered)

Remove all block rows (B1-B14). Add junction rows (J1-J4). No schema change needed — same columns:

| Column | Type | Description |
|--------|------|-------------|
| node_id | UUID PK | Platform, yard, or junction ID |
| x | Float | X coordinate |
| y | Float | Y coordinate |

Final contents: 7 platform/yard rows + 4 junction rows = 11 rows (down from 21).

### `junction_blocks` (new)

| Column | Type | Description |
|--------|------|-------------|
| from_block_id | UUID PK | Source block in the block-to-block connection |
| to_block_id | UUID PK | Target block in the block-to-block connection |
| junction_id | UUID NOT NULL, FK -> node_layouts.node_id | Junction between these blocks |

Seed data (8 rows):

| from_block_id | to_block_id | junction_id |
|---|---|---|
| B3 | B5 | J1 |
| B4 | B5 | J1 |
| B6 | B7 | J2 |
| B6 | B8 | J2 |
| B9 | B11 | J3 |
| B10 | B11 | J3 |
| B12 | B13 | J4 |
| B12 | B14 | J4 |

### Migration strategy

Squash all existing migrations into a single migration. User handles existing DB migration manually.

## Domain Layer

### New: `domain/read_model/`

A new folder for read-model interfaces — rendering data that is not domain entities. `LayoutData` and `LayoutRepository` must not import from `application` or `infra`.

```
domain/read_model/
├── __init__.py
└── layout.py
```

**`layout.py`**:

```python
@dataclass(frozen=True)
class LayoutData:
    positions: dict[UUID, tuple[float, float]]
    junction_blocks: dict[tuple[UUID, UUID], UUID]

class LayoutRepository(ABC):
    async def find_all(self) -> LayoutData
```

- `positions` — maps platform/yard/junction UUIDs to (x, y) coordinates
- `junction_blocks` — maps (from_block_id, to_block_id) to junction_id

### Deleted

- `domain/network/node_layout_repository.py` — replaced by `domain/read_model/layout.py`

### Unchanged

- `domain/network/model.py` (Node, NodeConnection)
- `domain/network/repository.py` (ConnectionRepository)
- `domain/block/`, `domain/station/`, `domain/vehicle/`, `domain/service/`
- All domain services (RouteFinder, ConflictDetectionService)

## Infrastructure Layer

### New: `infra/postgres/layout_repo.py`

Implements `LayoutRepository`. Two queries:
1. `SELECT * FROM node_layouts` -> positions dict
2. `SELECT * FROM junction_blocks` -> junction_blocks dict

Returns combined `LayoutData`.

### New: `junction_blocks` table in `infra/postgres/tables.py`

```python
junction_blocks_table = Table(
    "junction_blocks",
    metadata,
    Column("from_block_id", Uuid, primary_key=True),
    Column("to_block_id", Uuid, primary_key=True),
    Column("junction_id", Uuid, ForeignKey("node_layouts.node_id"), nullable=False),
)
```

### Deleted

- `infra/postgres/node_layout_repo.py` — replaced by `layout_repo.py`

### Seed data (`infra/seed.py`)

- Remove block coordinates from `create_node_layouts()`
- Add junction UUIDs and coordinates
- Add `create_junction_blocks()` function returning the 8 mapping rows
- Fix `JUNCTION_ID_BY_NAME` to: `{"J1": uuid7(), "J2": uuid7(), "J3": uuid7(), "J4": uuid7()}`

## Application Layer

### `GraphData` (`application/graph/dto.py`)

Replace `layouts: dict[UUID, tuple[float, float]]` with `layout: LayoutData`.

### `GraphAppService` (`application/graph/service.py`)

- Inject `LayoutRepository` instead of `NodeLayoutRepository`
- Pass `LayoutData` into `GraphData`

### DI wiring (`api/dependencies.py`)

- Replace `get_node_layout_repo` with `get_layout_repo` returning `PostgresLayoutRepository`
- Update `get_graph_service` to inject the new repository

## API Layer

### New schemas (`api/shared/schemas.py`)

```python
class JunctionSchema(BaseModel):
    id: UUID
    x: float
    y: float

class EdgeSchema(BaseModel):
    id: UUID
    name: str
    from_id: UUID
    to_id: UUID
```

### `NodeSchema` (`api/shared/schemas.py`)

Remove `BlockNodeSchema` from the union. Delete `BlockNodeSchema` — it is not used by `PATCH /api/blocks` (that uses `BlockResponse` from `api/block/schemas.py`). Nodes are now platform/yard only:

```python
NodeSchema = Annotated[
    PlatformNodeSchema | YardNodeSchema,
    Field(discriminator="type"),
]
```

### `GraphSchema` (`api/service/schemas.py`)

Replace `connections: list[ConnectionSchema]` with:
- `edges: list[EdgeSchema]`
- `junctions: list[JunctionSchema]`

Remove blocks from `nodes` list. Delete `ConnectionSchema`.

### Edge computation algorithm in `from_graph_data()`

**Step 1: Preprocess junction index.**

```python
block_junction: dict[UUID, UUID] = {}
for (from_b, to_b), jid in layout.junction_blocks.items():
    block_junction[from_b] = jid
    block_junction[to_b] = jid
```

This maps each block that touches a junction to its junction ID. Blocks not in this dict (B1, B2) connect only to platforms/yards.

**Step 2: Build adjacency from `node_connections`.**

For each block, collect its unique non-block neighbors (platforms/yards).

**Step 3: Compute edge endpoints for each block.**

- Non-block neighbors become direct `from_id`/`to_id` endpoints
- If the block is in `block_junction`, the junction ID is the other endpoint
- B1/B2 (bidirectional, no junction): both endpoints are platform/yard (e.g., B1: from_id=Y, to_id=P1A)

**Step 4: Build junction list.**

```python
junction_ids = set(block_junction.values())
junctions = [JunctionSchema(id=jid, x=..., y=...) for jid in junction_ids]
```

### Unchanged endpoints

- `PATCH /api/blocks/{id}` — still updates traversal time on domain Block
- `PATCH /api/services/{id}/route` — still sends platform/yard stop IDs
- `POST /api/routes/validate` — same
- `GET /api/services` — same

## Testing

- **Domain tests**: No changes needed (domain untouched)
- **Application tests**: Update `GraphData` construction in tests using `LayoutData`. Update `tests/fakes/node_layout_repo.py` to become `InMemoryLayoutRepository` implementing the new `LayoutRepository` interface.
- **API/integration tests**: Update expected graph response shape — nodes count drops from 21 to 7, new `edges`/`junctions` fields replace `connections`, block-specific assertions removed or rewritten as edge assertions.
- **Seed data tests**: Verify junction positions and mapping data

## Junction Positions (seed data)

4 junctions derived from the track topology:

| Junction | Blocks | Description |
|----------|--------|-------------|
| J1 | B3, B4, B5 | Merge point: B3+B4 into B5 (S1->S2 outbound) |
| J2 | B6, B7, B8 | Diverge point: B6 into B7+B8 (S2->S3) |
| J3 | B9, B10, B11 | Merge point: B9+B10 into B11 (S3->S2 return) |
| J4 | B12, B13, B14 | Diverge point: B12 into B13+B14 (S2->S1 return) |

X/Y coordinates to be determined from existing block positions (midpoint of the connected blocks).
