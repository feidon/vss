# Auto-Generate Schedule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a CP-SAT–based automatic schedule generator that produces conflict-free services for all available vehicles within a time range.

**Architecture:** New `application/schedule/` package contains all scheduling logic (solver, route variant pre-computation, orchestration). CP-SAT dependency is isolated to a single file (`solver.py`). The API layer adds one new endpoint. A `delete_all()` method is added to `ServiceRepository`.

**Tech Stack:** Python 3.14, FastAPI, Google OR-Tools CP-SAT, existing domain services (RouteFinder, ConflictDetectionService, build_full_route)

**Spec:** `docs/superpowers/specs/2026-04-05-auto-schedule-generation-design.md`

---

### Task 1: Add `delete_all()` to ServiceRepository

**Files:**
- Modify: `domain/service/repository.py`
- Modify: `infra/postgres/service_repo.py`
- Modify: `tests/fakes/service_repo.py`
- Test: `tests/infra/test_delete_all.py`

- [ ] **Step 1: Add abstract method to repository interface**

In `domain/service/repository.py`, add:

```python
@abstractmethod
async def delete_all(self) -> None: ...
```

- [ ] **Step 2: Implement in fake repository**

In `tests/fakes/service_repo.py`, add:

```python
async def delete_all(self) -> None:
    self._store.clear()
    self._counter = 0
```

- [ ] **Step 3: Implement in PostgreSQL repository**

In `infra/postgres/service_repo.py`, add:

```python
async def delete_all(self) -> None:
    await self._session.execute(delete(services_table))
    await self._session.commit()
```

- [ ] **Step 4: Write integration test**

Create `tests/infra/test_delete_all.py`:

```python
import pytest
from domain.service.model import Service
from domain.shared.types import EpochSeconds
from infra.postgres.service_repo import PostgresServiceRepository
from uuid import uuid7

from tests.conftest import insert_vehicle


@pytest.mark.postgres
class TestDeleteAll:
    async def test_delete_all_removes_all_services(self, pg_session):
        vid = uuid7()
        await insert_vehicle(pg_session, vid)
        repo = PostgresServiceRepository(pg_session)

        for name in ["S1", "S2", "S3"]:
            await repo.create(Service(name=name, vehicle_id=vid, route=[], timetable=[]))

        assert len(await repo.find_all()) == 3
        await repo.delete_all()
        assert len(await repo.find_all()) == 0

    async def test_delete_all_on_empty_is_noop(self, pg_session):
        repo = PostgresServiceRepository(pg_session)
        await repo.delete_all()
        assert len(await repo.find_all()) == 0
```

- [ ] **Step 5: Run test**

Run: `uv run pytest tests/infra/test_delete_all.py -v -m postgres`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add domain/service/repository.py infra/postgres/service_repo.py tests/fakes/service_repo.py tests/infra/test_delete_all.py
git commit -m "feat: add delete_all() to ServiceRepository"
```

---

### Task 2: Route variant pre-computation

**Files:**
- Create: `application/schedule/model.py`
- Create: `application/schedule/route_variant.py`
- Test: `tests/application/schedule/test_route_variant.py`

- [ ] **Step 1: Create data models**

Create `application/schedule/__init__.py` (empty) and `application/schedule/model.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.shared.types import EpochSeconds


@dataclass(frozen=True)
class BlockTiming:
    """Occupancy interval for one block in a route variant, relative to trip departure."""
    block_id: UUID
    enter_offset: int   # seconds after trip departs yard
    exit_offset: int    # enter_offset + traversal_time


@dataclass(frozen=True)
class StationArrival:
    """When a trip visits a station, relative to trip departure."""
    station_name: str
    platform_id: UUID
    arrival_offset: int


@dataclass(frozen=True)
class RouteVariant:
    """One of the 8 possible route patterns through the network."""
    index: int
    s1_out: int         # 0=P1A, 1=P1B
    s3: int             # 0=P3A, 1=P3B
    s1_ret: int         # 0=P1A, 1=P1B
    stop_ids: list[UUID]          # ordered platform/yard IDs for build_full_route
    block_timings: list[BlockTiming]
    station_arrivals: list[StationArrival]  # 2 per station (outbound + return)
    cycle_time: int     # total seconds from yard departure to yard arrival
    num_blocks: int


@dataclass(frozen=True)
class SolverInput:
    """Everything the CP-SAT solver needs — no domain objects."""
    variants: list[RouteVariant]
    num_vehicles: int
    vehicle_ids: list[UUID]
    trips_per_vehicle: int
    interval_seconds: int
    start_time: EpochSeconds
    end_time: EpochSeconds
    min_yard_dwells: list[int]       # per variant index
    cycle_times: list[int]           # per variant index
    interlocking_groups: dict[int, list[UUID]]  # group_id -> block_ids


@dataclass(frozen=True)
class TripAssignment:
    """Solver output for one trip."""
    vehicle_index: int
    trip_index: int
    depart_time: EpochSeconds
    variant_index: int


@dataclass(frozen=True)
class SolverOutput:
    """Complete solver result."""
    assignments: list[TripAssignment]
```

- [ ] **Step 2: Write failing test for route variant computation**

Create `tests/application/schedule/__init__.py` (empty) and `tests/application/schedule/test_route_variant.py`:

```python
from infra.seed import (
    BLOCK_ID_BY_NAME,
    PLATFORM_ID_BY_NAME,
    YARD_ID,
    create_blocks,
    create_connections,
    create_stations,
)
from application.schedule.route_variant import compute_route_variants


class TestComputeRouteVariants:
    def test_produces_eight_variants(self):
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        assert len(variants) == 8

    def test_all_variants_have_ten_blocks(self):
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        for v in variants:
            assert v.num_blocks == 10, f"Variant {v.index} has {v.num_blocks} blocks"

    def test_cycle_time_with_uniform_30s_blocks_and_30s_dwell(self):
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        # 10 blocks * 30s + 5 platform dwells * 30s = 450s
        for v in variants:
            assert v.cycle_time == 450, f"Variant {v.index}: {v.cycle_time}"

    def test_variant_zero_uses_p1a_and_p3a(self):
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        v0 = next(v for v in variants if v.s1_out == 0 and v.s3 == 0 and v.s1_ret == 0)
        block_ids = {bt.block_id for bt in v0.block_timings}
        # Should use B1, B3, B5, B6, B7, B10, B11, B12, B13, B1 (B1 twice)
        assert BLOCK_ID_BY_NAME["B1"] in block_ids
        assert BLOCK_ID_BY_NAME["B3"] in block_ids
        assert BLOCK_ID_BY_NAME["B7"] in block_ids
        assert BLOCK_ID_BY_NAME["B13"] in block_ids
        # Should NOT use B2, B4, B8, B9, B14
        assert BLOCK_ID_BY_NAME["B2"] not in block_ids
        assert BLOCK_ID_BY_NAME["B4"] not in block_ids

    def test_each_variant_has_six_station_arrivals(self):
        """Each trip visits S1, S2, S3 twice (outbound + return) = 6 arrivals."""
        variants = compute_route_variants(
            stations=create_stations(),
            blocks=create_blocks(),
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        for v in variants:
            assert len(v.station_arrivals) == 6, f"Variant {v.index}: {len(v.station_arrivals)}"

    def test_non_uniform_traversal_times(self):
        blocks = create_blocks()
        # Make B5 60s instead of 30s
        for b in blocks:
            if b.name == "B5":
                b.traversal_time_seconds = 60

        variants = compute_route_variants(
            stations=create_stations(),
            blocks=blocks,
            connections=create_connections(),
            dwell_time_seconds=30,
        )
        # 9 blocks * 30s + 1 block * 60s + 5 dwells * 30s = 270 + 60 + 150 = 480s
        for v in variants:
            assert v.cycle_time == 480, f"Variant {v.index}: {v.cycle_time}"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/application/schedule/test_route_variant.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'application.schedule'`

- [ ] **Step 4: Implement route variant computation**

Create `application/schedule/__init__.py` (empty) and `application/schedule/route_variant.py`:

```python
from __future__ import annotations

from itertools import product
from uuid import UUID

from domain.block.model import Block
from domain.domain_service.route_builder import build_full_route
from domain.network.model import NodeConnection, NodeType
from domain.station.model import Station

from application.schedule.model import (
    BlockTiming,
    RouteVariant,
    StationArrival,
)


def compute_route_variants(
    stations: list[Station],
    blocks: list[Block],
    connections: frozenset[NodeConnection],
    dwell_time_seconds: int,
) -> list[RouteVariant]:
    yard = next(s for s in stations if s.is_yard)
    platform_by_name = {
        p.name: p for s in stations for p in s.platforms
    }
    station_by_platform_id = {
        p.id: s for s in stations for p in s.platforms
    }
    block_by_id = {b.id: b for b in blocks}

    variants: list[RouteVariant] = []

    for index, (s1_out, s3_choice, s1_ret) in enumerate(product(range(2), repeat=3)):
        out_p1 = platform_by_name["P1B" if s1_out else "P1A"]
        p2a = platform_by_name["P2A"]
        s3_plat = platform_by_name["P3B" if s3_choice else "P3A"]
        p2b = platform_by_name["P2B"]
        ret_p1 = platform_by_name["P1B" if s1_ret else "P1A"]

        stop_ids = [yard.id, out_p1.id, p2a.id, s3_plat.id, p2b.id, ret_p1.id, yard.id]
        dwell_by_stop = {sid: dwell_time_seconds for sid in stop_ids}
        dwell_by_stop[yard.id] = 0  # yard dwell handled by solver

        route, timetable = build_full_route(
            stop_ids, dwell_by_stop, 0, connections, stations, blocks
        )

        block_timings: list[BlockTiming] = []
        station_arrivals: list[StationArrival] = []
        num_blocks = 0

        for node, entry in zip(route, timetable):
            if node.type == NodeType.BLOCK:
                block_timings.append(
                    BlockTiming(
                        block_id=node.id,
                        enter_offset=entry.arrival,
                        exit_offset=entry.departure,
                    )
                )
                num_blocks += 1
            elif node.type == NodeType.PLATFORM:
                station = station_by_platform_id[node.id]
                station_arrivals.append(
                    StationArrival(
                        station_name=station.name,
                        platform_id=node.id,
                        arrival_offset=entry.arrival,
                    )
                )

        cycle_time = timetable[-1].departure  # departure from final yard node

        variants.append(
            RouteVariant(
                index=index,
                s1_out=s1_out,
                s3=s3_choice,
                s1_ret=s1_ret,
                stop_ids=stop_ids,
                block_timings=block_timings,
                station_arrivals=station_arrivals,
                cycle_time=cycle_time,
                num_blocks=num_blocks,
            )
        )

    return variants
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/application/schedule/test_route_variant.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add application/schedule/ tests/application/schedule/
git commit -m "feat: add route variant pre-computation for schedule generation"
```

---

### Task 3: CP-SAT solver

**Files:**
- Create: `application/schedule/solver.py`
- Test: `tests/application/schedule/test_solver.py`

- [ ] **Step 1: Add ortools dependency**

```bash
cd /home/feidon/Documents/vss/backend && uv add ortools
```

- [ ] **Step 2: Write failing test for solver feasibility**

Create `tests/application/schedule/test_solver.py`:

```python
from uuid import uuid7

import pytest
from application.schedule.model import (
    BlockTiming,
    RouteVariant,
    SolverInput,
    SolverOutput,
    StationArrival,
)
from application.schedule.route_variant import compute_route_variants
from application.schedule.solver import solve_schedule
from infra.seed import (
    BLOCK_ID_BY_NAME,
    VEHICLE_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
)


def _build_solver_input(
    interval: int = 300,
    num_vehicles: int = 2,
    dwell: int = 30,
    start: int = 0,
    end: int = 3600,
) -> SolverInput:
    blocks = create_blocks()
    variants = compute_route_variants(
        stations=create_stations(),
        blocks=blocks,
        connections=create_connections(),
        dwell_time_seconds=dwell,
    )
    vehicle_ids = list(VEHICLE_ID_BY_NAME.values())[:num_vehicles]

    max_cycle = max(v.cycle_time for v in variants)
    max_blocks = max(v.num_blocks for v in variants)
    worst_yard_dwell = max_blocks * 12

    interval_per_vehicle = num_vehicles * interval
    trips_per_vehicle = (end - start) // interval_per_vehicle

    interlocking_groups: dict[int, list] = {}
    for b in blocks:
        if b.group != 0:
            interlocking_groups.setdefault(b.group, []).append(b.id)

    return SolverInput(
        variants=variants,
        num_vehicles=num_vehicles,
        vehicle_ids=vehicle_ids,
        trips_per_vehicle=max(trips_per_vehicle, 1),
        interval_seconds=interval,
        start_time=start,
        end_time=end,
        min_yard_dwells=[v.num_blocks * 12 for v in variants],
        cycle_times=[v.cycle_time for v in variants],
        interlocking_groups=interlocking_groups,
    )


class TestSolveSchedule:
    def test_feasible_returns_assignments(self):
        solver_input = _build_solver_input(
            interval=300, num_vehicles=2, start=0, end=3600,
        )
        result = solve_schedule(solver_input, timeout_seconds=30)
        assert result is not None
        total_trips = solver_input.num_vehicles * solver_input.trips_per_vehicle
        assert len(result.assignments) == total_trips

    def test_all_departures_within_time_range(self):
        solver_input = _build_solver_input(
            interval=300, num_vehicles=2, start=0, end=3600,
        )
        result = solve_schedule(solver_input, timeout_seconds=30)
        max_cycle = max(solver_input.cycle_times)
        for a in result.assignments:
            assert a.depart_time >= solver_input.start_time
            assert a.depart_time + max_cycle <= solver_input.end_time

    def test_variant_indices_are_valid(self):
        solver_input = _build_solver_input(
            interval=300, num_vehicles=2, start=0, end=3600,
        )
        result = solve_schedule(solver_input, timeout_seconds=30)
        for a in result.assignments:
            assert 0 <= a.variant_index < 8

    def test_vehicle_continuity_respected(self):
        solver_input = _build_solver_input(
            interval=300, num_vehicles=2, start=0, end=7200,
        )
        result = solve_schedule(solver_input, timeout_seconds=30)

        # Group by vehicle and sort by departure
        by_vehicle: dict[int, list] = {}
        for a in result.assignments:
            by_vehicle.setdefault(a.vehicle_index, []).append(a)
        for trips in by_vehicle.values():
            trips.sort(key=lambda t: t.depart_time)
            for i in range(len(trips) - 1):
                prev, nxt = trips[i], trips[i + 1]
                cycle = solver_input.cycle_times[prev.variant_index]
                yard_dwell = solver_input.min_yard_dwells[prev.variant_index]
                assert nxt.depart_time >= prev.depart_time + cycle + yard_dwell

    def test_infeasible_returns_none(self):
        # Interval so tight that 3 vehicles can't handle it
        solver_input = _build_solver_input(
            interval=10, num_vehicles=3, start=0, end=600,
        )
        result = solve_schedule(solver_input, timeout_seconds=5)
        assert result is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/application/schedule/test_solver.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'application.schedule.solver'`

- [ ] **Step 4: Implement CP-SAT solver**

Create `application/schedule/solver.py`:

```python
from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from ortools.sat.python import cp_model

from application.schedule.model import (
    SolverInput,
    SolverOutput,
    TripAssignment,
)


def solve_schedule(
    inp: SolverInput,
    timeout_seconds: int = 30,
) -> SolverOutput | None:
    model = cp_model.CpModel()
    total_trips = inp.num_vehicles * inp.trips_per_vehicle

    # ── Decision variables ──────────────────────────────────
    depart = []
    s1_out = []
    s3_var = []
    s1_ret = []
    variant_idx = []

    for s in range(total_trips):
        depart.append(
            model.new_int_var(inp.start_time, inp.end_time, f"depart_{s}")
        )
        s1_out.append(model.new_bool_var(f"s1_out_{s}"))
        s3_var.append(model.new_bool_var(f"s3_{s}"))
        s1_ret.append(model.new_bool_var(f"s1_ret_{s}"))

        vi = model.new_int_var(0, 7, f"variant_{s}")
        # variant_index = s1_out * 4 + s3 * 2 + s1_ret
        model.add(vi == s1_out[s] * 4 + s3_var[s] * 2 + s1_ret[s])
        variant_idx.append(vi)

    # ── Derived: cycle_time and yard_dwell per trip ─────────
    cycle_of_trip = []
    yard_dwell_of_trip = []
    for s in range(total_trips):
        ct = model.new_int_var(
            min(inp.cycle_times), max(inp.cycle_times), f"cycle_{s}"
        )
        model.add_element(variant_idx[s], inp.cycle_times, ct)
        cycle_of_trip.append(ct)

        yd = model.new_int_var(
            min(inp.min_yard_dwells), max(inp.min_yard_dwells), f"yd_{s}"
        )
        model.add_element(variant_idx[s], inp.min_yard_dwells, yd)
        yard_dwell_of_trip.append(yd)

    # ── C3: Vehicle continuity ──────────────────────────────
    for v in range(inp.num_vehicles):
        for t in range(inp.trips_per_vehicle - 1):
            s_prev = v * inp.trips_per_vehicle + t
            s_next = s_prev + 1
            model.add(
                depart[s_next]
                >= depart[s_prev] + cycle_of_trip[s_prev] + yard_dwell_of_trip[s_prev]
            )

    # ── C6: Time range ──────────────────────────────────────
    max_cycle = max(inp.cycle_times)
    for s in range(total_trips):
        model.add(depart[s] + max_cycle <= inp.end_time)

    # ── Precompute variant->block usage for C1 and C2 ───────
    # block_id -> list of (variant_index, enter_offset, exit_offset)
    block_variant_map: dict[UUID, list[tuple[int, int, int]]] = defaultdict(list)
    for var in inp.variants:
        for bt in var.block_timings:
            block_variant_map[bt.block_id].append(
                (var.index, bt.enter_offset, bt.exit_offset)
            )

    # ── Helper: is_variant[s][v] bool vars ──────────────────
    is_var: list[list[cp_model.IntVar]] = []
    for s in range(total_trips):
        trip_vars = []
        for v_idx in range(8):
            bv = model.new_bool_var(f"is_v{v_idx}_t{s}")
            model.add(variant_idx[s] == v_idx).only_enforce_if(bv)
            model.add(variant_idx[s] != v_idx).only_enforce_if(~bv)
            trip_vars.append(bv)
        is_var.append(trip_vars)

    # ── C1: Block occupancy ─────────────────────────────────
    for block_id, usages in block_variant_map.items():
        for s1 in range(total_trips):
            for s2 in range(s1 + 1, total_trips):
                for v1_idx, enter1, exit1 in usages:
                    for v2_idx, enter2, exit2 in usages:
                        both = model.new_bool_var(
                            f"blk_{block_id}_{s1}v{v1_idx}_{s2}v{v2_idx}"
                        )
                        model.add_bool_and([is_var[s1][v1_idx], is_var[s2][v2_idx]]).only_enforce_if(both)
                        model.add_bool_or([~is_var[s1][v1_idx], ~is_var[s2][v2_idx]]).only_enforce_if(~both)

                        # No overlap: s1 exits before s2 enters, or vice versa
                        order = model.new_bool_var(
                            f"ord_{block_id}_{s1}v{v1_idx}_{s2}v{v2_idx}"
                        )
                        model.add(
                            depart[s1] + exit1 <= depart[s2] + enter2
                        ).only_enforce_if(both, order)
                        model.add(
                            depart[s2] + exit2 <= depart[s1] + enter1
                        ).only_enforce_if(both, ~order)

    # ── C2: Interlocking ────────────────────────────────────
    for group_id, group_block_ids in inp.interlocking_groups.items():
        group_usages: list[tuple[UUID, int, int, int]] = []
        for bid in group_block_ids:
            for vi, enter, exit_ in block_variant_map.get(bid, []):
                group_usages.append((bid, vi, enter, exit_))

        for s1 in range(total_trips):
            for s2 in range(s1 + 1, total_trips):
                for bid1, vi1, enter1, exit1 in group_usages:
                    for bid2, vi2, enter2, exit2 in group_usages:
                        if bid1 == bid2:
                            continue  # same block handled by C1

                        both = model.new_bool_var(
                            f"ilk_g{group_id}_{s1}v{vi1}b{bid1}_{s2}v{vi2}b{bid2}"
                        )
                        model.add_bool_and(
                            [is_var[s1][vi1], is_var[s2][vi2]]
                        ).only_enforce_if(both)
                        model.add_bool_or(
                            [~is_var[s1][vi1], ~is_var[s2][vi2]]
                        ).only_enforce_if(~both)

                        order = model.new_bool_var(
                            f"ilk_ord_g{group_id}_{s1}v{vi1}_{s2}v{vi2}"
                        )
                        model.add(
                            depart[s1] + exit1 <= depart[s2] + enter2
                        ).only_enforce_if(both, order)
                        model.add(
                            depart[s2] + exit2 <= depart[s1] + enter1
                        ).only_enforce_if(both, ~order)

    # ── C5: Station frequency ───────────────────────────────
    # For each station, each trip visits it twice (outbound + return).
    # Use AddElement to pick the arrival offset for the active variant,
    # giving exactly 2 * total_trips arrival IntVars per station.
    # Then sort via permutation variables and constrain consecutive gaps.
    station_names = ["S1", "S2", "S3"]

    # Pre-build per-station, per-visit-type offset arrays (indexed by variant)
    # Each station has 2 visits: outbound (first occurrence) and return (second)
    station_offsets: dict[str, tuple[list[int], list[int]]] = {}
    for sname in station_names:
        out_offsets = []  # one per variant
        ret_offsets = []
        for var in inp.variants:
            hits = [sa for sa in var.station_arrivals if sa.station_name == sname]
            out_offsets.append(hits[0].arrival_offset)
            ret_offsets.append(hits[1].arrival_offset)
        station_offsets[sname] = (out_offsets, ret_offsets)

    for sname in station_names:
        out_offsets, ret_offsets = station_offsets[sname]
        arrivals: list[cp_model.IntVar] = []

        for s in range(total_trips):
            # Outbound arrival
            out_off = model.new_int_var(
                min(out_offsets), max(out_offsets), f"out_off_{sname}_{s}"
            )
            model.add_element(variant_idx[s], out_offsets, out_off)
            out_arr = model.new_int_var(
                inp.start_time, inp.end_time + max_cycle, f"out_arr_{sname}_{s}"
            )
            model.add(out_arr == depart[s] + out_off)
            arrivals.append(out_arr)

            # Return arrival
            ret_off = model.new_int_var(
                min(ret_offsets), max(ret_offsets), f"ret_off_{sname}_{s}"
            )
            model.add_element(variant_idx[s], ret_offsets, ret_off)
            ret_arr = model.new_int_var(
                inp.start_time, inp.end_time + max_cycle, f"ret_arr_{sname}_{s}"
            )
            model.add(ret_arr == depart[s] + ret_off)
            arrivals.append(ret_arr)

        # Sort arrivals via permutation: pos[i] = sorted position of arrivals[i]
        n = len(arrivals)
        pos = [model.new_int_var(0, n - 1, f"pos_{sname}_{i}") for i in range(n)]
        model.add_all_different(pos)

        sorted_arr = [
            model.new_int_var(
                inp.start_time, inp.end_time + max_cycle, f"sorted_{sname}_{k}"
            )
            for k in range(n)
        ]
        # Link: arrivals[i] == sorted_arr[pos[i]]
        for i in range(n):
            model.add_element(pos[i], sorted_arr, arrivals[i])

        # Sorted order
        for k in range(n - 1):
            model.add(sorted_arr[k] <= sorted_arr[k + 1])

        # Consecutive gap <= interval
        for k in range(n - 1):
            model.add(sorted_arr[k + 1] - sorted_arr[k] <= inp.interval_seconds)

    # ── Solve ───────────────────────────────────────────────
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds

    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    assignments: list[TripAssignment] = []
    for s in range(total_trips):
        v_idx = s // inp.trips_per_vehicle
        t_idx = s % inp.trips_per_vehicle
        assignments.append(
            TripAssignment(
                vehicle_index=v_idx,
                trip_index=t_idx,
                depart_time=solver.value(depart[s]),
                variant_index=solver.value(variant_idx[s]),
            )
        )

    return SolverOutput(assignments=assignments)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/application/schedule/test_solver.py -v`
Expected: PASS (may take a few seconds for solver)

- [ ] **Step 6: Commit**

```bash
git add application/schedule/solver.py tests/application/schedule/test_solver.py pyproject.toml uv.lock
git commit -m "feat: add CP-SAT solver for schedule generation"
```

---

### Task 4: Schedule application service

**Files:**
- Create: `application/schedule/dto.py`
- Create: `application/schedule/schedule_service.py`
- Test: `tests/application/schedule/test_schedule_service.py`

- [ ] **Step 1: Create DTOs**

Create `application/schedule/dto.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.shared.types import EpochSeconds


@dataclass(frozen=True)
class GenerateScheduleRequest:
    interval_seconds: int
    start_time: EpochSeconds
    end_time: EpochSeconds
    dwell_time_seconds: int


@dataclass(frozen=True)
class GenerateScheduleResponse:
    services_created: int
    vehicles_used: list[UUID]
    cycle_time_seconds: int
```

- [ ] **Step 2: Write failing test**

Create `tests/application/schedule/test_schedule_service.py`:

```python
from uuid import uuid7

import pytest
from application.schedule.dto import GenerateScheduleRequest
from application.schedule.schedule_service import ScheduleAppService
from domain.error import DomainError
from domain.vehicle.model import Vehicle
from infra.seed import (
    VEHICLE_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
    create_vehicles,
)

from tests.fakes.block_repo import InMemoryBlockRepository
from tests.fakes.connection_repo import InMemoryConnectionRepository
from tests.fakes.service_repo import InMemoryServiceRepository
from tests.fakes.station_repo import InMemoryStationRepository
from tests.fakes.vehicle_repo import InMemoryVehicleRepository


def _make_app():
    block_repo = InMemoryBlockRepository()
    for b in create_blocks():
        block_repo._store[b.id] = b

    station_repo = InMemoryStationRepository()
    for s in create_stations():
        station_repo._store[s.id] = s

    connection_repo = InMemoryConnectionRepository(create_connections())

    vehicle_repo = InMemoryVehicleRepository()
    for v in create_vehicles():
        vehicle_repo._store[v.id] = v

    service_repo = InMemoryServiceRepository()

    return ScheduleAppService(
        service_repo=service_repo,
        block_repo=block_repo,
        connection_repo=connection_repo,
        vehicle_repo=vehicle_repo,
        station_repo=station_repo,
    ), service_repo


class TestScheduleAppService:
    async def test_generates_services(self):
        app, service_repo = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=300,
            start_time=0,
            end_time=3600,
            dwell_time_seconds=30,
        )
        result = await app.generate_schedule(req)
        assert result.services_created > 0
        assert len(await service_repo.find_all()) == result.services_created

    async def test_clears_existing_services_first(self):
        app, service_repo = _make_app()
        # Generate once
        req = GenerateScheduleRequest(
            interval_seconds=300, start_time=0, end_time=3600, dwell_time_seconds=30,
        )
        first = await app.generate_schedule(req)
        # Generate again — should clear and recreate
        second = await app.generate_schedule(req)
        assert len(await service_repo.find_all()) == second.services_created

    async def test_rejects_invalid_interval(self):
        app, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=0, start_time=0, end_time=3600, dwell_time_seconds=30,
        )
        with pytest.raises(DomainError, match="interval"):
            await app.generate_schedule(req)

    async def test_rejects_invalid_time_range(self):
        app, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=300, start_time=3600, end_time=0, dwell_time_seconds=30,
        )
        with pytest.raises(DomainError, match="end_time"):
            await app.generate_schedule(req)

    async def test_vehicles_used_in_response(self):
        app, _ = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=300, start_time=0, end_time=3600, dwell_time_seconds=30,
        )
        result = await app.generate_schedule(req)
        assert len(result.vehicles_used) > 0
        for vid in result.vehicles_used:
            assert vid in VEHICLE_ID_BY_NAME.values()

    async def test_service_names_follow_convention(self):
        app, service_repo = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=300, start_time=0, end_time=3600, dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()
        for svc in services:
            assert svc.name.startswith("Auto-V")

    async def test_no_conflicts_in_generated_schedule(self):
        """Verify ConflictDetectionService finds zero conflicts."""
        app, service_repo = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=300, start_time=0, end_time=3600, dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()
        blocks = create_blocks()

        from domain.domain_service.conflict import detect_conflicts
        for svc in services:
            others = [s for s in services if s.id != svc.id]
            conflicts = detect_conflicts(svc, others, blocks)
            assert not conflicts.has_conflicts, f"Service {svc.name} has conflicts"

    async def test_station_frequency_within_interval(self):
        """At every station, max gap between arrivals <= interval."""
        app, service_repo = _make_app()
        interval = 300
        req = GenerateScheduleRequest(
            interval_seconds=interval, start_time=0, end_time=3600, dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()
        blocks = create_blocks()
        stations = create_stations()

        block_ids = {b.id for b in blocks}
        platform_to_station = {
            p.id: s.name for s in stations for p in s.platforms
        }

        # Collect arrival times per station
        arrivals_by_station: dict[str, list[int]] = {"S1": [], "S2": [], "S3": []}
        for svc in services:
            for entry in svc.timetable:
                sname = platform_to_station.get(entry.node_id)
                if sname:
                    arrivals_by_station[sname].append(entry.arrival)

        for sname, times in arrivals_by_station.items():
            times.sort()
            for i in range(len(times) - 1):
                gap = times[i + 1] - times[i]
                assert gap <= interval, (
                    f"Station {sname}: gap {gap}s between arrivals "
                    f"at t={times[i]} and t={times[i+1]} exceeds interval {interval}s"
                )

    async def test_vehicle_yard_dwell_sufficient_for_recharge(self):
        """Between consecutive trips, yard dwell >= num_blocks * 12s."""
        app, service_repo = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=300, start_time=0, end_time=7200, dwell_time_seconds=30,
        )
        await app.generate_schedule(req)
        services = await service_repo.find_all()

        from domain.network.model import NodeType
        # Group by vehicle, sort by start time
        by_vehicle: dict[str, list] = {}
        for svc in services:
            by_vehicle.setdefault(str(svc.vehicle_id), []).append(svc)
        for trips in by_vehicle.values():
            trips.sort(key=lambda s: s.timetable[0].arrival)
            for i in range(len(trips) - 1):
                prev_end = trips[i].timetable[-1].departure
                next_start = trips[i + 1].timetable[0].arrival
                yard_dwell = next_start - prev_end
                num_blocks = sum(
                    1 for n in trips[i].route if n.type == NodeType.BLOCK
                )
                min_dwell = num_blocks * 12
                assert yard_dwell >= min_dwell, (
                    f"Yard dwell {yard_dwell}s < min {min_dwell}s for {num_blocks} blocks"
                )
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/application/schedule/test_schedule_service.py -v`
Expected: FAIL

- [ ] **Step 4: Implement schedule service**

Create `application/schedule/schedule_service.py`:

```python
from __future__ import annotations

import math

from domain.block.repository import BlockRepository
from domain.domain_service.conflict.block import detect_block_conflicts
from domain.domain_service.conflict.interlocking import detect_interlocking_conflicts
from domain.domain_service.conflict.shared import (
    build_occupancies,
    build_vehicle_schedule,
)
from domain.domain_service.conflict.vehicle import detect_vehicle_conflicts
from domain.domain_service.route_builder import build_full_route
from domain.error import DomainError, ErrorCode
from domain.network.repository import ConnectionRepository
from domain.service.model import Service
from domain.service.repository import ServiceRepository
from domain.station.repository import StationRepository
from domain.vehicle.repository import VehicleRepository

from application.schedule.dto import GenerateScheduleRequest, GenerateScheduleResponse
from application.schedule.model import SolverInput
from application.schedule.route_variant import compute_route_variants
from application.schedule.solver import solve_schedule


class ScheduleAppService:
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

    async def generate_schedule(
        self, req: GenerateScheduleRequest
    ) -> GenerateScheduleResponse:
        # ── Validate input ──────────────────────────────────
        if req.interval_seconds <= 0:
            raise DomainError(ErrorCode.VALIDATION, "interval_seconds must be > 0")
        if req.dwell_time_seconds <= 0:
            raise DomainError(ErrorCode.VALIDATION, "dwell_time_seconds must be > 0")
        if req.end_time <= req.start_time:
            raise DomainError(ErrorCode.VALIDATION, "end_time must be after start_time")

        # ── Load data ───────────────────────────────────────
        blocks = await self._block_repo.find_all()
        stations = await self._station_repo.find_all()
        connections = await self._connection_repo.find_all()
        vehicles = await self._vehicle_repo.find_all()

        # ── Pre-compute route variants ──────────────────────
        variants = compute_route_variants(
            stations, blocks, connections, req.dwell_time_seconds
        )

        # ── Vehicle count ───────────────────────────────────
        max_cycle = max(v.cycle_time for v in variants)
        max_blocks = max(v.num_blocks for v in variants)
        worst_yard_dwell = max_blocks * 12
        effective_cycle = max_cycle + worst_yard_dwell
        num_vehicles = math.ceil(effective_cycle / req.interval_seconds) + 1

        if num_vehicles > len(vehicles):
            raise DomainError(
                ErrorCode.VALIDATION,
                f"Need {num_vehicles} vehicles but only {len(vehicles)} available",
            )

        used_vehicles = vehicles[:num_vehicles]

        # ── Trip count ──────────────────────────────────────
        interval_per_vehicle = num_vehicles * req.interval_seconds
        trips_per_vehicle = max(
            (req.end_time - req.start_time) // interval_per_vehicle, 1
        )

        # ── Build interlocking groups ───────────────────────
        interlocking_groups: dict[int, list] = {}
        for b in blocks:
            if b.group != 0:
                interlocking_groups.setdefault(b.group, []).append(b.id)

        # ── Solve ───────────────────────────────────────────
        solver_input = SolverInput(
            variants=variants,
            num_vehicles=num_vehicles,
            vehicle_ids=[v.id for v in used_vehicles],
            trips_per_vehicle=trips_per_vehicle,
            interval_seconds=req.interval_seconds,
            start_time=req.start_time,
            end_time=req.end_time,
            min_yard_dwells=[v.num_blocks * 12 for v in variants],
            cycle_times=[v.cycle_time for v in variants],
            interlocking_groups=interlocking_groups,
        )

        result = solve_schedule(solver_input)
        if result is None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "Cannot generate a conflict-free schedule with the given parameters",
            )

        # ── Post-process: build Service objects ─────────────
        await self._service_repo.delete_all()

        services: list[Service] = []
        for assignment in result.assignments:
            variant = variants[assignment.variant_index]
            vehicle = used_vehicles[assignment.vehicle_index]

            dwell_by_stop = {
                sid: req.dwell_time_seconds for sid in variant.stop_ids
            }
            yard_id = variant.stop_ids[0]
            dwell_by_stop[yard_id] = 0

            route, timetable = build_full_route(
                variant.stop_ids,
                dwell_by_stop,
                assignment.depart_time,
                connections,
                stations,
                blocks,
            )

            name = f"Auto-V{assignment.vehicle_index + 1}-T{assignment.trip_index + 1}"
            service = Service(
                name=name,
                vehicle_id=vehicle.id,
                route=route,
                timetable=timetable,
            )
            created = await self._service_repo.create(service)
            services.append(created)

        # ── Sanity check: run conflict detection ────────────
        block_occ, group_occ = build_occupancies(services, blocks)
        block_conflicts = detect_block_conflicts(block_occ)
        interlocking_conflicts = detect_interlocking_conflicts(group_occ)

        vehicle_conflicts = []
        for v in used_vehicles:
            schedule = build_vehicle_schedule(v.id, services)
            vehicle_conflicts.extend(
                detect_vehicle_conflicts(v.id, schedule.windows, schedule.endpoints)
            )

        if block_conflicts or interlocking_conflicts or vehicle_conflicts:
            raise RuntimeError(
                "BUG: Generated schedule has conflicts. "
                f"Block: {len(block_conflicts)}, "
                f"Interlocking: {len(interlocking_conflicts)}, "
                f"Vehicle: {len(vehicle_conflicts)}"
            )

        return GenerateScheduleResponse(
            services_created=len(services),
            vehicles_used=[v.id for v in used_vehicles],
            cycle_time_seconds=max_cycle,
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/application/schedule/test_schedule_service.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add application/schedule/dto.py application/schedule/schedule_service.py tests/application/schedule/test_schedule_service.py
git commit -m "feat: add ScheduleAppService orchestrating schedule generation"
```

---

### Task 5: API endpoint

**Files:**
- Create: `api/schedule/routes.py`
- Create: `api/schedule/schemas.py`
- Modify: `api/dependencies.py`
- Modify: `main.py`
- Test: `tests/api/test_schedule_routes.py`

- [ ] **Step 1: Create Pydantic schemas**

Create `api/schedule/__init__.py` (empty) and `api/schedule/schemas.py`:

```python
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from application.schedule.dto import GenerateScheduleResponse


class GenerateScheduleRequestSchema(BaseModel):
    interval_seconds: int = Field(gt=0)
    start_time: int
    end_time: int
    dwell_time_seconds: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            msg = "end_time must be greater than start_time"
            raise ValueError(msg)
        return self


class GenerateScheduleResponseSchema(BaseModel):
    services_created: int
    vehicles_used: list[UUID]
    cycle_time_seconds: int

    @classmethod
    def from_dto(cls, dto: GenerateScheduleResponse) -> GenerateScheduleResponseSchema:
        return cls(
            services_created=dto.services_created,
            vehicles_used=dto.vehicles_used,
            cycle_time_seconds=dto.cycle_time_seconds,
        )
```

- [ ] **Step 2: Create API route**

Create `api/schedule/routes.py`:

```python
from __future__ import annotations

from application.schedule.dto import GenerateScheduleRequest
from application.schedule.schedule_service import ScheduleAppService
from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from api.dependencies import get_schedule_app_service
from api.schedule.schemas import (
    GenerateScheduleRequestSchema,
    GenerateScheduleResponseSchema,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post(
    "/generate",
    response_model=GenerateScheduleResponseSchema,
    status_code=HTTP_200_OK,
)
async def generate_schedule(
    body: GenerateScheduleRequestSchema,
    service: ScheduleAppService = Depends(get_schedule_app_service),
) -> GenerateScheduleResponseSchema:
    dto = GenerateScheduleRequest(
        interval_seconds=body.interval_seconds,
        start_time=body.start_time,
        end_time=body.end_time,
        dwell_time_seconds=body.dwell_time_seconds,
    )
    result = await service.generate_schedule(dto)
    return GenerateScheduleResponseSchema.from_dto(result)
```

- [ ] **Step 3: Add DI wiring**

In `api/dependencies.py`, add the import and factory function:

```python
from application.schedule.schedule_service import ScheduleAppService

def get_schedule_app_service(
    service_repo: ServiceRepository = Depends(get_service_repo),
    block_repo: BlockRepository = Depends(get_block_repo),
    connection_repo: ConnectionRepository = Depends(get_connection_repo),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repo),
    station_repo: StationRepository = Depends(get_station_repo),
) -> ScheduleAppService:
    return ScheduleAppService(
        service_repo, block_repo, connection_repo, vehicle_repo, station_repo
    )
```

- [ ] **Step 4: Register router in main.py**

In `main.py`, add:

```python
from api.schedule.routes import router as schedule_router
# ...
app.include_router(schedule_router, prefix=API_PREFIX)
```

- [ ] **Step 5: Write API test**

Create `tests/api/test_schedule_routes.py`:

```python
import pytest
from infra.seed import VEHICLE_ID_BY_NAME

pytestmark = pytest.mark.postgres


class TestGenerateSchedule:
    async def test_generate_returns_200(self, client):
        resp = await client.post(
            "schedules/generate",
            json={
                "interval_seconds": 300,
                "start_time": 0,
                "end_time": 3600,
                "dwell_time_seconds": 30,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["services_created"] > 0
        assert len(data["vehicles_used"]) > 0
        assert data["cycle_time_seconds"] > 0

    async def test_generated_services_are_persisted(self, client):
        await client.post(
            "schedules/generate",
            json={
                "interval_seconds": 300,
                "start_time": 0,
                "end_time": 3600,
                "dwell_time_seconds": 30,
            },
        )
        resp = await client.get("services")
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    async def test_clears_existing_services(self, client):
        # Create a manual service first
        vid = str(list(VEHICLE_ID_BY_NAME.values())[0])
        await client.post("services", json={"name": "Manual", "vehicle_id": vid})

        # Generate schedule — should clear the manual service
        resp = await client.post(
            "schedules/generate",
            json={
                "interval_seconds": 300,
                "start_time": 0,
                "end_time": 3600,
                "dwell_time_seconds": 30,
            },
        )
        assert resp.status_code == 200
        services = (await client.get("services")).json()
        assert all(s["name"].startswith("Auto-") for s in services)

    async def test_invalid_interval_returns_422(self, client):
        resp = await client.post(
            "schedules/generate",
            json={
                "interval_seconds": 0,
                "start_time": 0,
                "end_time": 3600,
                "dwell_time_seconds": 30,
            },
        )
        assert resp.status_code == 422
```

- [ ] **Step 6: Run API test**

Run: `uv run pytest tests/api/test_schedule_routes.py -v -m postgres`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add api/schedule/ api/dependencies.py main.py tests/api/test_schedule_routes.py
git commit -m "feat: add POST /api/schedules/generate endpoint"
```

---

### Task 6: Architecture lint and full test suite

**Files:** None new — verification only.

- [ ] **Step 1: Run architecture lint**

Run: `uv run lint-imports`
Expected: PASS — `application/schedule/solver.py` imports `ortools` (external, not in the layered contracts). Domain remains pure.

- [ ] **Step 2: Run ruff check**

Run: `uv run ruff check`
Expected: PASS or only pre-existing warnings

- [ ] **Step 3: Run all unit and application tests**

Run: `uv run pytest -v`
Expected: All PASS

- [ ] **Step 4: Run all PostgreSQL integration tests**

Run: `uv run pytest -v -m postgres`
Expected: All PASS

- [ ] **Step 5: Commit any lint fixes**

```bash
git add -A
git commit -m "chore: fix lint issues from schedule generation feature"
```

(Skip if no changes needed.)
