## 1. Fix Block Group Column Centering

- [x] 1.1 Add `text-center` to the group column `<td>` and `<th>` in `block-config.ts` template
- [x] 1.2 Verify both "-" placeholder and group badges are horizontally centered

## 2. Vehicle List Component

- [x] 2.1 Create `VehicleListComponent` standalone component in `src/app/features/config/`
- [x] 2.2 Inject `VehicleService`, fetch vehicles on init, store in signal, sort by name (natural alphanumeric)
- [x] 2.3 Build template with table displaying vehicle names, matching block-config table styling
- [x] 2.4 Add loading state and error handling using `ErrorAlertComponent`

## 3. Config Page Integration

- [x] 3.1 Import `VehicleListComponent` in `ConfigComponent` and add `<app-vehicle-list />` below `<app-block-config />`
- [x] 3.2 Verify full config page renders both sections correctly

## 4. Testing

- [x] 4.1 Write unit tests for `VehicleListComponent` (loading, display, sort order, error state)
- [x] 4.2 Run `ng test` and `ng lint` to confirm all tests pass and no lint errors
