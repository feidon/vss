## Why

The frontend workflow is: list services -> select one -> show service detail on the track graph. Currently `GET /graph` is a standalone endpoint returning the entire network, and `GET /services/{id}` returns only the service data (path + timetable) without any graph context. This forces the frontend to make two separate calls and stitch the data together. Embedding the graph inside the service detail response simplifies the client and matches the actual use case.

## What Changes

- **BREAKING**: Remove the standalone `GET /graph` endpoint entirely (route, schema, service wiring).
- Extend `GET /services/{id}` to include the full graph (nodes, connections, stations, vehicles) alongside the existing service fields.
- `GET /services` (list) remains unchanged — no graph data, just the service summary.
- `GraphAppService.get_graph()` moves from being called by the graph route to being called internally by the service detail route.

## Non-goals

- No changes to `GET /services` list response shape.
- No changes to write endpoints (`POST /services`, `PATCH /services/{id}/route`, `DELETE /services/{id}`, `POST /routes/validate`).
- No changes to the domain layer or graph data itself — only where it's served.

## Capabilities

### New Capabilities

- `service-detail-with-graph`: Extend `GET /services/{id}` to embed graph data (nodes, connections, stations, vehicles) in the response.

### Modified Capabilities

_(none — no existing spec-level requirements change)_

## Impact

- **API layer**: `api/graph/` routes and schemas removed; `api/service/schemas.py` and `api/service/routes.py` updated with graph fields.
- **Application layer**: `GraphAppService` may be inlined into `ServiceAppService.get_service()` or called as a dependency.
- **DI container**: `api/dependencies.py` updated to remove graph router wiring, inject graph dependencies into service router.
- **Tests**: Graph route tests removed; service detail tests updated to assert graph fields.
- **Frontend consumers**: Must switch from `GET /graph` + `GET /services/{id}` to single `GET /services/{id}`.
