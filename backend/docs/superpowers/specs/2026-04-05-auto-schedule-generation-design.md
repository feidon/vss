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
| 422 | Invalid input (interval <= 0, dwell <= 0, start >= end) |
| 409 | Not enough vehicles, or solver finds no feasible schedule |
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

3 choices x 2 options = **8 route variants**. For each variant:

1. Determine the full node path (block + platform sequence)
2. Load current `block.traversal_time_seconds` from DB for each block
3. Compute timing offset table: `block_id -> (arrival_offset, departure_offset)` relative to trip `depart_time`
4. Compute platform arrival offsets for frequency constraints
5. Compute total cycle time (sum of block traversals + platform dwells)

### Step 2 — Vehicle count

```
max_cycle = max(cycle_time for all 8 variants)
yard_dwell = min charging time to restore battery to 80%
effective_cycle = max_cycle + yard_dwell
num_vehicles = ceil(effective_cycle / interval_seconds) + 1
```

If `num_vehicles > len(available_vehicles)`: return 409 error immediately.

### Step 3 — Trip count

```
interval_per_vehicle = num_vehicles * interval_seconds
trips_per_vehicle = floor((end_time - start_time) / interval_per_vehicle)
total_trips = num_vehicles * trips_per_vehicle
```

### Step 4 — Yard dwell / battery

Between consecutive trips of the same vehicle:

```
battery_after_loop = 80 - num_blocks_in_route  (1% per block)
charge_needed = 80 - battery_after_loop
min_yard_dwell = charge_needed * 12  seconds  (Vehicle.charge(): +1% per 12s)
```

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

For each trip, the route variant is determined by the 3 booleans. From the pre-computed timing offset table, all block occupancy intervals and platform arrival times are fixed functions of `depart_time[s]`.

### Constraints

**C1 — Block occupancy** (mirrors `conflict/block.py`):

For every pair of trips `(s1, s2)` and every block `b`: if both trips use `b` (determined by platform-choice combinations), their occupancy intervals must not overlap.

```
depart_time[s1] + departure_offset[s1, b] <= depart_time[s2] + arrival_offset[s2, b]
OR
depart_time[s2] + departure_offset[s2, b] <= depart_time[s1] + arrival_offset[s1, b]
```

Enforced conditionally via `OnlyEnforceIf` on the platform-choice booleans.

**C2 — Interlocking** (mirrors `conflict/interlocking.py`):

For every pair of trips `(s1, s2)` and every pair of blocks `(b1, b2)` in the same interlocking group where `b1 != b2`: if s1 uses b1 AND s2 uses b2, their occupancy intervals must not overlap. Same conditional enforcement as C1.

Interlocking groups:
- Group 1: B1, B2
- Group 2: B3, B4, B13, B14
- Group 3: B7, B8, B9, B10

**C3 — Vehicle continuity:**

Trips are pre-assigned to vehicles. For consecutive trips `(s_prev, s_next)` of the same vehicle:

```
depart_time[s_next] >= depart_time[s_prev] + cycle_time[s_prev] + min_yard_dwell
```

**C4 — Battery** (mirrors `conflict/battery.py`):

- Each trip traverses at most ~10 blocks = 10% battery drain
- Battery starts at 80%, critical threshold is 30% — always satisfied for 10-block loops
- Yard dwell in C3 guarantees recharge to 80% before next trip
- Encoded as a sanity bound, not an active constraint for this network size

**C5 — Station frequency** (passenger wait constraint):

For each station, collect all arrival times across all trips and all platforms of that station. For each pair of consecutive arrivals when sorted:

```
arrival[i+1] - arrival[i] <= interval_seconds
```

**C6 — Time range:**

```
depart_time[s] >= start_time
depart_time[s] + max_possible_cycle_time <= end_time
```

### Objective

Primary: feasibility (no objective — constraint satisfaction).
Optional secondary: minimize maximum gap across all stations for even spacing.

## Post-processing

1. Extract `depart_time[s]` and platform choices from solver solution
2. For each trip, look up route variant -> get full node path
3. Build `Service` objects using existing `build_full_route()` (route + timetable)
4. Assign vehicle from pool
5. Sanity check: run all services through `ConflictDetectionService.detect_conflicts()`. Any conflict = bug in CP-SAT model -> 500 error
6. Persist all services via `ServiceRepository.create()` in a single transaction

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

- `solver.py`: Only file that imports `ortools`. Takes `SolverInput` (plain dataclasses), returns `SolverOutput` (departure times + platform choices).
- `route_variant.py`: Pure Python. Uses domain entities (Block, NodeConnection) to pre-compute timing tables.
- `schedule_service.py`: Orchestrates everything. Calls domain services (`RouteFinder`, `ConflictDetectionService`, `build_full_route`) for post-processing and validation.

Dependency flow: `api -> application -> domain <- infra` (unchanged).

## Error Handling

**Pre-solver (fail fast):**
- Invalid input -> 422
- Not enough vehicles -> 409

**Solver:**
- INFEASIBLE -> 409 "Cannot generate a conflict-free schedule with the given parameters"
- Timeout (30s limit) -> 500

**Post-validation:**
- ConflictDetectionService finds conflicts -> 500 internal error (CP-SAT model bug)

**Atomicity:** Delete existing services + create new ones in a single transaction.

## Testing

**Unit tests (no I/O, no solver):**
- `route_variant.py`: Verify all 8 variants produce correct block sequences and timing offsets given known block traversal times

**Application tests (with solver, in-memory repos):**
- Feasible case: verify solver output, all services conflict-free via ConflictDetectionService
- Infeasible case: interval too tight, verify proper error
- Not enough vehicles: verify pre-solver rejection
- Variable traversal times: non-uniform blocks, verify adaptation
- Frequency: verify max gap at every station <= interval
- Battery: verify yard dwell sufficient for recharging

**API tests (PostgreSQL, `@pytest.mark.postgres`):**
- POST returns correct response shape
- Existing services deleted before generation
- Generated services persisted and retrievable via GET /api/services
