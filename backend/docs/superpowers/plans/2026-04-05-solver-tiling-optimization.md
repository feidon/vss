# Solver Tiling Optimization Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce schedule auto-generation time by solving one cycle (num_vehicles trips) with wraparound constraints, then tiling across the time range.

**Architecture:** The CP-SAT solver currently solves all trips at once (num_vehicles * trips_per_vehicle). This changes to: (1) solve a single cycle of num_vehicles trips with ghost intervals for wraparound safety, (2) tile the solution across [start_time, end_time] with a fixed tile_period, (3) trim trips that overflow. Vehicle continuity is guaranteed by tile_period >= max(cycle + yard_dwell).

**Tech Stack:** Python 3.14, OR-Tools CP-SAT, pytest

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `application/schedule/model.py:42-55` | Replace `trips_per_vehicle`, `start_time`, `end_time` with `tile_period` in `SolverInput` |
| Modify | `application/schedule/solver.py` (full rewrite) | Single-cycle solver with ghost intervals for wraparound |
| Modify | `application/schedule/schedule_service.py:60-96,108-134` | Compute tile_period, tile solver output, trim |
| Modify | `tests/application/schedule/test_solver.py` | Adapt to single-cycle output, add wraparound tests |
| Modify | `tests/application/schedule/test_schedule_service.py` | Existing tests should still pass (behavior preserved) |

---

### Task 1: Update `SolverInput` model

**Files:**
- Modify: `application/schedule/model.py:42-55`

The solver no longer needs `start_time`, `end_time`, or `trips_per_vehicle`. It works with 0-based offsets within one tile period.

- [ ] **Step 1: Update SolverInput dataclass**

Replace the three removed fields with `tile_period`:

```python
@dataclass(frozen=True)
class SolverInput:
    """Everything the CP-SAT solver needs - no domain objects."""

    variants: list[RouteVariant]
    num_vehicles: int
    vehicle_ids: list[UUID]
    tile_period: int  # seconds; max(cycle_time + yard_dwell) across variants
    interval_seconds: int
    min_yard_dwells: list[int]  # per variant index
    cycle_times: list[int]  # per variant index
    interlocking_groups: dict[int, list[UUID]]  # group_id -> block_ids
```

- [ ] **Step 2: Verify no import breakage**

Run: `cd /home/feidon/Documents/vss/backend && uv run python -c "from application.schedule.model import SolverInput; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add application/schedule/model.py
git commit -m "refactor: replace trips_per_vehicle with tile_period in SolverInput"
```

---

### Task 2: Rewrite solver for single-cycle with wraparound

**Files:**
- Modify: `application/schedule/solver.py` (full file)

Key changes from the current solver:
- `total_trips = inp.num_vehicles` (one trip per vehicle)
- Departure domain: `[0, tile_period - 1]` (0-based offsets)
- **C1/C2**: Add ghost intervals shifted by `+tile_period` into every `NoOverlap` constraint
- **C3**: Remove entirely (1 trip per vehicle, continuity guaranteed by tile_period)
- **C5**: Add one linear wraparound constraint instead of ghost arrivals

- [ ] **Step 1: Write failing test for single-cycle output**

Add to `tests/application/schedule/test_solver.py`:

```python
def _build_cycle_input(
    interval: int = 360,
    num_vehicles: int = 2,
    dwell: int = 30,
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

    cycle_times = [v.cycle_time for v in variants]
    min_yard_dwells = [v.num_blocks * 12 for v in variants]
    tile_period = max(c + y for c, y in zip(cycle_times, min_yard_dwells))

    return SolverInput(
        variants=variants,
        num_vehicles=num_vehicles,
        vehicle_ids=list(VEHICLE_ID_BY_NAME.values())[:num_vehicles],
        tile_period=tile_period,
        interval_seconds=interval,
        min_yard_dwells=min_yard_dwells,
        cycle_times=cycle_times,
        interlocking_groups=interlocking_groups,
    )


class TestSolveCycle:
    def test_returns_one_assignment_per_vehicle(self):
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        assert len(result.assignments) == inp.num_vehicles

    def test_departures_within_tile_period(self):
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        for a in result.assignments:
            assert 0 <= a.depart_time < inp.tile_period

    def test_variant_indices_valid(self):
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None
        for a in result.assignments:
            assert 0 <= a.variant_index < 8
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_solver.py::TestSolveCycle -v`
Expected: FAIL (SolverInput constructor mismatch or wrong assignment count)

- [ ] **Step 3: Rewrite solver.py**

Replace the entire `solve_schedule` function:

```python
def solve_schedule(
    inp: SolverInput,
    *,
    timeout_seconds: int = 60,
) -> SolverOutput | None:
    """Solve one cycle of the vehicle scheduling problem using CP-SAT.

    Produces exactly num_vehicles trip assignments (one per vehicle).
    Departures are 0-based offsets within [0, tile_period).
    Ghost intervals shifted by +tile_period enforce wraparound safety
    so the solution can be tiled without conflicts.

    Constraints:
        C1 - Block occupancy (no overlap on same block, incl. wraparound ghosts)
        C2 - Interlocking (no overlap in same group, incl. wraparound ghosts)
        C5 - Station frequency (consecutive arrivals within interval + wraparound)
        C6 - Departures within [0, tile_period)
    """
    model = cp_model.CpModel()
    num_trips = inp.num_vehicles
    P = inp.tile_period

    # -- Decision variables --------------------------------------------------

    depart: list[cp_model.IntVar] = []
    variant_idx: list[cp_model.IntVar] = []
    is_variant: list[list[cp_model.IntVar]] = []

    for s in range(num_trips):
        d = model.new_int_var(0, P - 1, f"depart_{s}")
        depart.append(d)

        b_s1_out = model.new_bool_var(f"s1_out_{s}")
        b_s3 = model.new_bool_var(f"s3_{s}")
        b_s1_ret = model.new_bool_var(f"s1_ret_{s}")

        vi = model.new_int_var(0, 7, f"variant_{s}")
        model.add(vi == b_s1_out * 4 + b_s3 * 2 + b_s1_ret)
        variant_idx.append(vi)

        bools = [model.new_bool_var(f"is_v{v}_t{s}") for v in range(8)]
        for v in range(8):
            model.add(vi == v).only_enforce_if(bools[v])
            model.add(vi != v).only_enforce_if(~bools[v])
        is_variant.append(bools)

    # -- Block-to-variant timing lookup --------------------------------------

    block_occurrences: dict[UUID, list[tuple[int, int, int]]] = defaultdict(list)
    for var in inp.variants:
        for bt in var.block_timings:
            block_occurrences[bt.block_id].append(
                (var.index, bt.enter_offset, bt.exit_offset)
            )

    group_block_set: set[UUID] = set()
    for gblocks in inp.interlocking_groups.values():
        group_block_set.update(gblocks)

    # -- Interval helpers ----------------------------------------------------

    def _make_interval(
        s: int, var_i: int, enter_off: int, exit_off: int,
        prefix: str, shift: int = 0,
    ) -> cp_model.IntervalVar:
        """Create optional interval at depart[s] + shift + enter_off."""
        lit = is_variant[s][var_i]
        duration = exit_off - enter_off
        lo = shift + enter_off
        hi = P - 1 + shift + enter_off
        start = model.new_int_var(lo, hi, f"{prefix}_st_t{s}_v{var_i}")
        model.add(start == depart[s] + shift + enter_off).only_enforce_if(lit)
        return model.new_optional_fixed_size_interval_var(
            start, duration, lit, f"{prefix}_iv_t{s}_v{var_i}"
        )

    def _block_intervals(
        bid: UUID, occs: list[tuple[int, int, int]], prefix: str,
    ) -> list[cp_model.IntervalVar]:
        """Real + ghost intervals for one block across all trips."""
        intervals: list[cp_model.IntervalVar] = []
        for s in range(num_trips):
            for var_i, enter_off, exit_off in occs:
                intervals.append(
                    _make_interval(s, var_i, enter_off, exit_off, prefix)
                )
                intervals.append(
                    _make_interval(s, var_i, enter_off, exit_off,
                                   f"g_{prefix}", shift=P)
                )
        return intervals

    # -- C1: Block occupancy (non-interlocking) + wraparound -----------------

    for bid, occs in block_occurrences.items():
        if bid in group_block_set:
            continue
        intervals = _block_intervals(bid, occs, f"b_{bid}")
        if len(intervals) > 1:
            model.add_no_overlap(intervals)

    # -- C2: Interlocking groups + wraparound --------------------------------

    for group_id, group_block_ids in inp.interlocking_groups.items():
        group_intervals: list[cp_model.IntervalVar] = []
        for bid in group_block_ids:
            occs = block_occurrences.get(bid, [])
            group_intervals.extend(
                _block_intervals(bid, occs, f"g{group_id}_{bid}")
            )
        if len(group_intervals) > 1:
            model.add_no_overlap(group_intervals)

    # -- C5: Station frequency + wraparound ----------------------------------

    station_names = ["S1", "S2", "S3"]
    for sname in station_names:
        visits_per_variant: list[list[int]] = []
        for var in inp.variants:
            hits = [sa for sa in var.station_arrivals if sa.station_name == sname]
            visits_per_variant.append([h.arrival_offset for h in hits])

        num_visits = len(visits_per_variant[0])
        time_horizon = 2 * P + max(
            off for offsets in visits_per_variant for off in offsets
        )

        arrivals: list[cp_model.IntVar] = []
        for visit_idx in range(num_visits):
            offsets = [visits_per_variant[v][visit_idx] for v in range(8)]
            for s in range(num_trips):
                off_var = model.new_int_var(
                    min(offsets), max(offsets),
                    f"off_{sname}_v{visit_idx}_t{s}",
                )
                model.add_element(variant_idx[s], offsets, off_var)
                arr = model.new_int_var(
                    0, time_horizon, f"arr_{sname}_v{visit_idx}_t{s}",
                )
                model.add(arr == depart[s] + off_var)
                arrivals.append(arr)

        n = len(arrivals)
        if n <= 1:
            continue

        sorted_arr = [
            model.new_int_var(0, time_horizon, f"sorted_{sname}_{k}")
            for k in range(n)
        ]
        pos = [model.new_int_var(0, n - 1, f"pos_{sname}_{i}") for i in range(n)]
        model.add_all_different(pos)

        for i in range(n):
            model.add_element(pos[i], sorted_arr, arrivals[i])

        for k in range(n - 1):
            model.add(sorted_arr[k] <= sorted_arr[k + 1])
            model.add(sorted_arr[k + 1] - sorted_arr[k] <= inp.interval_seconds)

        # Wraparound: gap from last arrival to first arrival of next tile
        # (first_of_next_tile) - last_of_this_tile <= interval
        # (sorted_arr[0] + P) - sorted_arr[n-1] <= interval
        model.add(
            sorted_arr[0] + P - sorted_arr[n - 1] <= inp.interval_seconds
        )

    # -- Solve ---------------------------------------------------------------

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_seconds
    solver.parameters.num_workers = 8

    status = solver.solve(model)

    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return None

    assignments: list[TripAssignment] = []
    for s in range(num_trips):
        assignments.append(
            TripAssignment(
                vehicle_index=s,
                trip_index=0,
                depart_time=solver.value(depart[s]),
                variant_index=solver.value(variant_idx[s]),
            )
        )

    return SolverOutput(assignments=assignments)
```

- [ ] **Step 4: Run the new tests**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_solver.py::TestSolveCycle -v`
Expected: all 3 PASS

- [ ] **Step 5: Write wraparound correctness tests**

Add to `TestSolveCycle`:

```python
    def test_block_no_overlap_across_tiles(self):
        """Simulate 3 tiles; verify no block overlaps."""
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None

        from collections import defaultdict
        block_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for tile in range(3):
            for a in result.assignments:
                var = inp.variants[a.variant_index]
                for bt in var.block_timings:
                    enter = tile * inp.tile_period + a.depart_time + bt.enter_offset
                    exit_ = tile * inp.tile_period + a.depart_time + bt.exit_offset
                    block_intervals[bt.block_id].append((enter, exit_))

        for bid, intervals in block_intervals.items():
            intervals.sort()
            for i in range(len(intervals) - 1):
                assert intervals[i][1] <= intervals[i + 1][0], (
                    f"Block {bid} overlap: {intervals[i]} and {intervals[i + 1]}"
                )

    def test_station_frequency_across_tiles(self):
        """Simulate 3 tiles; verify all station gaps <= interval."""
        inp = _build_cycle_input(interval=360, num_vehicles=2)
        result = solve_schedule(inp, timeout_seconds=30)
        assert result is not None

        for sname in ["S1", "S2", "S3"]:
            arrivals = []
            for tile in range(3):
                for a in result.assignments:
                    var = inp.variants[a.variant_index]
                    for sa in var.station_arrivals:
                        if sa.station_name == sname:
                            arrivals.append(
                                tile * inp.tile_period + a.depart_time + sa.arrival_offset
                            )
            arrivals.sort()
            for i in range(len(arrivals) - 1):
                gap = arrivals[i + 1] - arrivals[i]
                assert gap <= inp.interval_seconds, (
                    f"{sname} gap {gap} > {inp.interval_seconds} "
                    f"between {arrivals[i]} and {arrivals[i + 1]}"
                )

    def test_infeasible_returns_none(self):
        inp = _build_cycle_input(interval=10, num_vehicles=3)
        result = solve_schedule(inp, timeout_seconds=5)
        assert result is None
```

- [ ] **Step 6: Run all solver tests**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_solver.py -v`
Expected: all PASS

- [ ] **Step 7: Delete old TestSolveSchedule class and _build_solver_input helper**

The old `_build_solver_input` constructs a `SolverInput` with `trips_per_vehicle`, `start_time`, `end_time` which no longer exist. Remove the entire `_build_solver_input` function and `TestSolveSchedule` class.

- [ ] **Step 8: Run solver tests again to confirm clean**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_solver.py -v`
Expected: all PASS (only `TestSolveCycle` tests remain)

- [ ] **Step 9: Commit**

```bash
git add application/schedule/solver.py tests/application/schedule/test_solver.py
git commit -m "feat: rewrite solver for single-cycle with wraparound ghost constraints"
```

---

### Task 3: Update schedule service with tiling logic

**Files:**
- Modify: `application/schedule/schedule_service.py:60-134`

The service now: (1) computes tile_period, (2) calls solver for one cycle, (3) tiles assignments across [start_time, end_time], (4) trims, (5) builds services.

- [ ] **Step 1: Write failing test for tiling behavior**

Add to `tests/application/schedule/test_schedule_service.py`:

```python
    async def test_tiling_produces_multiple_trips_per_vehicle(self):
        """With a 2-hour window, each vehicle should serve multiple trips."""
        app, service_repo = _make_app()
        req = GenerateScheduleRequest(
            interval_seconds=360,
            start_time=0,
            end_time=7200,
            dwell_time_seconds=30,
        )
        result = await app.generate_schedule(req)
        services = await service_repo.find_all()

        by_vehicle: dict[str, list] = {}
        for svc in services:
            by_vehicle.setdefault(str(svc.vehicle_id), []).append(svc)

        for vid, trips in by_vehicle.items():
            assert len(trips) > 1, f"Vehicle {vid} has only {len(trips)} trip(s)"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_schedule_service.py::TestScheduleAppService::test_tiling_produces_multiple_trips_per_vehicle -v`
Expected: FAIL (SolverInput constructor mismatch)

- [ ] **Step 3: Rewrite generate_schedule method**

Replace `schedule_service.py` steps 4-9 with tiling logic:

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

        # 4. Compute tile_period and num_vehicles
        cycle_times = [v.cycle_time for v in variants]
        min_yard_dwells = [v.num_blocks * 12 for v in variants]
        tile_period = max(c + y for c, y in zip(cycle_times, min_yard_dwells))
        num_vehicles = math.ceil(tile_period / req.interval_seconds) + 1

        if num_vehicles > len(vehicles):
            await self._vehicle_repo.add_by_number(num_vehicles - len(vehicles))
            vehicles = await self._vehicle_repo.find_all()

        used_vehicles = vehicles[:num_vehicles]

        # 5. Build interlocking groups
        interlocking_groups: dict[int, list] = {}
        for b in blocks:
            if b.group != 0:
                interlocking_groups.setdefault(b.group, []).append(b.id)

        # 6. Solve one cycle
        solver_input = SolverInput(
            variants=variants,
            num_vehicles=num_vehicles,
            vehicle_ids=[v.id for v in used_vehicles],
            tile_period=tile_period,
            interval_seconds=req.interval_seconds,
            min_yard_dwells=min_yard_dwells,
            cycle_times=cycle_times,
            interlocking_groups=interlocking_groups,
        )

        result = solve_schedule(solver_input)

        if result is None:
            raise DomainError(
                ErrorCode.SCHEDULE_INFEASIBLE,
                "Schedule is infeasible: solver could not find a valid assignment",
            )

        # 7. Delete all existing services
        await self._service_repo.delete_all()

        # 8. Tile across [start_time, end_time], only emit complete tiles
        #    A tile is "complete" when every trip finishes before end_time.
        #    Partial tiles would break the station frequency guarantee.
        max_cycle = max(cycle_times)
        cycle_end = max(
            a.depart_time + variants[a.variant_index].cycle_time
            for a in result.assignments
        )
        yard = next(s for s in stations if s.is_yard)
        services: list[Service] = []
        tile = 0
        while True:
            tile_start = req.start_time + tile * tile_period
            if tile_start + cycle_end > req.end_time:
                break
            for assignment in result.assignments:
                depart_abs = tile_start + assignment.depart_time
                variant = variants[assignment.variant_index]
                vehicle = used_vehicles[assignment.vehicle_index]

                dwell_by_stop = {sid: req.dwell_time_seconds for sid in variant.stop_ids}
                dwell_by_stop[yard.id] = 0

                route, timetable = build_full_route(
                    variant.stop_ids,
                    dwell_by_stop,
                    depart_abs,
                    connections,
                    stations,
                    blocks,
                )

                service = Service(
                    name=f"Auto-V{assignment.vehicle_index + 1}-T{tile + 1}",
                    vehicle_id=vehicle.id,
                    route=route,
                    timetable=timetable,
                )
                created = await self._service_repo.create(service)
                services.append(created)
            tile += 1

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

        # 10. Return response
        return GenerateScheduleResponse(
            services_created=len(services),
            vehicles_used=[v.id for v in used_vehicles],
            cycle_time_seconds=max_cycle,
        )
```

- [ ] **Step 4: Run the new test**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_schedule_service.py::TestScheduleAppService::test_tiling_produces_multiple_trips_per_vehicle -v`
Expected: PASS

- [ ] **Step 5: Run ALL schedule service tests**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest tests/application/schedule/test_schedule_service.py -v`
Expected: all PASS (existing behavior preserved by tiling)

- [ ] **Step 6: Commit**

```bash
git add application/schedule/schedule_service.py tests/application/schedule/test_schedule_service.py
git commit -m "feat: tile single-cycle solver output across time range"
```

---

### Task 4: Run full test suite and fix any breakage

**Files:**
- Possibly modify: any file with stale `SolverInput` usage

- [ ] **Step 1: Run all tests**

Run: `cd /home/feidon/Documents/vss/backend && uv run pytest -v`
Expected: all PASS

- [ ] **Step 2: Run architecture lint**

Run: `cd /home/feidon/Documents/vss/backend && uv run lint-imports`
Expected: PASS (no new cross-layer imports)

- [ ] **Step 3: Fix any failures**

If any test fails, diagnose from the error message. Likely causes:
- Stale references to `trips_per_vehicle` or old `SolverInput` fields
- Timing edge cases in tiling boundary

- [ ] **Step 4: Commit fixes if any**

```bash
git add -u
git commit -m "fix: resolve test breakage from solver tiling refactor"
```

---

## Design Decisions

1. **tile_period is a precomputed constant** — `max(cycle_time[v] + yard_dwell[v])` per variant, not independent maxima. This is tighter than the old `max(cycle) + max(yard_dwell)` formula and more correct: it guarantees `tile_period >= cycle + yard_dwell` for every variant individually.

2. **Forward ghosts only** (+tile_period). Backward overlap is algebraically equivalent to forward overlap, so one direction suffices.

3. **Station frequency wraparound uses a single linear constraint** (`sorted[0] + P - sorted[n-1] <= interval`) instead of ghost arrivals. Fewer variables, same correctness.

4. **Each vehicle uses the same variant across all tiles.** More restrictive than the old solver (which could vary variants per trip), but produces regular schedules and drastically reduces solver complexity.

5. **Vehicle continuity has no explicit solver constraint.** It's guaranteed by `tile_period >= cycle + yard_dwell` for every variant. The post-solve sanity check in the service validates this.

6. **Only complete tiles are emitted.** The tiling loop breaks when any trip in a tile would overflow `end_time`. This preserves the station frequency invariant at all tile boundaries. The trade-off is up to `tile_period` seconds of unused time at the end of the range.
