## Why

The current UI has 4 top-level tabs (Editor, Viewer, Blocks, Map) which fragments the workflow. The editor and viewer are separate pages for the same data, and the track map is an empty placeholder. Users must navigate between tabs to create and then view services. Consolidating into 2 pages — a schedule viewer (with inline editing) and a configuration page — simplifies navigation and makes the track map the primary route-building interface.

## What Changes

- **Reduce navigation from 4 tabs to 2**: "Schedule" (default) and "Config"
- **Merge editor into viewer**: The schedule list becomes the entry point; clicking a service or "Create" opens an editor sub-page
- **Add "Create Service" dialog**: Modal dialog on the schedule page to set name, vehicle, and start time before entering the editor
- **Editor becomes a child route**: `/schedule/:id/edit` instead of a separate top-level `/editor` route
- **Track map as the route editor**: Replace the current stop-list route editor with a d3.js track map where users click platforms/yards to build the route queue
- **Config page combines blocks + map**: Block traversal time editing and a read-only track overview in one page

## Non-goals

- No backend API changes — all data is already available
- No new conflict detection logic — existing 409 handling is reused
- No changes to the block-config editing logic itself (just relocated)

## Capabilities

### New Capabilities

- `create-service-dialog`: Modal dialog for creating a new service (name, vehicle, start time selection)
- `track-map-editor`: Interactive d3.js track map for building service routes by clicking platforms/yards

### Modified Capabilities

- `app-shell`: Navigation restructured from 4 tabs to 2 ("Schedule", "Config"); default route changes to `/schedule`
- `service-list`: Moves from editor feature into the schedule viewer; gains "Create Service" button; becomes the main schedule page
- `service-form`: Replaced by the create-service-dialog modal (name + vehicle + start time in one step)

## Impact

- **Routes**: `/editor` and `/viewer` replaced by `/schedule` (list) and `/schedule/:id/edit` (editor). `/blocks` and `/map` merged into `/config`.
- **Components**: `ScheduleEditorComponent` and `ScheduleViewerComponent` consolidated. `ServiceFormComponent` replaced by dialog. `RouteEditorComponent` refactored to use track map.
- **Feature directories**: `schedule-editor/` and `schedule-viewer/` merge into `schedule/`. `block-config/` and `track-map/` merge into `config/`.
- **No API changes**: All existing endpoints and models remain unchanged.
