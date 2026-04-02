## Why

HTTP status codes are expressed inconsistently across the codebase. Route decorators use `starlette.status` constants (`HTTP_201_CREATED`, `HTTP_204_NO_CONTENT`), while the error handler and all test files use raw integers (`404`, `409`, etc.). This makes it harder to grep for status code usage and increases the chance of typos in magic numbers.

## What Changes

- Replace all raw integer status codes in `api/error_handler.py` with `starlette.status` constants
- Replace all raw integer status codes in test assertions with `starlette.status` constants
- Establish `starlette.status` as the single convention for HTTP status codes project-wide

## Non-goals

- Changing any HTTP status code values or error-mapping logic
- Modifying domain or application layers (they don't deal with HTTP status codes)
- Introducing custom status code enums or wrappers

## Capabilities

### New Capabilities

- `consistent-status-constants`: Standardize all HTTP status code references to use `starlette.status` named constants instead of raw integers

### Modified Capabilities

## Impact

- `api/error_handler.py` — `STATUS_MAP` values change from raw ints to constants
- `tests/api/test_service_routes.py` — status assertions use constants
- `tests/api/test_block_routes.py` — status assertions use constants
- `tests/api/test_route_routes.py` — status assertions use constants
- `tests/api/test_graph_routes.py` — status assertions use constants
- No API behavior changes, no breaking changes
