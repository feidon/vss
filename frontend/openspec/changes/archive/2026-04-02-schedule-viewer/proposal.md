## Why

The schedule-viewer route currently renders a placeholder heading with no functionality. Users need a read-only view to inspect all scheduled services — their timetables, paths, and vehicle assignments — without risk of accidental edits. This is a core page listed in the project requirements alongside the schedule editor.

## What Changes

- Replace the placeholder `ScheduleViewerComponent` with a full read-only schedule display
- Add a service list showing all services grouped/filterable by vehicle
- Add a timetable detail view displaying arrival/departure times per node for a selected service
- Reuse existing `ServiceService.getServices()` and `GraphService.getGraph()` for data fetching — no new API calls needed

## Non-goals

- Editing, creating, or deleting services (that's the schedule-editor)
- Real-time updates or polling for schedule changes
- Conflict detection or display (read-only context, no route mutations)
- Export or print functionality

## Capabilities

### New Capabilities

- `schedule-list`: Filterable list of all services with vehicle assignment, grouped by vehicle
- `timetable-display`: Read-only timetable view for a selected service showing ordered nodes with arrival/departure times

### Modified Capabilities

_(none)_

## Impact

- **Components**: `ScheduleViewerComponent` (rewrite from placeholder), new child components for list and timetable
- **Services**: Consumes existing `ServiceService` and `GraphService` — no modifications needed
- **Models**: Uses existing `ServiceResponse`, `TimetableEntry`, `GraphResponse`, `Node` types from `src/app/shared/models/`
- **Routes**: No changes — `/viewer` route already wired in `app.routes.ts`
