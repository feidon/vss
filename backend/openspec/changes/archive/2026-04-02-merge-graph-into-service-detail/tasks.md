## 1. Application Layer

- [x] 1.1 ~~Inject `GraphAppService` into `ServiceAppService` constructor~~ Kept at route layer (already injected via FastAPI Depends)
- [x] 1.2 ~~Update `ServiceAppService.get_service()`~~ Composition done at route handler level instead
- [x] 1.3 ~~Write/update application-layer test~~ Not needed; graph composition tested at API layer

## 2. API Layer — Schema & Response

- [x] 2.1 Create `ServiceDetailResponse` schema extending `ServiceResponse` with a nested `graph` field (nodes, connections, stations, vehicles)
- [x] 2.2 Update `GET /services/{id}` route handler to return `ServiceDetailResponse`
- [x] 2.3 ~~Update DI container~~ No changes needed; `get_graph_service` already exists and is used by service routes

## 3. Remove Standalone Graph Endpoint

- [x] 3.1 Remove `api/graph/` package and its inclusion in the FastAPI app
- [x] 3.2 ~~Remove graph router wiring from DI container~~ `get_graph_service` retained (still used by service routes)
- [x] 3.3 Delete or update graph-specific API tests

## 4. Integration Tests

- [x] 4.1 Write API test: `GET /services/{id}` returns service fields + graph data
- [x] 4.2 Write API test: `GET /services` does NOT include graph data
- [x] 4.3 Write API test: `GET /graph` returns 404 (route removed)
- [x] 4.4 Run full test suite and verify all tests pass
