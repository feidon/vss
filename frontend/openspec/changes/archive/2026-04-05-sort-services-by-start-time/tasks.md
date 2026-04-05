## 1. Implementation

- [x] 1.1 Add `sortedServices` computed signal to `ScheduleListComponent` that sorts `services()` by `start_time` ascending, with null values last
- [x] 1.2 Update template to iterate `sortedServices()` instead of `services()`

## 2. Testing

- [x] 2.1 Write test: services are displayed sorted by start_time ascending
- [x] 2.2 Write test: services with null start_time appear after services with start_time
- [x] 2.3 Write test: all-null start_time list renders without error
- [x] 2.4 Run existing tests to verify no regressions
