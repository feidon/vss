## Why

The frontend models and API expectations have drifted from the backend's actual responses, causing multiple bugs:
1. The vehicle dropdown in "Create Service" is always empty because the frontend calls `GET /graph` which no longer exists — the backend merged graph data into `GET /services/{id}`.
2. The block traversal time has no visual indicator that it's editable.
3. Several frontend models use wrong field names or shapes vs what the backend returns.

## What Changes

- **Add `GET /vehicles` backend endpoint** so the frontend can load vehicles independently of service details.
- **Replace `GraphService.getGraph()` usage** in `ScheduleEditorComponent` with a new `VehicleService`.
- **Align all frontend models with actual backend responses**:
  - Split `ServiceResponse` into list type (`id`, `name`, `vehicle_id` only) and `ServiceDetailResponse` (includes `route`, `timetable`, `graph`).
  - Rename `path` → `route` in detail response to match backend field name.
  - Rename `StopRequest.platform_id` → `node_id` to match backend's `RouteStopInput`.
  - Fix `InsufficientChargeConflict` to use `service_id` (single field) instead of `service_a_id` + `service_b_id`.
  - Add `x`, `y` fields to `BlockNode`, `PlatformNode`, `YardNode`.
  - Remove `GET /blocks/{id}` and `GET /graph` from CLAUDE.md; add `GET /vehicles` and `POST /routes/validate`.
- **Add pencil icon** next to block traversal time values for edit discoverability.

## Non-goals

- Redesigning the block configuration page layout.
- Adding loading spinners or skeleton states.
- Changing the inline-edit interaction (click-to-edit, Enter/Escape/blur stays the same).
- Implementing `POST /routes/validate` in the frontend (document only).

## Capabilities

### New Capabilities

- `vehicle-loading`: Frontend service and backend endpoint for loading the vehicle list independently.
- `route-path-naming-alignment`: Rename field mismatches across models, services, and components.

### Modified Capabilities

- `block-list`: Add a visible edit affordance (pencil icon) to each block's traversal time cell.
- `api-services`: Split service response types, add `VehicleService`, align field names.
- `api-models`: Fix `InsufficientChargeConflict`, add `x`/`y` to nodes, rename `StopRequest.platform_id` → `node_id`, split service response types.

## Impact

- **Backend**: New `GET /vehicles` route (minimal — vehicle repo already exists).
- **Frontend models**: `service.ts`, `conflict.ts`, `node.ts`, `graph.ts` — field renames + type splits.
- **Frontend services**: New `VehicleService`; updated `ServiceService` return types.
- **Frontend components**: `ScheduleEditorComponent`, `RouteEditorComponent`, `ServiceListComponent`, `ViewerServiceListComponent`, `TimetableDetailComponent`, `BlockConfigComponent`.
- **Tests**: All component and service specs referencing changed field names.
- **Documentation**: `CLAUDE.md` API table update.
