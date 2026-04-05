## Why

The route editor's stops queue is append-only — users must remove and re-add stops to fix ordering mistakes. This is tedious, especially for longer routes. Drag-and-drop reordering lets users correct stop order in-place, significantly improving the route editing workflow.

## What Changes

- Add drag-and-drop reordering to the stops list in `RouteEditorComponent`
- Leverage `@angular/cdk/drag-drop` (already installed, v21.2.5) for accessible, touch-friendly drag behavior
- Update the track map's queued-stop order numbers in real time as stops are reordered
- Preserve existing add (map click), remove (X button), and dwell-time editing behaviors

## Non-goals

- Drag-and-drop on the track map itself (reordering is list-only)
- Multi-select or batch reordering
- Undo/redo support for reorder actions
- Keyboard-only reordering (CDK drag-drop provides basic keyboard support out of the box)

## Capabilities

### New Capabilities

- `stops-drag-reorder`: Drag-and-drop reordering of stops in the route editor's stops queue

### Modified Capabilities

_(none — no existing spec-level requirements change)_

## Impact

- **Components**: `RouteEditorComponent` (template + class logic)
- **Visual feedback**: Track map order numbers update reactively via existing `queuedStopIds` signal
- **Dependencies**: Uses `@angular/cdk/drag-drop` (already in `package.json`, no new install)
- **API**: No backend changes — stop order is determined client-side before submission
