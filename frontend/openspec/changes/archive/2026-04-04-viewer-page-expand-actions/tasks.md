## 1. Component State & Data Fetching

- [x] 1.1 Add `expandedServiceId` signal (`signal<number | null>(null)`) and `detailCache` signal (`signal<ReadonlyMap<number, ServiceDetailResponse>>(new Map())`) to `ScheduleListComponent`
- [x] 1.2 Implement `toggleExpand(service)` method: if same ID → collapse (set null), else → set ID and fetch detail if not cached
- [x] 1.3 Clear `detailCache` and `expandedServiceId` in `loadServices()` so stale data is discarded after delete/refresh

## 2. Template: Expandable Row

- [x] 2.1 Add `(click)="toggleExpand(service)"` and `cursor-pointer` to each `<tr>` in the service table
- [x] 2.2 Add expansion `<tr>` after each service row, conditionally shown when `expandedServiceId() === service.id`
- [x] 2.3 Display route path as `node.name` joined by ` → ` inside a `<td colspan="6">` with `bg-gray-50` styling
- [x] 2.4 Show "Loading..." while detail is being fetched, "No route defined" for empty routes

## 3. Testing

- [x] 3.1 Write test: clicking a row sets `expandedServiceId` and fetches detail
- [x] 3.2 Write test: clicking the same row again clears `expandedServiceId`
- [x] 3.3 Write test: cached detail is reused on re-expand (no second HTTP call)
- [x] 3.4 Write test: Edit/Delete button clicks do not trigger expansion (stopPropagation)
