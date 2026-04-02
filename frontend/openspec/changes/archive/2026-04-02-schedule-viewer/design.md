## Context

The schedule-viewer feature is a core page in the VSS frontend that currently renders a placeholder `<h2>`. The schedule-editor already implements service listing with vehicles, so there's an established pattern for fetching and displaying services via `ServiceService` and `GraphService`. The viewer needs a read-only counterpart focused on timetable inspection.

Existing infrastructure:
- `ServiceService.getServices()` / `getService(id)` — fetch services with path and timetable
- `GraphService.getGraph()` — provides vehicle names for UUID→name resolution
- `ServiceResponse`, `TimetableEntry`, `Vehicle`, `Node` models already defined in `shared/models/`
- Route `/viewer` already wired with lazy loading in `app.routes.ts`

## Goals / Non-Goals

**Goals:**
- Read-only display of all services with timetable details
- Filter and group services by vehicle assignment
- Show arrival/departure times formatted as human-readable time (HH:mm:ss)
- Follow established component patterns from schedule-editor (signals, standalone, Tailwind)

**Non-Goals:**
- Any mutation of services (create/edit/delete)
- Real-time refresh or polling
- Conflict visualization
- Service path visualization on the track map

## Decisions

### 1. Container + presentational component split

**Decision**: `ScheduleViewerComponent` (container) owns data fetching and state. Two presentational children: `ViewerServiceListComponent` (service table with filter) and `TimetableDetailComponent` (timetable for selected service).

**Rationale**: Mirrors the schedule-editor pattern (`ScheduleEditorComponent` → `ServiceListComponent`, `RouteEditorComponent`). Keeps presentation testable without HTTP mocking.

**Alternative considered**: Single monolithic component — rejected because it violates the project's established separation and makes unit testing harder.

### 2. Angular signals for state, not NgRx or service-based stores

**Decision**: Use component-level `signal()` for services list, selected service, and filter state. No shared state store.

**Rationale**: The viewer is self-contained with no cross-feature state sharing needs. Signals are already the project's standard (see schedule-editor). Adding a store would be overengineering for read-only data.

### 3. Vehicle filter via computed signal

**Decision**: A `vehicleFilter` signal holds the selected vehicle ID (or `null` for "all"). A `filteredServices` computed signal derives the visible list.

**Rationale**: Computed signals automatically re-derive on dependency changes, keeping the template declarative. No manual subscription management needed.

**Alternative considered**: Pipe-based filtering in template — rejected because computed signals are more testable and align with Angular 21 best practices.

### 4. Epoch seconds → HH:mm:ss formatting via pure pipe

**Decision**: Create a shared `EpochTimePipe` in `shared/` that transforms epoch seconds to `HH:mm:ss` format using `Date`.

**Rationale**: Timetable times are epoch seconds (per API). A pipe keeps formatting reusable (schedule-editor could also use it later) and testable in isolation. Pure pipes are performant with signal-driven change detection.

**Alternative considered**: Formatting in the component — rejected because it mixes presentation logic into the component and isn't reusable.

### 5. Group-by-vehicle mode via toggle

**Decision**: A toggle button switches between flat list and grouped-by-vehicle display. Grouping is computed from the services signal.

**Rationale**: The requirements call for both filter and group by vehicle. A toggle keeps the UI simple while supporting both use cases.

## Risks / Trade-offs

- **Large service count**: If many services exist, the full list loads at once. This is acceptable for the assignment scope (small dataset). → Mitigation: pagination could be added later if needed.
- **Stale data**: Viewer doesn't auto-refresh. If another user modifies services via the editor, the viewer shows stale data until page reload. → Mitigation: acceptable for interview scope; manual refresh button could be added.
- **Naming collision with editor's `ServiceListComponent`**: Both features have a service list. → Mitigation: prefix the viewer's component as `ViewerServiceListComponent` to avoid ambiguity in imports and debugging.
