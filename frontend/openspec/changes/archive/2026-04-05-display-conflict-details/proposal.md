## Why

The conflict alert component currently displays raw UUIDs for blocks (`block_id`, `block_a_id`, `block_b_id`) and vehicles (`vehicle_id`) instead of human-readable names like "B3" or "V1". When a user triggers a 409 conflict on route update, the alert says _where_ a conflict occurred using opaque identifiers that are meaningless to the operator. The conflict is detected and shown, but the user cannot understand the content.

## What Changes

- Pass graph data (nodes, vehicles) into the conflict-alert component so it can resolve IDs to names
- Display block names (e.g. "B3"), vehicle names (e.g. "V1"), and service names (e.g. "S101") instead of raw UUIDs/IDs
- For interlocking conflicts, show block names instead of block UUIDs

## Non-goals

- Changing the backend conflict response schema (names are already available in the graph)
- Adding new conflict types or changing conflict detection logic
- Highlighting conflicts on the track map (separate feature)

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `conflict-display`: Conflict alert must resolve IDs to human-readable names using graph data, instead of displaying raw UUIDs and numeric IDs

## Impact

- **Components**: `ConflictAlertComponent` — needs graph input for name resolution; `ScheduleEditorComponent` — must pass graph data to conflict alert
- **Models**: No changes to `ConflictResponse` or graph interfaces
- **Tests**: Existing conflict alert tests and schedule-editor 409 tests need updating to verify name resolution
