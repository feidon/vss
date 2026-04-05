## Context

The `ScheduleAppService.generate()` computes the number of vehicles needed for a schedule and calls `VehicleRepository.add_by_number(deficit)` when existing vehicles are insufficient. The `add_by_number` method exists in the interface and both implementations (Postgres, in-memory fake), but:

1. The Postgres implementation has a bug — `len(self.find_all())` is missing `await`, so it calls `len()` on a coroutine object.
2. No tests exist for `add_by_number` at any layer.
3. No tests exercise the "insufficient vehicles" path in the schedule service.

## Goals / Non-Goals

**Goals:**
- Fix the missing-await bug in `PostgresVehicleRepository.add_by_number()`
- Add unit tests for `InMemoryVehicleRepository.add_by_number()` (naming, count, idempotency)
- Add Postgres integration tests for `PostgresVehicleRepository.add_by_number()`
- Add application-level tests for `ScheduleAppService` covering the auto-generation path (0 vehicles, fewer vehicles than needed)

**Non-Goals:**
- Changing vehicle naming scheme or generation algorithm
- Adding vehicle creation API endpoints
- Modifying the `Vehicle` domain model

## Decisions

### 1. Fix inline rather than refactor

**Decision:** Fix the missing `await` in `add_by_number` directly. No architectural change needed.

**Rationale:** The method signature and logic are correct — it's a single missing keyword. Refactoring would be over-engineering for a one-character fix.

### 2. Test `add_by_number` at both repository layers

**Decision:** Add tests to `tests/fakes/` for the in-memory repo and `tests/infra/` for the Postgres repo (marked `@pytest.mark.postgres`).

**Rationale:** The bug only exists in the Postgres implementation — testing both layers catches implementation-specific issues while the fake tests run fast without a database.

### 3. Test schedule service with 0 and partial vehicle counts

**Decision:** Add two new test cases in `tests/application/schedule/test_schedule_service.py`:
- Start with 0 vehicles — service auto-generates all needed
- Start with 1 vehicle when 2+ are needed — service generates the deficit

**Rationale:** These are the two realistic edge cases. The existing tests already seed 3 vehicles which satisfies most schedules.

### 4. Vehicle naming continuity

**Decision:** `add_by_number` names new vehicles `V{N}` where N continues from the current count. Tests SHALL verify this.

**Rationale:** The naming convention is already implemented — we just need test coverage to prevent regressions.

## Risks / Trade-offs

- **[Low] Fake repo diverges from Postgres repo** — The fake uses `len(self._store.items())` (sync) while Postgres uses `len(await self.find_all())` (async). This is inherent to the fake pattern and acceptable since both are tested independently.
- **[Low] Vehicle name collision on concurrent generation** — Not a concern per CLAUDE.md ("no high-concurrency support").
