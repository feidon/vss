## Context

The schedule list (`ScheduleListComponent`) displays services in a flat table. Each row shows name, vehicle, start time, origin, destination, and action buttons. There is no way to see the full route without navigating to the editor.

The service detail endpoint (`GET /api/services/{id}`) already returns the full `route: Node[]` array with node names and types. No backend changes are needed.

## Goals / Non-Goals

**Goals:**
- Allow users to expand any service row to see its full route path inline
- Fetch service detail lazily on first expand, cache for subsequent toggles
- Keep the existing table layout and action buttons working

**Non-Goals:**
- No new components — the expand panel lives inside `ScheduleListComponent`'s template
- No timetable display in the expanded row (that's the editor's job)
- No changes to edit/delete flows

## Decisions

### 1. Expand state as a signal of expanded service ID

Store `expandedServiceId = signal<number | null>(null)`. Clicking a row sets it (or clears it if already expanded). This is simpler than a Set of expanded IDs since only one row expands at a time — consistent with accordion UX.

**Alternative considered:** `Set<number>` for multi-expand. Rejected — the list is compact and multi-expand would clutter the view with no clear benefit.

### 2. Cache detail responses in a Map signal

Use `detailCache = signal<ReadonlyMap<number, ServiceDetailResponse>>(new Map())`. On expand, check cache first; if miss, fetch and update the map immutably. This avoids re-fetching when collapsing and re-expanding.

**Alternative considered:** Re-fetch every time. Rejected — adds unnecessary latency and server load for data that doesn't change during a list view session.

### 3. Route display as arrow-joined node names

Map `route: Node[]` to `node.name` and join with ` → `. This produces `Y → B1 → B3 → P2A` which is compact and readable. Show in a single line inside a `<td colspan="6">` row beneath the service row.

**Alternative considered:** Show only stops (filter out blocks). Rejected — the TODO explicitly says "simple path Y → B1 → P1A" which includes blocks.

### 4. Click handler on `<tr>` with stopPropagation on buttons

The row `<tr>` gets a `(click)="toggleExpand(service)"` handler. The existing Edit and Delete buttons already use `$event.stopPropagation()`, so they won't trigger expansion.

## Risks / Trade-offs

- **Long routes overflow** → The path string could be long for services with many blocks. Mitigation: use `text-wrap` and `break-words` in the expanded row. The typical route is 4-8 nodes, so this is unlikely to be an issue.
- **Stale cache** → If user edits a service in another tab, the cached detail becomes stale. Acceptable for a single-user system. The cache is cleared on `loadServices()` (list refresh).
