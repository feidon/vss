## Context

The domain layer currently has 101 passing tests across 6 test files. While the primary flows are well-tested, analysis of the source code reveals untested branches and edge cases in:

- **RouteFinder**: Only forward platform-to-platform paths tested; no direct adjacency (zero blocks between stops), no bidirectional block paths (Y via B1/B2)
- **RouteBuilder**: No yard-as-stop tests, no unknown-node-in-resolve error path (`_resolve_nodes` line 67)
- **Conflict shared utilities**: `find_time_overlaps`, `build_vehicle_schedule`, `build_occupancies` tested only through higher-level detector tests — no direct unit tests exercising empty inputs, single entries, or edge-case sorting
- **Vehicle conflict detection**: No single-service test, no multiple-discontinuity test, no combined overlap+discontinuity test
- **Interlocking conflicts**: No same-block/same-group overlap (should be skipped), no multi-group scenario, no different-groups-no-conflict scenario
- **Block conflicts**: No multi-block scenario, no touching-boundary (departure == next arrival) test
- **Battery**: No empty-steps test, no single-traversal test
- **Service model**: `__eq__`/`__hash__` with `None` id not tested, `_validate_connectivity` empty route not tested
- **ServiceConflicts model**: `has_conflicts` property not directly tested for each conflict type in isolation

## Goals / Non-Goals

**Goals:**
- Cover all identified untested branches in domain services
- Add direct unit tests for shared conflict utilities
- Test boundary conditions and degenerate inputs
- All new tests are pure unit tests (no I/O, no async)

**Non-Goals:**
- No production code changes
- No test infrastructure changes (no new fixtures, conftest, or pytest plugins)
- No application or API layer test additions
- No coverage tooling setup

## Decisions

### 1. New file for conflict shared utilities vs. extending existing test_conflict.py

**Decision**: Create a new `tests/domain/test_conflict_shared.py` for direct unit tests of `find_time_overlaps`, `build_vehicle_schedule`, and `build_occupancies`.

**Rationale**: These are low-level utility functions with their own contract. Mixing them into the existing `test_conflict.py` (which tests through the `detect_conflicts` orchestrator) would conflate unit-level and integration-level concerns.

**Alternative considered**: Adding to `test_conflict.py` — rejected because the existing file tests the detector facade, not individual functions.

### 2. Extend existing test files for other scenarios

**Decision**: Add new test classes/methods to the existing `test_route_finder.py`, `test_route_builder.py`, `test_conflict.py`, and `test_service.py` files.

**Rationale**: These scenarios extend the same modules already tested. Keeping them co-located improves discoverability.

### 3. Use real seed data for route tests, synthetic data for conflict tests

**Decision**: Route finder/builder tests continue using `infra.seed` fixtures (real track network). Conflict tests continue using synthetic `make_block()` / `make_service_with_window()` helpers.

**Rationale**: Route tests need the actual track topology to be meaningful. Conflict tests need precise control over timing and topology.

## Risks / Trade-offs

- **Risk**: Some edge-case tests may be brittle if they test implementation details (e.g., exact error messages) → **Mitigation**: Test behavior (raises DomainError) not message strings where possible
- **Risk**: Shared utility tests may duplicate coverage already achieved indirectly → **Mitigation**: Direct unit tests provide regression safety even if the higher-level tests happen to cover the same path today
- **Trade-off**: More tests = slightly slower test suite → Acceptable since domain tests are pure and run in ~0.07s total
