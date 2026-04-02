## Context

The backend API has evolved but the frontend models were never updated to match. The main issues:

1. **`GET /graph` removed** — graph data is now embedded in `GET /services/{id}`. Frontend still calls the deleted endpoint, so vehicles never load.
2. **`GET /services` response changed** — backend returns summary only (`id`, `name`, `vehicle_id`), but frontend `ServiceResponse` includes `path` and `timetable`.
3. **`GET /services/{id}` field rename** — backend returns `route` (list of nodes), frontend expects `path`.
4. **`StopRequest` field rename** — backend expects `node_id`, frontend sends `platform_id`.
5. **`InsufficientChargeConflict` shape change** — backend returns `{ service_id }`, frontend expects `{ service_a_id, service_b_id }`.
6. **Node types missing `x`, `y`** — backend includes layout coordinates on all nodes.
7. **Missing endpoints in CLAUDE.md** — `GET /blocks/{id}` doesn't exist; `POST /routes/validate` and `GET /vehicles` not documented.

### Affected files

| File | Issue |
|------|-------|
| `shared/models/service.ts` | `ServiceResponse` includes `path`+`timetable` (backend doesn't return them on list); `StopRequest.platform_id` should be `node_id` |
| `shared/models/conflict.ts` | `InsufficientChargeConflict` has wrong shape |
| `shared/models/node.ts` | Missing `x`, `y` on all node types |
| `core/services/graph.service.ts` | Calls `GET /graph` which returns 404 |
| `core/services/service.service.ts` | `getService()` returns `ServiceResponse` instead of detail type |
| `features/schedule-editor/route-editor.ts` | Sends `platform_id`, references `path` |
| `features/schedule-editor/schedule-editor.ts` | Loads vehicles from `GraphService` |
| `features/schedule-editor/service-list.ts` | References `service.path` |
| `features/schedule-viewer/viewer-service-list.ts` | References `service.path` |
| `features/schedule-viewer/timetable-detail.ts` | References `service().path` |
| `features/block-config/block-config.ts` | No edit affordance icon |

## Goals / Non-Goals

**Goals:**
- All frontend models match actual backend API responses
- Vehicle dropdown works when creating a service
- Block traversal time has a visible edit indicator
- CLAUDE.md documents actual available endpoints

**Non-Goals:**
- Adding loading/skeleton states
- Changing inline-edit UX (Enter/Escape/blur stays)
- Implementing `POST /routes/validate` frontend flow (document only)
- Redesigning any page layouts

## Decisions

### 1. Add `GET /vehicles` backend endpoint

**Decision**: Add a simple `GET /vehicles` route returning `[{ id, name }]`.

**Rationale**: Vehicles are needed *before* any service exists (to create the first service). Can't extract from `GET /services/{id}` without a chicken-and-egg problem.

**Alternatives considered**:
- Re-add `GET /graph`: Over-fetches data not needed for the create form.
- Load from first service detail: Fails when no services exist.

### 2. Split `ServiceResponse` into list vs. detail types

**Decision**: `ServiceResponse` keeps only `{ id, name, vehicle_id }` for list endpoint. New `ServiceDetailResponse` adds `route`, `timetable`, and `graph`.

**Rationale**: Matches what the backend actually returns — `GET /services` returns summaries, `GET /services/{id}` returns full detail with graph.

### 3. Rename `path` → `route` across the frontend

**Decision**: Rename the field in `ServiceDetailResponse` and all component references from `path` to `route`.

**Rationale**: The backend uses `route`. The frontend should match the API response field names to avoid confusion and potential deserialization issues.

### 4. Rename `StopRequest.platform_id` → `node_id`

**Decision**: Match the backend's `RouteStopInput.node_id`.

**Rationale**: The backend accepts `node_id`. Sending `platform_id` means the field is silently ignored, breaking route updates.

### 5. Fix `InsufficientChargeConflict` shape

**Decision**: Change from `{ service_a_id, service_b_id }` to `{ service_id }` to match backend.

**Rationale**: Backend 409 response serializes `insufficient_charge_conflicts` as `[{ service_id }]`. Frontend type is wrong.

### 6. Add `x`, `y` to node types

**Decision**: Add optional `x` and `y` fields (default 0) to `BlockNode`, `PlatformNode`, `YardNode`.

**Rationale**: Backend includes layout coordinates on all nodes. The track map feature needs these for d3.js rendering.

### 7. Pencil icon for block edit

**Decision**: Inline SVG pencil icon next to traversal time, styled `text-gray-400 hover:text-blue-600`.

**Rationale**: Universally understood edit affordance. Single icon doesn't justify an icon library.

## Risks / Trade-offs

- **Backend change required** → `GET /vehicles` is trivial (~10 lines) but must be deployed before frontend fix is complete. Mitigation: vehicle repo already exists.
- **Field renames touch many files** → `path` → `route` and `platform_id` → `node_id` affect components and tests. Mitigation: TypeScript strict mode will catch all missed references at compile time.
- **`ServiceResponse` split is a breaking change** → Components using `path`/`timetable` from the list endpoint will get compile errors. Mitigation: these fields were never populated anyway (backend doesn't return them on list), so the code was already broken — just silently.
