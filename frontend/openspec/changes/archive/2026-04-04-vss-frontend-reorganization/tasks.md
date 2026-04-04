## 1. Directory Restructure and Route Setup

- [x] 1.1 Create `features/schedule/` directory and move reusable components from `schedule-editor/` (route-editor.ts, conflict-alert.ts) and `schedule-viewer/` (timetable-detail.ts)
- [x] 1.2 Create `features/config/` directory and move `block-config.ts` from `block-config/`
- [x] 1.3 Update `app.routes.ts`: replace 4 flat routes with `/schedule` (parent + `:id/edit` child) and `/config`; default redirect to `/schedule`
- [x] 1.4 Update `app.ts` and `app.html`: change nav bar from 4 links to 2 (Schedule, Config); verify `routerLinkActive` works for child routes
- [x] 1.5 Remove old feature directories (`schedule-editor/`, `schedule-viewer/`, `block-config/`, `track-map/`) and fix all import paths
- [x] 1.6 Verify app compiles and routes render correctly (`ng serve`)

## 2. Schedule List Component

- [x] 2.1 Create `ScheduleListComponent` in `features/schedule/schedule-list.ts` — unified service list with columns: name, vehicle, start time, origin, destination
- [x] 2.2 Add "Create Service" button that opens the create-service dialog
- [x] 2.3 Add Edit button per row that navigates to `/schedule/:id/edit`
- [x] 2.4 Add Delete button per row with confirmation prompt, calling `DELETE /api/services/{id}`
- [x] 2.5 Add `<router-outlet>` in schedule parent for child route rendering (list vs editor)
- [x] 2.6 Write tests for schedule list: service loading, empty state, delete confirmation, navigation

## 3. Create Service Dialog

- [x] 3.1 Install `@angular/cdk` dependency (`npm install @angular/cdk`)
- [x] 3.2 Create `CreateServiceDialogComponent` in `features/schedule/create-service-dialog.ts` with form: name input, vehicle dropdown, start time datetime-local input
- [x] 3.3 Implement vehicle loading on dialog open from `GET /api/vehicles`; disable dropdown while loading
- [x] 3.4 Implement form validation: all fields required; show errors on submit attempt
- [x] 3.5 On submit: call `POST /api/services`, close dialog, return service ID + start time
- [x] 3.6 Wire dialog open from schedule list "Create Service" button; navigate to `/schedule/:id/edit` on success
- [x] 3.7 Write tests for dialog: validation, successful creation, cancel behavior, vehicle loading error

## 4. Schedule Editor (Route Editor Shell)

- [x] 4.1 Create `ScheduleEditorComponent` in `features/schedule/schedule-editor.ts` as the child route component for `/schedule/:id/edit`
- [x] 4.2 Load service detail via `GET /api/services/{id}` on init; derive initial stops from route (filter `type !== "block"`), dwell times, and start time from timetable
- [x] 4.3 Integrate existing `RouteEditorComponent` (stop queue, dwell times, save) with the editor shell
- [x] 4.4 Display timetable after successful route save (reuse existing timetable rendering logic)
- [x] 4.5 Display conflict alerts on 409 response (reuse `ConflictAlertComponent`)
- [x] 4.6 Add prominent "Back to Schedule" navigation link/button (routerLink to `/schedule`)
- [x] 4.7 Write tests for editor: service loading, initial stop derivation, save success, conflict display

## 5. Track Map Editor

- [x] 5.1 Create `TrackMapEditorComponent` in `features/schedule/track-map-editor.ts` with d3.js rendering of graph nodes at (x, y) positions and connections between them
- [x] 5.2 Style clickable nodes (platforms, yards) distinctly from non-clickable blocks; add name labels
- [x] 5.3 Implement click handler: clicking platform/yard appends to stop queue signal; blocks are not clickable
- [x] 5.4 Add hover feedback (highlight + tooltip) and selected-node visual indication (filled color or number overlay for queued nodes)
- [x] 5.5 Integrate track map editor into `ScheduleEditorComponent` alongside the stop queue panel
- [x] 5.6 Write tests for track map: node rendering, click-to-add, visual state updates

## 6. Config Page

- [x] 6.1 Create `ConfigComponent` in `features/config/config.ts` as a shell with sections for block config and track overview
- [x] 6.2 Move `BlockConfigComponent` into `features/config/block-config.ts`; verify inline editing still works
- [x] 6.3 Create `TrackMapOverviewComponent` in `features/config/track-map-overview.ts` — read-only d3.js track map (reuse rendering from track-map-editor without click interaction)
- [x] 6.4 Write tests for config page: block config renders, track overview renders

## 7. Cleanup and Verification

- [x] 7.1 Remove all unused components, imports, and files from old feature directories
- [x] 7.2 Run `ng lint` and fix all linting errors
- [x] 7.3 Run `npx prettier --check "src/**/*.{ts,html,css}"` and fix formatting
- [x] 7.4 Run `ng test` and verify all tests pass
- [x] 7.5 Manual smoke test: navigate Schedule → Create → Edit → Save → Back → Config → Block edit
