## Why

The domain service test suite (101 tests) covers the primary happy paths and basic error cases, but leaves meaningful gaps in edge cases for `RouteFinder`, `RouteBuilder`, conflict detection (`shared.py`, `vehicle.py`, `interlocking.py`, `block.py`, `battery.py`), and the top-level `detect_conflicts` orchestrator. These gaps reduce confidence when refactoring domain logic and risk letting regressions slip through.

## What Changes

- Add new test scenarios for **RouteFinder** edge cases (direct adjacency, duplicate stops, bidirectional blocks)
- Add new test scenarios for **RouteBuilder** covering yard-based routes, intermediate timing, and unknown-node-in-path error path
- Add new test scenarios for **conflict detection shared utilities** (`find_time_overlaps`, `build_vehicle_schedule`, `build_occupancies`) which are currently tested only indirectly
- Add new test scenarios for **vehicle conflict detection** edge cases (single service, multiple discontinuities, overlapping + discontinuity combo)
- Add new test scenarios for **interlocking conflict detection** (same-block same-group overlap, multi-group conflicts, different groups no conflict)
- Add new test scenarios for **block conflict detection** (multiple blocks, touching-but-not-overlapping boundaries)
- Add new test scenarios for **battery conflict detection** (empty steps, single block traversal, boundary arithmetic)
- Add new test scenarios for **ServiceConflicts model** (`has_conflicts` property with various combinations)
- Add new test scenarios for **Service model** (`__eq__`/`__hash__` with `None` id, `_validate_connectivity` edge cases)

## Non-goals

- No changes to production domain code
- No application-layer or API-layer test additions
- No integration/postgres tests in this change
- No test coverage tooling setup (e.g., pytest-cov)

## Capabilities

### New Capabilities
- `route-finder-edge-cases`: Test scenarios for RouteFinder covering direct adjacency, self-loop, bidirectional paths, and duplicate stops
- `route-builder-edge-cases`: Test scenarios for RouteBuilder covering yard starts/ends, timing continuity, and resolve-node error paths
- `conflict-shared-unit-tests`: Direct unit tests for `find_time_overlaps`, `build_vehicle_schedule`, and `build_occupancies`
- `conflict-detection-edge-cases`: Additional edge-case scenarios across vehicle, block, interlocking, and battery conflict detectors
- `service-model-edge-cases`: Test scenarios for Service equality/hashing with None ids and connectivity validation

### Modified Capabilities

## Impact

- **Affected code**: `tests/domain/test_route_finder.py`, `tests/domain/test_route_builder.py`, `tests/domain/test_conflict.py`, `tests/domain/test_service.py`; new file `tests/domain/test_conflict_shared.py`
- **No production code changes**
- **No API or schema changes**
- **No dependency changes**
