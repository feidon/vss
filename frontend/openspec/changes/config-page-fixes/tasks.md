## 1. Fix click-outside dismiss (auto-focus input)

- [x] 1.1 In `BlockConfigComponent`, add `afterNextRender` to `startEdit()` that focuses the input element after Angular renders it (use a template ref `#editInput` on the `<input>`)
- [x] 1.2 Update `block-config.spec.ts` — add test verifying the input receives focus when editing starts
- [x] 1.3 Verify existing blur/save tests still pass (`ng test`)

## 2. Add backend `GET /api/graph` route

- [x] 2.1 Create `backend/api/graph/routes.py` with a `GET /graph` route that uses `GraphAppService` to return a `GraphResponse`
- [x] 2.2 Create `backend/api/graph/schemas.py` with Pydantic response schema (or reuse existing graph schema from service module)
- [x] 2.3 Register the graph router in `backend/main.py`
- [x] 2.4 Add/update test in `backend/tests/api/test_graph_routes.py` verifying `GET /api/graph` returns valid graph data with node coordinates

## 3. Verify end-to-end

- [x] 3.1 Run frontend tests (`ng test`) — all pass
- [x] 3.2 Run backend tests (`pytest`) — all pass
- [ ] 3.3 Manual verification: config page track map renders correctly, click-outside dismiss works (user)
