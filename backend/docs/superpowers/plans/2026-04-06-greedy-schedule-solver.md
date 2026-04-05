# Greedy Schedule Solver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the CP-SAT cyclic tiling solver with a greedy sequential dispatch solver that works for any user-provided interval.

**Architecture:** The greedy solver places trips one at a time in temporal order, picking the first available vehicle and first conflict-free route variant. Block/interlocking occupancies are tracked incrementally — conflicts are impossible by construction. The schedule service passes start/end time directly to the solver (no tiling).

**Tech Stack:** Python 3.14, pytest, no new dependencies (removes ortools)

**Spec:** `docs/superpowers/specs/2026-04-05-greedy-schedule-solver-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `application/schedule/model.py` | Simplify SolverInput (drop tile_period, add start/end), remove trip_index from TripAssignment |
| Rewrite | `application/schedule/solver.py` | Greedy dispatch algorithm |
| Modify | `application/schedule/schedule_service.py` | Remove tiling loop, use absolute departure times from solver |
| Rewrite | `tests/application/schedule/test_solver.py` | New tests for greedy behavior |
| Modify | `tests/application/schedule/test_schedule_service.py` | Adapt to new solver interface |
| Modify | `pyproject.toml` | Remove ortools dependency |

---

### Task 1: Update data models

**Files:**
- Modify: `application/schedule/model.py`

- [ ] **Step 1: Update SolverInput dataclass**

Replace `tile_period`, `min_yard_dwells`, `cycle_times` with `start_time` and `end_time`:

```python
@dataclass(frozen=True)
class SolverInput:
    """Everything the solver needs - no domain objects."""

    variants: list[RouteVariant]
    num_vehicles: int
    vehicle_ids: list[UUID]
    start_time: int  # epoch seconds
    end_time: int  # epoch seconds
    interval_seconds: int
    interlocking_groups: dict[int, list[UUID]]  # group_id -> block_ids
```

- [ ] **Step 2: Remove trip_index from TripAssignment**

```python
@dataclass(frozen=True)
class TripAssignment:
    """Solver output for one trip."""

    vehicle_index: int
    depart_time: EpochSeconds  # absolute epoch seconds
    variant_index: int
```

- [ ] **Step 3: Verify import**

Run: `cd /home/feidon/Documents/vss/backend && uv run python -c "from application.schedule.model import SolverInput, TripAssignment; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add application/schedule/model.py
git commit -m "refactor: simplify SolverInput and TripAssignment for greedy solver"
```

---

### Task 2: Rewrite solver with greedy dispatch

**Files:**
- Rewrite: `application/schedule/solver.py`
- Rewrite: `tests/application/schedule/test_solver.py`

- [ ] **Step 1: Write test helper and basic test**

Replace the entire `tests/application/schedule/test_solver.py` with:

```python
from collections import defaultdict
from uuid import UUID

from application.schedule.model import SolverInput
from application.schedule.route_variant import compute_route_variants
from application.schedule.solver import solve_schedule
from infra.seed import (
    VEHICLE_ID_BY_NAME,
    create_blocks,
    create_connections,
    create_stations,
)


def _build_input(
    interval: int = 360,
    num_vehicles: int = 2,
    dwell: int = 30,
    start_time: int = 0,
    end_time: int = 3600,
) -> SolverInput:
    blocks = create_blocks()
    variants = compute_route_variants(
        stations=create_stations(),
        blocks=blocks,
        connections=create_connections(),
        dwell_time_seconds=dwell,
    )

    interlocking_groups: dict[int, list] = {}
    for b in blocks:
        if b.group != 0:
            interlocking_groups.setdefault(b.group, []).append(b.id)

    return SolverInput(
        variants=variants,
        num_vehicles=num_vehicles,
        vehicle_ids=list(VEHICLE_ID_BY_NAME.values())[:num_vehicles],
        start_time=start_time,
        end_time=end_time,
        interval_seconds=interval,
        interlocking_groups=interlocking_groups,
    )


class TestGreedySolver:
    def test_produces_assignments(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

    def test_departures_within_time_range(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert a.depart_time >= inp.start_time
            variant = inp.variants[a.variant_index]
            assert a.depart_time + variant.cycle_time <= inp.end_time

    def test_variant_indices_valid(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert 0 <= a.variant_index < len(inp.variants)

    def test_vehicle_indices_valid(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        for a in result.assignments:
            assert 0 <= a.vehicle_index < inp.num_vehicles

    def test_no_block_overlaps(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        block_intervals: dict[UUID, list[tuple[int, int]]] = defaultdict(list)
        for a in result.assignments:
            var = inp.variants[a.variant_index]
            for bt in var.block_timings:
                enter = a.depart_time + bt.enter_offset
                exit_ = a.depart_time + bt.exit_offset
                block_intervals[bt.block_id].append((enter, exit_))

        for bid, intervals in block_intervals.items():
            intervals.sort()
            for i in range(len(intervals) - 1):
                assert intervals[i][1] <= intervals[i + 1][0], (
                    f"Block {bid} overlap: {intervals[i]} and {intervals[i + 1]}"
                )

    def test_no_interlocking_overlaps(self):
        inp = _build_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp)
        block_intervals: dict[UUID, list[tuple[int, int]]] = defaultdict(list)
        for a in result.assignments:
            var = inp.variants[a.variant_index]
            for bt in var.block_timings:
                enter = a.depart_time + bt.enter_offset
                exit_ = a.depart_time + bt.exit_offset
                block_intervals[bt.block_id].append((enter, exit_))

        for group_block_ids in inp.interlocking_groups.values():
            group_intervals = []
            for bid in group_block_ids:
                group_intervals.extend(block_intervals.get(bid, []))
            group_intervals.sort()
            for i in range(len(group_intervals) - 1):
                assert group_intervals[i][1] <= group_intervals[i + 1][0], (
                    f"Interlocking overlap: {group_intervals[i]} and {group_intervals[i + 1]}"
                )

    def test_tight_interval_still_produces_result(self):
        """interval=120s was infeasible with CP-SAT cyclic solver."""
        inp = _build_input(interval=120, num_vehicles=6, end_time=7200)
        result = solve_schedule(inp)
        assert len(result.assignments) > 0

    def test_empty_when_time_range_too_short(self):
        inp = _build_input(interval=360, num_vehicles=2, start_time=0, end_time=100)
        result = solve_schedule(inp)
        assert len(result.assignments) == 0

    def test_vehicle_recharge_respected(self):
        """Same vehicle's consecutive trips have enough yard dwell."""
        inp = _build_input(interval=360, num_vehicles=2, end_time=7200)
        result = solve_schedule(inp)

        by_vehicle: dict[int, list] = defaultdict(list)
        for a in result.assignments:
            by_vehicle[a.vehicle_index].append(a)

        for trips in by_vehicle.values():
            trips.sort(key=lambda a: a.depart_time)
            for i in range(len(trips) - 1):
                prev = trips[i]
                curr = trips[i + 1]
                prev_var = inp.variants[prev.variant_index]
                cycle_end = prev.depart_time + prev_var.cycle_time
                yard_dwell = prev_var.num_blocks * 12
                assert curr.depart_time >= cycle_end + yard_dwell, (
                    f"V{prev.vehicle_index}: next trip at {curr.depart_time} "
                    f"but earliest available at {cycle_end + yard_dwell}"
                )

    def test_deterministic(self):
        """Same input produces same output."""
        inp = _build_input(interval=300, num_vehicles=3, end_time=7200)
        r1 = solve_schedule(inp)
        r2 = solve_schedule(inp)
        assert len(r1.assignments) == len(r2.assignments)
        for a1, a2 in zip(r1.assignments, r2.assignments):
            assert a1.depart_time == a2.depart_time
            assert a1.variant_index == a2.variant_index
            assert a1.vehicle_index == a2.vehicle_index
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_solver.py -v 2>&1 | tail -20`
Expected: FAIL (SolverInput constructor mismatch or import error)

- [ ] **Step 3: Rewrite solver.py**

Replace the entire `application/schedule/solver.py` with:

```python
"""Greedy sequential dispatch solver for automatic schedule generation.

Pure function — no I/O, no async, no domain objects.
Takes SolverInput, returns SolverOutput (possibly with empty assignments).
"""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from application.schedule.model import (
    SolverInput,
    SolverOutput,
    TripAssignment,
)


def solve_schedule(inp: SolverInput) -> SolverOutput:
    """Place trips one at a time in temporal order.

    For each departure slot, pick the first available vehicle
    (tie-break: lowest index) and the first route variant (index
    order 0-7) that has no block or interlocking conflicts with
    already-placed trips.
    """
    occupancies: dict[UUID, list[tuple[int, int]]] = defaultdict(list)
    vehicle_available = {i: inp.start_time for i in range(inp.num_vehicles)}
    assignments: list[TripAssignment] = []

    group_for_block = _build_group_lookup(inp.interlocking_groups)
    min_cycle = min(v.cycle_time for v in inp.variants)

    next_desired = inp.start_time
    while next_desired + min_cycle <= inp.end_time:
        vehicle = min(vehicle_available, key=lambda v: (vehicle_available[v], v))
        depart = max(vehicle_available[vehicle], next_desired)

        placed = False
        earliest_conflict_end = next_desired
        for variant in inp.variants:
            if depart + variant.cycle_time > inp.end_time:
                continue
            conflict_end = _find_conflict(
                depart, variant, occupancies, inp.interlocking_groups, group_for_block
            )
            if conflict_end is None:
                _record_occupancies(depart, variant, occupancies)
                yard_dwell = variant.num_blocks * 12
                vehicle_available[vehicle] = depart + variant.cycle_time + yard_dwell
                assignments.append(
                    TripAssignment(
                        vehicle_index=vehicle,
                        depart_time=depart,
                        variant_index=variant.index,
                    )
                )
                next_desired = depart + inp.interval_seconds
                placed = True
                break
            earliest_conflict_end = max(earliest_conflict_end, conflict_end)

        if not placed:
            if earliest_conflict_end <= next_desired:
                break  # stuck — no progress possible
            next_desired = earliest_conflict_end

    return SolverOutput(assignments=assignments)


def _build_group_lookup(
    interlocking_groups: dict[int, list[UUID]],
) -> dict[UUID, int]:
    """Map each block_id to its interlocking group_id (0 if none)."""
    lookup: dict[UUID, int] = {}
    for group_id, block_ids in interlocking_groups.items():
        for bid in block_ids:
            lookup[bid] = group_id
    return lookup


def _find_conflict(
    depart: int,
    variant,
    occupancies: dict[UUID, list[tuple[int, int]]],
    interlocking_groups: dict[int, list[UUID]],
    group_for_block: dict[UUID, int],
) -> int | None:
    """Return the earliest conflict-end time, or None if no conflicts."""
    for bt in variant.block_timings:
        enter = depart + bt.enter_offset
        exit_ = depart + bt.exit_offset

        # Check same block
        conflict_end = _check_overlap(enter, exit_, occupancies.get(bt.block_id, []))
        if conflict_end is not None:
            return conflict_end

        # Check interlocking group peers
        group_id = group_for_block.get(bt.block_id)
        if group_id is not None:
            for peer_bid in interlocking_groups[group_id]:
                if peer_bid == bt.block_id:
                    continue
                conflict_end = _check_overlap(
                    enter, exit_, occupancies.get(peer_bid, [])
                )
                if conflict_end is not None:
                    return conflict_end

    return None


def _check_overlap(
    enter: int, exit_: int, existing: list[tuple[int, int]]
) -> int | None:
    """Return the exit time of the first overlapping occupancy, or None."""
    for ex_enter, ex_exit in existing:
        if enter < ex_exit and exit_ > ex_enter:
            return ex_exit
    return None


def _record_occupancies(depart: int, variant, occupancies: dict[UUID, list[tuple[int, int]]]) -> None:
    for bt in variant.block_timings:
        occupancies[bt.block_id].append(
            (depart + bt.enter_offset, depart + bt.exit_offset)
        )
```

- [ ] **Step 4: Run tests**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_solver.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add application/schedule/solver.py tests/application/schedule/test_solver.py
git commit -m "feat: replace CP-SAT solver with greedy sequential dispatch"
```

---

### Task 3: Update schedule service

**Files:**
- Modify: `application/schedule/schedule_service.py`

- [ ] **Step 1: Rewrite generate_schedule method**

Replace the entire `generate_schedule` method. Key changes:
- Build `SolverInput` with `start_time`/`end_time` instead of `tile_period`
- No tiling — iterate solver output directly (absolute departure times)
- Keep sanity check

```python
    async def generate_schedule(
        self,
        req: GenerateScheduleRequest,
    ) -> GenerateScheduleResponse:
        # 1. Validate input
        self._validate_request(req)

        # 2. Load all data from repos
        blocks = await self._block_repo.find_all()
        stations = await self._station_repo.find_all()
        connections = await self._connection_repo.find_all()
        vehicles = await self._vehicle_repo.find_all()

        # 3. Compute route variants
        variants = compute_route_variants(
            stations, blocks, connections, req.dwell_time_seconds
        )

        # 4. Compute num_vehicles
        cycle_times = [v.cycle_time for v in variants]
        min_yard_dwells = [v.num_blocks * 12 for v in variants]
        max_turnaround = max(c + y for c, y in zip(cycle_times, min_yard_dwells))
        num_vehicles = math.ceil(max_turnaround / req.interval_seconds) + 1

        if num_vehicles > len(vehicles):
            await self._vehicle_repo.add_by_number(num_vehicles - len(vehicles))
            vehicles = await self._vehicle_repo.find_all()

        used_vehicles = vehicles[:num_vehicles]

        # 5. Build interlocking groups
        interlocking_groups: dict[int, list] = {}
        for b in blocks:
            if b.group != 0:
                interlocking_groups.setdefault(b.group, []).append(b.id)

        # 6. Solve
        solver_input = SolverInput(
            variants=variants,
            num_vehicles=num_vehicles,
            vehicle_ids=[v.id for v in used_vehicles],
            start_time=req.start_time,
            end_time=req.end_time,
            interval_seconds=req.interval_seconds,
            interlocking_groups=interlocking_groups,
        )

        result = solve_schedule(solver_input)

        # 7. Delete all existing services
        await self._service_repo.delete_all()

        # 8. Create services from solver output (absolute departure times)
        yard = next(s for s in stations if s.is_yard)
        services: list[Service] = []
        for assignment in result.assignments:
            variant = variants[assignment.variant_index]
            vehicle = used_vehicles[assignment.vehicle_index]

            dwell_by_stop = {sid: req.dwell_time_seconds for sid in variant.stop_ids}
            dwell_by_stop[yard.id] = 0

            route, timetable = build_full_route(
                variant.stop_ids,
                dwell_by_stop,
                assignment.depart_time,
                connections,
                stations,
                blocks,
            )

            trip_num = sum(
                1
                for a in result.assignments
                if a.vehicle_index == assignment.vehicle_index
                and a.depart_time <= assignment.depart_time
            )
            service = Service(
                name=f"Auto-V{assignment.vehicle_index + 1}-T{trip_num}",
                vehicle_id=vehicle.id,
                route=route,
                timetable=timetable,
            )
            created = await self._service_repo.create(service)
            services.append(created)

        # 9. Sanity check: run conflict detection on all generated services
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
            conflict_details = []
            if block_conflicts:
                conflict_details.append(f"{len(block_conflicts)} block conflicts")
            if interlocking_conflicts:
                conflict_details.append(
                    f"{len(interlocking_conflicts)} interlocking conflicts"
                )
            if vehicle_conflicts:
                conflict_details.append(f"{len(vehicle_conflicts)} vehicle conflicts")
            raise RuntimeError(
                f"BUG: Generated schedule has conflicts: {', '.join(conflict_details)}"
            )

        # 10. Station frequency assertion
        platform_to_station = {p.id: s.name for s in stations for p in s.platforms}
        arrivals_by_station: dict[str, list[int]] = defaultdict(list)
        for svc in services:
            for entry in svc.timetable:
                sname = platform_to_station.get(entry.node_id)
                if sname:
                    arrivals_by_station[sname].append(entry.arrival)
        for sname, times in arrivals_by_station.items():
            times.sort()
            for i in range(len(times) - 1):
                gap = times[i + 1] - times[i]
                if gap > req.interval_seconds:
                    import logging

                    logging.getLogger(__name__).warning(
                        "Station %s: gap %ds > interval %ds (at t=%d)",
                        sname,
                        gap,
                        req.interval_seconds,
                        times[i],
                    )

        # 11. Return response
        return GenerateScheduleResponse(
            services_created=len(services),
            vehicles_used=[v.id for v in used_vehicles],
            cycle_time_seconds=max(cycle_times),
        )
```

- [ ] **Step 2: Update imports**

At the top of `schedule_service.py`:
- Add `from collections import defaultdict`
- Remove the `SCHEDULE_INFEASIBLE` error code usage — the greedy solver never returns None. The `ErrorCode.SCHEDULE_INFEASIBLE` enum value can stay in `domain/error.py` (it's also used by the error handler mapping).

- [ ] **Step 3: Run schedule service tests**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_schedule_service.py -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add application/schedule/schedule_service.py
git commit -m "refactor: simplify schedule service to use greedy solver output directly"
```

---

### Task 4: Run full test suite and remove ortools

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Run all tests**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest -v 2>&1 | tail -30`
Expected: all PASS

- [ ] **Step 2: Run architecture lint**

Run: `cd /home/feidon/Documents/vss/backend && uv run lint-imports`
Expected: PASS

- [ ] **Step 3: Remove ortools from pyproject.toml**

Remove the line `"ortools>=9.15.6755",` from the `dependencies` list in `pyproject.toml`.

- [ ] **Step 4: Sync dependencies**

Run: `cd /home/feidon/Documents/vss/backend && uv sync`
Expected: completes without error

- [ ] **Step 5: Run all tests again (without ortools)**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest -v 2>&1 | tail -30`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: remove ortools dependency (replaced by greedy solver)"
```

---

### Task 5: Verify with the failing curl request

- [ ] **Step 1: Start the server and test the previously-failing request**

Run: `cd /home/feidon/Documents/vss/backend && uv run uvicorn main:app --reload`

Then in another terminal:
```bash
curl 'http://localhost/api/schedules/generate' \
  -H 'Content-Type: application/json' \
  --data-raw '{"interval_seconds":120,"start_time":1775399040,"end_time":1775402700,"dwell_time_seconds":15}'
```

Expected: HTTP 200 with `services_created > 0` (previously returned 409)

- [ ] **Step 2: Verify the 5-minute interval case still works**

```bash
curl 'http://localhost/api/schedules/generate' \
  -H 'Content-Type: application/json' \
  --data-raw '{"interval_seconds":300,"start_time":1775376000,"end_time":1775412000,"dwell_time_seconds":15}'
```

Expected: HTTP 200 with services for the 10-hour range
