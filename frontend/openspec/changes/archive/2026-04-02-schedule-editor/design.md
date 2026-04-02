## Context

The foundation layer is in place: API types, services (`ServiceService`, `GraphService`), and the placeholder `ScheduleEditorComponent` at route `/editor`. The backend provides route computation — the frontend sends platform stops + start_time, the backend returns the full path with timetable. On conflict, the backend returns 409 with detailed conflict info.

## Goals / Non-Goals

**Goals:**
- Full service CRUD (create, read/list, update route, delete)
- Clean separation: container component orchestrates, presentational components render
- Display conflict details from 409 responses in a readable format

**Non-Goals:**
- No state management library (signals + service calls are sufficient)
- No optimistic updates
- No pagination (small dataset — ~10s of services)

## Decisions

### 1. Component structure: container + presentational

```
schedule-editor/
├── schedule-editor.ts        # Container: orchestrates data loading + actions
├── service-list.ts           # Presentational: table of services
├── service-form.ts           # Presentational: create form (name + vehicle)
├── route-editor.ts           # Presentational: stop selector + start time
└── conflict-alert.ts         # Presentational: renders conflict details
```

`ScheduleEditorComponent` is the smart container. It holds signals for the services list, graph data, selected service, and error state. Child components receive data via inputs and emit events via outputs.

**Why:** Keeps business logic in one place. Presentational components are easy to test and reuse (e.g., conflict-alert could be reused in schedule-viewer later).

**Alternative considered:** One big component. Rejected — would exceed 400 lines quickly given the form + list + conflict display.

### 2. Workflow: list → create → edit route

The editor page shows the service list by default. User flow:

1. **List view** — table of services. Each row has Edit and Delete buttons.
2. **Create** — inline form above the list (name + vehicle dropdown). On submit, calls `POST /services`, then navigates to route editing for the new service.
3. **Edit route** — shows the selected service's current path. User selects platform stops (checkboxes from graph stations), sets start_time, and submits via `PATCH /services/{id}/route`.
4. **Conflict** — if 409, display conflict details in an alert below the form. User adjusts and retries.
5. **Delete** — confirmation dialog, then `DELETE /services/{id}`.

**Why:** Single-page flow avoids extra routes. The service count is small enough that a list + inline edit works well.

**Alternative considered:** Separate routes for list/create/edit. Rejected — adds routing complexity for a small page.

### 3. Platform stop selection from graph data

Load graph via `GraphService.getGraph()` on init. Extract stations (non-yard) and their platforms. Present as a sequential picker: user adds stops one at a time from a dropdown, building an ordered list.

**Why:** The backend computes intermediate blocks — frontend only needs to send platform_ids in order. A dropdown per stop is simpler than a drag-and-drop interface.

### 4. Start time as datetime-local input

Use an HTML `<input type="datetime-local">` for start_time. Convert to/from epoch seconds on submit/display.

**Why:** Native browser input is good enough. No date library needed for a single input.

### 5. Conflict display: grouped by type

Show conflicts in a dismissable alert panel, grouped by conflict type (vehicle, block, interlocking, battery). Each group shows a human-readable summary.

**Why:** The 409 response has 5 conflict arrays. Grouping makes it scannable. User needs to understand what went wrong to adjust their route.

### 6. Dwell time: fixed default with per-stop override

Each stop gets a default dwell_time of 30 seconds. User can adjust per stop in the route editor.

**Why:** Simplest approach. The backend accepts any non-negative integer, so a sensible default reduces friction.

## Risks / Trade-offs

- **Graph data loaded on every editor visit** → Acceptable for small dataset. Could cache in a signal service later if needed.
- **No form validation library** → Using Angular reactive forms with built-in validators. Sufficient for name (required) and start_time (required).
- **Single-page complexity** → The container component may grow. Mitigated by extracting presentational components aggressively.
