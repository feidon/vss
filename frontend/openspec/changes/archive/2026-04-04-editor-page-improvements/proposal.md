## Why

The schedule editor has two bugs that break the editing workflow for existing services. When a user navigates to an already-created service, the stop queue and start time are not populated from the existing route/timetable — forcing users to re-enter everything. Additionally, when a route update triggers a 409 conflict response, the conflict details are not displayed to the user, leaving them with no feedback on what went wrong.

## What Changes

- **Fix initial state loading**: When entering the editor for an existing service with a route, derive and populate the stop queue (filter `route` for `type !== "block"`), dwell times (`departure - arrival` per timetable entry), and start time (`timetable[0].arrival`) from the service detail response. The `deriveInitialState()` method in `RouteEditorComponent` exists but isn't working correctly.
- **Fix conflict message display**: When `PATCH /api/services/{id}/route` returns 409, parse the conflict response and display it via `ConflictAlertComponent`. The wiring exists in `ScheduleEditorComponent` but the conflict alert is not rendering. Investigate whether the error response shape (`err.error.detail`) matches the `ConflictResponse` interface.

## Non-goals

- No backend API changes needed — both fixes are frontend-only.
- No UI redesign of the editor layout or back button.
- No new features (track map interaction, validation preview, etc.).

## Capabilities

### New Capabilities

_(none — these are bug fixes to existing capabilities)_

### Modified Capabilities

_(no spec-level requirement changes — the existing specs already define this behavior; the implementation is just broken)_

## Impact

- **Components**: `RouteEditorComponent` (route-editor.ts), `ScheduleEditorComponent` (schedule-editor.ts)
- **Models**: Potentially `ConflictResponse` if the interface doesn't match the API response shape
- **Tests**: Existing specs for `schedule-editor` and route-editor may need updates to cover the fixed behavior
