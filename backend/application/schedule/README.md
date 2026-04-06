# Auto-generated Schedule

This module turns a few high-level parameters (headway, time window, dwell time)
into a complete set of `Service` rows with fully-expanded routes and timetables,
guaranteed to be conflict-free on the fixed VSS track network.

**Entry point:** `POST /api/schedules/generate` → `api/schedule/routes.py:18` →
`ScheduleAppService.generate_schedule` (`schedule_service.py:51`).

Everything in this package is a **pure application-layer use case**: no I/O
outside the repositories it's given, no async except for those repository
calls, no domain mutation except through `ServiceRepository`.

---

## Inputs & output

```python
GenerateScheduleRequest(
    interval_seconds: int,     # desired passenger-facing headway at S1
    start_time: EpochSeconds,  # first allowed departure from yard
    end_time: EpochSeconds,    # last allowed yard return
    dwell_time_seconds: int,   # how long each trip stops at every platform
)
```

```python
GenerateScheduleResponse(
    services_created: int,
    vehicles_used: list[UUID],
    cycle_time_seconds: int,   # longest variant's cycle time
)
```

On infeasibility or malformed input the service raises a `DomainError`
(`INVALID_INTERVAL`, `INVALID_DWELL_TIME`, `INVALID_TIME_RANGE`,
`INTERVAL_BELOW_MINIMUM`, `SCHEDULE_INFEASIBLE`). The structured `context`
on `INTERVAL_BELOW_MINIMUM` contains `requested_interval`,
`minimum_interval`, `dwell_time`, and `min_departure_gap` so the frontend
can show "the minimum passenger wait is N seconds."

---

## The fixed trip shape

Every trip runs the same seven-stop skeleton:

```
Y → S1 → S2 → S3 → S2 → S1 → Y
```

with exactly three binary decision points:

| Decision      | Platform choices | Why there is a choice                         |
|---------------|------------------|-----------------------------------------------|
| Outbound S1   | P1A or P1B       | Both reachable from Yard via B1 / B2          |
| Turnaround S3 | P3A or P3B       | Both reachable from P2A via B6 → B7 / B8      |
| Return S1     | P1A or P1B       | Both reachable from P2B via B12 → B13 / B14   |

S2 is **not** a decision point because the tracks are physically directional
(B5 only reaches P2A outbound, B11 only reaches P2B on return).

`2 × 2 × 2 = 8` variants total. Every assumption about this shape lives in
`network_layout.py` — that module is the one place to touch if the topology
ever changes.

### What a `RouteVariant` carries

`compute_route_variants` (`route_variant.py:18`) produces eight
`RouteVariant` records (`model.py:28`), each containing:

- `stop_ids` — the ordered list of platform / yard IDs used by
  `build_full_route` to expand the full `block → platform → block …` path.
- `block_timings` — for every block the trip uses, the `(enter_offset,
  exit_offset)` in seconds relative to yard departure (`t = 0`).
- `station_arrivals` — two `StationArrival`s per station (outbound + return)
  for passenger-facing scheduling metadata.
- `cycle_time` — total seconds from yard departure to yard arrival.
- `num_blocks` — total block traversals (drives the yard-recharge dwell).

Everything downstream (feasibility check, solver, service creation) treats
variants as opaque data. Nothing else needs to know how they were enumerated.

---

## End-to-end flow in `generate_schedule`

```
 1. _validate_request            → reject bad interval / dwell / time range
 2. load reference data          → blocks, stations, connections, vehicles
 3. compute_route_variants       → 8 variants with precomputed timings
 4. _compute_min_departure_gap   → necessary lower bound, else raise
 5. num_vehicles = ceil(max_turnaround / effective_interval) + FLEET_BUFFER
 6. build interlocking_groups    → {group_id: [block_ids]}
 7. solve_schedule                → list[TripAssignment]
 8. delete existing services
 9. for each assignment          → build_full_route + ServiceRepository.create
10. sanity check                 → run full conflict detection on the output
11. station-frequency warning    → log if any station gap exceeds interval
12. return GenerateScheduleResponse
```

Each of those lines is a numbered comment in `schedule_service.py:55-222`,
so the file reads top-to-bottom as this list.

### Step 4 — feasibility check (quick version)

`effective_interval = interval_seconds + dwell_time_seconds` is the true
back-to-back gap between departures (the requested passenger wait plus the
mandatory platform dwell).

`_compute_min_departure_gap(variants, blocks)` returns a **necessary lower
bound** on that gap derived from the interlocking constraints. If
`effective_interval < min_departure_gap`, no schedule can exist and we raise
`INTERVAL_BELOW_MINIMUM` immediately. See the deep dive below.

### Step 5 — fleet sizing

```python
cycle_times    = [v.cycle_time for v in variants]
min_yard_dwell = [v.num_blocks * SECONDS_TO_RECHARGE_PER_BLOCK for v in variants]
max_turnaround = max(cycle + dwell for cycle, dwell in zip(cycle_times, min_yard_dwell))
num_vehicles   = ceil(max_turnaround / effective_interval) + FLEET_BUFFER
```

`SECONDS_TO_RECHARGE_PER_BLOCK = TRAVERSAL_DRAIN * CHARGE_SECONDS_PER_PERCENT`
— a trip that traverses N blocks must recharge N of those before leaving the
yard again. `max_turnaround` is the worst case round-trip including recharge,
and dividing by the effective headway gives the minimum fleet size. The
`+ FLEET_BUFFER` (currently 1) absorbs rounding so we never leave a slot
empty because a vehicle is fractionally unavailable.

If the existing DB vehicle count is short, the service creates new ones
via `VehicleRepository.add_by_number` and re-reads the list. Only the first
`num_vehicles` are handed to the solver.

### Step 9 — creating services

For each `TripAssignment` the service calls
`build_full_route(stop_ids, dwell_by_stop, depart_time, connections, stations, blocks)`
to expand the variant's abstract stop list into the full `route` and
`timetable` that a `Service` needs. Names follow
`Auto-V{vehicle_index + 1}-T{trip_counter}` per vehicle.

### Steps 10–11 — sanity checks

- Re-runs `detect_block_conflicts`, `detect_interlocking_conflicts`, and
  `detect_vehicle_conflicts` on the freshly-created services. Any conflict
  at this point is a **solver bug** and raises `RuntimeError` rather than a
  `DomainError`.
- Logs a warning (non-fatal) if any station's consecutive arrival gap
  exceeds `effective_interval` — useful for spotting unexpected "holes" in
  the passenger-facing cadence.

---

## Deep dive: `_compute_min_departure_gap`

Lives at `schedule_service.py:243`. The task: for a departure gap `G`, when
can we guarantee two consecutive trips don't violate the same interlocking
group?

### Step 1 — collect group windows per variant

For every variant, walk its `block_timings` and group them by
`block.group`. Blocks with `group == 0` are ignored (no mutual exclusion).
The result per variant is a dict `{group_id: [(enter_offset, exit_offset), …]}`.
A single variant can produce multiple windows on the same group (outbound
and return halves of the trip both crossing Group 2, for example).

### Step 2 — derive forbidden-gap ranges for each variant pair

For each ordered pair of variants (earlier, later), each shared group, and
each `(earlier_window, later_window)` combination, compute when the two
windows overlap on the absolute timeline. Treating occupancy as half-open
`[enter, exit)`, overlap happens iff:

```
enter_e < G + exit_l   AND   G + enter_l < exit_e
⇔  enter_e - exit_l  <  G  <  exit_e - enter_l
```

Restricted to integers:

```python
forbidden_lo = earlier_enter - later_exit + 1
forbidden_hi = earlier_exit  - later_enter - 1
```

If `forbidden_lo > forbidden_hi` the two windows can never clash. Otherwise
the closed integer range `[forbidden_lo, forbidden_hi]` is one forbidden
gap value list entry.

### Step 3 — smallest positive gap outside all forbidden ranges

`_min_positive_outside(intervals)` (`schedule_service.py:292`) clamps each
interval to positives, sorts them, merges overlapping/adjacent intervals,
and returns either `1` (if the first merged block doesn't cover it) or
`merged[0].hi + 1`. That's the tightest gap for **this one** variant pair.

### Step 4 — minimum across pairs = necessary lower bound

The outer loop returns the minimum pair-level gap across all ordered pairs.
Interpretation: if `effective_interval` is below this number, **no pair of
variants** could be placed consecutively at that interval, so no schedule
exists. This is a necessary condition, not sufficient — the solver still
has to find an actual valid sequence above that bound.

### Why 5 nested loops

```
variants × variants × groups × earlier_windows × later_windows
```

Each level is a real degree of freedom: any variant can follow any other,
only same-group windows can clash, and a single variant can occupy one
group in multiple windows. Flattening any level would either miss conflicts
or hide the constraint structure. Problem size stays tiny in practice
(8 variants × 3 groups × ≤2 windows ≈ low hundreds of iterations).

---

## Deep dive: `solve_schedule`

A **greedy sequential dispatch** solver in `solver.py:22`. It places trips
one at a time in temporal order, never backtracks, and assumes the upstream
feasibility check already rejected impossible headways.

### State

- `occupancies[block_id] = [(enter, exit), …]` — absolute windows already
  booked, kept sorted by enter (via `bisect.insort`).
- `vehicle_available[i]` — absolute time vehicle `i` can next depart.
- `next_desired` — the next target departure time; starts at `start_time`,
  advances by `departure_gap_seconds` on success.

### Main loop

```python
while next_desired + min_cycle <= end_time:
    vehicle = min(vehicle_available, key=lambda v: (vehicle_available[v], v))
    depart  = max(vehicle_available[vehicle], next_desired)

    for variant in variants:              # tried in index order, 0..7
        if depart + variant.cycle_time > end_time: continue
        conflict_end = _find_conflict(depart, variant, …)
        if conflict_end is None:
            record_occupancies(depart, variant)
            vehicle_available[vehicle] = depart + variant.cycle_time \
                                        + variant.num_blocks * SECONDS_TO_RECHARGE_PER_BLOCK
            assignments.append(TripAssignment(vehicle, depart, variant.index))
            next_desired = depart + departure_gap_seconds
            break
        earliest_conflict_end = max(earliest_conflict_end, conflict_end)

    if not placed:
        if earliest_conflict_end <= next_desired: break  # deadlock
        next_desired = earliest_conflict_end             # jump forward and retry
```

- **Vehicle pick**: earliest free, lowest index on ties. Naturally
  load-balances because each used vehicle jumps to the back of the queue.
- **Variant pick**: first one in index order that fits. The variant list's
  ordering is effectively a priority list — variant 0 is the "default"
  route shape.
- **Jump forward**: when every variant clashed, skip `next_desired` ahead
  to `max` of the conflict hints returned by each failed variant, then
  retry. See the note below on `max` vs `min`.
- **Deadlock guard**: if the jump wouldn't move `next_desired` forward at
  all, the solver gives up.

### `_find_conflict` (`solver.py:85`)

For each block timing in the variant:

1. **Same-block check**: does `occupancies[block_id]` contain a window that
   overlaps `[depart + enter_offset, depart + exit_offset)`?
2. **Interlocking peers**: for every other block in the same group, does
   `occupancies[peer_bid]` contain an overlapping window?

On the first overlap found, return
`conflict_exit - bt.enter_offset` — the absolute departure time that
would slide this trip's entry to the moment the existing occupancy ends.
`None` means the entire variant is clear at `depart`.

Two subtleties worth flagging:

- It returns on the **first** conflict encountered. Later blocks in the
  same trip may still clash at the hinted depart time, which is why the
  outer loop may need multiple jumps to place a single trip.
- Peer blocks are checked at read time, not at write time. `_record_occupancies`
  only stores the actual blocks the trip uses, not the whole group. That
  keeps `occupancies` compact.

### `_check_overlap` early-exit (`solver.py:122`)

`occupancies[block_id]` is sorted by enter, so as soon as we see
`ex_enter >= exit_` we can `break` — no later window can possibly overlap.
Makes the per-check cost sub-linear on average.

### Note on `max(earliest_conflict_end, conflict_end)`

The jump-forward line uses `max` across variant hints, not `min`. This is
a **heuristic**, not a correctness requirement:

- `min` would jump to "as early as any variant might start working" — more
  thorough, catches earlier placements, more iterations per congestion
  point.
- `max` jumps to "wait until every tried variant's first conflict has
  cleared" — fewer iterations, but can delay trips past a depart time where
  an earlier-index variant would have fit.

Both are correct. The current `max` biases toward throughput and emergent
schedule spacing. If you need tighter schedules it is safe to change to
`min`; the sanity check in step 10 will catch any regression.

---

## Key constants

All defined in `network_layout.py`:

| Constant                       | Value              | Meaning |
|--------------------------------|--------------------|---------|
| `ENDPOINT_STATION_NAME`        | `"S1"`             | Trip start/end station, both platforms are decision options |
| `MIDDLE_STATION_NAME`          | `"S2"`             | Pass-through, directional |
| `TURNAROUND_STATION_NAME`      | `"S3"`             | Reversal point, both platforms are decision options |
| `MIDDLE_OUTBOUND_PLATFORM_INDEX` | `0`              | P2A — outbound side of S2 (seed order) |
| `MIDDLE_RETURN_PLATFORM_INDEX`   | `1`              | P2B — return side of S2 (seed order) |
| `SECONDS_TO_RECHARGE_PER_BLOCK`| `TRAVERSAL_DRAIN * CHARGE_SECONDS_PER_PERCENT` | Yard dwell per block traversed |
| `FLEET_BUFFER`                 | `1`                | Safety buffer added to fleet size |

---

## Where to look when things go wrong

| Symptom                                                  | Where to look |
|----------------------------------------------------------|---------------|
| `INVALID_*` raised on valid-looking input                | `_validate_request` (`schedule_service.py:224`) |
| `INTERVAL_BELOW_MINIMUM` but you think it should fit     | `_compute_min_departure_gap` (`schedule_service.py:243`) — check `min_departure_gap` in `error.context` |
| `SCHEDULE_INFEASIBLE` with an empty assignment list      | `solve_schedule` loop (`solver.py:37`) — likely deadlock; check `min_cycle` and the jump-forward logic |
| `RuntimeError: BUG: Generated schedule has conflicts`    | Solver bug — the sanity check in step 10 caught it. Inspect the offending conflict in `occupancies` vs the placed `TripAssignment` list |
| "Station X: gap Ns > effective interval" warning         | Expected slack from a slow variant landing late in the window, or a chain of `max`-jump-forward delays in the solver |
| Topology change (new station, renamed block)             | `network_layout.py` — update constants and assertions there first, then re-run tests |
| Adding a new decision point / variant axis               | `route_variant.py:compute_route_variants` and the trip-shape docstring in `network_layout.py` |

---

## Related files

- `schedule_service.py` — `ScheduleAppService.generate_schedule` orchestration, feasibility check
- `solver.py` — greedy sequential dispatch solver
- `route_variant.py` — variant enumeration from the fixed trip shape
- `network_layout.py` — single source of truth for topology assumptions
- `model.py` — `BlockTiming`, `RouteVariant`, `SolverInput`, `SolverOutput`, `TripAssignment`
- `dto.py` — `GenerateScheduleRequest` / `GenerateScheduleResponse`
- `api/schedule/routes.py` — HTTP entry point
- `tests/application/schedule/test_schedule_service.py` — end-to-end tests with in-memory repos
