## Context

The schedule list page (`ScheduleListComponent`) currently supports manual service creation via `CreateServiceDialogComponent` and per-service edit/delete. The backend has a `POST /api/schedules/generate` endpoint that uses a constraint solver to auto-generate a conflict-free schedule, but the frontend has no way to trigger it. This endpoint **deletes all existing services** before generating new ones.

The existing dialog infrastructure uses Angular CDK Dialog with a consistent pattern: inject `DialogRef`/`DIALOG_DATA`, use signals for form state, and return a typed result on close.

## Goals / Non-Goals

**Goals:**
- Let users trigger auto-scheduling from the schedule list page
- Collect the four required parameters (interval, start time, end time, dwell time)
- Warn users clearly that this action is destructive (deletes all services)
- Show a success summary after generation completes
- Refresh the service list to reflect newly generated services

**Non-Goals:**
- Schedule preview or dry-run mode
- Incremental generation (keeping existing services)
- Custom route variant selection

## Decisions

### 1. New `ScheduleService` in `core/services/`

**Decision**: Create a dedicated `ScheduleService` rather than adding the generate method to `ServiceService`.

**Rationale**: The generate endpoint lives under `/api/schedules/`, not `/api/services/`. Keeping services aligned with API resource paths maintains the existing convention. `ServiceService` handles CRUD for individual services; schedule generation is a different concern.

**Alternative considered**: Adding `generate()` to `ServiceService` — rejected because it mixes resource boundaries and the endpoint prefix differs.

### 2. Standalone `AutoScheduleDialogComponent` in `features/schedule/`

**Decision**: Place the dialog component alongside `schedule-list.ts` and `create-service-dialog.ts` in the schedule feature directory.

**Rationale**: Follows the existing pattern — `CreateServiceDialogComponent` is co-located with `ScheduleListComponent` since it's only opened from there. Same applies here.

### 3. Time input via `datetime-local` HTML inputs

**Decision**: Use `<input type="datetime-local">` for start/end times, consistent with the route editor's existing time input pattern.

**Rationale**: The project already uses `localDatetimeToEpoch()` and `epochToLocalDatetime()` utilities in `time-utils.ts` for this conversion. Reuse them.

### 4. Two-phase dialog: form → confirmation

**Decision**: Single dialog with a warning banner always visible (not a separate confirmation step).

**Rationale**: A two-step flow adds complexity for four fields. A prominent destructive-action warning (amber/red banner with icon) within the form dialog is sufficient — the same pattern is used in the existing `ConfirmDialogComponent` for delete actions.

### 5. Success result shown in-dialog before closing

**Decision**: After successful generation, replace the form with a success summary (services created, vehicles used, cycle time) and a "Done" button that closes the dialog.

**Rationale**: Closing immediately loses the generation result. Showing it in-place lets the user read the summary before the list refreshes.

## Risks / Trade-offs

- **Destructive action without undo** → Mitigation: prominent warning text and distinct button styling (red/amber). The dialog title and warning explicitly state all services will be deleted.
- **Long solver computation** → Mitigation: disable form controls and show a loading spinner during the API call. The dialog cannot be dismissed while generating.
- **`SCHEDULE_INFEASIBLE` error** → Mitigation: display the error message in-dialog using the existing `ErrorAlertComponent` pattern. User can adjust parameters and retry.
