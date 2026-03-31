## 1. Vehicle Model — Battery Methods

- [x] 1.1 Clean up existing `Vehicle` model: fix `battery` field (default 100), ensure `charge()`, `canDeparture()`, `cost()` methods work correctly
- [x] 1.2 Rename `canDeparture` to `can_depart` (PEP 8) and `cost` to `consume_battery` for clarity
- [x] 1.3 Add unit tests for `charge()` — partial charge, full charge cap at 100, zero idle time
- [x] 1.4 Add unit tests for `can_depart()` — at threshold (80), below, above
- [x] 1.5 Add unit tests for `consume_battery()` — normal deduction, exactly at 30%, below 30% raises error

## 2. Conflict Value Objects

- [x] 2.1 Define `LowBatteryConflict` frozen dataclass with `service_id` field
- [x] 2.2 Define `InsufficientChargeConflict` frozen dataclass with `service_a_id` and `service_b_id` fields
- [x] 2.3 Extend `ServiceConflicts` with `low_battery_conflicts` and `insufficient_charge_conflicts` lists
- [x] 2.4 Update `has_conflicts` property to include new conflict types

## 3. ConflictDetector — Battery Detection Logic

- [x] 3.1 Fix existing `_detect_battery_conflict` method: correct type annotations, operate on a copy of the vehicle
- [x] 3.2 Wire `_detect_battery_conflict` into `validate_service()` — expand signature to accept `vehicles: list[Vehicle]`
- [x] 3.3 Add unit test: no conflicts when battery is sufficient across all services
- [x] 3.4 Add unit test: `LowBatteryConflict` raised when service drains battery below 30%
- [x] 3.5 Add unit test: `InsufficientChargeConflict` raised when idle time insufficient to reach 80%
- [x] 3.6 Add unit test: charging during idle brings battery above threshold — no conflict
- [x] 3.7 Add unit test: multiple services for same vehicle — cumulative drain detected

## 4. Application Layer Integration

- [x] 4.1 Update `ServiceAppService` to fetch vehicles and pass them to `ConflictDetector.validate_service()`
- [x] 4.2 Add integration test: route update returns battery conflicts in `ConflictError`

## 5. API Layer — Response Schema

- [x] 5.1 Add Pydantic schemas for `LowBatteryConflict` and `InsufficientChargeConflict` response models
- [x] 5.2 Extend the 409 conflict error response to include new conflict types
- [x] 5.3 Add API test: PATCH route returns 409 with `low_battery_conflicts` when applicable
- [x] 5.4 Add API test: PATCH route returns 409 with `insufficient_charge_conflicts` when applicable
