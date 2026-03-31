## Context

The ConflictDetector currently validates services against three conflict types (vehicle, block, interlocking) but ignores battery constraints. Partial implementation already exists: `Vehicle` has been extended with `battery`, `charge()`, `canDeparture()`, and `cost()` methods, and a `_detect_battery_conflict` private method exists in `ConflictDetector` but is not wired into the public `validate_service()` flow.

Key domain constants already chosen by the user:
- Battery range: 0–100%
- Charging rate: 1% per 12 seconds idle
- Departure threshold: 80% minimum to depart
- Critical threshold: 30% — battery must not drop below this during traversal
- Cost: 1% per block traversed

## Goals / Non-Goals

**Goals:**
- Integrate battery conflict detection into the existing `validate_service()` pipeline
- Detect low-battery conflicts (battery drops below 30% during a service)
- Detect insufficient-charge conflicts (idle gap between services too short to reach 80%)
- Return battery conflicts in the existing 409 error response
- Maintain the pure domain service pattern (no repository dependencies in ConflictDetector)

**Non-Goals:**
- Regenerative braking or variable energy consumption per block
- Battery degradation over time
- Charging station modeling (charging only happens during idle time at any location)
- Persisting battery state across API calls (battery is simulated fresh each validation)

## Decisions

### 1. Battery simulation is stateless, computed per-validation

Each call to `validate_service()` simulates battery from a starting value (100%) across all services for a vehicle in chronological order. No battery state is persisted.

**Rationale:** Matches the existing conflict detection pattern — everything is computed from current service data. Avoids state management complexity. If a service is deleted or reordered, the simulation naturally adjusts.

**Alternative considered:** Persist battery state on the Vehicle entity — rejected because it would couple validation to mutation order and require recalculation on any service change.

### 2. Vehicle methods use mutation (charge/cost) but only on simulation copies

The existing `charge()` and `cost()` methods mutate `self.battery`. During conflict detection, the caller must work on a copy or a simulation vehicle instance, not the canonical domain entity.

**Rationale:** The user's existing code uses mutation. We preserve that interface but ensure the domain entity passed from the application layer is never mutated by validation.

### 3. ConflictDetector receives vehicles alongside services and blocks

`validate_service()` signature expands to accept a `vehicles: list[Vehicle]` parameter. The detector groups services by vehicle and runs battery simulation per vehicle.

**Rationale:** Keeps ConflictDetector as a pure domain service. The application layer already fetches vehicles — it just needs to pass them through.

### 4. Battery conflicts extend ServiceConflicts

`ServiceConflicts` gains two new fields: `low_battery_conflicts: list[LowBatteryConflict]` and `insufficient_charge_conflicts: list[InsufficientChargeConflict]`. The existing `has_conflicts` property checks all fields including the new ones.

**Rationale:** Single return type, consistent with existing pattern. API layer already serializes ServiceConflicts — just needs new fields in the schema.

## Risks / Trade-offs

- **Simulation accuracy vs. simplicity** — Flat 1% per block and 1% per 12s charging are approximations. Sufficient for the assignment but not production-grade. → Acceptable for scope; constants are easy to adjust later.
- **Mutation on Vehicle** — `charge()` and `cost()` mutate in place, which conflicts with the project's immutability preference. → Mitigated by operating on a copy during simulation. Documented as a known deviation.
- **First-error-only detection** — The existing `_detect_battery_conflict` stops at the first failure per vehicle. This means later conflicts are hidden. → Acceptable UX trade-off; fixing the first conflict may resolve later ones.
