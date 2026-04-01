# VSS Frontend

## Tech Stack

- Angular (latest stable)
- Node.js LTS (managed via mise)
- d3.js (interactive track map)

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

Route update returns 409 with conflict details (block occupancy, interlocking, vehicle, battery).

## Running

```bash
npm install
ng serve
```

## Testing

```bash
ng test          # Unit tests (Karma)
ng e2e           # E2E tests
```
