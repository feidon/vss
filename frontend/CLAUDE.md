# VSS Frontend

## Tech Stack

- Angular 21 (standalone components, signals)
- TypeScript 5.9 (strict mode)
- Tailwind CSS 4 (via PostCSS)
- RxJS 7.8 (async streams)
- Vitest 4.0 + jsdom (unit tests)
- d3.js (interactive track map)
- ESLint + angular-eslint (linting)
- Prettier (100 char, single quotes)

## Architecture

Feature-based structure with standalone components:

```
src/app/
├── core/services/  # Singleton API client services (HttpClient)
├── shared/
│   ├── models/     # TypeScript interfaces (Block, Service, Node, Graph, Conflict)
│   └── pipes/      # EpochTimePipe (Unix timestamp → HH:MM:SS)
├── features/
│   ├── schedule/           # Schedule list, editor, track-map-editor
│   └── config/             # Block config table + track map overview
└── app.routes.ts           # Lazy-loaded feature routes
```

- Standalone components (no NgModules)
- Angular signals for reactive state (`signal()`, `computed()`)
- `input()` / `output()` for component communication
- Services use `inject(HttpClient)` with typed API responses
- Lazy-loaded feature routes

## Routes

| Path              | Component               | Description                          |
|-------------------|-------------------------|--------------------------------------|
| `/schedule`       | ScheduleListComponent   | Service list (default)               |
| `/schedule/:id/edit` | ScheduleEditorComponent | Edit service route and timetable  |
| `/config`         | ConfigComponent         | Block config table + track map       |

## Pages

### Schedule List
- List all scheduled services
- Expandable rows showing route path
- Navigate to editor for each service

### Schedule Editor
- Edit service route: select platform stops, intermediate blocks auto-filled via backend
- Set dwell times per stop and start time
- Assign vehicle (V1, V2, V3) to service
- PATCH `/api/services/{id}/route` for updates — handle 409 conflict responses
- Interactive d3.js track map for stop selection

### Config
- **Block Configuration**: list all blocks grouped by interlocking group, inline editing of traversal times, pencil icon toggle, click-outside saves
- **Track Map Overview**: read-only d3.js visualization of the track network (14 blocks, 6 platforms, 1 yard)

## Backend API

Base URL: configured via environment files (`src/environments/`).
- Dev (`ng serve`): `http://localhost:8000/api`
- Production (Docker): `/api` (relative, proxied by nginx)

| Method | Path                       | Description                        |
|--------|----------------------------|------------------------------------|
| GET    | `/api/vehicles`            | List all vehicles                  |
| GET    | `/api/blocks`              | List all blocks                    |
| PATCH  | `/api/blocks/{id}`         | Update traversal time              |
| POST   | `/api/services`            | Create service                     |
| GET    | `/api/services`            | List all services (summary only)   |
| GET    | `/api/services/{id}`       | Get service detail (incl. graph)   |
| PATCH  | `/api/services/{id}/route` | Update service route               |
| DELETE | `/api/services/{id}`       | Delete service                     |
| POST   | `/api/routes/validate`     | Validate route for conflicts       |

### Key Response Schemas

**Node** (discriminated union by `type`):
```json
{ "type": "block|platform|yard", "id": "uuid", "name": "B1", "x": 0.0, "y": 0.0 }
```
Blocks additionally include: `group`, `traversal_time_seconds`

**Service list** (GET `/api/services`):
```json
{ "id": 101, "name": "S101", "vehicle_id": "uuid", "vehicle_name": "V1" }
```

**Service detail** (GET `/api/services/{id}`):
```json
{ "id": 101, "name": "S101", "vehicle_id": "uuid", "route": [Node], "timetable": [TimetableEntry], "graph": GraphResponse }
```

**TimetableEntry**:
```json
{ "order": 0, "node_id": "uuid", "arrival": 1700000000, "departure": 1700000030 }
```

**Route Update Request** (PATCH `/api/services/{id}/route`):
```json
{ "stops": [{ "node_id": "uuid", "dwell_time": 30 }], "start_time": 1700000000 }
```

**409 Conflict Response** (route update):
```json
{
  "detail": {
    "message": "Conflicts detected",
    "vehicle_conflicts": [{ "vehicle_id": "uuid", "service_a_id": 1, "service_b_id": 2, "reason": "Overlapping time windows" }],
    "block_conflicts": [{ "block_id": "uuid", "service_a_id": 1, "service_b_id": 2, "overlap_start": 170000, "overlap_end": 170030 }],
    "interlocking_conflicts": [{ "group": 1, "block_a_id": "uuid", "block_b_id": "uuid", "service_a_id": 1, "service_b_id": 2, "overlap_start": 170000, "overlap_end": 170030 }],
    "battery_conflicts": [{ "type": "low_battery", "service_id": 1 }]
  }
}
```
`battery_conflicts[].type` is `"low_battery"` or `"insufficient_charge"`.

**Route Validation Request** (POST `/api/routes/validate`):
```json
{ "vehicle_id": "uuid", "stops": [{ "node_id": "uuid", "dwell_time": 30 }], "start_time": 1700000000 }
```

**Route Validation Response**:
```json
{ "route": ["uuid", "uuid", "..."], "battery_conflicts": [{ "type": "low_battery", "service_id": 1 }] }
```

## Running

```bash
npm install
ng serve              # Frontend on http://localhost:4200

# Docker (full stack)
docker compose up     # App on http://localhost
```

## Testing

```bash
ng test          # Unit tests (Vitest, no-watch in CI)
ng lint          # ESLint
npx prettier --check "src/**/*.{ts,html,css}"  # Prettier check
```

## Conventions

- Strict TypeScript — no `any`, no implicit returns, `noImplicitOverride`
- Tailwind utility classes for styling
- Immutable state updates
- Component selector prefix: `app-`
- Conventional commits: feat, fix, refactor, docs, test, chore
