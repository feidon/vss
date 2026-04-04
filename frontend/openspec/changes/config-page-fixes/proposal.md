## Why

The config page has two broken UX interactions: (1) clicking outside the traversal time input field does not close it because the input is never auto-focused on edit start — so the `blur` event never fires, and (2) the track map overview calls `GET /api/graph` which does not exist in the backend (no graph router is registered), making the map permanently show "Failed to load track map data."

## What Changes

- **Auto-focus input on edit start**: When the user opens the traversal time editor (via pencil icon or clicking the value), the input field will be programmatically focused so that clicking outside triggers the existing `blur` → `save` flow.
- **Fix track map data source**: Replace the non-existent `GET /api/graph` call with a working data source. The schedule editor already gets graph data from `GET /api/services/{id}` (the `graph` field). The config page needs to fetch graph data from an endpoint that actually exists — either add a `GET /api/graph` backend route, or reuse graph data from the service detail.

## Non-goals

- No changes to the track map d3.js rendering logic (it works correctly once data is provided).
- No changes to the schedule editor's track map.
- No changes to block config validation logic.

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `click-outside-dismiss`: Input must be auto-focused when editing starts so blur-based dismiss actually works.
- `track-map-geometry`: Config page track map must load graph data from a working API endpoint.

## Impact

- **Components**: `BlockConfigComponent` (auto-focus), `TrackMapOverviewComponent` (data source)
- **Services**: `GraphService` — either fix the endpoint URL or add a backend `GET /api/graph` route
- **Backend**: May need a new `GET /api/graph` route (preferred), or frontend works around it
