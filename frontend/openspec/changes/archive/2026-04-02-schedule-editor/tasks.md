## 1. Container component & data loading

- [x] 1.1 Rewrite `ScheduleEditorComponent` as container: load services + graph on init, hold signals for state (services, graph, selectedService, conflicts)
- [x] 1.2 Add view mode signal (`list` | `edit`) to toggle between list and route editor views

## 2. Service list

- [x] 2.1 Create `ServiceListComponent` — table with name, vehicle name, stop count, Edit/Delete buttons
- [x] 2.2 Implement vehicle name resolution using graph vehicles data
- [x] 2.3 Implement delete with `window.confirm()` confirmation
- [x] 2.4 Write service list component tests

## 3. Service creation form

- [x] 3.1 Create `ServiceFormComponent` — name input + vehicle dropdown + submit
- [x] 3.2 Wire form submission to `ServiceService.createService()`, then switch to route editor for new service
- [x] 3.3 Write service form component tests

## 4. Route editor

- [x] 4.1 Create `RouteEditorComponent` — stop picker (dropdown grouped by station), ordered stop list with dwell_time inputs, start_time datetime-local input, submit button
- [x] 4.2 Implement add/remove stops with ordered list management
- [x] 4.3 Wire submit to `ServiceService.updateRoute()`, reload service on success to show timetable
- [x] 4.4 Display timetable table (node name, arrival, departure as formatted times) after successful route update
- [x] 4.5 Add "Back to list" navigation
- [x] 4.6 Write route editor component tests

## 5. Conflict display

- [x] 5.1 Create `ConflictAlertComponent` — receives `ConflictResponse`, renders grouped conflict details with dismiss button
- [x] 5.2 Wire 409 error handling in container: parse error, set conflicts signal, pass to alert component
- [x] 5.3 Write conflict alert component tests
