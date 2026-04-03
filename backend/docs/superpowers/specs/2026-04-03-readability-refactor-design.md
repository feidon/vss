# Readability Refactor: Service App Service + Conflict Module

**Date:** 2026-04-03
**Type:** Pure structural refactor (no behavior changes)

## Problem

1. **`application/service/service.py`** (227 lines) mixes route-building logic with service CRUD orchestration. Four static methods (`_build_route`, `_resolve_nodes`, `_compute_timetable`, `_validate_stops_exist`) don't use `self` and are pure domain logic stranded in the app service.

2. **`domain/domain_service/conflict/`** (5 files, ~511 lines) is organized by processing phase (preparation -> detection -> service) rather than by what is being detected. Too many intermediate data classes leak across files. You have to jump between 3 files to follow any single conflict type's logic.

## Solution

### 1. Extract Route Builder

Create a new pure domain service:

```
domain/domain_service/route_builder.py
```

Move these static methods from `ServiceAppService`:
- `_validate_stops_exist` -> `validate_stops`
- `_resolve_nodes` -> `resolve_nodes`
- `_compute_timetable` -> `compute_timetable`
- `_build_route` -> `build_full_route` (orchestrates the above three)

All are pure synchronous functions — no I/O, no repository access. Note: `_build_route` is currently declared `async` despite having no `await` calls. The extracted `build_full_route` will be a plain synchronous function, and callers must drop the `await`.

**Domain boundary:** `RouteStop` is an application-layer DTO (`application/service/dto.py`) and cannot be used in the domain layer (`import-linter` enforces `application -> domain`, not the reverse). The route builder functions accept primitives:
- `validate_stops(stop_ids: list[UUID], ...)` — not `list[RouteStop]`
- `build_full_route(stop_ids: list[UUID], dwell_by_stop: dict[UUID, int], ...)` — not `list[RouteStop]`

The `ServiceAppService` extracts these from `RouteStop` before calling into the domain service.

`ServiceAppService` becomes a thin orchestrator (~95 lines):
1. Load data from repos
2. Call route builder to build route + timetable
3. Call `detect_conflicts`
4. Persist

### 2. Reorganize Conflict Module by Detection Target

**Before:**
```
conflict/
├── __init__.py       # re-exports
├── model.py          # all data classes (public + intermediate)
├── preparation.py    # all prep functions
├── detection.py      # all detection functions
└── service.py        # orchestrator
```

**After:**
```
conflict/
├── __init__.py       # re-exports detect_conflicts + all public result types from model.py
├── model.py          # public result types only
├── shared.py         # shared functions + intermediate data classes
├── vehicle.py        # vehicle conflict detection
├── block.py          # block conflict detection
├── interlocking.py   # interlocking conflict detection
├── battery.py        # battery conflict detection (including battery-specific prep)
└── detector.py       # orchestrator
```

#### `model.py` — Public Result Types

Contains only what callers need to see:
- `VehicleConflict`
- `BlockConflict` (without `from_overlap` — see below)
- `InterlockingConflict` (without `from_overlap` — see below)
- `BatteryConflict`, `BatteryConflictType`
- `ServiceConflicts`

The `from_overlap` factory methods on `BlockConflict` and `InterlockingConflict` move to their respective detection files (`block.py`, `interlocking.py`) as module-level factory functions. This avoids `model.py` depending on intermediate types from `shared.py`.

Removed: `InsufficientChargeConflict` (unused — `BatteryConflict` with `INSUFCHARGE` type covers this).

#### `shared.py` — Shared Functions + Intermediate Types

Intermediate data classes (used across multiple detection files):
- `Timed` (protocol)
- `ServiceWindow`
- `ServiceEndpoints`
- `VehicleSchedule`
- `BlockOccupancy`
- `GroupOccupancy`

Shared functions:
- `find_time_overlaps()` — sweep-line algorithm used by block and interlocking detection
- `build_vehicle_schedule()` — builds schedule from services, used by vehicle detection
- `build_occupancies()` — builds block/group occupancy maps, used by block and interlocking detection

#### `vehicle.py` — Vehicle Conflict Detection

- `detect_vehicle_conflicts()` — combines time overlap + location discontinuity checks
- Internal helpers: `_detect_time_overlaps()`, `_detect_location_discontinuities()`

#### `block.py` — Block Conflict Detection

- `detect_block_conflicts()` — uses `find_time_overlaps` from shared

#### `interlocking.py` — Interlocking Conflict Detection

- `detect_interlocking_conflicts()` — uses `find_time_overlaps` from shared

#### `battery.py` — Battery Conflict Detection

- `build_battery_steps()` — battery-specific prep (stays here since no other detector uses it)
- `detect_battery_conflicts()` — simulation logic
- Internal types: `NodeEntry`, `ChargeStop`, `BlockTraversal` (only used within this file)

#### `detector.py` — Orchestrator

- `detect_conflicts()` — single entry point, wires shared prep functions to per-target detectors
- Replaces current `service.py`

### 3. Caller Impact

**Conflict API unchanged:**
- `from domain.domain_service.conflict import detect_conflicts, ServiceConflicts` — same
- `from domain.domain_service.conflict.battery import detect_battery_conflicts, build_battery_steps` — new path (was `detection` and `preparation`)

**App service changes:**
- Route-building logic imported from `domain.domain_service.route_builder` instead of being inline methods
- `await self._build_route(...)` becomes `build_full_route(...)` (sync, no await)
- `ServiceAppService` extracts `stop_ids` and `dwell_by_stop` from `RouteStop` list before calling domain functions

**Tests affected:**
- `tests/domain/test_conflict.py` — may need import path updates if importing from `preparation` or `detection` directly
- `tests/application/` — app service tests may need updates for route builder import changes
- `tests/api/` — integration tests unchanged (they call HTTP endpoints, not internal functions)
- Assertions stay the same — no behavior changes
