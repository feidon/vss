# Readability Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract route-building logic from `ServiceAppService` into a pure domain service, and reorganize the conflict detection module by detection target instead of processing phase.

**Architecture:** Two independent refactors. (1) Move route-building pure functions from the application layer into `domain/domain_service/route_builder.py`, accepting primitives instead of application DTOs. (2) Reorganize `domain/domain_service/conflict/` from phase-based files (preparation, detection, service) into target-based files (vehicle, block, interlocking, battery) with shared utilities.

**Tech Stack:** Python 3.14, pytest, ruff, import-linter

---

## File Map

### New Files
- `domain/domain_service/route_builder.py` — pure functions: validate_stops, resolve_nodes, compute_timetable, build_full_route
- `domain/domain_service/conflict/shared.py` — intermediate types + shared functions (find_time_overlaps, build_vehicle_schedule, build_occupancies)
- `domain/domain_service/conflict/vehicle.py` — vehicle conflict detection
- `domain/domain_service/conflict/block.py` — block conflict detection + from_overlap factory
- `domain/domain_service/conflict/interlocking.py` — interlocking conflict detection + from_overlap factory
- `domain/domain_service/conflict/battery.py` — battery prep + detection + internal types (NodeEntry, ChargeStop, BlockTraversal)
- `domain/domain_service/conflict/detector.py` — orchestrator (replaces service.py)
- `tests/domain/test_route_builder.py` — unit tests for route builder

### Modified Files
- `application/service/service.py` — remove static methods, use route_builder, update conflict imports
- `domain/domain_service/conflict/model.py` — keep only public result types, remove intermediates + from_overlap
- `domain/domain_service/conflict/__init__.py` — re-export from detector.py instead of service.py

### Deleted Files
- `domain/domain_service/conflict/detection.py` — split into vehicle.py, block.py, interlocking.py, battery.py
- `domain/domain_service/conflict/preparation.py` — split into shared.py + battery.py
- `domain/domain_service/conflict/service.py` — replaced by detector.py

### Unchanged Files (verify imports still work)
- `tests/domain/test_conflict.py` — imports from `conflict` and `conflict.model` (stable)
- `tests/api/test_error_handler.py` — imports from `conflict.model` (stable)
- `tests/application/test_update_route.py` — imports `ServiceAppService` (stable)
- `tests/application/test_validate_route.py` — imports `ServiceAppService` (stable)
- `tests/application/test_service_service.py` — imports `ServiceAppService` (stable)
- `application/service/dto.py` — imports `BatteryConflict` from `conflict.model` (stable)
- `application/service/errors.py` — imports `ServiceConflicts` from `conflict` (stable)
- `api/route/schemas.py` — imports `BatteryConflictType` from `conflict.model` (stable)

---

## Task 1: Create route_builder.py

**Files:**
- Create: `domain/domain_service/route_builder.py`
- Create: `tests/domain/test_route_builder.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/domain/test_route_builder.py
from uuid import uuid7

import pytest
from domain.block.model import Block
from domain.domain_service.route_builder import build_full_route
from domain.error import DomainError
from domain.network.model import NodeConnection, NodeType
from domain.station.model import Platform, Station


def _make_station(name: str, platform_names: list[str]) -> Station:
    platforms = [
        Platform(id=uuid7(), name=pname) for pname in platform_names
    ]
    return Station(id=uuid7(), name=name, platforms=platforms, is_yard=False)


def _make_yard(name: str) -> Station:
    return Station(id=uuid7(), name=name, platforms=[], is_yard=True)


def _make_block(name: str, group: int = 0) -> Block:
    return Block(id=uuid7(), name=name, group=group, traversal_time_seconds=30)


class TestBuildFullRoute:
    def test_two_stop_route(self):
        s1 = _make_station("S1", ["P1"])
        s2 = _make_station("S2", ["P2"])
        b1 = _make_block("B1")
        p1 = s1.platforms[0]
        p2 = s2.platforms[0]

        connections = frozenset(
            {
                NodeConnection(from_id=p1.id, to_id=b1.id),
                NodeConnection(from_id=b1.id, to_id=p2.id),
            }
        )

        stop_ids = [p1.id, p2.id]
        dwell_by_stop = {p1.id: 60, p2.id: 90}

        route, timetable = build_full_route(
            stop_ids, dwell_by_stop, 1000, connections, [s1, s2], [b1]
        )

        assert len(route) == 3  # P1 -> B1 -> P2
        assert route[0].id == p1.id
        assert route[0].type == NodeType.PLATFORM
        assert route[1].id == b1.id
        assert route[1].type == NodeType.BLOCK
        assert route[2].id == p2.id

        assert len(timetable) == 3
        assert timetable[0].arrival == 1000
        assert timetable[0].departure == 1060  # dwell 60
        assert timetable[1].arrival == 1060
        assert timetable[1].departure == 1090  # traversal 30
        assert timetable[2].arrival == 1090

    def test_unknown_stop_rejected(self):
        s1 = _make_station("S1", ["P1"])
        b1 = _make_block("B1")
        p1 = s1.platforms[0]

        connections = frozenset[NodeConnection]()

        with pytest.raises(DomainError, match="Stop.*not found"):
            build_full_route(
                [p1.id, uuid7()], {p1.id: 0}, 0, connections, [s1], [b1]
            )

    def test_returns_pure_data(self):
        """build_full_route is synchronous — no await needed."""
        s1 = _make_station("S1", ["P1"])
        s2 = _make_station("S2", ["P2"])
        b1 = _make_block("B1")
        p1 = s1.platforms[0]
        p2 = s2.platforms[0]

        connections = frozenset(
            {
                NodeConnection(from_id=p1.id, to_id=b1.id),
                NodeConnection(from_id=b1.id, to_id=p2.id),
            }
        )

        result = build_full_route(
            [p1.id, p2.id], {p1.id: 0, p2.id: 0}, 0, connections, [s1, s2], [b1]
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/domain/test_route_builder.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'domain.domain_service.route_builder'`

- [ ] **Step 3: Write route_builder.py**

```python
# domain/domain_service/route_builder.py
from __future__ import annotations

from uuid import UUID

from domain.block.model import Block
from domain.domain_service.route_finder import RouteFinder
from domain.error import DomainError, ErrorCode
from domain.network.model import Node, NodeConnection
from domain.service.model import TimetableEntry
from domain.shared.types import EpochSeconds
from domain.station.model import Platform, Station


def build_full_route(
    stop_ids: list[UUID],
    dwell_by_stop: dict[UUID, int],
    start_time: EpochSeconds,
    connections: frozenset[NodeConnection],
    stations: list[Station],
    blocks: list[Block],
) -> tuple[list[Node], list[TimetableEntry]]:
    all_platforms = {p.id: p for s in stations for p in s.platforms}
    yards = {s.id: s for s in stations if s.is_yard}
    blocks_by_id = {b.id: b for b in blocks}

    _validate_stops(stop_ids, all_platforms, yards)

    full_path_ids = RouteFinder.build_full_path(
        stop_ids, connections, {b.id for b in blocks}
    )

    full_route = _resolve_nodes(full_path_ids, blocks_by_id, all_platforms, yards)

    timetable = _compute_timetable(
        full_route, blocks_by_id, all_platforms, yards, dwell_by_stop, start_time
    )

    return full_route, timetable


def _validate_stops(
    stop_ids: list[UUID],
    all_platforms: dict[UUID, Platform],
    yards: dict[UUID, Station],
) -> None:
    valid_ids = set(all_platforms.keys()) | set(yards.keys())
    for stop_id in stop_ids:
        if stop_id not in valid_ids:
            raise DomainError(ErrorCode.VALIDATION, f"Stop {stop_id} not found")


def _resolve_nodes(
    path_ids: list[UUID],
    blocks_by_id: dict[UUID, Block],
    all_platforms: dict[UUID, Platform],
    yards: dict[UUID, Station],
) -> list[Node]:
    nodes: list[Node] = []
    for nid in path_ids:
        if nid in blocks_by_id:
            nodes.append(blocks_by_id[nid].to_node())
        elif nid in all_platforms:
            nodes.append(all_platforms[nid].to_node())
        elif nid in yards:
            nodes.append(yards[nid].to_node())
        else:
            raise DomainError(ErrorCode.VALIDATION, f"Unknown node {nid} in path")
    return nodes


def _compute_timetable(
    full_path: list[Node],
    blocks_by_id: dict[UUID, Block],
    all_platforms: dict[UUID, Platform],
    yards: dict[UUID, Station],
    dwell_by_stop: dict[UUID, int],
    start_time: EpochSeconds,
) -> list[TimetableEntry]:
    entries: list[TimetableEntry] = []
    current_time = start_time

    for order, node in enumerate(full_path):
        if node.id in blocks_by_id:
            entry = blocks_by_id[node.id].to_timetable_entry(order, current_time)
        elif node.id in all_platforms:
            dwell = dwell_by_stop.get(node.id, 0)
            entry = all_platforms[node.id].to_timetable_entry(
                order, current_time, dwell
            )
        elif node.id in yards:
            dwell = dwell_by_stop.get(node.id, 0)
            entry = yards[node.id].to_timetable_entry(order, current_time, dwell)
        else:
            raise DomainError(
                ErrorCode.VALIDATION, f"Unknown node {node.id} in timetable"
            )
        entries.append(entry)
        current_time = entry.departure

    return entries
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/domain/test_route_builder.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add domain/domain_service/route_builder.py tests/domain/test_route_builder.py
git commit -m "refactor: extract route builder as pure domain service"
```

---

## Task 2: Update ServiceAppService to use route_builder

**Files:**
- Modify: `application/service/service.py`

- [ ] **Step 1: Replace route-building logic with route_builder calls**

Replace the entire file content of `application/service/service.py` with:

```python
from __future__ import annotations

from uuid import UUID

from domain.domain_service.conflict import detect_conflicts
from domain.domain_service.conflict.detection import detect_battery_conflicts
from domain.domain_service.conflict.preparation import build_battery_steps
from domain.domain_service.route_builder import build_full_route
from domain.error import DomainError, ErrorCode
from domain.service.model import Service
from domain.service.repository import ServiceRepository
from domain.block.repository import BlockRepository
from domain.network.repository import ConnectionRepository
from domain.shared.types import EpochSeconds
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository

from application.service.dto import RouteStop, RouteValidationResult
from application.service.errors import ConflictError


class ServiceAppService:
    def __init__(
        self,
        service_repo: ServiceRepository,
        block_repo: BlockRepository,
        connection_repo: ConnectionRepository,
        vehicle_repo: VehicleRepository,
        station_repo: StationRepository,
    ) -> None:
        self._service_repo = service_repo
        self._block_repo = block_repo
        self._connection_repo = connection_repo
        self._vehicle_repo = vehicle_repo
        self._station_repo = station_repo

    async def create_service(self, name: str, vehicle_id: UUID) -> Service:
        if not name or not name.strip():
            raise DomainError(ErrorCode.VALIDATION, "Service name must not be empty")

        vehicle = await self._vehicle_repo.find_by_id(vehicle_id)
        if vehicle is None:
            raise DomainError(ErrorCode.VALIDATION, f"Vehicle {vehicle_id} not found")

        service = Service(
            name=name,
            vehicle_id=vehicle_id,
            route=[],
            timetable=[],
        )

        return await self._service_repo.create(service)

    async def get_service(self, id: int) -> Service:
        service = await self._service_repo.find_by_id(id)

        if service is None:
            raise DomainError(ErrorCode.NOT_FOUND, f"Service {id} not found")

        return service

    async def list_services(self) -> list[Service]:
        return await self._service_repo.find_all()

    async def update_service_route(
        self, id: int, stops: list[RouteStop], start_time: EpochSeconds
    ) -> Service:
        service = await self.get_service(id)
        connections = await self._connection_repo.find_all()
        all_stations = await self._station_repo.find_all()
        all_blocks = await self._block_repo.find_all()

        stop_ids = [s.node_id for s in stops]
        dwell_by_stop = {s.node_id: s.dwell_time for s in stops}
        full_route, timetable = build_full_route(
            stop_ids, dwell_by_stop, start_time, connections, all_stations, all_blocks
        )
        service.update_route(full_route, timetable, connections)

        all_services = await self._service_repo.find_all()
        all_vehicles = await self._vehicle_repo.find_all()
        conflicts = detect_conflicts(
            service,
            all_services,
            all_blocks,
            all_vehicles,
        )

        if conflicts.has_conflicts:
            raise ConflictError(conflicts)

        await self._service_repo.update(service)
        return service

    async def validate_route(
        self,
        vehicle_id: UUID,
        stops: list[RouteStop],
        start_time: EpochSeconds,
    ) -> RouteValidationResult:
        vehicle = await self._vehicle_repo.find_by_id(vehicle_id)
        if vehicle is None:
            raise DomainError(ErrorCode.VALIDATION, f"Vehicle {vehicle_id} not found")

        connections = await self._connection_repo.find_all()
        all_stations = await self._station_repo.find_all()
        all_blocks = await self._block_repo.find_all()

        stop_ids = [s.node_id for s in stops]
        dwell_by_stop = {s.node_id: s.dwell_time for s in stops}
        full_route, timetable = build_full_route(
            stop_ids, dwell_by_stop, start_time, connections, all_stations, all_blocks
        )

        temp_service = Service(
            id=0,
            name="_validation",
            vehicle_id=vehicle_id,
            route=full_route,
            timetable=timetable,
        )

        steps = build_battery_steps(vehicle_id, [temp_service])
        battery_conflicts = detect_battery_conflicts(vehicle, steps)

        return RouteValidationResult(
            route=full_route,
            battery_conflicts=battery_conflicts,
        )

    async def delete_service(self, id: int) -> None:
        await self._service_repo.delete(id)
```

- [ ] **Step 2: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass. The app service now delegates route building to `route_builder.py`.

- [ ] **Step 3: Run architecture lint**

Run: `uv run lint-imports`
Expected: No violations. `route_builder.py` is in the domain layer and has no application-layer imports.

- [ ] **Step 4: Commit**

```bash
git add application/service/service.py
git commit -m "refactor: use route_builder in ServiceAppService"
```

---

## Task 3: Create conflict/shared.py

**Files:**
- Create: `domain/domain_service/conflict/shared.py`

- [ ] **Step 1: Create shared.py with intermediate types and shared functions**

```python
# domain/domain_service/conflict/shared.py
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from domain.block.model import Block
from domain.service.model import Service
from domain.shared.types import EpochSeconds


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


def find_time_overlaps[T: Timed](entries: list[T]) -> list[tuple[T, T]]:
    """Find all pairs with overlapping time windows.

    Sweep-line algorithm: sort by arrival, break inner loop
    when next arrival >= current departure.
    """
    sorted_entries = sorted(entries, key=lambda x: x.arrival)
    pairs: list[tuple[T, T]] = []

    for i in range(len(sorted_entries)):
        dep_i = sorted_entries[i].departure
        for j in range(i + 1, len(sorted_entries)):
            if sorted_entries[j].arrival >= dep_i:
                break
            pairs.append((sorted_entries[i], sorted_entries[j]))

    return pairs


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

        windows.append(
            ServiceWindow(
                service_id=svc.id,
                start=min(e.arrival for e in entries),
                end=max(e.departure for e in entries),
            )
        )

        endpoints.append(
            ServiceEndpoints(
                service_id=svc.id,
                first_node_id=entries[0].node_id,
                last_node_id=entries[-1].node_id,
                start=min(e.arrival for e in entries),
            )
        )

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
```

- [ ] **Step 2: Verify no import errors**

Run: `uv run python -c "from domain.domain_service.conflict.shared import find_time_overlaps, build_vehicle_schedule, build_occupancies"`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add domain/domain_service/conflict/shared.py
git commit -m "refactor: create conflict/shared.py with intermediate types and shared functions"
```

---

## Task 4: Create conflict/vehicle.py

**Files:**
- Create: `domain/domain_service/conflict/vehicle.py`

- [ ] **Step 1: Create vehicle.py**

```python
# domain/domain_service/conflict/vehicle.py
from __future__ import annotations

from uuid import UUID

from domain.domain_service.conflict.model import VehicleConflict
from domain.domain_service.conflict.shared import ServiceEndpoints, ServiceWindow


def detect_vehicle_conflicts(
    vehicle_id: UUID,
    windows: list[ServiceWindow],
    endpoints: list[ServiceEndpoints],
) -> list[VehicleConflict]:
    return _detect_time_overlaps(vehicle_id, windows) + _detect_location_discontinuities(
        vehicle_id, endpoints
    )


def _detect_time_overlaps(
    vehicle_id: UUID,
    windows: list[ServiceWindow],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []
    for i in range(len(windows)):
        for j in range(i + 1, len(windows)):
            prev, curr = windows[i], windows[j]
            if curr.start >= prev.end:
                break
            conflicts.append(
                VehicleConflict(
                    vehicle_id,
                    prev.service_id,
                    curr.service_id,
                    "Overlapping time windows",
                )
            )
    return conflicts


def _detect_location_discontinuities(
    vehicle_id: UUID,
    endpoints: list[ServiceEndpoints],
) -> list[VehicleConflict]:
    conflicts: list[VehicleConflict] = []
    for i in range(1, len(endpoints)):
        prev, curr = endpoints[i - 1], endpoints[i]
        if curr.first_node_id != prev.last_node_id:
            conflicts.append(
                VehicleConflict(
                    vehicle_id,
                    prev.service_id,
                    curr.service_id,
                    "Location discontinuity",
                )
            )
    return conflicts
```

- [ ] **Step 2: Verify no import errors**

Run: `uv run python -c "from domain.domain_service.conflict.vehicle import detect_vehicle_conflicts"`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add domain/domain_service/conflict/vehicle.py
git commit -m "refactor: create conflict/vehicle.py for vehicle conflict detection"
```

---

## Task 5: Create conflict/block.py

**Files:**
- Create: `domain/domain_service/conflict/block.py`

- [ ] **Step 1: Create block.py**

```python
# domain/domain_service/conflict/block.py
from __future__ import annotations

from uuid import UUID

from domain.domain_service.conflict.model import BlockConflict
from domain.domain_service.conflict.shared import BlockOccupancy, find_time_overlaps


def detect_block_conflicts(
    by_block: dict[UUID, list[BlockOccupancy]],
) -> list[BlockConflict]:
    conflicts: list[BlockConflict] = []
    for block_id, occupancies in by_block.items():
        for a, b in find_time_overlaps(occupancies):
            conflicts.append(_block_conflict_from_overlap(block_id, a, b))
    return conflicts


def _block_conflict_from_overlap(
    block_id: UUID, a: BlockOccupancy, b: BlockOccupancy
) -> BlockConflict:
    return BlockConflict(
        block_id=block_id,
        service_a_id=a.service_id,
        service_b_id=b.service_id,
        overlap_start=b.arrival,
        overlap_end=a.departure,
    )
```

- [ ] **Step 2: Verify no import errors**

Run: `uv run python -c "from domain.domain_service.conflict.block import detect_block_conflicts"`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add domain/domain_service/conflict/block.py
git commit -m "refactor: create conflict/block.py for block conflict detection"
```

---

## Task 6: Create conflict/interlocking.py

**Files:**
- Create: `domain/domain_service/conflict/interlocking.py`

- [ ] **Step 1: Create interlocking.py**

```python
# domain/domain_service/conflict/interlocking.py
from __future__ import annotations

from domain.domain_service.conflict.model import InterlockingConflict
from domain.domain_service.conflict.shared import GroupOccupancy, find_time_overlaps


def detect_interlocking_conflicts(
    by_group: dict[int, list[GroupOccupancy]],
) -> list[InterlockingConflict]:
    """Detect different blocks in the same interlocking group
    occupied by different services at overlapping times."""
    conflicts: list[InterlockingConflict] = []
    for group, occupancies in by_group.items():
        if group == 0:
            continue  # group 0 means "no interlocking group"
        for a, b in find_time_overlaps(occupancies):
            if a.block_id == b.block_id:
                continue  # already caught by block conflict detection
            conflicts.append(_interlocking_conflict_from_overlap(group, a, b))
    return conflicts


def _interlocking_conflict_from_overlap(
    group: int, a: GroupOccupancy, b: GroupOccupancy
) -> InterlockingConflict:
    return InterlockingConflict(
        group=group,
        block_a_id=a.block_id,
        block_b_id=b.block_id,
        service_a_id=a.service_id,
        service_b_id=b.service_id,
        overlap_start=b.arrival,
        overlap_end=a.departure,
    )
```

- [ ] **Step 2: Verify no import errors**

Run: `uv run python -c "from domain.domain_service.conflict.interlocking import detect_interlocking_conflicts"`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add domain/domain_service/conflict/interlocking.py
git commit -m "refactor: create conflict/interlocking.py for interlocking conflict detection"
```

---

## Task 7: Create conflict/battery.py

**Files:**
- Create: `domain/domain_service/conflict/battery.py`

- [ ] **Step 1: Create battery.py**

```python
# domain/domain_service/conflict/battery.py
from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from domain.domain_service.conflict.model import BatteryConflict, BatteryConflictType
from domain.network.model import NodeType
from domain.service.model import Service
from domain.shared.types import EpochSeconds
from domain.vehicle.model import Vehicle


@dataclass(frozen=True)
class NodeEntry:
    """Intermediate timetable entry for battery simulation."""

    time: EpochSeconds
    node_type: NodeType
    service_id: int


@dataclass(frozen=True)
class ChargeStop:
    """A yard stop where the vehicle charges."""

    charge_seconds: int
    service_id: int


@dataclass(frozen=True)
class BlockTraversal:
    """A block traversal that consumes 1% battery."""

    service_id: int


def build_battery_steps(
    vehicle_id: UUID,
    services: list[Service],
) -> list[ChargeStop | BlockTraversal]:
    node_entries: list[NodeEntry] = []

    for service in services:
        if service.vehicle_id != vehicle_id or not service.timetable:
            continue

        node_map = {n.id: n.type for n in service.route}
        for t in service.timetable:
            if node_map[t.node_id] != NodeType.PLATFORM:
                node_entries.append(
                    NodeEntry(t.arrival, node_map[t.node_id], service.id)
                )

    node_entries.sort(key=lambda e: e.time)

    steps: list[ChargeStop | BlockTraversal] = []
    for i, entry in enumerate(node_entries):
        if entry.node_type == NodeType.YARD:
            next_time = (
                node_entries[i + 1].time if i + 1 < len(node_entries) else entry.time
            )
            steps.append(ChargeStop(next_time - entry.time, entry.service_id))
        else:
            steps.append(BlockTraversal(entry.service_id))

    return steps


def detect_battery_conflicts(
    vehicle: Vehicle,
    steps: list[ChargeStop | BlockTraversal],
) -> list[BatteryConflict]:
    battery_conflicts: list[BatteryConflict] = []

    if not steps:
        return battery_conflicts

    sim = replace(vehicle)

    for step in steps:
        match step:
            case ChargeStop():
                sim.charge(step.charge_seconds)
                if not sim.can_depart():
                    battery_conflicts.append(
                        BatteryConflict(
                            type=BatteryConflictType.INSUFCHARGE,
                            service_id=step.service_id,
                        )
                    )
                    break
            case BlockTraversal():
                sim.traverse_block()
                if sim.is_battery_critical():
                    battery_conflicts.append(
                        BatteryConflict(
                            type=BatteryConflictType.LOWBATTERY,
                            service_id=step.service_id,
                        )
                    )
                    break

    return battery_conflicts
```

- [ ] **Step 2: Verify no import errors**

Run: `uv run python -c "from domain.domain_service.conflict.battery import build_battery_steps, detect_battery_conflicts"`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add domain/domain_service/conflict/battery.py
git commit -m "refactor: create conflict/battery.py for battery conflict detection"
```

---

## Task 8: Create conflict/detector.py

**Files:**
- Create: `domain/domain_service/conflict/detector.py`

- [ ] **Step 1: Create detector.py**

```python
# domain/domain_service/conflict/detector.py
from __future__ import annotations

from domain.block.model import Block
from domain.domain_service.conflict.battery import (
    build_battery_steps,
    detect_battery_conflicts,
)
from domain.domain_service.conflict.block import detect_block_conflicts
from domain.domain_service.conflict.interlocking import detect_interlocking_conflicts
from domain.domain_service.conflict.model import BatteryConflict, ServiceConflicts
from domain.domain_service.conflict.shared import (
    build_occupancies,
    build_vehicle_schedule,
)
from domain.domain_service.conflict.vehicle import detect_vehicle_conflicts
from domain.service.model import Service
from domain.vehicle.model import Vehicle


def detect_conflicts(
    candidate: Service,
    other_services: list[Service],
    blocks: list[Block],
    vehicles: list[Vehicle] | None = None,
) -> ServiceConflicts:
    """Check all conflicts for a candidate service against other services."""
    all_services = [s for s in other_services if s.id != candidate.id]
    all_services.append(candidate)

    schedule = build_vehicle_schedule(candidate.vehicle_id, all_services)
    block_occupancies, group_occupancies = build_occupancies(all_services, blocks)

    battery_conflicts: list[BatteryConflict] = []

    if vehicles:
        vehicle_by_id = {v.id: v for v in vehicles}
        candidate_vehicle = vehicle_by_id.get(candidate.vehicle_id)
        if candidate_vehicle is not None:
            battery_steps = build_battery_steps(
                candidate_vehicle.id,
                all_services,
            )
            battery_conflicts = detect_battery_conflicts(
                candidate_vehicle,
                battery_steps,
            )

    return ServiceConflicts(
        vehicle_conflicts=detect_vehicle_conflicts(
            candidate.vehicle_id, schedule.windows, schedule.endpoints
        ),
        block_conflicts=detect_block_conflicts(block_occupancies),
        interlocking_conflicts=detect_interlocking_conflicts(group_occupancies),
        battery_conflicts=battery_conflicts,
    )
```

- [ ] **Step 2: Verify no import errors**

Run: `uv run python -c "from domain.domain_service.conflict.detector import detect_conflicts"`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add domain/domain_service/conflict/detector.py
git commit -m "refactor: create conflict/detector.py as conflict orchestrator"
```

---

## Task 9: Switch over — update imports, clean up model.py, delete old files

**Files:**
- Modify: `domain/domain_service/conflict/__init__.py`
- Modify: `domain/domain_service/conflict/model.py`
- Modify: `application/service/service.py` (update battery imports)
- Delete: `domain/domain_service/conflict/detection.py`
- Delete: `domain/domain_service/conflict/preparation.py`
- Delete: `domain/domain_service/conflict/service.py`

- [ ] **Step 1: Update `__init__.py`**

Replace the entire content of `domain/domain_service/conflict/__init__.py` with:

```python
from domain.domain_service.conflict.detector import detect_conflicts
from domain.domain_service.conflict.model import (
    BatteryConflict,
    BatteryConflictType,
    BlockConflict,
    InterlockingConflict,
    ServiceConflicts,
    VehicleConflict,
)

__all__ = [
    "BatteryConflict",
    "BatteryConflictType",
    "BlockConflict",
    "InterlockingConflict",
    "ServiceConflicts",
    "VehicleConflict",
    "detect_conflicts",
]
```

- [ ] **Step 2: Trim `model.py` to public types only**

Replace the entire content of `domain/domain_service/conflict/model.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID


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


@dataclass(frozen=True)
class InterlockingConflict:
    group: int
    block_a_id: UUID
    block_b_id: UUID
    service_a_id: int
    service_b_id: int
    overlap_start: int
    overlap_end: int


class BatteryConflictType(Enum):
    LOWBATTERY = "low_battery"
    INSUFCHARGE = "insufficient_charge"


@dataclass(frozen=True)
class BatteryConflict:
    type: BatteryConflictType
    service_id: int


@dataclass(frozen=True)
class ServiceConflicts:
    vehicle_conflicts: list[VehicleConflict]
    block_conflicts: list[BlockConflict]
    interlocking_conflicts: list[InterlockingConflict]
    battery_conflicts: list[BatteryConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(
            self.vehicle_conflicts
            or self.block_conflicts
            or self.interlocking_conflicts
            or self.battery_conflicts
        )
```

- [ ] **Step 3: Update battery imports in `application/service/service.py`**

Change lines 8-9 from:
```python
from domain.domain_service.conflict.detection import detect_battery_conflicts
from domain.domain_service.conflict.preparation import build_battery_steps
```
to:
```python
from domain.domain_service.conflict.battery import (
    build_battery_steps,
    detect_battery_conflicts,
)
```

- [ ] **Step 4: Delete old files**

```bash
git rm domain/domain_service/conflict/detection.py
git rm domain/domain_service/conflict/preparation.py
git rm domain/domain_service/conflict/service.py
```

- [ ] **Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass.

- [ ] **Step 6: Run architecture lint**

Run: `uv run lint-imports`
Expected: No violations.

- [ ] **Step 7: Commit**

```bash
git add -A domain/domain_service/conflict/ application/service/service.py
git commit -m "refactor: reorganize conflict module by detection target

Switch __init__.py to use detector.py, trim model.py to public types,
update battery import paths, delete old phase-based files."
```

---

## Task 10: Final verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass.

- [ ] **Step 2: Run ruff check + format**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: No issues.

- [ ] **Step 3: Run architecture lint**

Run: `uv run lint-imports`
Expected: No violations.

- [ ] **Step 4: Verify file counts**

The conflict module should now have 8 files:
```
domain/domain_service/conflict/
├── __init__.py
├── model.py
├── shared.py
├── vehicle.py
├── block.py
├── interlocking.py
├── battery.py
└── detector.py
```

Run: `ls domain/domain_service/conflict/`
Expected: The 8 files listed above, no others.
