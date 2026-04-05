## 1. Error Response Pydantic Models

- [x] 1.1 Add `ErrorResponse` model (detail: str) to `api/shared/schemas.py`
- [x] 1.2 Add conflict sub-schemas (`VehicleConflictSchema`, `BlockConflictSchema`, `InterlockingConflictSchema`, `BatteryConflictSchema`) and `ConflictDetail` model to `api/shared/schemas.py`, mirroring `_build_conflict_detail()` structure
- [x] 1.3 Add `ConflictDetailResponse` model (detail: ConflictDetail) to `api/shared/schemas.py`
- [x] 1.4 Add response constants (`NOT_FOUND_RESPONSE`, `VALIDATION_RESPONSE`, `CONFLICT_RESPONSE`, `NO_ROUTE_RESPONSE`) to `api/shared/schemas.py`

## 2. Route Decorator Updates

- [x] 2.1 Add `responses={**NOT_FOUND_RESPONSE}` to `PATCH /api/blocks/{id}` in `api/block/routes.py`
- [x] 2.2 Add `responses={**VALIDATION_RESPONSE}` to `POST /api/services` in `api/service/routes.py`
- [x] 2.3 Add `responses={**NOT_FOUND_RESPONSE}` to `GET /api/services/{id}` in `api/service/routes.py`
- [x] 2.4 Add `responses={**NOT_FOUND_RESPONSE, **VALIDATION_RESPONSE, **CONFLICT_RESPONSE, **NO_ROUTE_RESPONSE}` to `PATCH /api/services/{id}/route` in `api/service/routes.py`
- [x] 2.5 Add `responses={**NOT_FOUND_RESPONSE}` to `DELETE /api/services/{id}` in `api/service/routes.py`
- [x] 2.6 Add `responses={**VALIDATION_RESPONSE, **NO_ROUTE_RESPONSE}` to `POST /api/routes/validate` in `api/route/routes.py`

## 3. Tests

- [x] 3.1 Add test that verifies `ErrorResponse` validates against the simple error handler output shape
- [x] 3.2 Add test that verifies `ConflictDetailResponse` validates against the structured conflict handler output shape
- [x] 3.3 Add test that verifies the OpenAPI schema includes error responses for documented routes (inspect `app.openapi()`)
