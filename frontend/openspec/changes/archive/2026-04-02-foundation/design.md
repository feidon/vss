## Context

Greenfield Angular 21 project with only the CLI scaffold in place. The backend API is stable and fully documented. This change establishes the shared layer that all feature changes depend on.

## Goals / Non-Goals

**Goals:**
- Define TypeScript types that mirror backend API schemas exactly
- Provide thin service wrappers around each endpoint group
- Set up app shell with navigation and lazy-loaded routes
- Establish the `core/` → `shared/` → `features/` directory convention

**Non-Goals:**
- No caching, retry, or offline support
- No global error/loading interceptors (defer until needed)
- No feature logic in placeholder components

## Decisions

### 1. API types live in `shared/models/`

All TypeScript interfaces/types matching backend responses go in `src/app/shared/models/`. One file per domain concept: `node.ts`, `block.ts`, `service.ts`, `graph.ts`, `conflict.ts`.

**Why:** Shared across all features. Flat structure keeps imports short. Barrel export via `index.ts`.

**Alternative considered:** Colocate types with the service that uses them. Rejected — multiple features need the same types.

### 2. One service per endpoint group in `core/services/`

- `GraphService` — `GET /graph`
- `BlockService` — `GET /blocks`, `PATCH /blocks/{id}`
- `ServiceService` — `POST /services`, `GET /services`, `GET /services/{id}`, `PATCH /services/{id}/route`, `DELETE /services/{id}`

Each service injects `HttpClient` directly. No base `ApiService` class — that's premature abstraction for three small services.

**Why:** Keeps each service focused and independently testable. The base URL is a single constant or `environment` value.

**Alternative considered:** Single `ApiService` with all endpoints. Rejected — becomes a god service as features grow.

### 3. App shell: simple header nav + router-outlet

Minimal layout: horizontal nav bar with links to Editor, Viewer, Blocks, Map. `<router-outlet>` below. Tailwind utility classes only.

**Why:** Simplest thing that works. No sidebar needed for four routes.

**Alternative considered:** Sidebar layout. Rejected — overkill for four pages in an interview assignment.

### 4. Lazy-loaded routes with placeholder components

Each feature gets a route that lazy-loads its component:
```
/editor  → ScheduleEditorComponent (placeholder)
/viewer  → ScheduleViewerComponent (placeholder)
/blocks  → BlockConfigComponent (placeholder)
/map     → TrackMapComponent (placeholder)
```
Default redirect: `/editor` (the core feature).

**Why:** Lazy loading is free with Angular standalone components and establishes the pattern for when real feature code lands.

### 5. Epoch seconds as `number`, not `Date`

Timetable times stay as `number` (Unix epoch seconds) in API types. Feature components convert to display format as needed.

**Why:** Matches backend exactly. Avoids premature conversion that complicates PATCH payloads. Features can format for display locally.

## Risks / Trade-offs

- **Backend URL hardcoded** → Acceptable for interview scope. Use `environment.ts` if it becomes a problem.
- **No error handling in services** → Services return raw `Observable<T>`. Features handle errors at the call site. This is intentional — avoids interceptor complexity for now.
- **`ServiceService` naming** → Slightly awkward name. Alternatives (`ScheduleService`, `TrainServiceService`) are worse. Keeping it consistent with the backend resource name.
