## 1. Domain Tests (TDD — RED)

- [x] 1.1 Update `test_yard_at_end_triggers_insufficient_charge_when_battery_low` to expect zero conflicts (trailing Yard with no subsequent service should not trigger INSUFCHARGE)
- [x] 1.2 Add `test_round_trip_yard_to_yard_no_false_insufficient_charge` — single service: Yard → N blocks → Yard, battery drops below 80%, expect no battery conflicts
- [x] 1.3 Add `test_trailing_yard_with_subsequent_service_still_triggers_insufficient_charge` — service A ends at Yard, service B starts shortly after, insufficient gap → INSUFCHARGE expected
- [x] 1.4 Run tests, confirm 1.1 and 1.2 FAIL (RED), 1.3 passes (existing behavior)

## 2. Domain Implementation (GREEN)

- [x] 2.1 Fix `build_battery_steps` in `domain/domain_service/conflict/battery.py`: skip appending `ChargeStop` when the Yard entry is the last in `node_entries` (`i + 1 >= len(node_entries)`)
- [x] 2.2 Run all domain tests, confirm all pass (GREEN)

## 3. Application-Layer Tests

- [x] 3.1 Add async test in `tests/application/test_update_route.py`: round-trip route (Y → platforms → Y) with sufficient battery should save successfully (no 409)
- [x] 3.2 Run application tests, confirm pass

## 4. Verification

- [x] 4.1 Run full test suite (`uv run pytest`) — all tests pass
- [x] 4.2 Run linter (`uv run ruff check . && uv run lint-imports`) — no violations
