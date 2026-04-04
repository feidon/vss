## Why

When the schedule editor loads a service with a saved route, `RouteEditorComponent.deriveInitialState()` populates the stops queue with all nodes from `svc.route` including block nodes. This violates the `editor-bugfixes` spec which requires blocks to be filtered out — only platform and yard nodes should appear in the stop queue. The bug causes block nodes (B1, B3, etc.) to show as numbered markers on the track map and as entries in the stop list, confusing operators.

## What Changes

- **Filter block nodes in `deriveInitialState()`**: When populating the stops queue from an existing service route, exclude nodes whose type is `'block'`. Only platform and yard nodes should be included.
- **Emit only non-block node IDs via `stopsChanged`**: The `stopsChanged` output (which drives `queuedNodeIds` on the track map) already derives from the stops signal, so filtering at the source fixes both the stop list and the map markers.

## Non-goals

- Changing the timetable display (block nodes should still appear there)
- Modifying the track map click behavior (already blocks-only-non-clickable)
- Changing the route update API request format

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `editor-bugfixes`: The "Editor populates stop queue from existing service route" requirement is already correct in the spec but not implemented — this change fixes the implementation to match the spec

## Impact

- `src/app/features/schedule/route-editor.ts` — `deriveInitialState()` method (line 165): filter `svc.route` to exclude block nodes
- `src/app/features/schedule/route-editor.spec.ts` — add/update test verifying blocks are excluded from initial stops
