## Context

The codebase uses two styles for HTTP status codes:
- `starlette.status` constants in route decorators (`api/service/routes.py`)
- Raw integers everywhere else: `STATUS_MAP` in `api/error_handler.py` and all test assertions

FastAPI re-exports `starlette.status` via `fastapi.status`, but since FastAPI itself is built on Starlette, importing directly from `starlette.status` is the canonical source.

## Goals / Non-Goals

**Goals:**
- Adopt `starlette.status` constants as the single convention for all HTTP status codes
- Apply to production code (`api/`) and test code (`tests/api/`)

**Non-Goals:**
- Changing any HTTP status code values or error-mapping behavior
- Touching domain or application layers (no HTTP concepts there)
- Introducing custom enums or wrapper types

## Decisions

### Use `starlette.status` over `fastapi.status`

`api/service/routes.py` already imports from `starlette.status`. FastAPI's `status` module is just a re-export of Starlette's. Using the original source is more explicit and avoids the indirection.

**Alternative considered:** Import from `fastapi.status` for consistency with the FastAPI ecosystem. Rejected because `starlette.status` is already established in the codebase and is the actual source.

### Apply to tests as well

Test assertions like `assert response.status_code == 200` will become `assert response.status_code == HTTP_200_OK`. This makes tests self-documenting and consistent with production code.

**Alternative considered:** Keep raw integers in tests for brevity. Rejected because the inconsistency is the problem we're solving — half the codebase using constants while tests use raw numbers defeats the purpose.

## Risks / Trade-offs

- **Verbosity**: `HTTP_200_OK` is longer than `200`. Acceptable — clarity over brevity for status codes.
- **Import lines**: Test files will gain one import line. Negligible cost.
- **No functional risk**: This is a pure refactor — all values remain identical.
