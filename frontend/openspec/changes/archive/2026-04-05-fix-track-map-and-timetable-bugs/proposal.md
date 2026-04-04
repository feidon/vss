## Why

Three visual bugs remain in the schedule editor after recent fix attempts: timetable entries show raw UUIDs instead of block names, directional edges render without visible arrowheads, and edge labels overlap on the track map. These degrade usability for operators building and reviewing service routes.

## What Changes

- **Fix timetable node name resolution**: `timetable-detail.ts` only searches `service().route` for node names but block nodes live in the graph edges. Add graph access and edge lookup matching the pattern already used in `route-editor.ts`.
- **Fix arrowhead rendering on directional edges**: The SVG marker definition exists but arrows are not visually appearing. Adjust marker sizing, positioning (accounting for node radius), and ensure proper rendering across browsers.
- **Fix edge label overlap**: The perpendicular offset of 10px is insufficient to separate text bounding boxes. Increase offset distance and/or add index-based staggering for edges sharing the same endpoints.

## Non-goals

- Changing the track map layout algorithm or node positions
- Adding new track map interaction features
- Modifying the backend API responses

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `timetable-display`: Timetable must resolve block node names from graph edges, not just the route array
- `directional-edge-rendering`: Arrowheads must be visually visible, properly sized, and positioned to account for target node radius
- `perpendicular-edge-label-offset`: Offset must be large enough to prevent text bounding box overlap for parallel/crossing edges

## Impact

- `src/app/features/schedule/timetable-detail.ts` — add graph input, fix `findNode()` / `nodeName()` to search edges
- `src/app/features/schedule/track-map-editor.ts` — fix marker sizing/positioning, increase label offset
- `src/app/shared/models/node.ts` — may need `BlockNode` type added to the `Node` union
- Corresponding test files for updated behavior
