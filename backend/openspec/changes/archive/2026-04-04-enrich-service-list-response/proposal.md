## Why

The frontend viewer page needs to display start time, origin, and destination for each service in the list view. The current `GET /api/services` response only returns `{id, name, vehicle_id, vehicle_name}`, forcing the frontend to fetch every service's detail individually — an N+1 problem that degrades UX as service count grows.

## What Changes

- Add `start_time` (epoch seconds), `origin_name` (string), and `destination_name` (string) to each item in the `GET /api/services` list response
- All three fields are derived from existing persisted data (`timetable[0].arrival`, first/last route node names) — no schema migration needed
- Fields are nullable to handle services with no route yet (newly created)

## Capabilities

### New Capabilities

- `service-list-summary`: Enrich the service list endpoint with summary fields (start time, origin, destination) derived from existing route and timetable data

### Modified Capabilities

_(none — no existing spec-level requirements change)_

## Impact

- **API**: `GET /api/services` response shape changes (additive — new optional fields)
- **Code**: `ServiceResponse` schema, `ServiceAppService.list_services()` or route handler, and corresponding tests
- **No DB migration**: all data already persisted in route/timetable JSONB columns
