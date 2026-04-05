## Why

There is no way for users to auto-generate a full schedule from the UI. Currently, services must be created and routed one-by-one manually. The backend already exposes `POST /api/schedules/generate` which computes an optimal schedule using a constraint solver, but the frontend has no trigger for it. Adding this lets users generate a complete timetable in one action.

## What Changes

- Add an "Auto Schedule" button to the `ScheduleListComponent` header (next to "Create Service")
- Create a new `AutoScheduleDialogComponent` that collects four parameters: service interval, start time, end time, and dwell time
- Display a destructive-action warning in the dialog: generating a schedule **deletes all existing services**
- On confirm, call `POST /api/schedules/generate` and show a success summary (services created, vehicles used, cycle time)
- Add a `ScheduleService` (or extend existing service layer) to wrap the generate endpoint
- Refresh the service list after successful generation

## Non-goals

- Editing individual generated services from this dialog
- Previewing the generated schedule before confirming
- Partial generation (keeping some existing services)

## Capabilities

### New Capabilities

- `auto-schedule-dialog`: Dialog component for collecting generation parameters, displaying the destructive warning, calling the backend generate API, and showing the result summary
- `schedule-api`: Frontend service integration for `POST /api/schedules/generate` endpoint

### Modified Capabilities

_(none)_

## Impact

- **Components**: `ScheduleListComponent` (add button), new `AutoScheduleDialogComponent`
- **Services**: New API method in service layer for the generate endpoint
- **Models**: New request/response interfaces for generate schedule
- **Dependencies**: Uses existing `@angular/cdk/dialog` pattern (same as create-service and confirm dialogs)
