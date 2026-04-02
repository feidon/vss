## 1. API Layer — Production Code

- [ ] 1.1 Replace raw integer status codes in `api/error_handler.py` `STATUS_MAP` with `starlette.status` constants
- [ ] 1.2 Verify all route decorators in `api/service/routes.py`, `api/block/routes.py`, `api/route/routes.py` already use `starlette.status` (no raw integers)

## 2. Test Layer — API Tests

- [ ] 2.1 Replace raw integer status codes in `tests/api/test_service_routes.py` with `starlette.status` constants
- [ ] 2.2 Replace raw integer status codes in `tests/api/test_block_routes.py` with `starlette.status` constants
- [ ] 2.3 Replace raw integer status codes in `tests/api/test_route_routes.py` with `starlette.status` constants
- [ ] 2.4 Replace raw integer status codes in `tests/api/test_graph_routes.py` with `starlette.status` constants

## 3. Verification

- [ ] 3.1 Run full test suite (`uv run pytest`) to confirm no regressions
- [ ] 3.2 Grep codebase for remaining raw integer status codes in `api/` and `tests/api/` to confirm none remain
