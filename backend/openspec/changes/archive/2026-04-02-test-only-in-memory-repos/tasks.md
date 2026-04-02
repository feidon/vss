## 1. Rewrite DI Container

- [x] 1.1 Remove env-var branching and in-memory imports from `api/dependencies.py` — all `get_*_repo()` functions unconditionally return PostgreSQL repo instances with `AsyncSession` via `Depends(get_session)`
- [x] 1.2 Remove `from infra.memory.*` and `from infra.seed import ...` lines from `api/dependencies.py`

## 2. Simplify Application Startup

- [x] 2.1 Remove `if os.getenv("DB") == "postgres"` guard from `main.py` lifespan — always run `metadata.create_all` and `seed_database`
- [x] 2.2 Move postgres imports (`infra.postgres.tables`, `infra.postgres.seed`, `infra.postgres.session`) to top-level in `main.py` since they are no longer conditional

## 3. Verify Tests

- [x] 3.1 Confirm application tests (`tests/application/`) still pass — they already construct in-memory repos directly in fixtures
- [x] 3.2 Confirm API tests (`tests/api/`) still pass — they already override DI with PostgreSQL
- [x] 3.3 Confirm domain tests (`tests/domain/`) still pass — no DI dependency
- [x] 3.4 Grep production source (`api/`, `application/`, `main.py`) to verify zero `infra.memory` imports remain

## 4. Update Documentation

- [x] 4.1 Update `CLAUDE.md` to remove references to the `DB` env-var fallback and document that PostgreSQL is always required
