## Why

Edge labels (block names) on the track map overlap when crossing edges share the same midpoint. Specifically, B8/B10 at S3 and B4/B13 at S2-S1 form symmetric X-crossing patterns where both edges have mathematically identical midpoints, rendering their labels on top of each other and making them unreadable.

Current label positioning uses a simple midpoint formula: `(from.x + to.x) / 2, (from.y + to.y) / 2 - 8`. This fails for crossing edges.

## What Changes

- Offset edge labels perpendicular to their edge line instead of placing all labels above the midpoint with a fixed -8px offset
- Each label shifts slightly away from its edge line's center in the perpendicular direction, naturally separating crossing-edge labels because they have different line angles

## Non-goals

- No changes to the Edge data model or API
- No changes to node rendering, click behavior, or stop queue
- No changes to the config/overview track map
- Not adding collision detection for arbitrary overlaps — this targets the geometric root cause

## Capabilities

### New Capabilities

- `perpendicular-edge-label-offset`: Position edge labels offset perpendicular to their edge line direction, resolving overlap for crossing edges

### Modified Capabilities

_(none)_

## Impact

- **Component**: `TrackMapEditorComponent` (`src/app/features/schedule/track-map-editor.ts`) — label positioning logic (lines 119–134)
- **Test**: `track-map-editor.spec.ts` — update or add test for label positioning
- **No API changes**
- **No dependency changes**
