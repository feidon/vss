# Graph Layout & Route Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add spatial coordinates to the graph API for frontend track map rendering, and a route validation endpoint for interactive route building with single-service battery checking.

**Architecture:** Extends the existing hexagonal architecture. Node layout is a read-side concern (no domain entity). Route validation reuses existing RouteFinder and conflict detection with extracted shared logic. Conflict detector is reorganized from a single file into a package.

**Tech Stack:** Python 3.14, FastAPI, SQLAlchemy Core (async), PostgreSQL, Pydantic, pytest

**Spec:** `docs/superpowers/specs/2026-04-02-graph-layout-and-route-validation-design.md`

---

## File Map

### New Files

| File | Responsibility |
|------|---------------|
| `infra/postgres/node_layout_repo.py` | PostgreSQL repository for node layouts |
| `infra/memory/node_layout_repo.py` | In-memory repository for node layouts |
| `application/graph/node_layout_repository.py` | Read-only repository interface (application layer, not domain — rendering concern) |
| `api/route/__init__.py` | Package init |
| `api/route/routes.py` | `POST /routes/validate` endpoint |
| `api/route/schemas.py` | Request/response schemas for route validation (imports `RouteStopInput` from `api/service/schemas.py`) |
| `domain/domain_service/conflict/__init__.py` | Re-exports public API |
| `domain/domain_service/conflict/model.py` | Conflict value objects |
| `domain/domain_service/conflict/preparation.py` | Data building functions (public) |
| `domain/domain_service/conflict/detection.py` | Detection logic |
| `domain/domain_service/conflict/service.py` | `detect_conflicts()` entry point |
| `tests/domain/test_conflict_preparation.py` | Tests for public preparation functions |
| `tests/domain/test_conflict_detection.py` | Tests for detection functions |
| `tests/application/test_validate_route.py` | Tests for validate_route app service method |
| `tests/api/test_route_routes.py` | API tests for `POST /routes/validate` |
| `tests/infra/test_postgres_node_layout_repo.py` | PostgreSQL node layout repo tests |

### Modified Files

| File | Changes |
|------|---------|
| `infra/postgres/tables.py` | Add `node_layouts_table` |
| `infra/seed.py` | Add `create_node_layouts()` returning `dict[UUID, tuple[float, float]]` |
| `infra/postgres/seed.py` | Seed `node_layouts_table` |
| `api/dependencies.py` | Add `get_node_layout_repo`, update `get_graph_service` |
| `api/graph/schemas.py` | Add `x, y` to node schemas in `GraphResponse.from_graph_data()` |
| `api/shared/schemas.py` | Add `x, y` fields to `BlockNodeSchema`, `PlatformNodeSchema`, `YardNodeSchema` |
| `application/graph/service.py` | Inject `NodeLayoutRepository`, merge coords into `GraphData` |
| `application/graph/dto.py` | Add `layouts` field to `GraphData` |
| `application/service/dto.py` | Rename `platform_id` → `node_id` in `RouteStop` |
| `application/service/service.py` | Extract `_build_route()`, add `validate_route()`, rename platform refs to node/stop refs, support yard stops |
| `api/service/schemas.py` | Rename `platform_id` → `node_id` in `RouteStopInput` |
| `api/service/routes.py` | Update `RouteStop` construction to use `node_id`, fix `InsufficientChargeConflict` serialization bug |
| `main.py` | Register route router |
| `tests/application/test_update_route.py` | Update `RouteStop(platform_id=...)` → `RouteStop(node_id=...)` |
| `tests/domain/test_conflict.py` | Move/adapt tests to new package structure |

### Deleted Files

| File | Reason |
|------|--------|
| `domain/domain_service/conflict.py` | Replaced by `domain/domain_service/conflict/` package |

---

## Task 1: Reorganize Conflict Detector into Package

Extract the existing single-file conflict detector into a package with separate modules. No logic changes — pure structural refactor.

**Files:**
- Create: `domain/domain_service/conflict/__init__.py`
- Create: `domain/domain_service/conflict/model.py`
- Create: `domain/domain_service/conflict/preparation.py`
- Create: `domain/domain_service/conflict/detection.py`
- Create: `domain/domain_service/conflict/service.py`
- Delete: `domain/domain_service/conflict.py`
- Modify: `tests/domain/test_conflict.py` (update imports)

- [ ] **Step 1: Create conflict package with model.py**

Move all frozen dataclasses (public + private value objects) from `conflict.py:15-157` into `domain/domain_service/conflict/model.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from domain.network.model import NodeType
from domain.shared.types import EpochSeconds


# ── Public value objects ────────────────────────────────────


@dataclass(frozen=True)
class VehicleConflict:
    vehicle_id: UUID
    service_a_id: int
    service_b_id: int
    reason: str


@dataclass(frozen=True)
class BlockConflict:
    block_id: UUID
    service_a_id: int
    service_b_id: int
    overlap_start: int
    overlap_end: int

    @classmethod
    def from_overlap(cls, block_id: UUID, a: BlockOccupancy, b: BlockOccupancy) -> BlockConflict:
        return cls(
            block_id=block_id,
            service_a_id=a.service_id,
            service_b_id=b.service_id,
            overlap_start=b.arrival,
            overlap_end=a.departure,
        )


@dataclass(frozen=True)
class InterlockingConflict:
    group: int
    block_a_id: UUID
    block_b_id: UUID
    service_a_id: int
    service_b_id: int
    overlap_start: int
    overlap_end: int

    @classmethod
    def from_overlap(cls, group: int, a: GroupOccupancy, b: GroupOccupancy) -> InterlockingConflict:
        return cls(
            group=group,
            block_a_id=a.block_id,
            block_b_id=b.block_id,
            service_a_id=a.service_id,
            service_b_id=b.service_id,
            overlap_start=b.arrival,
            overlap_end=a.departure,
        )


@dataclass(frozen=True)
class LowBatteryConflict:
    service_id: int


@dataclass(frozen=True)
class InsufficientChargeConflict:
    service_id: int


@dataclass(frozen=True)
class ServiceConflicts:
    vehicle_conflicts: list[VehicleConflict]
    block_conflicts: list[BlockConflict]
    interlocking_conflicts: list[InterlockingConflict]
    low_battery_conflicts: list[LowBatteryConflict] = field(default_factory=list)
    insufficient_charge_conflicts: list[InsufficientChargeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(
            self.vehicle_conflicts
            or self.block_conflicts
            or self.interlocking_conflicts
            or self.low_battery_conflicts
            or self.insufficient_charge_conflicts
        )


# ── Data structures for preparation/detection ──────────────


class Timed(Protocol):
    arrival: EpochSeconds
    departure: EpochSeconds


@dataclass(frozen=True)
class ServiceWindow:
    service_id: int
    start: EpochSeconds
    end: EpochSeconds


@dataclass(frozen=True)
class ServiceEndpoints:
    service_id: int
    first_node_id: UUID
    last_node_id: UUID
    start: EpochSeconds


@dataclass(frozen=True)
class VehicleSchedule:
    windows: list[ServiceWindow]
    endpoints: list[ServiceEndpoints]


@dataclass(frozen=True)
class BlockOccupancy:
    service_id: int
    arrival: EpochSeconds
    departure: EpochSeconds


@dataclass(frozen=True)
class GroupOccupancy:
    service_id: int
    block_id: UUID
    arrival: EpochSeconds
    departure: EpochSeconds


@dataclass(frozen=True)
class NodeEntry:
    time: EpochSeconds
    node_type: NodeType
    service_id: int


@dataclass(frozen=True)
class ChargeStop:
    charge_seconds: int
    service_id: int


@dataclass(frozen=True)
class BlockTraversal:
    service_id: int
```

Note: All private `_`-prefixed types are now public (no underscore). `from_overlap` references updated from `_BlockOccupancy` → `BlockOccupancy`, `_GroupOccupancy` → `GroupOccupancy`.

- [ ] **Step 2: Create preparation.py**

Move data preparation functions from `conflict.py:205-281` into `domain/domain_service/conflict/preparation.py`. Remove `_` prefix:

```python
from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from domain.block.model import Block
from domain.network.model import NodeType
from domain.service.model import Service
from domain.domain_service.conflict.model import (
    BlockOccupancy,
    BlockTraversal,
    ChargeStop,
    GroupOccupancy,
    NodeEntry,
    ServiceEndpoints,
    ServiceWindow,
    VehicleSchedule,
)


def build_vehicle_schedule(
    vehicle_id: UUID,
    services: list[Service],
) -> VehicleSchedule:
    windows: list[ServiceWindow] = []
    endpoints: list[ServiceEndpoints] = []
    for svc in services:
        if svc.vehicle_id != vehicle_id or not svc.timetable:
            continue

        entries = sorted(svc.timetable, key=lambda e: e.order)

        windows.append(ServiceWindow(
            service_id=svc.id,
            start=min(e.arrival for e in entries),
            end=max(e.departure for e in entries),
        ))

        endpoints.append(ServiceEndpoints(
            service_id=svc.id,
            first_node_id=entries[0].node_id,
            last_node_id=entries[-1].node_id,
            start=min(e.arrival for e in entries),
        ))

    windows.sort(key=lambda w: w.start)
    endpoints.sort(key=lambda w: w.start)
    return VehicleSchedule(windows, endpoints)


def build_occupancies(
    services: list[Service],
    blocks: list[Block],
) -> tuple[dict[UUID, list[BlockOccupancy]], dict[int, list[GroupOccupancy]]]:
    block_by_id = {b.id: b for b in blocks}
    by_block: dict[UUID, list[BlockOccupancy]] = defaultdict(list)
    by_group: dict[int, list[GroupOccupancy]] = defaultdict(list)
    for svc in services:
        for entry in svc.timetable:
            block = block_by_id.get(entry.node_id)
            if block is None:
                continue
            by_block[entry.node_id].append(
                BlockOccupancy(svc.id, entry.arrival, entry.departure),
            )
            by_group[block.group].append(
                GroupOccupancy(svc.id, block.id, entry.arrival, entry.departure),
            )
    return (by_block, by_group)


def build_battery_steps(
    vehicle_id: UUID,
    services: list[Service],
) -> list[ChargeStop | BlockTraversal]:
    node_entries: list[NodeEntry] = []

    for service in services:
        if service.vehicle_id != vehicle_id or not service.timetable:
            continue

        node_map = {n.id: n.type for n in service.path}
        for t in service.timetable:
            if node_map[t.node_id] != NodeType.PLATFORM:
                node_entries.append(NodeEntry(t.arrival, node_map[t.node_id], service.id))

    node_entries.sort(key=lambda e: e.time)

    steps: list[ChargeStop | BlockTraversal] = []
    for i, entry in enumerate(node_entries):
        if entry.node_type == NodeType.YARD:
            next_time = node_entries[i + 1].time if i + 1 < len(node_entries) else entry.time
            steps.append(ChargeStop(next_time - entry.time, entry.service_id))
        else:
            steps.append(BlockTraversal(entry.service_id))

    return steps
```

- [ ] **Step 3: Create detection.py**

Move detection functions from `conflict.py:287-389` into `domain/domain_service/conflict/detection.py`:

```python
from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from domain.vehicle.model import Vehicle
from domain.domain_service.conflict.model import (
    BlockConflict,
    BlockOccupancy,
    BlockTraversal,
    ChargeStop,
    GroupOccupancy,
    InsufficientChargeConflict,
    InterlockingConflict,
    LowBatteryConflict,
    ServiceEndpoints,
    ServiceWindow,
    Timed,
    VehicleConflict,
)


def find_time_overlaps[T: Timed](entries: list[T]) -> list[tuple[T, T]]:
    sorted_entries = sorted(entries, key=lambda x: x.arrival)
    pairs: list[tuple[T, T]] = []

    for i in range(len(sorted_entries)):
        dep_i = sorted_entries[i].departure
        for j in range(i + 1, len(sorted_entries)):
            if sorted_entries[j].arrival >= dep_i:
                break
            pairs.append((sorted_entries[i], sorted_entries[j]))

    return pairs


def detect_time_overlap_conflicts(
    vehicle_id: UUID,
    windows: list[ServiceWindow],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []
    for i in range(len(windows)):
        for j in range(i + 1, len(windows)):
            prev, curr = windows[i], windows[j]
            if curr.start >= prev.end:
                break
            conflicts.append(VehicleConflict(
                vehicle_id, prev.service_id, curr.service_id,
                "Overlapping time windows",
            ))
    return conflicts


def detect_location_discontinuity_conflicts(
    vehicle_id: UUID,
    endpoints: list[ServiceEndpoints],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []
    for i in range(1, len(endpoints)):
        prev, curr = endpoints[i - 1], endpoints[i]
        if curr.first_node_id != prev.last_node_id:
            conflicts.append(VehicleConflict(
                vehicle_id, prev.service_id, curr.service_id,
                "Location discontinuity",
            ))
    return conflicts


def detect_block_conflicts(
    by_block: dict[UUID, list[BlockOccupancy]],
) -> list[BlockConflict]:
    conflicts: list[BlockConflict] = []
    for block_id, occupancies in by_block.items():
        for a, b in find_time_overlaps(occupancies):
            conflicts.append(BlockConflict.from_overlap(block_id, a, b))
    return conflicts


def detect_interlocking_conflicts(
    by_group: dict[int, list[GroupOccupancy]],
) -> list[InterlockingConflict]:
    conflicts: list[InterlockingConflict] = []
    for group, occupancies in by_group.items():
        if group == 0:
            continue
        for a, b in find_time_overlaps(occupancies):
            if a.block_id == b.block_id:
                continue
            conflicts.append(InterlockingConflict.from_overlap(group, a, b))
    return conflicts


def detect_battery_conflicts(
    vehicle: Vehicle,
    steps: list[ChargeStop | BlockTraversal],
) -> tuple[list[LowBatteryConflict], list[InsufficientChargeConflict]]:
    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []

    if not steps:
        return (low_battery, insufficient_charge)

    sim = replace(vehicle)

    for step in steps:
        match step:
            case ChargeStop():
                sim.charge(step.charge_seconds)
                if not sim.can_depart():
                    insufficient_charge.append(InsufficientChargeConflict(service_id=step.service_id))
                    break
            case BlockTraversal():
                sim.traverse_block()
                if sim.is_battery_critical():
                    low_battery.append(LowBatteryConflict(service_id=step.service_id))
                    break

    return (low_battery, insufficient_charge)
```

- [ ] **Step 4: Create service.py (entry point)**

Move `detect_conflicts()` from `conflict.py:162-199` into `domain/domain_service/conflict/service.py`:

```python
from __future__ import annotations

from domain.block.model import Block
from domain.service.model import Service
from domain.vehicle.model import Vehicle
from domain.domain_service.conflict.model import (
    InsufficientChargeConflict,
    LowBatteryConflict,
    ServiceConflicts,
)
from domain.domain_service.conflict.preparation import (
    build_battery_steps,
    build_occupancies,
    build_vehicle_schedule,
)
from domain.domain_service.conflict.detection import (
    detect_battery_conflicts,
    detect_block_conflicts,
    detect_interlocking_conflicts,
    detect_location_discontinuity_conflicts,
    detect_time_overlap_conflicts,
)


def detect_conflicts(
    candidate: Service,
    other_services: list[Service],
    blocks: list[Block],
    vehicles: list[Vehicle] | None = None,
) -> ServiceConflicts:
    all_services = [s for s in other_services if s.id != candidate.id]
    all_services.append(candidate)

    schedule = build_vehicle_schedule(candidate.vehicle_id, all_services)
    block_occupancies, group_occupancies = build_occupancies(all_services, blocks)

    low_battery: list[LowBatteryConflict] = []
    insufficient_charge: list[InsufficientChargeConflict] = []
    if vehicles:
        vehicle_by_id = {v.id: v for v in vehicles}
        candidate_vehicle = vehicle_by_id.get(candidate.vehicle_id)
        if candidate_vehicle is not None:
            battery_steps = build_battery_steps(
                candidate_vehicle.id, all_services,
            )
            low_battery, insufficient_charge = detect_battery_conflicts(
                candidate_vehicle, battery_steps,
            )

    vehicle_conflicts = (
        detect_time_overlap_conflicts(candidate.vehicle_id, schedule.windows)
        + detect_location_discontinuity_conflicts(candidate.vehicle_id, schedule.endpoints)
    )

    return ServiceConflicts(
        vehicle_conflicts=vehicle_conflicts,
        block_conflicts=detect_block_conflicts(block_occupancies),
        interlocking_conflicts=detect_interlocking_conflicts(group_occupancies),
        low_battery_conflicts=low_battery,
        insufficient_charge_conflicts=insufficient_charge,
    )
```

- [ ] **Step 5: Create `__init__.py` with re-exports**

```python
from domain.domain_service.conflict.model import (
    BlockConflict,
    InsufficientChargeConflict,
    InterlockingConflict,
    LowBatteryConflict,
    ServiceConflicts,
    VehicleConflict,
)
from domain.domain_service.conflict.service import detect_conflicts

__all__ = [
    "BlockConflict",
    "InsufficientChargeConflict",
    "InterlockingConflict",
    "LowBatteryConflict",
    "ServiceConflicts",
    "VehicleConflict",
    "detect_conflicts",
]
```

- [ ] **Step 6: Delete old `conflict.py`**

```bash
rm domain/domain_service/conflict.py
```

- [ ] **Step 7: Update imports in consumers**

Update `application/service/service.py:12`:
```python
# Before:
from domain.domain_service.conflict import detect_conflicts
# After (no change needed — __init__.py re-exports it):
from domain.domain_service.conflict import detect_conflicts
```

Update `application/service/errors.py` if it imports conflict types — check and update.

Update `api/service/routes.py` if it imports conflict types directly.

- [ ] **Step 8: Update existing test imports in `tests/domain/test_conflict.py`**

All imports from `domain.domain_service.conflict` should still work via `__init__.py`. Verify by running:

```bash
uv run pytest tests/domain/test_conflict.py -v
```

- [ ] **Step 9: Run full test suite**

```bash
uv run pytest -v
```

Expected: All existing tests pass with zero changes to test logic.

- [ ] **Step 10: Commit**

```bash
git add domain/domain_service/conflict/ tests/domain/test_conflict.py
git add -u  # catches deletion of conflict.py
git commit -m "refactor: reorganize conflict detector into package"
```

---

## Task 2: Fix InsufficientChargeConflict Serialization Bug

Fix the pre-existing bug where `api/service/routes.py:66-68` references `icc.service_a_id` and `icc.service_b_id` but `InsufficientChargeConflict` only has `service_id`.

**Files:**
- Modify: `api/service/routes.py:66-68`

- [ ] **Step 1: Fix the serialization**

In `api/service/routes.py`, change lines 66-68:

```python
# Before:
"insufficient_charge_conflicts": [
    {"service_a_id": icc.service_a_id, "service_b_id": icc.service_b_id}
    for icc in c.insufficient_charge_conflicts
],

# After:
"insufficient_charge_conflicts": [
    {"service_id": icc.service_id}
    for icc in c.insufficient_charge_conflicts
],
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add api/service/routes.py
git commit -m "fix: InsufficientChargeConflict serialization uses correct field"
```

---

## Task 3: Rename `platform_id` → `node_id` in RouteStop

Yards are now valid stops alongside platforms. Rename the field across all layers.

**Files:**
- Modify: `application/service/dto.py`
- Modify: `api/service/schemas.py:25-27`
- Modify: `api/service/routes.py:118-119`
- Modify: `application/service/service.py:81,101-107,110-127`
- Modify: `tests/application/test_update_route.py` (all `RouteStop(platform_id=...)`)

- [ ] **Step 1: Update `RouteStop` DTO**

In `application/service/dto.py`:

```python
# Before:
@dataclass(frozen=True)
class RouteStop:
    platform_id: UUID
    dwell_time: int  # seconds

# After:
@dataclass(frozen=True)
class RouteStop:
    node_id: UUID
    dwell_time: int  # seconds
```

- [ ] **Step 2: Update `RouteStopInput` schema**

In `api/service/schemas.py:25-27`:

```python
# Before:
class RouteStopInput(BaseModel):
    platform_id: UUID
    dwell_time: int = Field(ge=0)

# After:
class RouteStopInput(BaseModel):
    node_id: UUID
    dwell_time: int = Field(ge=0)
```

- [ ] **Step 3: Update route handler**

In `api/service/routes.py:118-119`:

```python
# Before:
stops = [
    RouteStop(platform_id=s.platform_id, dwell_time=s.dwell_time)
    for s in request.stops
]

# After:
stops = [
    RouteStop(node_id=s.node_id, dwell_time=s.dwell_time)
    for s in request.stops
]
```

- [ ] **Step 4: Update ServiceAppService**

In `application/service/service.py`:

Rename `_validate_platforms_exist` → `_validate_stops_exist`. Update to accept both platform IDs and yard station IDs:

```python
@staticmethod
def _validate_stops_exist(
    stops: list[RouteStop],
    all_platforms: dict[UUID, object],
    yard_ids: set[UUID],
) -> None:
    valid_ids = set(all_platforms.keys()) | yard_ids
    for stop in stops:
        if stop.node_id not in valid_ids:
            raise ValueError(f"Stop {stop.node_id} not found")
```

Update `_build_node_path` to handle yard nodes:

```python
@staticmethod
def _build_node_path(
    stops: list[RouteStop],
    connections: frozenset,
    all_blocks: list[Block],
    all_platforms: dict[UUID, object],
    yard_ids: set[UUID],
) -> list[Node]:
    block_ids = {b.id for b in all_blocks}
    stop_ids = [s.node_id for s in stops]
    full_path_ids = RouteFinder.build_full_path(stop_ids, connections, block_ids)

    node_types: dict[UUID, NodeType] = {}
    for b in all_blocks:
        node_types[b.id] = NodeType.BLOCK
    for pid in all_platforms:
        node_types[pid] = NodeType.PLATFORM
    for yid in yard_ids:
        node_types[yid] = NodeType.YARD

    return [Node(id=nid, type=node_types[nid]) for nid in full_path_ids]
```

Update `update_service_route` to compute `yard_ids` and pass to the renamed methods:

```python
async def update_service_route(
    self, id: int, stops: list[RouteStop], start_time: EpochSeconds
) -> Service:
    service = await self.get_service(id)

    stations = await self._station_repo.find_all()
    all_platforms = {p.id: p for s in stations for p in s.platforms}
    yard_ids = {s.id for s in stations if s.is_yard}
    self._validate_stops_exist(stops, all_platforms, yard_ids)

    connections = await self._connection_repo.find_all()
    all_blocks = await self._block_repo.find_all()

    full_path = self._build_node_path(stops, connections, all_blocks, all_platforms, yard_ids)
    timetable = self._compute_timetable(
        full_path,
        {b.id: b for b in all_blocks},
        {s.node_id: s.dwell_time for s in stops},
        start_time,
    )

    service.update_route(full_path, timetable, connections)

    all_services = await self._service_repo.find_all()
    all_vehicles = await self._vehicle_repo.find_all()
    conflicts = detect_conflicts(
        service, all_services, all_blocks, all_vehicles,
    )
    if conflicts.has_conflicts:
        raise ConflictError(conflicts)

    await self._service_repo.save(service)
    return service
```

Note the change on the dwell_by_stop dict: `s.platform_id` → `s.node_id`.

Also rename the `dwell_by_stop` parameter in `_compute_timetable` (line 132 of current file):

```python
# Before:
def _compute_timetable(
    full_path: list[Node],
    blocks_by_id: dict[UUID, Block],
    dwell_by_platform: dict[UUID, int],
    start_time: EpochSeconds,
) -> list[TimetableEntry]:

# After:
def _compute_timetable(
    full_path: list[Node],
    blocks_by_id: dict[UUID, Block],
    dwell_by_stop: dict[UUID, int],
    start_time: EpochSeconds,
) -> list[TimetableEntry]:
```

And update the reference inside the method body: `dwell_by_platform.get(node.id, 0)` → `dwell_by_stop.get(node.id, 0)`.

- [ ] **Step 5: Update all tests**

In `tests/application/test_update_route.py`, replace all `RouteStop(platform_id=...)` with `RouteStop(node_id=...)`. Use find-and-replace:

```python
# Before:
RouteStop(platform_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60)
# After:
RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60)
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest -v
```

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add application/service/dto.py api/service/schemas.py api/service/routes.py application/service/service.py tests/application/test_update_route.py
git commit -m "refactor: rename platform_id to node_id in RouteStop for yard support"
```

---

## Task 4: Add Node Layout Infrastructure

Add the `node_layouts` table, repository interface, implementations, and seed data.

**Files:**
- Modify: `infra/postgres/tables.py`
- Create: `application/graph/node_layout_repository.py`
- Create: `infra/postgres/node_layout_repo.py`
- Create: `infra/memory/node_layout_repo.py`
- Modify: `infra/seed.py`
- Modify: `infra/postgres/seed.py`
- Test: `tests/infra/test_postgres_node_layout_repo.py`

- [ ] **Step 1: Write failing test for postgres node layout repo**

Create `tests/infra/test_postgres_node_layout_repo.py`:

```python
from uuid import uuid7

import pytest

from infra.postgres.node_layout_repo import PostgresNodeLayoutRepository

pytestmark = pytest.mark.postgres


class TestPostgresNodeLayoutRepository:
    @pytest.fixture
    def repo(self, pg_session):
        return PostgresNodeLayoutRepository(pg_session)

    async def test_find_all_empty(self, repo):
        layouts = await repo.find_all()
        assert layouts == {}

    async def test_find_all_returns_seeded_data(self, repo, pg_session):
        from sqlalchemy.dialects.postgresql import insert
        from infra.postgres.tables import node_layouts_table

        node_id = uuid7()
        await pg_session.execute(
            insert(node_layouts_table).values(node_id=node_id, x=100.0, y=200.0)
        )
        await pg_session.commit()

        layouts = await repo.find_all()
        assert node_id in layouts
        assert layouts[node_id] == (100.0, 200.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/infra/test_postgres_node_layout_repo.py -v -m postgres
```

Expected: ImportError (module doesn't exist yet).

- [ ] **Step 3: Add `node_layouts_table` to tables.py**

In `infra/postgres/tables.py`, add after `node_connections_table`:

```python
node_layouts_table = Table(
    "node_layouts",
    metadata,
    Column("node_id", Uuid, primary_key=True),
    Column("x", Float, nullable=False),
    Column("y", Float, nullable=False),
)
```

Add `Float` to the import:

```python
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Uuid,
)
```

- [ ] **Step 4: Create repository interface**

Create `application/graph/node_layout_repository.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class NodeLayoutRepository(ABC):
    @abstractmethod
    async def find_all(self) -> dict[UUID, tuple[float, float]]:
        """Return {node_id: (x, y)} for all nodes with layout data."""
```

- [ ] **Step 5: Create PostgreSQL implementation**

Create `infra/postgres/node_layout_repo.py`:

```python
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.graph.node_layout_repository import NodeLayoutRepository
from infra.postgres.tables import node_layouts_table


class PostgresNodeLayoutRepository(NodeLayoutRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> dict[UUID, tuple[float, float]]:
        result = await self._session.execute(select(node_layouts_table))
        return {
            row.node_id: (row.x, row.y)
            for row in result.mappings().all()
        }
```

- [ ] **Step 6: Create in-memory implementation**

Create `infra/memory/node_layout_repo.py`:

```python
from __future__ import annotations

from uuid import UUID

from application.graph.node_layout_repository import NodeLayoutRepository


class InMemoryNodeLayoutRepository(NodeLayoutRepository):
    def __init__(self, layouts: dict[UUID, tuple[float, float]] | None = None) -> None:
        self._store: dict[UUID, tuple[float, float]] = dict(layouts) if layouts else {}

    async def find_all(self) -> dict[UUID, tuple[float, float]]:
        return dict(self._store)
```

- [ ] **Step 7: Add seed data for node layouts**

In `infra/seed.py`, add `create_node_layouts()` function. These are hand-authored x/y positions for the 21-node network. The layout follows the track topology left-to-right:

```python
def create_node_layouts() -> dict[UUID, tuple[float, float]]:
    """Hand-authored x/y positions for the track map.

    Layout: Y on the left, S1 center-left, S2 center, S3 right.
    Vertical spread separates A/B platform tracks.
    """
    b = BLOCK_ID_BY_NAME
    p = PLATFORM_ID_BY_NAME

    return {
        # Yard (leftmost)
        YARD_ID: (0.0, 150.0),
        # B1/B2 (yard to S1)
        b["B1"]: (75.0, 100.0),
        b["B2"]: (75.0, 200.0),
        # S1 platforms
        p["P1A"]: (150.0, 100.0),
        p["P1B"]: (150.0, 200.0),
        # S1 → S2 outbound
        b["B3"]: (225.0, 75.0),
        b["B4"]: (225.0, 175.0),
        b["B5"]: (300.0, 125.0),
        # S2 platforms
        p["P2A"]: (375.0, 100.0),
        p["P2B"]: (375.0, 200.0),
        # S2 → S3
        b["B6"]: (450.0, 100.0),
        b["B7"]: (525.0, 75.0),
        b["B8"]: (525.0, 125.0),
        # S3 platforms
        p["P3A"]: (600.0, 75.0),
        p["P3B"]: (600.0, 125.0),
        # S3 → S2 return
        b["B10"]: (525.0, 225.0),
        b["B9"]: (525.0, 275.0),
        b["B11"]: (450.0, 250.0),
        # S2 → S1 return
        b["B12"]: (300.0, 225.0),
        b["B13"]: (225.0, 225.0),
        b["B14"]: (225.0, 275.0),
    }
```

- [ ] **Step 8: Seed node layouts in PostgreSQL**

In `infra/postgres/seed.py`, add after the node_connections insert:

```python
from infra.postgres.tables import node_layouts_table
from infra.seed import create_node_layouts

# ... inside seed_database():

    # Node layouts
    layouts = create_node_layouts()
    await session.execute(
        insert(node_layouts_table)
        .values([{"node_id": nid, "x": x, "y": y} for nid, (x, y) in layouts.items()])
        .on_conflict_do_nothing(index_elements=["node_id"])
    )
```

Add the import of `node_layouts_table` and `create_node_layouts`.

- [ ] **Step 9: Generate Alembic migration (if Alembic is in use)**

Note: The project currently has an empty `versions/` directory (no existing migrations). If using `metadata.create_all` for schema management, skip this step. If adopting Alembic migrations:

```bash
cd /home/feidon/Documents/vss/backend
uv run alembic revision --autogenerate -m "add node_layouts table"
```

Review the generated migration file to ensure it only creates `node_layouts`.

- [ ] **Step 10: Run postgres tests**

```bash
uv run pytest tests/infra/test_postgres_node_layout_repo.py -v -m postgres
```

Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add infra/postgres/tables.py application/graph/node_layout_repository.py infra/postgres/node_layout_repo.py infra/memory/node_layout_repo.py infra/seed.py infra/postgres/seed.py tests/infra/test_postgres_node_layout_repo.py
git commit -m "feat: add node_layouts table and repositories for track map positioning"
```

---

## Task 5: Add Coordinates to Graph API Response

Merge x/y coordinates into the `/graph` response.

**Files:**
- Modify: `api/shared/schemas.py`
- Modify: `application/graph/dto.py`
- Modify: `application/graph/service.py`
- Modify: `api/graph/schemas.py`
- Modify: `api/dependencies.py`
- Test: `tests/application/test_graph_service.py`
- Test: `tests/api/test_graph_routes.py`

- [ ] **Step 1: Write failing test**

Add to `tests/application/test_graph_service.py`:

```python
async def test_get_graph_includes_layouts(self, ...):
    # Setup: create a graph service with a layout repo containing coords
    graph = await service.get_graph()
    assert graph.layouts is not None
    # Verify layouts dict is populated
```

The exact test depends on fixtures — add a `node_layout_repo` fixture. The key assertion is that `GraphData.layouts` is populated.

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/application/test_graph_service.py -v -k "layouts"
```

Expected: AttributeError — `GraphData` has no `layouts` field.

- [ ] **Step 3: Add `layouts` to `GraphData`**

In `application/graph/dto.py`, add the layouts field:

```python
@dataclass(frozen=True)
class GraphData:
    stations: list[Station]
    blocks: list[Block]
    connections: frozenset[NodeConnection]
    vehicles: list[Vehicle]
    layouts: dict[UUID, tuple[float, float]] = field(default_factory=dict)
```

Add `from dataclasses import field` and `from uuid import UUID` to imports.

- [ ] **Step 4: Update `GraphAppService` to inject and use layout repo**

In `application/graph/service.py`:

```python
from application.graph.node_layout_repository import NodeLayoutRepository

class GraphAppService:
    def __init__(
        self,
        station_repo: StationRepository,
        block_repo: BlockRepository,
        connection_repo: ConnectionRepository,
        vehicle_repo: VehicleRepository,
        node_layout_repo: NodeLayoutRepository,
    ) -> None:
        self._station_repo = station_repo
        self._block_repo = block_repo
        self._connection_repo = connection_repo
        self._vehicle_repo = vehicle_repo
        self._node_layout_repo = node_layout_repo

    async def get_graph(self) -> GraphData:
        stations = await self._station_repo.find_all()
        blocks = await self._block_repo.find_all()
        connections = await self._connection_repo.find_all()
        vehicles = await self._vehicle_repo.find_all()
        layouts = await self._node_layout_repo.find_all()
        return GraphData(
            stations=stations, blocks=blocks,
            connections=connections, vehicles=vehicles,
            layouts=layouts,
        )
```

- [ ] **Step 5: Add x, y to shared node schemas**

In `api/shared/schemas.py`. Use `= 0.0` defaults so that existing code constructing these schemas (e.g., `ServiceResponse.from_domain()`) continues to work without passing coordinates:

```python
class BlockNodeSchema(BaseModel):
    type: Literal["block"] = "block"
    id: UUID
    name: str
    group: int
    traversal_time_seconds: int
    x: float = 0.0
    y: float = 0.0


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
```

- [ ] **Step 6: Update `GraphResponse.from_graph_data()` to pass coordinates**

In `api/graph/schemas.py`, update `from_graph_data()`:

```python
@classmethod
def from_graph_data(cls, data: GraphData) -> GraphResponse:
    nodes: list[BlockNodeSchema | PlatformNodeSchema | YardNodeSchema] = []
    layouts = data.layouts

    yard = data.yard
    if yard is not None:
        x, y = layouts.get(yard.id, (0.0, 0.0))
        nodes.append(YardNodeSchema(id=yard.id, name=yard.name, x=x, y=y))

    for platform in data.all_platforms:
        x, y = layouts.get(platform.id, (0.0, 0.0))
        nodes.append(PlatformNodeSchema(id=platform.id, name=platform.name, x=x, y=y))

    for block in data.blocks:
        x, y = layouts.get(block.id, (0.0, 0.0))
        nodes.append(BlockNodeSchema(
            id=block.id,
            name=block.name,
            group=block.group,
            traversal_time_seconds=block.traversal_time_seconds,
            x=x, y=y,
        ))
    # ... rest unchanged
```

- [ ] **Step 7: Update `api/dependencies.py`**

Add node layout repo provider and update `get_graph_service`:

```python
from infra.postgres.node_layout_repo import PostgresNodeLayoutRepository
from infra.memory.node_layout_repo import InMemoryNodeLayoutRepository
from application.graph.node_layout_repository import NodeLayoutRepository
from infra.seed import create_node_layouts

# In postgres branch:
def get_node_layout_repo(session: AsyncSession = Depends(get_session)) -> NodeLayoutRepository:
    return PostgresNodeLayoutRepository(session)

# In memory branch:
_node_layout_repo = InMemoryNodeLayoutRepository(create_node_layouts())

def get_node_layout_repo() -> NodeLayoutRepository:
    return _node_layout_repo

# Update get_graph_service:
def get_graph_service(
    station_repo: StationRepository = Depends(get_station_repo),
    block_repo: BlockRepository = Depends(get_block_repo),
    connection_repo: ConnectionRepository = Depends(get_connection_repo),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
    node_layout_repo: NodeLayoutRepository = Depends(get_node_layout_repo),
) -> GraphAppService:
    return GraphAppService(station_repo, block_repo, connection_repo, vehicle_repo, node_layout_repo)
```

- [ ] **Step 8: Fix existing tests**

Update `tests/application/test_graph_service.py` — the `GraphAppService` constructor now requires a `node_layout_repo` parameter. Add an `InMemoryNodeLayoutRepository` fixture and pass it.

Update `tests/api/test_graph_routes.py` — if the test checks node structure, add assertions for `x` and `y` fields.

`ServiceResponse.from_domain()` continues to work without changes because the `x` and `y` fields default to `0.0`. Service responses will include `x=0.0, y=0.0` — acceptable tech debt since the frontend only uses coords from `/graph`.

- [ ] **Step 8b: Note about API test conftest**

The API test conftest does NOT need an explicit override for `get_node_layout_repo`. When `DB != "postgres"`, `dependencies.py` takes the `else` branch and returns an `InMemoryNodeLayoutRepository(create_node_layouts())` — pre-populated with the correct seed data. When `DB=postgres` (integration tests), the postgres branch resolves through `get_session`. Either way, the repo has correct layout data without a conftest override. The `node_layouts_table` is created by `metadata.create_all` and truncated by `metadata.sorted_tables` in the conftest — both pick up the new table automatically.

- [ ] **Step 9: Run full tests**

```bash
uv run pytest -v
```

Expected: All tests pass.

- [ ] **Step 10: Commit**

```bash
git add api/shared/schemas.py application/graph/dto.py application/graph/service.py api/graph/schemas.py api/dependencies.py tests/
git commit -m "feat: add x/y coordinates to graph API response"
```

---

## Task 6: Extract Shared Route Building Logic

Extract `_build_route()` from `update_service_route()` so it can be reused by `validate_route()`.

**Files:**
- Modify: `application/service/service.py`

- [ ] **Step 1: Extract `_build_route` method**

In `application/service/service.py`, add a new method that encapsulates the shared steps (validate stops, expand path, compute timetable):

```python
async def _build_route(
    self, stops: list[RouteStop], start_time: EpochSeconds,
) -> tuple[list[Node], list[TimetableEntry]]:
    """Validate stops, expand path via RouteFinder, compute timetable."""
    stations = await self._station_repo.find_all()
    all_platforms = {p.id: p for s in stations for p in s.platforms}
    yard_ids = {s.id for s in stations if s.is_yard}
    self._validate_stops_exist(stops, all_platforms, yard_ids)

    connections = await self._connection_repo.find_all()
    all_blocks = await self._block_repo.find_all()

    full_path = self._build_node_path(stops, connections, all_blocks, all_platforms, yard_ids)
    timetable = self._compute_timetable(
        full_path,
        {b.id: b for b in all_blocks},
        {s.node_id: s.dwell_time for s in stops},
        start_time,
    )
    return full_path, timetable
```

- [ ] **Step 2: Refactor `update_service_route` to use `_build_route`**

```python
async def update_service_route(
    self, id: int, stops: list[RouteStop], start_time: EpochSeconds
) -> Service:
    service = await self.get_service(id)

    full_path, timetable = await self._build_route(stops, start_time)
    connections = await self._connection_repo.find_all()
    service.update_route(full_path, timetable, connections)

    all_services = await self._service_repo.find_all()
    all_blocks = await self._block_repo.find_all()
    all_vehicles = await self._vehicle_repo.find_all()
    conflicts = detect_conflicts(
        service, all_services, all_blocks, all_vehicles,
    )
    if conflicts.has_conflicts:
        raise ConflictError(conflicts)

    await self._service_repo.save(service)
    return service
```

Note: `_build_route` fetches connections and blocks internally. `update_service_route` also needs them for `service.update_route(connections)` and `detect_conflicts(blocks)`. To avoid double-fetching, either: (a) have `_build_route` return the fetched data too, or (b) accept the extra queries (they're fast in-memory lookups in tests, and DB queries are cached in the same session for postgres). Option (b) is simpler — keep it.

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/application/test_update_route.py -v
```

Expected: All existing tests pass (pure refactor, no behavior change).

- [ ] **Step 4: Commit**

```bash
git add application/service/service.py
git commit -m "refactor: extract _build_route for shared route building logic"
```

---

## Task 7: Add `validate_route` Method and API Endpoint

Add the `validate_route()` application service method and `POST /routes/validate` endpoint.

**Files:**
- Modify: `application/service/service.py`
- Create: `api/route/__init__.py`
- Create: `api/route/schemas.py`
- Create: `api/route/routes.py`
- Modify: `api/dependencies.py`
- Modify: `main.py`
- Test: `tests/application/test_validate_route.py`
- Test: `tests/api/test_route_routes.py`

- [ ] **Step 1: Write failing application test**

Create `tests/application/test_validate_route.py`:

```python
from uuid import uuid7

import pytest

from application.service.dto import RouteStop
from application.service.service import ServiceAppService
from domain.vehicle.model import Vehicle
from infra.memory.block_repo import InMemoryBlockRepository
from infra.memory.connection_repo import InMemoryConnectionRepository
from infra.memory.service_repo import InMemoryServiceRepository
from infra.memory.station_repo import InMemoryStationRepository
from infra.memory.vehicle_repo import InMemoryVehicleRepository
from infra.seed import (
    BLOCK_ID_BY_NAME,
    PLATFORM_ID_BY_NAME,
    YARD_ID,
    create_blocks,
    create_connections,
    create_stations,
)


def _make_app():
    block_repo = InMemoryBlockRepository()
    for b in create_blocks():
        block_repo._store[b.id] = b

    station_repo = InMemoryStationRepository()
    for s in create_stations():
        station_repo._store[s.id] = s

    connection_repo = InMemoryConnectionRepository(create_connections())
    vehicle_repo = InMemoryVehicleRepository()
    service_repo = InMemoryServiceRepository()

    return ServiceAppService(
        service_repo=service_repo,
        block_repo=block_repo,
        connection_repo=connection_repo,
        vehicle_repo=vehicle_repo,
        station_repo=station_repo,
    ), vehicle_repo


def seed_vehicle(vehicle_repo, vid=None, battery=80):
    v = Vehicle(id=vid or uuid7(), name="V1", battery=battery)
    vehicle_repo._store[v.id] = v
    return v


class TestValidateRoute:
    async def test_valid_two_stop_route(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=90),
        ]
        result = await app.validate_route(v.id, stops, start_time=1000)

        # Path: P1A -> B3 -> B5 -> P2A
        assert len(result.path) == 4
        assert result.path[0].id == PLATFORM_ID_BY_NAME["P1A"]
        assert result.path[1].id == BLOCK_ID_BY_NAME["B3"]
        assert result.path[2].id == BLOCK_ID_BY_NAME["B5"]
        assert result.path[3].id == PLATFORM_ID_BY_NAME["P2A"]
        assert result.battery_conflicts == []

    async def test_yard_as_stop(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)

        stops = [
            RouteStop(node_id=YARD_ID, dwell_time=120),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
        ]
        result = await app.validate_route(v.id, stops, start_time=0)

        # Path: Y -> B1 -> P1A
        assert result.path[0].id == YARD_ID
        assert result.path[-1].id == PLATFORM_ID_BY_NAME["P1A"]
        assert result.battery_conflicts == []

    async def test_unreachable_route_raises(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)

        # P2A -> P1A has no route (wrong direction)
        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=0),
        ]
        with pytest.raises(ValueError, match="No route"):
            await app.validate_route(v.id, stops, start_time=0)

    async def test_low_battery_detected(self):
        app, vehicle_repo = _make_app()
        # Start with very low battery
        v = seed_vehicle(vehicle_repo, battery=30)

        # Long route: P1A -> P2A -> P3A (4 blocks = 4% battery drain)
        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=0),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P3A"], dwell_time=0),
        ]
        result = await app.validate_route(v.id, stops, start_time=0)
        assert len(result.battery_conflicts) > 0

    async def test_unknown_stop_rejected(self):
        app, vehicle_repo = _make_app()
        v = seed_vehicle(vehicle_repo)

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=uuid7(), dwell_time=60),
        ]
        with pytest.raises(ValueError, match="Stop.*not found"):
            await app.validate_route(v.id, stops, start_time=0)

    async def test_vehicle_not_found_rejected(self):
        app, _ = _make_app()

        stops = [
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P1A"], dwell_time=60),
            RouteStop(node_id=PLATFORM_ID_BY_NAME["P2A"], dwell_time=60),
        ]
        with pytest.raises(ValueError, match="Vehicle.*not found"):
            await app.validate_route(uuid7(), stops, start_time=0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/application/test_validate_route.py -v
```

Expected: AttributeError — `ServiceAppService` has no `validate_route`.

- [ ] **Step 3: Add `RouteValidationResult` DTO**

In `application/service/dto.py`, add:

```python
from domain.network.model import Node
from domain.domain_service.conflict.model import LowBatteryConflict, InsufficientChargeConflict


@dataclass(frozen=True)
class RouteValidationResult:
    path: list[Node]
    battery_conflicts: list[LowBatteryConflict | InsufficientChargeConflict]
```

- [ ] **Step 4: Implement `validate_route` in ServiceAppService**

In `application/service/service.py`, add:

```python
from application.service.dto import RouteValidationResult
from domain.domain_service.conflict.preparation import build_battery_steps
from domain.domain_service.conflict.detection import detect_battery_conflicts

# ... inside class ServiceAppService:

async def validate_route(
    self, vehicle_id: UUID, stops: list[RouteStop], start_time: EpochSeconds,
) -> RouteValidationResult:
    vehicle = await self._vehicle_repo.find_by_id(vehicle_id)
    if vehicle is None:
        raise ValueError(f"Vehicle {vehicle_id} not found")

    full_path, timetable = await self._build_route(stops, start_time)

    # Build temporary service for single-service battery check
    temp_service = Service(
        id=0,  # placeholder, not persisted
        name="_validation",
        vehicle_id=vehicle_id,
        path=full_path,
        timetable=timetable,
    )

    steps = build_battery_steps(vehicle_id, [temp_service])
    low_battery, insufficient_charge = detect_battery_conflicts(vehicle, steps)

    return RouteValidationResult(
        path=full_path,
        battery_conflicts=[*low_battery, *insufficient_charge],
    )
```

- [ ] **Step 5: Run application tests**

```bash
uv run pytest tests/application/test_validate_route.py -v
```

Expected: All PASS.

- [ ] **Step 6: Create API schemas**

Create `api/route/__init__.py` (empty file).

Create `api/route/schemas.py` (reuses `RouteStopInput` from `api/service/schemas.py` — no duplication):

```python
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from api.service.schemas import RouteStopInput


class ValidateRouteRequest(BaseModel):
    vehicle_id: UUID
    stops: list[RouteStopInput] = Field(min_length=2)
    start_time: int


class BatteryConflictSchema(BaseModel):
    type: str  # "low_battery" or "insufficient_charge"
    service_id: int


class ValidateRouteResponse(BaseModel):
    path: list[UUID]
    battery_conflicts: list[BatteryConflictSchema]
```

- [ ] **Step 7: Create API route**

Create `api/route/routes.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_service_app_service
from api.route.schemas import (
    BatteryConflictSchema,
    ValidateRouteRequest,
    ValidateRouteResponse,
)
from application.service.dto import RouteStop
from application.service.service import ServiceAppService
from domain.domain_service.conflict.model import (
    InsufficientChargeConflict,
    LowBatteryConflict,
)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/validate", response_model=ValidateRouteResponse)
async def validate_route(
    request: ValidateRouteRequest,
    service_app_service: ServiceAppService = Depends(get_service_app_service),
):
    stops = [
        RouteStop(node_id=s.node_id, dwell_time=s.dwell_time)
        for s in request.stops
    ]
    try:
        result = await service_app_service.validate_route(
            request.vehicle_id, stops, request.start_time,
        )
    except ValueError as e:
        if "No route" in str(e):
            raise HTTPException(status_code=422, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    battery_conflicts = []
    for c in result.battery_conflicts:
        match c:
            case LowBatteryConflict():
                battery_conflicts.append(
                    BatteryConflictSchema(type="low_battery", service_id=c.service_id)
                )
            case InsufficientChargeConflict():
                battery_conflicts.append(
                    BatteryConflictSchema(type="insufficient_charge", service_id=c.service_id)
                )

    return ValidateRouteResponse(
        path=[n.id for n in result.path],
        battery_conflicts=battery_conflicts,
    )
```

- [ ] **Step 8: Register router in main.py**

In `main.py`:

```python
from api.route.routes import router as route_router

# ... after existing includes:
app.include_router(route_router)
```

- [ ] **Step 9: Write API integration test**

Create `tests/api/test_route_routes.py`:

```python
import pytest

from infra.seed import PLATFORM_ID_BY_NAME, VEHICLE_ID_BY_NAME, YARD_ID

pytestmark = pytest.mark.postgres


class TestValidateRouteEndpoint:
    async def test_valid_route(self, client):
        resp = await client.post("/routes/validate", json={
            "vehicle_id": str(VEHICLE_ID_BY_NAME["V1"]),
            "stops": [
                {"node_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
                {"node_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 90},
            ],
            "start_time": 1000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["path"]) == 4
        assert data["battery_conflicts"] == []

    async def test_unreachable_returns_422(self, client):
        resp = await client.post("/routes/validate", json={
            "vehicle_id": str(VEHICLE_ID_BY_NAME["V1"]),
            "stops": [
                {"node_id": str(PLATFORM_ID_BY_NAME["P2A"]), "dwell_time": 0},
                {"node_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 0},
            ],
            "start_time": 0,
        })
        assert resp.status_code == 422

    async def test_yard_as_stop(self, client):
        resp = await client.post("/routes/validate", json={
            "vehicle_id": str(VEHICLE_ID_BY_NAME["V1"]),
            "stops": [
                {"node_id": str(YARD_ID), "dwell_time": 120},
                {"node_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
            ],
            "start_time": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["path"]) >= 2

    async def test_single_stop_rejected(self, client):
        resp = await client.post("/routes/validate", json={
            "vehicle_id": str(VEHICLE_ID_BY_NAME["V1"]),
            "stops": [
                {"node_id": str(PLATFORM_ID_BY_NAME["P1A"]), "dwell_time": 60},
            ],
            "start_time": 0,
        })
        assert resp.status_code == 422  # Pydantic validation: min_length=2
```

- [ ] **Step 10: Run all tests**

```bash
uv run pytest -v
```

Expected: All tests pass.

- [ ] **Step 11: Commit**

```bash
git add application/service/dto.py application/service/service.py api/route/ main.py tests/application/test_validate_route.py tests/api/test_route_routes.py
git commit -m "feat: add POST /routes/validate endpoint for interactive route building"
```

---

## Task 8: Update CLAUDE.md and Final Verification

Ensure documentation is up to date and all tests pass.

**Files:**
- Verify: `CLAUDE.md` (already updated during brainstorming)
- Run: Full test suite

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest -v
```

- [ ] **Step 2: Run postgres integration tests**

```bash
uv run pytest -m postgres -v
```

- [ ] **Step 3: Verify API manually (optional)**

```bash
DB=postgres uv run uvicorn main:app --reload
# In another terminal:
curl localhost:8000/graph | python -m json.tool | head -20
# Check nodes have x, y fields

curl -X POST localhost:8000/routes/validate \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": "...", "stops": [{"node_id": "...", "dwell_time": 60}, {"node_id": "...", "dwell_time": 90}], "start_time": 0}'
```

- [ ] **Step 4: Commit any remaining changes**

```bash
git add -A
git commit -m "chore: final verification and cleanup"
```
