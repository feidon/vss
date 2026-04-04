## Why

The schedule list currently shows only summary columns (name, vehicle, start time, origin, destination). Users cannot see the full route without navigating to the editor. Clicking any row should expand inline to show a simplified path (e.g., Y → B1 → B3 → P1A), giving quick context without leaving the list.

## What Changes

- **Expandable rows**: Clicking anywhere on a service row toggles an expansion panel showing the route path as a node-name chain (e.g., `Y → B1 → B3 → P2A`).
- **Lazy-fetch detail**: On first expand, fetch `GET /api/services/{id}` to retrieve the full route. Cache the result so subsequent toggles don't re-fetch.
- **Collapse on re-click**: Clicking an expanded row collapses it.

## Non-goals

- No changes to the editor or delete flows — those already work.
- No new backend endpoints — the existing service detail endpoint provides the route.
- No filtering, sorting, or grouping changes to the list.

## Capabilities

### New Capabilities

- `expandable-service-row`: Click-to-expand rows in the schedule list that display the full route path inline, with lazy-loaded service detail.

### Modified Capabilities

_(none)_

## Impact

- **ScheduleListComponent** (`features/schedule/schedule-list.ts`) — add expand/collapse state, detail fetching, and expanded row template.
- **ServiceService** (`core/services/service.service.ts`) — already has `getService(id)`, no changes needed.
- **ServiceDetailResponse model** (`shared/models/service.ts`) — already has `route: Node[]`, no changes needed.
