## Context

The frontend use case is: list services (summary only) -> select one -> view service detail overlaid on the track graph. Today the graph lives behind a standalone `GET /graph` endpoint and service detail behind `GET /services/{id}`. The client must call both and join them. Since the graph is only ever consumed alongside a specific service, we can embed it in the service detail response and remove the standalone graph endpoint.

Current flow:
```
Frontend -> GET /services          (list, no graph)
Frontend -> GET /services/{id}     (detail, no graph)
Frontend -> GET /graph             (full network)
```

Target flow:
```
Frontend -> GET /services          (list, no graph — unchanged)
Frontend -> GET /services/{id}     (detail + full graph embedded)
```

## Goals / Non-Goals

**Goals:**
- Embed graph data (nodes, connections, stations, vehicles) in `GET /services/{id}` response.
- Remove standalone `GET /graph` endpoint, router, and associated wiring.
- Keep the change minimal — reuse existing `GraphAppService` and schemas.

**Non-Goals:**
- Changing the service list endpoint shape.
- Modifying write endpoints or conflict detection logic.
- Filtering graph data to only the nodes relevant to a service (full graph is small and always needed for the UI).

## Decisions

### 1. Compose `GraphAppService` into `ServiceAppService` via constructor injection

**Rationale:** `GraphAppService` already encapsulates all repository calls for graph data. Rather than duplicating those calls in `ServiceAppService`, inject `GraphAppService` as a dependency. This keeps the application layer clean and avoids `ServiceAppService` depending on five extra repositories directly.

**Alternative considered:** Inline the graph repository calls directly in `ServiceAppService.get_service()`. Rejected because it couples the service layer to graph repository details and makes the method harder to read.

### 2. New `ServiceDetailResponse` schema (extends `ServiceResponse` with graph fields)

**Rationale:** `GET /services` returns `list[ServiceResponse]` (no graph). `GET /services/{id}` needs graph fields. Adding graph fields to `ServiceResponse` would bloat the list response with null/empty graph data. A dedicated `ServiceDetailResponse` keeps the list lightweight and the detail self-contained.

**Alternative considered:** Use a single `ServiceResponse` with optional graph fields. Rejected because it makes the list endpoint schema misleading (graph fields always null in list context).

### 3. Remove `api/graph/` package entirely

**Rationale:** With graph data served from the service detail endpoint, the standalone graph router has no consumers. Keeping dead code adds maintenance cost. `GraphAppService` and its DTOs remain in `application/graph/` since they're still used internally.

## Risks / Trade-offs

- **Breaking change for frontend** → The frontend must update to use `GET /services/{id}` for graph data. Since the frontend is not yet built (TBD), this is low risk.
- **Slightly larger service detail response** → Graph data (~14 blocks, 6 platforms, connections) is small. No performance concern.
- **Coupling graph retrieval to service detail** → If a future use case needs graph data without a service context, we'd need to re-add a graph endpoint. Acceptable risk given current requirements.
