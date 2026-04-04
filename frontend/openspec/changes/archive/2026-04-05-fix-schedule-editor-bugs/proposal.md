## Why

The schedule editor page has two bugs that degrade usability:

1. **Stops queue persists stale state on refresh** — When the page is refreshed, manually-added stops survive because the route editor only initializes stops in `ngOnInit()`, which doesn't re-run when the parent's `service` input signal changes. Users see a mix of API data and their pre-refresh additions.

2. **Timetable shows UUIDs for block nodes** — The conflict alert component resolves node names only from `graph.nodes` (platforms/yards), but block IDs come from `graph.edges`. Block conflicts display raw UUIDs instead of human-readable names like "B3".

## What Changes

- Route editor resets stops whenever the `service` input signal changes, not just on `ngOnInit()`
- Conflict alert's node name lookup includes both `graph.nodes` and `graph.edges` so block names resolve correctly

## Capabilities

### New Capabilities

- `stops-queue-refresh`: Fix stops queue to reset from API data when the service input changes
- `block-name-resolution`: Fix conflict alert to resolve block node names from graph edges

### Modified Capabilities

_(none)_

## Impact

- `frontend/src/app/features/schedule/route-editor.ts` — stops initialization logic
- `frontend/src/app/features/schedule/conflict-alert.ts` — `nodeNameMap` computed signal
- Existing tests may need updates to cover the new behavior
