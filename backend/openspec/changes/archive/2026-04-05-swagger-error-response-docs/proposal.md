## Why

Error responses (400, 404, 409, 422) are handled by a global `domain_error_handler` but are invisible in the OpenAPI/Swagger docs. Developers must read `error_handler.py` to discover which errors an endpoint can return and what shape the response body has. This makes the API harder to consume and error-prone to integrate with.

## What Changes

- Define Pydantic response models for error shapes: a simple `ErrorResponse` (string detail) and a structured `ConflictDetailResponse` (409 with conflict breakdowns)
- Add `responses` parameter to every route decorator so Swagger documents all possible error statuses and their body schemas
- Introduce a declarative mechanism (decorator or dict builder) that derives `responses` from the error codes an endpoint can produce, so future routes get error docs automatically without developers needing to remember

## Non-goals

- Changing the error handler logic or HTTP status mappings
- Changing the actual error response body format
- Adding error documentation for FastAPI's built-in 422 (Pydantic validation) - that's already auto-generated

## Capabilities

### New Capabilities
- `swagger-error-schemas`: Pydantic models for error response bodies and a declarative way to attach them to routes

### Modified Capabilities
- `domain-error`: The existing domain-error spec covers the handler and status mapping. This change adds the requirement that error responses must be visible in OpenAPI via `responses` on route decorators.

## Impact

- **api/shared/**: New error response schema file
- **api/block/routes.py**: Add `responses` to `PATCH /{block_id}`
- **api/service/routes.py**: Add `responses` to `POST`, `GET /{id}`, `PATCH /{id}/route`, `DELETE /{id}`
- **api/route/routes.py**: Add `responses` to `POST /validate`
- No database, domain, or application layer changes
