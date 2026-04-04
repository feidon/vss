## Why

The track map in the schedule editor renders edges as plain lines between nodes, even though the data model explicitly defines direction (`from_id` → `to_id`). Blocks in the track network are unidirectional, so users need to see which direction each edge goes to understand valid route paths and make correct stop selections.

## What Changes

- Add SVG arrowhead markers to edge lines in `TrackMapEditorComponent` to indicate direction (from → to)
- Edges will render with a small arrowhead at the `to_id` end of each line
- Edge styling updated to accommodate the marker without clipping or overlap with node circles

## Non-goals

- No changes to the config/overview track map — it remains read-only and undirected
- No changes to the Edge data model or API — direction data already exists
- No interactive behavior changes — click targets, hover, stop queue all unchanged
- No changes to edge label positioning

## Capabilities

### New Capabilities

- `directional-edge-rendering`: Render edge arrowheads on the track map editor to indicate block direction (from → to)

### Modified Capabilities

_(none — the track-map-editor spec covers node interaction and stop queue; edge direction is a new visual capability)_

## Impact

- **Component**: `TrackMapEditorComponent` (`src/app/features/schedule/track-map-editor.ts`) — SVG rendering logic
- **Test**: `track-map-editor.spec.ts` — verify arrowhead markers are rendered
- **No API changes**: Edge `from_id`/`to_id` already provides direction
- **No dependency changes**: d3.js already supports SVG markers
