# Greedy Schedule Solver

## Problem

The CP-SAT cyclic tiling solver fails for tight intervals. With interval=120s, the solver needs 6 vehicles in a 495s tile — the yard interlocking bottleneck (B1/B2, 30s traversal each, mutually exclusive) makes a repeating tile pattern infeasible. Since users control the interval, we need a solver that works for any reasonable input.

## Solution

Replace the CP-SAT solver with greedy sequential dispatch. Place one trip at a time in temporal order. For each trip, pick the first available vehicle and the first route variant that doesn't conflict with already-placed trips.

## Algorithm

```
occupancies = {}          # block_id -> sorted list of (enter, exit)
vehicle_available = {}    # vehicle_index -> earliest next departure time
assignments = []
min_cycle = min(variant.cycle_time for variant in variants)

next_desired = start_time
while next_desired + min_cycle <= end_time:
    vehicle = earliest available vehicle (tie-break: lowest index)
    depart = max(vehicle_available[vehicle], next_desired)

    for variant in variants (index order 0-7):
        if depart + variant.cycle_time > end_time:
            skip
        if no block/interlocking conflicts at (depart, variant):
            record block occupancies
            yard_dwell = variant.num_blocks * 12
            vehicle_available[vehicle] = depart + variant.cycle_time + yard_dwell
            save assignment
            next_desired = depart + interval
            break
    else:
        # No variant fits — jump to earliest conflicting occupancy end
        next_desired = earliest_conflict_end(depart, variants, occupancies)
        if next_desired is unchanged:
            break  # stuck, stop scheduling
```

### Conflict check

For a candidate (depart, variant), check each block timing:
- Compute absolute window: `[depart + enter_offset, depart + exit_offset]`
- Check overlap against all existing occupancies on the same block
- For blocks in an interlocking group: also check against occupancies on other blocks in the same group
- Any overlap -> reject this variant

### Why it works

- **Always produces a result**: trips are only placed when conflict-free. If the network is saturated, fewer trips are placed — returns empty schedule instead of error.
- **Battery/recharge**: built into `vehicle_available`. A vehicle can't depart until `last_depart + cycle_time + yard_dwell` (yard_dwell = num_blocks * 12s).
- **Fleet sizing**: `num_vehicles = ceil(max(cycle + yard_dwell) / interval) + 1`. The `+1` guarantees at least one vehicle is always idle at the yard.
- **Station max-gap**: the `+1` spare vehicle ensures a vehicle is always available before the interval expires. Post-validation asserts this holds; if a gap exceeds the interval (extreme edge case), the schedule is still returned — the gap is a physical limitation, not an algorithm bug.
- **Deterministic**: fixed vehicle tie-breaking (lowest index) and variant order (0-7) produce identical schedules for identical inputs.

## Changes

### `application/schedule/model.py`

Simplify `SolverInput` — replace `tile_period` with `start_time`/`end_time`, drop redundant `min_yard_dwells`/`cycle_times` lists (read from variants directly):

```python
@dataclass(frozen=True)
class SolverInput:
    variants: list[RouteVariant]
    num_vehicles: int
    vehicle_ids: list[UUID]
    start_time: int
    end_time: int
    interval_seconds: int
    interlocking_groups: dict[int, list[UUID]]
```

Remove `trip_index` from `TripAssignment` (vestigial — was always 0 in cyclic solver):

```python
@dataclass(frozen=True)
class TripAssignment:
    vehicle_index: int
    depart_time: int          # absolute epoch seconds
    variant_index: int
```

Return contract: `solve_schedule` returns `SolverOutput` always (possibly with empty `assignments`). Never returns `None`.

### `application/schedule/solver.py`

Full rewrite. Replace CP-SAT with pure Python greedy dispatch. No external dependencies.

### `application/schedule/schedule_service.py`

Simplify:
- Pass `start_time` and `end_time` to solver (instead of `tile_period`)
- Remove tiling loop — solver returns full schedule with absolute departure times
- Keep sanity check (conflict detection + station frequency assertion) — cheap and good defense-in-depth
- Keep: fleet sizing, variant computation, service creation from assignments

### Tests

- `test_solver.py`: rewrite for greedy behavior (no tile_period, no wraparound)
- `test_schedule_service.py`: existing tests should pass with minimal changes (same observable behavior)

### No changes

- `route_variant.py` — unchanged
- `dto.py`, `routes.py`, `schemas.py` — unchanged
- Domain conflict detection ��� still used for manual PATCH endpoint and sanity check

## Removed dependency

`ortools` (google OR-Tools CP-SAT) is no longer needed by the solver. Can be removed from `pyproject.toml` if nothing else uses it.
