# Junction Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add junction rendering data to the graph API so the frontend can render blocks as edges between platforms/yards/junctions.

**Architecture:** Read-model only approach. Junctions are stored in `node_layouts` + new `junction_blocks` table. Domain layer is untouched. The API layer transforms blocks into edges using a junction index built from `LayoutData`.

**Tech Stack:** Python 3.14, FastAPI, SQLAlchemy Core 2.0, Alembic, asyncpg, pytest

**Spec:** `docs/superpowers/specs/2026-04-04-junction-layout-design.md`

---

### Task 1: Domain read-model — LayoutData and LayoutRepository

**Files:**
- Create: `domain/read_model/__init__.py`
- Create: `domain/read_model/layout.py`
- Delete: `domain/network/node_layout_repository.py`

- [ ] **Step 1: Create `domain/read_model/__init__.py`**

Empty file:

```python
```

- [ ] **Step 2: Create `domain/read_model/layout.py`**

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LayoutData:
    positions: dict[UUID, tuple[float, float]]
    junction_blocks: dict[tuple[UUID, UUID], UUID]


class LayoutRepository(ABC):
    @abstractmethod
    async def find_all(self) -> LayoutData:
        """Return layout positions and junction-block mappings."""
```

- [ ] **Step 3: Delete `domain/network/node_layout_repository.py`**

```bash
rm domain/network/node_layout_repository.py
```

- [ ] **Step 4: Verify import-linter passes**

```bash
uv run lint-imports
```

Expected: All contracts KEPT.

- [ ] **Step 5: Commit**

```bash
git add domain/read_model/ && git rm domain/network/node_layout_repository.py
git commit -m "refactor: replace NodeLayoutRepository with LayoutRepository in domain/read_model"
```

---

### Task 2: In-memory fake — InMemoryLayoutRepository

**Files:**
- Create: `tests/fakes/layout_repo.py`
- Delete: `tests/fakes/node_layout_repo.py`

- [ ] **Step 1: Create `tests/fakes/layout_repo.py`**

```python
from __future__ import annotations

from uuid import UUID

from domain.read_model.layout import LayoutData, LayoutRepository


class InMemoryLayoutRepository(LayoutRepository):
    def __init__(
        self,
        positions: dict[UUID, tuple[float, float]] | None = None,
        junction_blocks: dict[tuple[UUID, UUID], UUID] | None = None,
    ) -> None:
        self._positions = dict(positions) if positions else {}
        self._junction_blocks = dict(junction_blocks) if junction_blocks else {}

    async def find_all(self) -> LayoutData:
        return LayoutData(
            positions=dict(self._positions),
            junction_blocks=dict(self._junction_blocks),
        )
```

- [ ] **Step 2: Delete `tests/fakes/node_layout_repo.py`**

```bash
rm tests/fakes/node_layout_repo.py
```

- [ ] **Step 3: Commit**

```bash
git add tests/fakes/layout_repo.py && git rm tests/fakes/node_layout_repo.py
git commit -m "refactor: replace InMemoryNodeLayoutRepository with InMemoryLayoutRepository"
```

---

### Task 3: GraphData and GraphAppService — use LayoutData

**Files:**
- Modify: `application/graph/dto.py`
- Modify: `application/graph/service.py`
- Modify: `tests/application/test_graph_service.py`

- [ ] **Step 1: Update `application/graph/dto.py`**

Replace the `layouts` field with `layout: LayoutData`:

```python
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.block.model import Block
from domain.network.model import NodeConnection
from domain.read_model.layout import LayoutData
from domain.station.model import Platform, Station
from domain.vehicle.model import Vehicle


@dataclass(frozen=True)
class GraphData:
    stations: list[Station]
    blocks: list[Block]
    connections: frozenset[NodeConnection]
    vehicles: list[Vehicle]
    layout: LayoutData

    @property
    def platform_to_station_dict(self) -> dict[UUID, Station]:
        return {p.id: s for s in self.stations for p in s.platforms}

    @property
    def platforms(self) -> list[Platform]:
        return [p for s in self.stations for p in s.platforms]

    @property
    def yards(self) -> list[Station]:
        return [s for s in self.stations if s.is_yard]
```

- [ ] **Step 2: Update `application/graph/service.py`**

```python
from __future__ import annotations

from domain.block.repository import BlockRepository
from domain.network.repository import ConnectionRepository
from domain.read_model.layout import LayoutRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository

from application.graph.dto import GraphData


class GraphAppService:
    def __init__(
        self,
        station_repo: StationRepository,
        block_repo: BlockRepository,
        connection_repo: ConnectionRepository,
        vehicle_repo: VehicleRepository,
        layout_repo: LayoutRepository,
    ) -> None:
        self._station_repo = station_repo
        self._block_repo = block_repo
        self._connection_repo = connection_repo
        self._vehicle_repo = vehicle_repo
        self._layout_repo = layout_repo

    async def get_graph(self) -> GraphData:
        stations = await self._station_repo.find_all()
        blocks = await self._block_repo.find_all()
        connections = await self._connection_repo.find_all()
        vehicles = await self._vehicle_repo.find_all()
        layout = await self._layout_repo.find_all()
        return GraphData(
            stations=stations,
            blocks=blocks,
            connections=connections,
            vehicles=vehicles,
            layout=layout,
        )
```

- [ ] **Step 3: Update `tests/application/test_graph_service.py`**

Replace all `InMemoryNodeLayoutRepository` with `InMemoryLayoutRepository` and update fixture names:

```python
from uuid import uuid7

import pytest
from application.graph.service import GraphAppService
from domain.block.model import Block
from domain.network.model import NodeConnection
from domain.station.model import Platform, Station
from domain.vehicle.model import Vehicle

from tests.fakes.block_repo import InMemoryBlockRepository
from tests.fakes.connection_repo import InMemoryConnectionRepository
from tests.fakes.layout_repo import InMemoryLayoutRepository
from tests.fakes.station_repo import InMemoryStationRepository
from tests.fakes.vehicle_repo import InMemoryVehicleRepository


class TestGraphAppService:
    @pytest.fixture
    def station_repo(self):
        repo = InMemoryStationRepository()
        s = Station(
            id=uuid7(),
            name="S1",
            is_yard=False,
            platforms=[
                Platform(id=uuid7(), name="P1A"),
            ],
        )
        repo._store[s.id] = s
        return repo

    @pytest.fixture
    def block_repo(self):
        repo = InMemoryBlockRepository()
        b = Block(id=uuid7(), name="B1", group=1, traversal_time_seconds=30)
        repo._store[b.id] = b
        return repo

    @pytest.fixture
    def connection_repo(self):
        return InMemoryConnectionRepository(
            frozenset(
                {
                    NodeConnection(from_id=uuid7(), to_id=uuid7()),
                }
            )
        )

    @pytest.fixture
    def vehicle_repo(self):
        repo = InMemoryVehicleRepository()
        v = Vehicle(id=uuid7(), name="V1")
        repo._store[v.id] = v
        return repo

    @pytest.fixture
    def layout_repo(self):
        return InMemoryLayoutRepository()

    @pytest.fixture
    def service(
        self, station_repo, block_repo, connection_repo, vehicle_repo, layout_repo
    ):
        return GraphAppService(
            station_repo=station_repo,
            block_repo=block_repo,
            connection_repo=connection_repo,
            vehicle_repo=vehicle_repo,
            layout_repo=layout_repo,
        )

    async def test_get_graph_assembles_all_data(
        self, service, station_repo, block_repo, vehicle_repo
    ):
        graph = await service.get_graph()
        assert len(graph.stations) == 1
        assert len(graph.blocks) == 1
        assert len(graph.connections) == 1
        assert len(graph.vehicles) == 1

    async def test_get_graph_empty_repos(self):
        svc = GraphAppService(
            station_repo=InMemoryStationRepository(),
            block_repo=InMemoryBlockRepository(),
            connection_repo=InMemoryConnectionRepository(),
            vehicle_repo=InMemoryVehicleRepository(),
            layout_repo=InMemoryLayoutRepository(),
        )
        graph = await svc.get_graph()
        assert graph.stations == []
        assert graph.blocks == []
        assert graph.connections == frozenset()
        assert graph.vehicles == []

    async def test_platform_to_station_mapping(self, service):
        graph = await service.get_graph()
        station = graph.stations[0]
        platform = station.platforms[0]
        assert graph.platform_to_station_dict[platform.id] == station

    async def test_yard_property(self):
        repo = InMemoryStationRepository()
        yard = Station(id=uuid7(), name="Y", is_yard=True, platforms=[])
        non_yard = Station(id=uuid7(), name="S1", is_yard=False, platforms=[])
        repo._store[yard.id] = yard
        repo._store[non_yard.id] = non_yard

        svc = GraphAppService(
            station_repo=repo,
            block_repo=InMemoryBlockRepository(),
            connection_repo=InMemoryConnectionRepository(),
            vehicle_repo=InMemoryVehicleRepository(),
            layout_repo=InMemoryLayoutRepository(),
        )
        graph = await svc.get_graph()
        assert graph.yards == [yard]
```

- [ ] **Step 4: Run unit tests**

```bash
uv run pytest tests/application/test_graph_service.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add application/graph/dto.py application/graph/service.py tests/application/test_graph_service.py
git commit -m "refactor: GraphData uses LayoutData instead of raw dict"
```

---

### Task 4: API schemas — EdgeSchema, JunctionSchema, remove BlockNodeSchema

**Files:**
- Modify: `api/shared/schemas.py`
- Modify: `api/service/schemas.py`

- [ ] **Step 1: Update `api/shared/schemas.py`**

Remove `BlockNodeSchema`. Add `JunctionSchema` and `EdgeSchema`. Update `NodeSchema` union:

```python
from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PlatformNodeSchema(BaseModel):
    type: Literal["platform"] = "platform"
    id: UUID
    name: str
    x: float = 0.0
    y: float = 0.0


class YardNodeSchema(BaseModel):
    type: Literal["yard"] = "yard"
    id: UUID
    name: str
    x: float = 0.0
    y: float = 0.0


NodeSchema = Annotated[
    PlatformNodeSchema | YardNodeSchema,
    Field(discriminator="type"),
]


class JunctionSchema(BaseModel):
    id: UUID
    x: float
    y: float


class EdgeSchema(BaseModel):
    id: UUID
    name: str
    from_id: UUID
    to_id: UUID


class TimetableEntrySchema(BaseModel):
    order: int
    node_id: UUID
    arrival: int
    departure: int
```

- [ ] **Step 2: Update `api/service/schemas.py` — imports and GraphSchema**

Replace `BlockNodeSchema` import, remove `ConnectionSchema`, update `GraphSchema` to use edges/junctions. The full file:

```python
from __future__ import annotations

from uuid import UUID

from application.graph.dto import GraphData
from application.service.dto import RouteStop
from domain.network.model import NodeType
from domain.service.model import Service
from domain.station.model import Platform
from domain.vehicle.model import Vehicle
from pydantic import BaseModel, Field

from api.shared.schemas import (
    EdgeSchema,
    JunctionSchema,
    NodeSchema,
    PlatformNodeSchema,
    TimetableEntrySchema,
    YardNodeSchema,
)


class CreateServiceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    vehicle_id: UUID


class RouteStopInput(BaseModel):
    node_id: UUID
    dwell_time: int = Field(ge=0)

    def to_route_stop(self) -> RouteStop:
        return RouteStop(node_id=self.node_id, dwell_time=self.dwell_time)


class UpdateRouteRequest(BaseModel):
    stops: list[RouteStopInput] = Field(min_length=1)
    start_time: int


class ServiceIdResponse(BaseModel):
    id: int


# ── List response (GET /services) ─────────────────────────────


class ServiceResponse(BaseModel):
    id: int
    name: str
    vehicle_id: UUID
    vehicle_name: str
    start_time: int | None = None
    origin_name: str | None = None
    destination_name: str | None = None

    @classmethod
    def from_domain(
        cls,
        service: Service,
        vehicle: Vehicle,
        node_names: dict[UUID, str],
    ) -> ServiceResponse:
        start_time = service.timetable[0].arrival if service.timetable else None

        origin_name = node_names.get(service.route[0].id) if service.route else None

        destination_name: str | None = None
        if service.route:
            for node in reversed(service.route):
                if node.type != NodeType.BLOCK:
                    destination_name = node_names.get(node.id)
                    break

        return cls(
            id=service.id,
            name=service.name,
            vehicle_id=service.vehicle_id,
            vehicle_name=vehicle.name,
            start_time=start_time,
            origin_name=origin_name,
            destination_name=destination_name,
        )


# ── Graph sub-schemas (for service detail) ────────────────────


class VehicleSchema(BaseModel):
    id: UUID
    name: str


class StationSchema(BaseModel):
    id: UUID
    name: str
    is_yard: bool
    platform_ids: list[UUID]


class GraphSchema(BaseModel):
    nodes: list[NodeSchema]
    edges: list[EdgeSchema]
    junctions: list[JunctionSchema]
    stations: list[StationSchema]
    vehicles: list[VehicleSchema]

    @classmethod
    def from_graph_data(cls, data: GraphData) -> GraphSchema:
        nodes: list[PlatformNodeSchema | YardNodeSchema] = []
        positions = data.layout.positions

        for yard in data.yards:
            x, y = positions.get(yard.id, (0.0, 0.0))
            nodes.append(YardNodeSchema(id=yard.id, name=yard.name, x=x, y=y))

        for platform in data.platforms:
            x, y = positions.get(platform.id, (0.0, 0.0))
            nodes.append(
                PlatformNodeSchema(id=platform.id, name=platform.name, x=x, y=y)
            )

        # Build block_junction index: block_id -> junction_id
        block_junction: dict[UUID, UUID] = {}
        for (from_b, to_b), jid in data.layout.junction_blocks.items():
            block_junction[from_b] = jid
            block_junction[to_b] = jid

        # Build adjacency: for each block, find its non-block neighbors
        block_ids = {b.id for b in data.blocks}
        adjacency: dict[UUID, set[UUID]] = {b.id: set() for b in data.blocks}
        for conn in data.connections:
            if conn.from_id in block_ids and conn.to_id not in block_ids:
                adjacency[conn.from_id].add(conn.to_id)
            if conn.to_id in block_ids and conn.from_id not in block_ids:
                adjacency[conn.to_id].add(conn.from_id)

        # Compute edges
        edges: list[EdgeSchema] = []
        for block in data.blocks:
            non_block_neighbors = adjacency.get(block.id, set())
            junction_id = block_junction.get(block.id)

            if junction_id is not None and len(non_block_neighbors) == 1:
                # Block connects a platform/yard to a junction
                neighbor = next(iter(non_block_neighbors))
                edges.append(
                    EdgeSchema(
                        id=block.id,
                        name=block.name,
                        from_id=neighbor,
                        to_id=junction_id,
                    )
                )
            elif junction_id is None and len(non_block_neighbors) == 2:
                # Bidirectional block (B1, B2): connects two platforms/yards directly
                neighbors = list(non_block_neighbors)
                edges.append(
                    EdgeSchema(
                        id=block.id,
                        name=block.name,
                        from_id=neighbors[0],
                        to_id=neighbors[1],
                    )
                )

        # Build junctions list
        junction_ids = set(block_junction.values())
        junctions = [
            JunctionSchema(id=jid, x=positions[jid][0], y=positions[jid][1])
            for jid in junction_ids
            if jid in positions
        ]

        return cls(
            nodes=nodes,
            edges=edges,
            junctions=junctions,
            stations=[
                StationSchema(
                    id=s.id,
                    name=s.name,
                    is_yard=s.is_yard,
                    platform_ids=[p.id for p in s.platforms],
                )
                for s in data.stations
            ],
            vehicles=[VehicleSchema(id=v.id, name=v.name) for v in data.vehicles],
        )


# ── Detail response (GET /services/{id}) ──────────────────────


class ServiceDetailResponse(BaseModel):
    id: int
    name: str
    vehicle_id: UUID
    route: list[NodeSchema]
    timetable: list[TimetableEntrySchema]
    graph: GraphSchema

    @classmethod
    def from_domain(
        cls,
        service: Service,
        graph_data: GraphData,
    ) -> ServiceDetailResponse:
        platform_dict = {p.id: p for p in graph_data.platforms}
        yard_name_dict = {y.id: y.name for y in graph_data.yards}
        route_nodes = cls._get_route_nodes(
            service, platform_dict, yard_name_dict
        )

        return cls(
            id=service.id,
            name=service.name,
            vehicle_id=service.vehicle_id,
            route=route_nodes,
            timetable=[
                TimetableEntrySchema(
                    order=e.order,
                    node_id=e.node_id,
                    arrival=e.arrival,
                    departure=e.departure,
                )
                for e in service.timetable
            ],
            graph=GraphSchema.from_graph_data(graph_data)
        )

    @classmethod
    def _get_route_nodes(
        cls,
        service: Service,
        platform_dict: dict[UUID, Platform],
        yard_name_dict: dict[UUID, str]
    ) -> list[PlatformNodeSchema | YardNodeSchema]:
        route_nodes: list[PlatformNodeSchema | YardNodeSchema] = []
        for node in service.route:
            if node.type == NodeType.PLATFORM and node.id in platform_dict:
                p = platform_dict[node.id]
                route_nodes.append(PlatformNodeSchema(id=p.id, name=p.name))
            elif node.type == NodeType.YARD:
                route_nodes.append(
                    YardNodeSchema(
                        id=node.id,
                        name=yard_name_dict.get(node.id, "Y"),
                    )
                )

        return route_nodes
```

- [ ] **Step 3: Run ruff to check for issues**

```bash
uv run ruff check api/shared/schemas.py api/service/schemas.py
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add api/shared/schemas.py api/service/schemas.py
git commit -m "feat: replace connections/block-nodes with edges/junctions in GraphSchema"
```

---

### Task 5: Infrastructure — junction_blocks table, PostgresLayoutRepository, seed data

**Files:**
- Modify: `infra/postgres/tables.py`
- Create: `infra/postgres/layout_repo.py`
- Delete: `infra/postgres/node_layout_repo.py`
- Modify: `infra/seed.py`

- [ ] **Step 1: Add `junction_blocks_table` to `infra/postgres/tables.py`**

Add after `node_layouts_table`:

```python
junction_blocks_table = Table(
    "junction_blocks",
    metadata,
    Column("from_block_id", Uuid, primary_key=True),
    Column("to_block_id", Uuid, primary_key=True),
    Column("junction_id", Uuid, ForeignKey("node_layouts.node_id"), nullable=False),
)
```

- [ ] **Step 2: Create `infra/postgres/layout_repo.py`**

```python
from __future__ import annotations

from uuid import UUID

from domain.read_model.layout import LayoutData, LayoutRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.postgres.tables import junction_blocks_table, node_layouts_table


class PostgresLayoutRepository(LayoutRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> LayoutData:
        layout_result = await self._session.execute(select(node_layouts_table))
        positions: dict[UUID, tuple[float, float]] = {
            row["node_id"]: (row["x"], row["y"]) for row in layout_result.mappings()
        }

        jb_result = await self._session.execute(select(junction_blocks_table))
        junction_blocks: dict[tuple[UUID, UUID], UUID] = {
            (row["from_block_id"], row["to_block_id"]): row["junction_id"]
            for row in jb_result.mappings()
        }

        return LayoutData(positions=positions, junction_blocks=junction_blocks)
```

- [ ] **Step 3: Delete `infra/postgres/node_layout_repo.py`**

```bash
rm infra/postgres/node_layout_repo.py
```

- [ ] **Step 4: Update `infra/seed.py`**

Fix `JUNCTION_ID_BY_NAME`, update `create_node_layouts()` to remove blocks and add junctions, add `create_junction_blocks()`:

Replace the existing malformed `JUNCTION_ID_BY_NAME` dict with:

```python
JUNCTION_ID_BY_NAME = {
    "J1": uuid7(),  # B3/B4 merge into B5
    "J2": uuid7(),  # B6 diverges into B7/B8
    "J3": uuid7(),  # B9/B10 merge into B11
    "J4": uuid7(),  # B12 diverges into B13/B14
}
```

Replace `create_node_layouts()` with:

```python
def create_node_layouts() -> dict[UUID, tuple[float, float]]:
    p = PLATFORM_ID_BY_NAME
    j = JUNCTION_ID_BY_NAME
    return {
        p["P3A"]: (50.0, 40.0),
        p["P3B"]: (50.0, 160.0),
        p["P2A"]: (400.0, 40.0),
        p["P2B"]: (400.0, 160.0),
        p["P1A"]: (750.0, 40.0),
        p["P1B"]: (750.0, 160.0),
        YARD_ID: (950.0, 100.0),
        j["J1"]: (580.0, 60.0),
        j["J2"]: (230.0, 80.0),
        j["J3"]: (230.0, 120.0),
        j["J4"]: (580.0, 140.0),
    }
```

Note: Junction coordinates are approximate midpoints. J2/J3 offset vertically to avoid overlap. Adjust after visual testing.

Add new function after `create_node_layouts()`:

```python
def create_junction_blocks() -> list[tuple[UUID, UUID, UUID]]:
    """Return (from_block_id, to_block_id, junction_id) tuples."""
    b = BLOCK_ID_BY_NAME
    j = JUNCTION_ID_BY_NAME
    return [
        (b["B3"], b["B5"], j["J1"]),
        (b["B4"], b["B5"], j["J1"]),
        (b["B6"], b["B7"], j["J2"]),
        (b["B6"], b["B8"], j["J2"]),
        (b["B9"], b["B11"], j["J3"]),
        (b["B10"], b["B11"], j["J3"]),
        (b["B12"], b["B13"], j["J4"]),
        (b["B12"], b["B14"], j["J4"]),
    ]
```

- [ ] **Step 5: Run unit tests (non-postgres)**

```bash
uv run pytest tests/application/ -v
```

Expected: All tests PASS (application tests use in-memory fakes, no DB needed).

- [ ] **Step 6: Commit**

```bash
git add infra/postgres/tables.py infra/postgres/layout_repo.py infra/seed.py && git rm infra/postgres/node_layout_repo.py
git commit -m "feat: add junction_blocks table, PostgresLayoutRepository, and junction seed data"
```

---

### Task 6: DI wiring — replace NodeLayoutRepository

**Files:**
- Modify: `api/dependencies.py`

- [ ] **Step 1: Update `api/dependencies.py`**

Replace `NodeLayoutRepository` and `PostgresNodeLayoutRepository` imports with new types. Replace `get_node_layout_repo` with `get_layout_repo`. Update `get_graph_service`:

```python
from application.block.service import BlockAppService
from application.graph.service import GraphAppService
from application.service.service import ServiceAppService
from application.vehicle.service import VehicleAppService
from domain.block.repository import BlockRepository
from domain.network.repository import ConnectionRepository
from domain.read_model.layout import LayoutRepository
from domain.service.repository import ServiceRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository
from fastapi import Depends
from infra.postgres.block_repo import PostgresBlockRepository
from infra.postgres.connection_repo import PostgresConnectionRepository
from infra.postgres.layout_repo import PostgresLayoutRepository
from infra.postgres.service_repo import PostgresServiceRepository
from infra.postgres.session import get_session
from infra.postgres.station_repo import PostgresStationRepository
from infra.postgres.vehicle_repo import PostgresVehicleRepository
from sqlalchemy.ext.asyncio import AsyncSession

# ── Dependency providers ────────────────────────────────────


def get_block_repo(session: AsyncSession = Depends(get_session)):
    return PostgresBlockRepository(session)


def get_service_repo(session: AsyncSession = Depends(get_session)) -> ServiceRepository:
    return PostgresServiceRepository(session)


def get_connection_repo(
    session: AsyncSession = Depends(get_session),
) -> ConnectionRepository:
    return PostgresConnectionRepository(session)


def get_station_repo(session: AsyncSession = Depends(get_session)) -> StationRepository:
    return PostgresStationRepository(session)


def get_vehicle_repo(session: AsyncSession = Depends(get_session)) -> VehicleRepository:
    return PostgresVehicleRepository(session)


def get_layout_repo(
    session: AsyncSession = Depends(get_session),
) -> LayoutRepository:
    return PostgresLayoutRepository(session)


def get_block_service(
    block_repo: BlockRepository = Depends(get_block_repo),
) -> BlockAppService:
    return BlockAppService(block_repo)


def get_vehicle_service(
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
) -> VehicleAppService:
    return VehicleAppService(vehicle_repo)


def get_service_app_service(
    service_repo: ServiceRepository = Depends(get_service_repo),
    block_repo: BlockRepository = Depends(get_block_repo),
    connection_repo: ConnectionRepository = Depends(get_connection_repo),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
    station_repo: StationRepository = Depends(get_station_repo),
) -> ServiceAppService:
    return ServiceAppService(
        service_repo, block_repo, connection_repo, vehicle_repo, station_repo
    )


def get_graph_service(
    station_repo: StationRepository = Depends(get_station_repo),
    block_repo: BlockRepository = Depends(get_block_repo),
    connection_repo: ConnectionRepository = Depends(get_connection_repo),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
    layout_repo: LayoutRepository = Depends(get_layout_repo),
) -> GraphAppService:
    return GraphAppService(
        station_repo, block_repo, connection_repo, vehicle_repo, layout_repo
    )
```

- [ ] **Step 2: Verify lint passes**

```bash
uv run ruff check api/dependencies.py && uv run lint-imports
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add api/dependencies.py
git commit -m "refactor: wire LayoutRepository into DI container"
```

---

### Task 7: Squash Alembic migrations

**Files:**
- Delete: `infra/postgres/alembic/versions/7b68506b7d08_create_schema.py`
- Delete: `infra/postgres/alembic/versions/001833da5c49_update_node_layout_coordinates.py`
- Create: `infra/postgres/alembic/versions/<new_rev>_create_schema.py`

- [ ] **Step 1: Delete old migrations and generate a new one**

```bash
rm infra/postgres/alembic/versions/7b68506b7d08_create_schema.py
rm infra/postgres/alembic/versions/001833da5c49_update_node_layout_coordinates.py
```

- [ ] **Step 2: Create the squashed migration**

Create a single migration file. Use `alembic revision` to generate the revision ID, then write the full migration that:
1. Creates all tables (blocks, node_connections, node_layouts, stations, vehicles, platforms, services, junction_blocks)
2. Seeds all reference data including junctions

The migration should import from `infra.seed` (including the new `create_junction_blocks`) and `infra.postgres.tables` (including `junction_blocks_table`).

The seed section appends after the existing seed pattern:

```python
junction_blocks = create_junction_blocks()
conn.execute(
    junction_blocks_table.insert(),
    [
        {"from_block_id": fb, "to_block_id": tb, "junction_id": jid}
        for fb, tb, jid in junction_blocks
    ],
)
```

- [ ] **Step 3: Commit**

```bash
git add infra/postgres/alembic/versions/
git commit -m "chore: squash migrations into single schema with junction support"
```

---

### Task 8: Update postgres integration tests

**Files:**
- Modify: `tests/infra/test_postgres_node_layout_repo.py` → rename to `tests/infra/test_postgres_layout_repo.py`
- Modify: `tests/api/test_graph_routes.py`

- [ ] **Step 1: Replace layout repo test**

Delete old file and create `tests/infra/test_postgres_layout_repo.py`:

```python
from uuid import uuid7

import pytest
from infra.postgres.layout_repo import PostgresLayoutRepository
from infra.postgres.tables import junction_blocks_table, node_layouts_table
from sqlalchemy.dialects.postgresql import insert

pytestmark = pytest.mark.postgres


class TestPostgresLayoutRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresLayoutRepository(pg_session)

    async def test_find_all_empty(self, repo):
        result = await repo.find_all()
        assert result.positions == {}
        assert result.junction_blocks == {}

    async def test_find_all_returns_positions(self, repo, pg_session):
        node_id = uuid7()
        await pg_session.execute(
            insert(node_layouts_table).values(node_id=node_id, x=100.0, y=200.0)
        )
        await pg_session.commit()

        result = await repo.find_all()
        assert result.positions[node_id] == (100.0, 200.0)

    async def test_find_all_returns_junction_blocks(self, repo, pg_session):
        junction_id = uuid7()
        block_a = uuid7()
        block_b = uuid7()

        await pg_session.execute(
            insert(node_layouts_table).values(node_id=junction_id, x=1.0, y=2.0)
        )
        await pg_session.execute(
            insert(junction_blocks_table).values(
                from_block_id=block_a, to_block_id=block_b, junction_id=junction_id
            )
        )
        await pg_session.commit()

        result = await repo.find_all()
        assert result.junction_blocks[(block_a, block_b)] == junction_id
```

- [ ] **Step 2: Delete old test file**

```bash
rm tests/infra/test_postgres_node_layout_repo.py
```

- [ ] **Step 3: Update `tests/api/test_graph_routes.py`**

Rewrite to test edges/junctions instead of block nodes and connections:

```python
import pytest
from infra.seed import VEHICLE_ID_BY_NAME
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

pytestmark = pytest.mark.postgres


async def _create_service(client):
    vid = str(VEHICLE_ID_BY_NAME["V1"])
    resp = await client.post("services", json={"name": "S1", "vehicle_id": vid})
    assert resp.status_code == HTTP_201_CREATED
    return resp.json()["id"]


class TestServiceDetailGraph:
    async def test_service_detail_includes_graph(self, client):
        sid = await _create_service(client)
        resp = await client.get(f"services/{sid}")
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert "graph" in data
        graph = data["graph"]
        assert "nodes" in graph
        assert "edges" in graph
        assert "junctions" in graph
        assert "stations" in graph
        assert "vehicles" in graph

    async def test_graph_has_yard_node(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        yard_nodes = [n for n in graph["nodes"] if n["type"] == "yard"]
        assert len(yard_nodes) == 1
        assert yard_nodes[0]["name"] == "Y"

    async def test_graph_has_all_platform_nodes(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        platform_nodes = [n for n in graph["nodes"] if n["type"] == "platform"]
        names = {p["name"] for p in platform_nodes}
        assert names == {"P1A", "P1B", "P2A", "P2B", "P3A", "P3B"}

    async def test_graph_node_count(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        # 1 yard + 6 platforms = 7 nodes (blocks are now edges)
        assert len(graph["nodes"]) == 7

    async def test_graph_has_edges_for_all_blocks(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        edge_names = {e["name"] for e in graph["edges"]}
        assert edge_names == {f"B{i}" for i in range(1, 15)}

    async def test_edges_have_from_and_to(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        for edge in graph["edges"]:
            assert "from_id" in edge
            assert "to_id" in edge
            assert "id" in edge
            assert "name" in edge

    async def test_graph_has_four_junctions(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        assert len(graph["junctions"]) == 4
        for junction in graph["junctions"]:
            assert "id" in junction
            assert "x" in junction
            assert "y" in junction

    async def test_platform_station_lookup_via_stations(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        p1a = next(n for n in graph["nodes"] if n.get("name") == "P1A")
        s1 = next(s for s in graph["stations"] if s["name"] == "S1")
        assert p1a["id"] in s1["platform_ids"]

    async def test_graph_has_stations(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        station_names = {s["name"] for s in graph["stations"]}
        assert station_names == {"Y", "S1", "S2", "S3"}

    async def test_graph_has_vehicles(self, client):
        sid = await _create_service(client)
        graph = (await client.get(f"services/{sid}")).json()["graph"]
        vehicle_names = {v["name"] for v in graph["vehicles"]}
        assert vehicle_names == {"V1", "V2", "V3"}
```

- [ ] **Step 4: Commit**

```bash
git add tests/infra/test_postgres_layout_repo.py tests/api/test_graph_routes.py && git rm tests/infra/test_postgres_node_layout_repo.py
git commit -m "test: update integration tests for edges/junctions graph response"
```

---

### Task 9: Run full test suite and verify

- [ ] **Step 1: Run unit tests**

```bash
uv run pytest -v
```

Expected: All non-postgres tests PASS.

- [ ] **Step 2: Run import-linter**

```bash
uv run lint-imports
```

Expected: All 3 contracts KEPT.

- [ ] **Step 3: Run ruff**

```bash
uv run ruff check . && uv run ruff format --check .
```

Expected: No errors.

- [ ] **Step 4: Run postgres integration tests** (requires running container)

```bash
uv run pytest -m postgres -v
```

Expected: All postgres tests PASS.

- [ ] **Step 5: Final commit (if any fixes needed)**

```bash
git commit -m "fix: address test/lint issues from junction layout changes"
```
