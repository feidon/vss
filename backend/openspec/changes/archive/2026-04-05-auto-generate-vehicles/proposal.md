## Why

The schedule generation service (`ScheduleAppService`) currently requires vehicles to be pre-seeded in the database. If the number of available vehicles is fewer than the computed requirement, it calls `VehicleRepository.add_by_number()` to create them. However, this method lacks test coverage — the Postgres implementation has a missing `await` bug, and there are no dedicated tests verifying the auto-generation behavior in the schedule service when vehicles are insufficient.

## What Changes

- **Fix bug** in `PostgresVehicleRepository.add_by_number()`: missing `await` on `self.find_all()` call (line 29)
- **Add application-level tests** for `ScheduleAppService` covering the case where fewer vehicles exist than the schedule requires, verifying new vehicles are auto-generated
- **Add repository-level tests** for `VehicleRepository.add_by_number()` — both the in-memory fake and the Postgres implementation
- **Add naming convention test** to verify auto-generated vehicles follow the `V{N}` naming pattern with correct sequential numbering

## Non-goals

- Changing the vehicle auto-generation algorithm or naming scheme
- Adding an API endpoint for manual vehicle creation
- Modifying the vehicle domain model

## Capabilities

### New Capabilities
- `vehicle-auto-generation-tests`: Tests for `add_by_number` across all layers (repository fake, Postgres repo, schedule service integration)

### Modified Capabilities

## Impact

- `infra/postgres/vehicle_repo.py` — bug fix (missing await)
- `tests/application/schedule/test_schedule_service.py` — new test cases for insufficient vehicles
- `tests/fakes/test_vehicle_repo.py` or `tests/infra/test_vehicle_repo.py` — new test files for `add_by_number`
