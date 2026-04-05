# Auto-Generate Schedule — Design Spec

## Overview

Automatic schedule generation using Google OR-Tools CP-SAT solver. Given a departure interval, time range, and dwell time, the system generates a full set of conflict-free services across available vehicles.

## API

### `POST /api/schedules/generate`

**Request:**

```json
{
  "interval_seconds": 300,
  "start_time": "2026-04-05T08:00:00Z",
  "end_time": "2026-04-05T18:00:00Z",
  "dwell_time_seconds": 30
}
```

**Success response (200):**

```json
{
  "services_created": 42,
  "vehicles_used": ["<vehicle_id>", "..."],
  "cycle_time_seconds": 450
}
```

**Error responses:**

| Status | Condition |
|--------|-----------|
| 422 | Invalid input (interval <= 0, dwell <= 0, start >= end), or not enough vehicles |
| 409 | Solver finds no feasible schedule |
| 500 | Post-validation conflict (bug in CP-SAT model) or solver timeout |

**Behavior:** Deletes all existing services first (clean slate), then generates and persists the new schedule.

## Pre-computation Phase

### Step 1 — Enumerate route variants

The track network has 3 binary platform choices per trip:

| Choice | Options | Affects blocks |
|--------|---------|----------------|
| S1 outbound | P1A or P1B | B1/B2 (departure), B3/B4 |
| S3 | P3A or P3B | B7/B8 (outbound), B9/B10 (return) |
| S1 return | P1A or P1B | B13/B14, B1/B2 (return) |

S2 is fixed: outbound always passes P2A, return always passes P2B.

3 choices x 2 options = **8 route variants**. For each variant `v`:

1. Determine the full node path (block + platform sequence)
2. Load current `block.traversal_time_seconds` from DB for each block
3. Compute timing offset table: `block_id -> (enter_offset, exit_offset)` relative to trip `depart_time`. "Enter" = when the vehicle arrives at the block; "exit" = when it departs (enter + traversal_time).
4. Compute platform arrival offsets for frequency constraints (per station)
5. Compute `num_blocks[v]` = exact block count in this variant's path
6. Compute `cycle_time[v]` = sum of all block traversals + all platform dwells

### Step 2 — Vehicle count

Use worst-case values across all 8 variants for a conservative estimate:

```
max_cycle = max(cycle_time[v] for all 8 variants)
max_blocks = max(num_blocks[v] for all 8 variants)
worst_yard_dwell = max_blocks * 12  seconds  (recharge 1% per 12s for each block traversed)
effective_cycle = max_cycle + worst_yard_dwell
num_vehicles = ceil(effective_cycle / interval_seconds) + 1
```

The `+ 1` is a tolerance buffer: the solver needs slack to find feasible platform assignments and stagger departures. Without it, the solver may be over-constrained at the boundary.

If `num_vehicles > len(available_vehicles)`: return 422 error immediately ("Need N vehicles but only M available").

### Step 3 — Trip count

This is a planning estimate for pre-allocating decision variables, not a hard constraint — the solver determines actual departure times.

```
interval_per_vehicle = num_vehicles * interval_seconds
trips_per_vehicle = floor((end_time - start_time) / interval_per_vehicle)
total_trips = num_vehicles * trips_per_vehicle
```

### Step 4 — Yard dwell / battery

Between consecutive trips of the same vehicle, the vehicle must recharge to 80% (the departure threshold from `Vehicle.can_depart()`). Per-variant computation:

```
battery_after_loop[v] = 80 - num_blocks[v]    (1% drain per block, departs at 80%)
charge_needed[v] = 80 - battery_after_loop[v]  = num_blocks[v]
min_yard_dwell[v] = charge_needed[v] * 12      seconds (Vehicle.charge(): +1% per 12s)
```

Note: `Vehicle.charge()` caps at 100, but we only need to reach the 80% departure threshold. Since battery after a loop is `80 - num_blocks[v]` (e.g., 70% for 10 blocks), we need `num_blocks[v]` percentage points back = `num_blocks[v] * 12` seconds.

## CP-SAT Model

### Decision variables

For each trip `s`:

| Variable | Type | Description |
|----------|------|-------------|
| `depart_time[s]` | IntVar | Departure from yard (epoch seconds) |
| `s1_out[s]` | BoolVar | 0=P1A, 1=P1B |
| `s3[s]` | BoolVar | 0=P3A, 1=P3B |
| `s1_ret[s]` | BoolVar | 0=P1A, 1=P1B |

### Derived values

For each trip, the route variant index is determined by the 3 booleans (0-7). From the pre-computed timing offset table, all block occupancy intervals and platform arrival times are fixed functions of `depart_time[s]` + the variant's offset constants.

To encode variant-dependent derived values in CP-SAT, use auxiliary integer variables with `AddElement`:

```python
# Pre-computed cycle times for each of the 8 variants
cycle_times = [cycle_time[v] for v in range(8)]

# variant_index[s] is an IntVar derived from the 3 booleans:
# variant_index = s1_out * 4 + s3 * 2 + s1_ret
# (encode via AddMultiplicationEquality / linear expression)

# cycle_time_of_trip[s] is an IntVar looked up from the table:
model.AddElement(variant_index[s], cycle_times, cycle_time_of_trip[s])
```

The same `AddElement` pattern applies to `min_yard_dwell` and `num_blocks` per trip.

### Constraints

**C1 — Block occupancy** (mirrors `conflict/block.py`):

For every pair of trips `(s1, s2)` and every block `b`: if both trips use `b` (determined by platform-choice combinations), their occupancy intervals must not overlap.

```
depart_time[s1] + exit_offset[v1, b] <= depart_time[s2] + enter_offset[v2, b]
OR
depart_time[s2] + exit_offset[v2, b] <= depart_time[s1] + enter_offset[v1, b]
```

Where `enter_offset[v, b]` = time the vehicle enters block `b` relative to trip start (for variant `v`), and `exit_offset[v, b]` = time it departs the block (= enter + traversal_time).

Encoding: for each block `b`, enumerate which variant pairs `(v1, v2)` both include `b`. For each such pair, create an auxiliary `BoolVar` representing "s1 is variant v1 AND s2 is variant v2", enforce the no-overlap disjunction `OnlyEnforceIf` that auxiliary.

**C2 — Interlocking** (mirrors `conflict/interlocking.py`):

For every pair of trips `(s1, s2)` and every pair of blocks `(b1, b2)` in the same interlocking group where `b1 != b2`: if s1 uses b1 AND s2 uses b2, their occupancy intervals must not overlap.

Encoding: for each interlocking group, enumerate all (block, variant) pairs that include a block in the group. For each cross-trip combination where s1's variant includes b1 and s2's variant includes b2 (b1 != b2, same group), add the no-overlap disjunction conditioned on both variant indicators.

Example: B7 is used when `s3=0` (P3A), B8 when `s3=1` (P3B). For trips s1 and s2, the interlocking constraint between B7(s1) and B8(s2) is enforced `OnlyEnforceIf(s3[s1].Not(), s3[s2])`.

Interlocking groups:
- Group 1: B1, B2
- Group 2: B3, B4, B13, B14
- Group 3: B7, B8, B9, B10

**C3 — Vehicle continuity:**

Trips are pre-assigned to vehicles. For consecutive trips `(s_prev, s_next)` of the same vehicle:

```
depart_time[s_next] >= depart_time[s_prev] + cycle_time_of_trip[s_prev] + yard_dwell_of_trip[s_prev]
```

Where `cycle_time_of_trip[s]` and `yard_dwell_of_trip[s]` are IntVars derived from the variant index via `AddElement` (see "Derived values" above).

This constraint also implicitly prevents vehicle time-overlap conflicts (mirrors `conflict/vehicle.py`): if a vehicle's next trip starts after the previous trip ends + yard dwell, the time windows cannot overlap. Location discontinuity is automatically satisfied since all trips start and end at the yard.

**C4 — Battery** (mirrors `conflict/battery.py`):

Battery per trip: starts at 80% (guaranteed by C3's yard dwell), drains 1% per block. The critical threshold is 30%.

For this network, all 8 variants have exactly 10 blocks, so battery drains to 70% — well above the 30% threshold. As a safety bound:

```
num_blocks_of_trip[s] <= 50   (80% - 30% = 50 blocks max before critical)
```

This is always satisfied for the current network but guards against future topology changes.

**C5 — Station frequency** (passenger wait constraint):

Applies to passenger stations only: **S1, S2, S3** (not the yard).

For each station, collect all arrival times across all trips and all platforms of that station. Arrival times are variant-dependent derived values:

```python
# For station S1: arrivals happen at P1A (outbound or return) and P1B (outbound or return)
# arrival_at_S1[s] depends on variant — use AddElement to look up the offset
arrival_time[s, station] = depart_time[s] + arrival_offset_of_variant[variant_index[s], station]
```

Note: each trip visits each station twice (outbound and return), on potentially different platforms. Both arrivals count toward the station's frequency.

To enforce max gap <= interval on sorted arrivals in CP-SAT:
1. Collect all arrival IntVars for a station (2 per trip — outbound and return)
2. Create pairwise ordering BoolVars: `before[i,j]` = 1 if arrival i <= arrival j
3. For each pair (i, j): if `before[i,j]` and no arrival k falls between them (i.e., they are consecutive), then `arrival[j] - arrival[i] <= interval_seconds`

Alternative (simpler): since we expect roughly uniform spacing, add the constraint for ALL pairs, not just consecutive:
```
For all i != j: arrival[j] - arrival[i] > interval_seconds => there exists k with arrival[i] < arrival[k] < arrival[j]
```

In practice, use CP-SAT's circuit constraint or sort the arrivals via a permutation variable and constrain consecutive elements of the sorted order.

**C6 — Time range:**

```
depart_time[s] >= start_time
depart_time[s] + max_cycle_time <= end_time
```

Where `max_cycle_time` = worst-case across all 8 variants (conservative bound to avoid variant-conditional encoding for the upper bound).

### Objective

Primary: feasibility (constraint satisfaction only).
Optional secondary: minimize maximum gap across all stations for the most evenly-spaced schedule.

## Post-processing

1. Extract `depart_time[s]` and platform choices from solver solution
2. For each trip, determine the route variant -> get full node path and timetable
3. Build `Service` objects using existing `build_full_route()` (route + timetable)
4. Name services with convention: `"Auto-V{vehicle_index}-T{trip_index}"` (e.g., "Auto-V1-T3")
5. Services are created with `id=None` — the repository assigns IDs on persist
6. Assign vehicle from pool by index
7. Sanity check: run all services through `ConflictDetectionService` using the batch approach — call `detect_block_conflicts()`, `detect_interlocking_conflicts()`, and `detect_vehicle_conflicts()` once on the full service list rather than per-service. Any conflict = bug in CP-SAT model -> 500 error.
8. Persist all services via `ServiceRepository.create()` in a single transaction

## Architecture

All auto-scheduling code lives in the application layer. The domain layer has no awareness of CP-SAT.

```
application/
  schedule/
    schedule_service.py      # Orchestrates: load data, solve, build services, persist
    solver.py                # CP-SAT model (only file importing ortools)
    route_variant.py         # Pre-computation of 8 route variants + timing offsets
    model.py                 # SolverInput, SolverOutput, RouteVariant dataclasses
    dto.py                   # GenerateScheduleRequest/Response DTOs

api/
  schedule/
    route.py                 # POST /api/schedules/generate endpoint
    schema.py                # Pydantic request/response schemas
```

- `solver.py`: Only file that imports `ortools`. Takes `SolverInput` (plain dataclasses), returns `SolverOutput` (departure times + platform choices per trip).
- `route_variant.py`: Pure Python. Uses domain entities (Block, NodeConnection) to pre-compute timing tables.
- `schedule_service.py`: Orchestrates everything. Calls domain services (`RouteFinder`, `ConflictDetectionService`, `build_full_route`) for post-processing and validation.

Dependency flow: `api -> application -> domain <- infra` (unchanged).

### Repository changes

Add `delete_all()` to `ServiceRepository` interface and PostgreSQL implementation. This replaces the current pattern of loading all + deleting one-by-one.

## Error Handling

**Pre-solver (fail fast):**
- Invalid input (interval <= 0, dwell <= 0, start >= end) -> 422
- Not enough vehicles -> 422 ("Need N vehicles but only M available")

**Solver:**
- INFEASIBLE -> 409 "Cannot generate a conflict-free schedule with the given parameters"
- Timeout (30s default, configurable) -> 500

**Post-validation:**
- ConflictDetectionService finds conflicts -> 500 internal error (CP-SAT model bug)

**Atomicity:** Delete existing services + create new ones in a single transaction.

## Testing

**Unit tests (no I/O, no solver):**
- `route_variant.py`: Verify all 8 variants produce correct block sequences, timing offsets, and cycle times given known block traversal times
- Verify with non-uniform traversal times (e.g., B5=60s, B6=45s)

**Application tests (with solver, in-memory repos):**
- Feasible case: verify solver output, all services conflict-free via ConflictDetectionService
- Infeasible case: interval too tight, verify 409 error
- Not enough vehicles: verify pre-solver 422 rejection
- Variable traversal times: non-uniform blocks, verify cycle time and solver adaptation
- Frequency: verify max gap at every station (S1, S2, S3) <= interval
- Battery: verify yard dwell between trips is sufficient for recharging to 80%
- Clean slate: verify existing services are deleted before generation

**API tests (PostgreSQL, `@pytest.mark.postgres`):**
- POST returns correct response shape
- Existing services deleted before generation
- Generated services persisted and retrievable via GET /api/services
