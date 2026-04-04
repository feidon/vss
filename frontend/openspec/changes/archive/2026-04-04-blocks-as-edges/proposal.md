## Why

The schedule editor's track map currently renders blocks as gray circle nodes alongside platforms and yards, cluttering the visualization. Since blocks are just track segments connecting platforms and yards, they should appear as labeled edges — not nodes. Additionally, the conflict display after route updates is unreliable: while the 409 handler exists, non-409 errors (network failures, 422 validation errors, 500 server errors) are silently swallowed, and the conflict alert may not render correctly for all conflict types depending on backend response shape variations.

## What Changes

- **Track map rendering**: Remove block nodes (gray circles) from the editor track map. Instead, render block names as text labels on the edge lines connecting platforms/yards. Blocks still exist in the graph data but are no longer rendered as discrete SVG circle elements.
- **Conflict/error display**: Make the schedule editor handle ALL HTTP error statuses from route updates — not just 409. Show conflict details for 409 responses (existing behavior, verified working) and show a generic error message for other failures (4xx, 5xx, network errors). Ensure every conflict type the backend can return is surfaced to the user.

## Capabilities

### New Capabilities

- `edge-label-trackmap`: Render blocks as labeled edges instead of nodes in the editor track map
- `robust-conflict-display`: Handle all error statuses from route updates and display conflicts/errors to the user

### Modified Capabilities

## Impact

- `track-map-editor.ts` — Rewrite block rendering from circle nodes to edge labels
- `schedule-editor.ts` — Expand error handler to cover non-409 statuses
- `conflict-alert.ts` — Potentially minor adjustments for edge cases in conflict rendering
- No API changes, no new dependencies, no breaking changes
