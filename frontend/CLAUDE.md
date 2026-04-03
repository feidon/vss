# VSS Frontend

## Tech Stack

- Angular 21 (standalone components, signals)
- TypeScript 5.9 (strict mode)
- Tailwind CSS 4 (via PostCSS)
- Vitest (unit tests)
- d3.js (interactive track map)
- Prettier (100 char, single quotes)

## Architecture

Feature-based structure with standalone components:

```
src/app/
├── core/           # Singleton services (API clients, interceptors, guards)
├── shared/         # Shared components, pipes, directives, API models/types
├── features/
│   ├── schedule-editor/    # Create/edit/delete services
│   ├── schedule-viewer/    # Read-only schedule display
│   ├── block-config/       # Block traversal time configuration
│   └── track-map/          # d3.js interactive track visualization (bonus)
└── app.routes.ts
```

- Standalone components (no NgModules)
- Angular signals for reactive state
- Lazy-loaded feature routes
- Services handle API calls; components handle presentation

## Pages

### Schedule Editor (core)
- Create, edit, and delete services
- Define service path: select platform stops, intermediate blocks are auto-filled via backend route finder
- Define timetable: set arrival/departure times per node
- Assign vehicle (V1, V2, V3) to service
- PATCH `/services/{id}/route` for updates — handle 409 conflict responses and display conflict details to user

### Schedule Viewer (core)
- Read-only view of all scheduled services
- Display timetable per service with arrival/departure times
- Filter/group by vehicle

### Block Configuration (core)
- List all blocks with current traversal times
- Edit traversal time per block via PATCH `/blocks/{id}`

### Interactive Track Map (bonus)
- d3.js visualization of the track network
- 14 blocks (B1-B14), 4 stations (Y, S1, S2, S3), 6 platforms
- Show block directionality and interlocking groups
- Highlight active services on the network

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

**Service list** (GET `/services`):
```json
{ "id": 101, "name": "S101", "vehicle_id": "uuid" }
```

**Service detail** (GET `/services/{id}`):
```json
{ "id": 101, "name": "S101", "vehicle_id": "uuid", "route": [Node], "timetable": [TimetableEntry], "graph": GraphResponse }
```

**TimetableEntry**:
```json
{ "order": 0, "node_id": "uuid", "arrival": 1700000000, "departure": 1700000030 }
```

**Route Update Request** (PATCH `/services/{id}/route`):
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
    "low_battery_conflicts": [{ "service_id": 1 }],
    "insufficient_charge_conflicts": [{ "service_id": 1 }]
  }
}
```

## Running

```bash
# Local development
export DATABASE_URL=postgresql+asyncpg://vss:vss@localhost:5432/vss
npm install
ng serve              # Frontend on http://localhost:4200

# Docker (production-like)
docker compose up     # App on http://localhost:80
```

## Testing

```bash
ng test          # Unit tests (Vitest)
```

## Conventions

- Strict TypeScript — no `any`, no implicit returns
- Tailwind utility classes for styling
- Immutable state updates
- Conventional commits: feat, fix, refactor, docs, test, chore
