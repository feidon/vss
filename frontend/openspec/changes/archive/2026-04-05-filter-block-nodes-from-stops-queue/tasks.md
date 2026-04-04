## 1. Filter Block Nodes from Stops Queue

- [x] 1.1 In `RouteEditorComponent.deriveInitialState()` (route-editor.ts:165), filter `svc.route` to exclude nodes with `type === 'block'` before mapping to `StopEntry[]`
- [x] 1.2 Add/update test in `route-editor.spec.ts` verifying that `deriveInitialState` excludes block nodes from the stops signal when route contains blocks
- [x] 1.3 Add test verifying that `stopsChanged` output only emits platform/yard node IDs (no block IDs)

## 2. Verify

- [x] 2.1 Run test suite (`ng test`) and fix any regressions
- [x] 2.2 Run lint and format check
