## Why

The system currently detects scheduling conflicts (vehicle overlap, block occupancy, interlocking) but has no awareness of vehicle battery state. A vehicle can be scheduled for services it physically cannot complete — departing with insufficient charge or running out of battery mid-route. This is a core requirement listed in the project's bonus objectives.

## What Changes

- Add battery simulation to the conflict detection pipeline: track charge level across a vehicle's ordered services
- Detect **Low Battery** conflicts: a service would drain the vehicle's battery below the critical threshold (30%) during traversal
- Detect **Insufficient Charge on Departure** conflicts: the idle time between consecutive services is not enough for the vehicle to charge to the minimum departure threshold (80%)
- Extend `Vehicle` model with battery state and charge/cost methods
- Extend `ServiceConflicts` to include the two new conflict types
- Return battery conflicts in the existing 409 conflict response on route updates

## Capabilities

### New Capabilities
- `low-battery-detection`: Detect when a service would drain a vehicle's battery below the critical 30% threshold during block traversal
- `insufficient-charge-detection`: Detect when idle time between consecutive services is not enough for a vehicle to charge to the 80% departure threshold

### Modified Capabilities

## Impact

- **Domain layer**: `Vehicle` model gains `battery` field and mutation methods; `ConflictDetector` gains `_detect_battery_conflict`; `ServiceConflicts` dataclass extended with two new conflict lists
- **Application layer**: `ServiceAppService` must pass vehicle data to conflict detection
- **API layer**: Conflict error response schema extended with new conflict types
- **Tests**: New unit tests for vehicle battery methods, conflict detection battery logic, and integration tests for the full pipeline
