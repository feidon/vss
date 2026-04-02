## 1. Shared Utilities

- [x] 1.1 Create `EpochTimePipe` in `src/app/shared/pipes/` — transforms epoch seconds to `HH:mm:ss`, returns `—` for zero values
- [x] 1.2 Write unit tests for `EpochTimePipe` covering valid timestamps, zero, and edge cases

## 2. Viewer Service List Component

- [x] 2.1 Create `ViewerServiceListComponent` (presentational) — table with name, vehicle, stop count columns; emits `select` event on row click
- [x] 2.2 Add vehicle filter dropdown and group-by-vehicle toggle with computed signal for filtered/grouped services
- [x] 2.3 Write unit tests for `ViewerServiceListComponent` — rendering, filtering, grouping, empty state, vehicle name resolution

## 3. Timetable Detail Component

- [x] 3.1 Create `TimetableDetailComponent` (presentational) — ordered timetable table with node name, type, arrival, departure; service header; back button
- [x] 3.2 Add platform stop highlighting (visual distinction for `platform` type nodes)
- [x] 3.3 Write unit tests for `TimetableDetailComponent` — timetable rendering, empty timetable message, platform highlighting, epoch time formatting via pipe

## 4. Container Component

- [x] 4.1 Rewrite `ScheduleViewerComponent` as container — fetch services and graph on init, manage `selectedService` and `vehicleFilter` signals
- [x] 4.2 Wire child components: `ViewerServiceListComponent` (list mode) and `TimetableDetailComponent` (detail mode) with signal-based view switching
- [x] 4.3 Write unit tests for `ScheduleViewerComponent` — data loading, service selection, back-to-list navigation
