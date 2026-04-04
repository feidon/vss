## 1. ConflictAlertComponent — Add graph input and name resolution

- [x] 1.1 Add `graph` input of type `GraphResponse` to `ConflictAlertComponent`
- [x] 1.2 Add `computed()` lookup maps: `nodeNameMap` (id → name from `graph.nodes`) and `vehicleNameMap` (id → name from `graph.vehicles`)
- [x] 1.3 Add helper methods `nodeName(id)` and `vehicleName(id)` with fallback to raw ID
- [x] 1.4 Update template: replace raw `block_id` with `nodeName(c.block_id)`, `block_a_id`/`block_b_id` with resolved names, `vehicle_id` with `vehicleName(c.vehicle_id)`, and service IDs with `S{{ id }}` format

## 2. ScheduleEditorComponent — Pass graph to conflict alert

- [x] 2.1 Update `<app-conflict-alert>` in `ScheduleEditorComponent` template to pass `[graph]="service()!.graph"`

## 3. Tests

- [x] 3.1 Write unit tests for `ConflictAlertComponent`: verify block names, vehicle names, service names, and unknown-ID fallback render correctly
- [x] 3.2 Update existing `ScheduleEditorComponent` 409 test to include graph in fixture and verify conflict alert receives it
