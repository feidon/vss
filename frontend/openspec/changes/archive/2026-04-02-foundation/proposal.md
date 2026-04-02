## Why

The Angular project is scaffolded but contains no application code. Every feature (schedule editor, viewer, block config) needs shared API types, HTTP services, and an app shell with navigation. Without this foundation layer, feature work cannot begin.

## What Changes

- Add TypeScript interfaces matching all backend API response/request shapes (Node discriminated union, Service, Block, TimetableEntry, Vehicle, Station, GraphResponse, conflict types)
- Create `core/` services: `ApiService` (base HTTP client), `GraphService`, `BlockService`, `ServiceService` wrapping each backend endpoint group
- Create app shell with top-level navigation (sidebar or header) and `<router-outlet>`
- Configure lazy-loaded routes for each feature area: `/editor`, `/viewer`, `/blocks`, `/map`
- Add placeholder components for each feature route

## Non-goals

- No feature logic — editor, viewer, block-config, and track-map are separate changes
- No state management beyond what Angular signals and services provide
- No authentication or authorization
- No error interceptor or global loading state (add when needed)

## Capabilities

### New Capabilities
- `api-models`: TypeScript interfaces for all backend API types (request and response shapes)
- `api-services`: Angular HttpClient services wrapping each backend endpoint group
- `app-shell`: Application layout with navigation and lazy-loaded feature routes

### Modified Capabilities

(none — greenfield project)

## Impact

- New files in `src/app/core/` (services), `src/app/shared/` (models/types), and `src/app/` (shell, routes)
- Placeholder components in each `src/app/features/*/` directory
- `app.routes.ts` updated with lazy-loaded feature routes
- `app.ts` and `app.html` replaced with shell layout
