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

Base URL: `http://localhost:8000`

| Method | Path                       | Description                        |
|--------|----------------------------|------------------------------------|
| GET    | `/graph`                   | Full track network (nodes + edges) |
| GET    | `/blocks`                  | List all blocks                    |
| GET    | `/blocks/{id}`             | Get block by ID                    |
| PATCH  | `/blocks/{id}`             | Update traversal time              |
| POST   | `/services`                | Create service                     |
| GET    | `/services`                | List all services                  |
| GET    | `/services/{id}`           | Get service by ID                  |
| PATCH  | `/services/{id}/route`     | Update service route               |
| DELETE | `/services/{id}`           | Delete service                     |

### Key Response Schemas

**Node** (discriminated union by `type`):
```json
{ "type": "block|platform|yard", "id": "uuid", "name": "B1" }
```
Blocks additionally include: `group`, `traversal_time_seconds`

**Service**:
```json
{ "id": 101, "name": "S101", "vehicle_id": "uuid", "path": [Node], "timetable": [TimetableEntry] }
```

**TimetableEntry**:
```json
{ "order": 0, "node_id": "uuid", "arrival": 1700000000, "departure": 1700000030 }
```

**Route Update Request** (PATCH `/services/{id}/route`):
```json
{ "stops": [{ "platform_id": "uuid", "dwell_time": 30 }], "start_time": 1700000000 }
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
npm install
ng serve
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
