## Context

The `ConflictAlertComponent` receives a `ConflictResponse` containing raw UUIDs for blocks (`block_id`, `block_a_id`, `block_b_id`) and vehicles (`vehicle_id`), plus numeric service IDs (`service_a_id`, `service_b_id`). It displays these directly in the template, making the conflict details unreadable to operators who think in terms of "B3", "V1", "S101".

The `GraphResponse` already contains all the lookup data needed: `nodes[]` has block/platform/yard names, `vehicles[]` has vehicle names. The parent `ScheduleEditorComponent` has access to this graph via `service().graph`.

## Goals / Non-Goals

**Goals:**
- Display human-readable names (block names, vehicle names, service names) in the conflict alert
- Keep the conflict-alert component presentational (dumb) — it receives data, not services

**Non-Goals:**
- Changing backend response format
- Adding a dedicated name-resolution service
- Highlighting conflicts on the track map

## Decisions

### 1. Pass graph as an additional input to ConflictAlertComponent

**Decision**: Add a `graph` input to `ConflictAlertComponent` and build internal lookup maps (id → name) from `graph.nodes` and `graph.vehicles`.

**Rationale**: The graph is already loaded and available in the parent. Passing it as an input keeps the component presentational with no injected services. A `computed()` signal can derive the lookup maps from the graph input, keeping resolution logic reactive and clean.

**Alternative considered**: Create a shared `NameResolverService` — rejected because it would require service injection in a presentational component and adds unnecessary complexity for a single use case.

### 2. Use a helper method for name resolution in the template

**Decision**: Add a `nodeName(id)` and `vehicleName(id)` method (or a single `resolveName(id)` backed by the computed lookup map). Fall back to showing the raw ID if not found.

**Rationale**: Template method calls are simple and the conflict list is always small (a handful of items), so performance is not a concern. A pipe would be overkill for this.

### 3. Service name display

**Decision**: Display service names as "S{id}" (e.g. "S101") since service IDs are numeric and the naming convention is already `S` + id.

**Rationale**: The conflict response only has numeric `service_a_id`/`service_b_id`. The graph doesn't carry a full service list, but the naming convention `S{id}` is consistent with what's shown in the schedule list. No additional API call needed.

## Risks / Trade-offs

- **[Stale graph data]** → The graph is fetched once when the service detail loads. If the track network changes mid-session, names could be slightly stale. Mitigation: graph data changes very rarely; acceptable risk.
- **[Missing ID in graph]** → A conflict could reference a node/vehicle not in the current graph. Mitigation: fall back to displaying the raw ID, same as current behavior.
