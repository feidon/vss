## 1. API Models (`shared/models/`)

- [x] 1.1 Create `node.ts` — `BlockNode`, `PlatformNode`, `YardNode`, `Node` discriminated union
- [x] 1.2 Create `block.ts` — `BlockResponse`, `UpdateBlockRequest`, `BlockIdResponse`
- [x] 1.3 Create `service.ts` — `ServiceResponse`, `CreateServiceRequest`, `UpdateRouteRequest`, `StopRequest`, `ServiceIdResponse`, `TimetableEntry`
- [x] 1.4 Create `graph.ts` — `GraphResponse`, `Connection`, `Station`, `Vehicle`
- [x] 1.5 Create `conflict.ts` — `ConflictResponse`, `VehicleConflict`, `BlockConflict`, `InterlockingConflict`, `LowBatteryConflict`, `InsufficientChargeConflict`
- [x] 1.6 Create `index.ts` barrel export

## 2. API Services (`core/services/`)

- [x] 2.1 Create `api.config.ts` — base URL constant
- [x] 2.2 Create `graph.service.ts` — `getGraph()`
- [x] 2.3 Create `block.service.ts` — `getBlocks()`, `updateBlock()`
- [x] 2.4 Create `service.service.ts` — `getServices()`, `getService()`, `createService()`, `updateRoute()`, `deleteService()`
- [x] 2.5 Write service unit tests (`graph.service.spec.ts`, `block.service.spec.ts`, `service.service.spec.ts`)

## 3. App Shell & Routes

- [x] 3.1 Create placeholder components for each feature (`schedule-editor`, `schedule-viewer`, `block-config`, `track-map`)
- [x] 3.2 Configure lazy-loaded routes in `app.routes.ts` with default redirect to `/editor`
- [x] 3.3 Replace `app.ts` and `app.html` with shell layout (nav bar + router-outlet)
- [x] 3.4 Write app shell test — nav links render, active route highlighted
