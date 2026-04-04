## Context

`build_battery_steps` in `domain/domain_service/conflict/battery.py` converts timetable entries into a sequence of `ChargeStop` and `BlockTraversal` steps for battery simulation. For Yard entries, it computes `charge_seconds = next_entry_time - this_entry_time`. When the Yard is the last entry in the sequence, `next_time` falls back to `entry.time`, producing `charge_seconds=0`. The subsequent `can_depart()` check then fails because the battery is below 80% after traversing blocks.

This is incorrect for the final Yard: the vehicle has returned home and does not need to depart. The `can_depart()` check is only meaningful when the vehicle must leave the Yard for another service.

## Goals / Non-Goals

**Goals:**
- Eliminate false `INSUFCHARGE` conflicts when a vehicle returns to Yard at the end of its last service
- Preserve correct `INSUFCHARGE` detection for mid-route Yard stops and cross-service gaps

**Non-Goals:**
- Changing the 80% departure threshold or charging formula
- Modifying `detect_battery_conflicts` logic
- Changing low-battery detection

## Decisions

### Decision 1: Skip ChargeStop for the trailing Yard entry

**Choice:** In `build_battery_steps`, do not append a `ChargeStop` when the Yard entry is the last in `node_entries` (i.e., `i + 1 >= len(node_entries)`).

**Rationale:** A `ChargeStop` models "charge for N seconds, then depart." When there is no departure, the step is semantically meaningless. Removing it from the step list means `detect_battery_conflicts` never runs `can_depart()` on a terminal Yard — which is the correct behavior.

**Alternative considered:** Add a boolean flag to `ChargeStop` (e.g., `is_terminal`) and skip the `can_depart()` check in `detect_battery_conflicts`. Rejected because it pushes a `build_battery_steps` concern into the detection function and adds unnecessary complexity.

**Alternative considered:** Use a sentinel value for `charge_seconds` (e.g., `float('inf')`). Rejected because it changes the type contract and adds a special case in the detection loop.

### Decision 2: Cross-service case is already correct

When multiple services share a vehicle, `build_battery_steps` merges all their entries chronologically. A Yard entry from service A's end will have `i + 1` pointing to service B's first block entry. The charge_seconds computation `next_time - entry.time` correctly represents the gap. No change needed for the cross-service case — the fix only affects the true terminal entry.

## Risks / Trade-offs

- **[Risk] Trailing Yard followed by a far-future service added later**: If the user saves service A (ending at Yard) first, the trailing Yard is terminal and no ChargeStop is generated. When service B is later added for the same vehicle, `build_battery_steps` is called with both services, and the Yard is no longer terminal — the ChargeStop is correctly generated. No risk because battery steps are rebuilt from scratch on every route update.
- **[Trade-off]**: The existing test `test_yard_at_end_triggers_insufficient_charge_when_battery_low` asserts the current (wrong) behavior. It must be updated to expect zero conflicts, which changes the documented contract. This is intentional — the test was codifying the bug.
