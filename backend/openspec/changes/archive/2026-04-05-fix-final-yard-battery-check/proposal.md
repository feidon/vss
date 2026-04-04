## Why

When a service ends at the Yard (round trip), `build_battery_steps` generates a `ChargeStop` with `charge_seconds=0` for the final Yard entry because there is no subsequent timetable entry. `detect_battery_conflicts` then runs `can_depart()` on this stop and raises `INSUFCHARGE` — even though the vehicle has returned home and does not need to depart again. This makes round-trip routes (Y → stations → Y) fail incorrectly when block traversals drain battery below 80%.

## What Changes

- **Fix `build_battery_steps`**: Skip generating a `ChargeStop` for the last Yard entry when there is no subsequent departure. A `ChargeStop` represents "charge before departing" — if there is no departure, there is no step to generate.
- **Update existing test**: The test `test_yard_at_end_triggers_insufficient_charge_when_battery_low` asserts the current (incorrect) behavior. It must be updated to expect no conflict for a trailing Yard with no subsequent service.
- **Add round-trip test**: Add a test that exercises a full round-trip route (Yard → blocks → Yard) to confirm no false INSUFCHARGE.

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `insufficient-charge-detection`: The departure threshold check should only apply when the vehicle has a subsequent departure, not when it returns to Yard with no further services.

## Non-goals

- Changing the 80% departure threshold or charging formula.
- Modifying low-battery detection logic.
- Changing how cross-service battery simulation works (the fix only affects the trailing-Yard edge case).

## Impact

- **Domain**: `domain/domain_service/conflict/battery.py` — `build_battery_steps` function
- **Tests**: `tests/domain/test_conflict.py` — update existing test, add round-trip test
- **Spec**: `openspec/specs/insufficient-charge-detection/spec.md` — clarify departure threshold applies only before an actual departure
