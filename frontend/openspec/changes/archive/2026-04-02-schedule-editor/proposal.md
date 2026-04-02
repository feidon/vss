## Why

The schedule editor is the core feature of the VSS frontend. Users need to create vehicle services, define their routes by selecting platform stops, set timetables with arrival/departure times, assign vehicles, and update routes — handling 409 conflict responses from the backend. Without this, the application has no write functionality.

## What Changes

- Replace the `ScheduleEditorComponent` placeholder with a full CRUD page
- Service list view: display all services with name, vehicle, and stop count
- Create service form: name input + vehicle selector (from graph data)
- Route editor: select platform stops in order, backend auto-fills intermediate blocks
- Timetable display: show the computed path with arrival/departure times per node
- Route update: send PATCH with stops + start_time, display conflict details on 409
- Delete service with confirmation

## Non-goals

- No drag-and-drop reordering of stops (select in order is sufficient)
- No inline timetable time editing (backend computes times from stops + start_time)
- No real-time updates or WebSocket integration
- No undo/redo functionality

## Capabilities

### New Capabilities
- `service-list`: List all services with summary info, link to edit, delete action
- `service-form`: Create new services and edit route (stops + start_time)
- `conflict-display`: Parse and display 409 conflict response details to user

### Modified Capabilities

(none)

## Impact

- `src/app/features/schedule-editor/` — new components and local services
- Uses `ServiceService`, `GraphService` from `core/services/`
- Uses all model types from `shared/models/`
- Route remains `/editor`, no routing changes needed
