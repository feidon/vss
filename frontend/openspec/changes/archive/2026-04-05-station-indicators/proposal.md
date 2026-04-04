## Why

The track map currently renders platforms and yards as individual circles with no visual grouping. The reference diagram (`track_map.png`) shows stations as labeled rectangles that frame their member platforms (e.g., S1 frames P1A and P1B). Without this grouping, operators cannot quickly identify which platforms belong to which station—especially as the network grows.

## What Changes

- Draw a rounded rectangle behind each station's platforms in the d3.js track map, labeled with the station name (S1, S2, S3, Y).
- Use the existing `Station` model (`GraphResponse.stations`) which already provides `platform_ids` for grouping—no API changes needed.
- Station rectangles render as a background layer (behind edges and nodes) with a light fill and subtle border, matching the reference image style.

## Non-goals

- No changes to the data model or backend API.
- No new station CRUD functionality—this is purely a visual indicator.
- No changes to click/hover interactivity on platforms; station rectangles are non-interactive.

## Capabilities

### New Capabilities
- `station-indicator-rendering`: Render station grouping rectangles around associated platforms in the d3.js track map visualization.

### Modified Capabilities
<!-- None — no existing spec-level requirements are changing -->

## Impact

- **Components**: `TrackMapEditorComponent` (`src/app/features/schedule/track-map-editor.ts`) — main rendering logic.
- **Models**: No changes. Uses existing `Station` and `GraphResponse` from `src/app/shared/models/graph.ts`.
- **Tests**: `track-map-editor.spec.ts` — add tests for station rectangle rendering.
- **Dependencies**: None new. Uses existing d3.js.
