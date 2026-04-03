## Context

The Angular SPA is currently baked into the FastAPI Docker image and served via a catch-all route. This causes route collisions (`GET /blocks` returns API JSON, not `index.html`), relies on a `sed` hack in the Dockerfile, and has hardcoded URLs scattered across the codebase.

## Goals / Non-Goals

**Goals:**
- Serve Angular via nginx with proper SPA fallback
- Eliminate route collisions between Angular routes and API endpoints
- Environment-based configuration for all URLs (frontend API, backend DB, test DB)
- Clean Docker architecture: nginx + FastAPI as separate services

**Non-Goals:**
- SSR or pre-rendering
- CDN or edge caching
- Changing Angular routing structure

## Decisions

### 1. Nginx as frontend server

**Decision**: Add nginx to serve the Angular build output, with `try_files` for SPA fallback and `proxy_pass` for `/api` routes.

**Rationale**: Industry-standard Angular deployment. Nginx handles static files efficiently, supports SPA fallback natively, and can reverse-proxy to the backend.

**Alternative considered**: Keep FastAPI serving static files but fix route priority. Rejected — mixes concerns and remains fragile when adding new API routes.

### 2. `/api` prefix on all backend routes

**Decision**: Prefix all FastAPI routers with `/api`.

**Rationale**: Cleanly separates API namespace from SPA namespace. Nginx routes `/api/*` to FastAPI, everything else to static files.

### 3. Angular environment files for API base URL

**Decision**: Use Angular's built-in `fileReplacements` in `angular.json` to swap `environment.ts` (dev) with `environment.production.ts` (prod).

- Dev: `apiBaseUrl = 'http://localhost:8000/api'` — direct to backend, no proxy needed
- Prod: `apiBaseUrl = '/api'` — relative, nginx proxies to backend

**Rationale**: Standard Angular pattern. No `sed` hack, no proxy for dev, works in both environments.

### 4. Backend DB URL — fail fast, no fallback

**Decision**: Remove the hardcoded fallback from `session.py`. If `DATABASE_URL` is not set, the app fails immediately.

**Rationale**: Fail-fast prevents accidentally connecting to a wrong database. Docker compose already sets `DATABASE_URL`. Local dev can use `.env` or export the variable.

### 5. Test DB URLs — env with localhost fallback

**Decision**: Read `TEST_DATABASE_URL` and `TEST_DATABASE_URL_SYNC` from env, with `localhost:5432/vss_test` as default.

**Rationale**: Tests always run locally, so a localhost fallback is safe. But env override allows CI to point to a different test database.

### 6. Docker architecture

```
nginx (port 80)
  ├── /api/*     → proxy_pass to fastapi:8000
  └── /*         → serve static files, fallback to index.html

fastapi (port 8000, internal only)
  └── /api/*     → API endpoints
```

## Risks / Trade-offs

- **[Risk] Backend `/api` prefix is a breaking change** → Only the Angular frontend is a client, so impact is contained.
- **[Risk] Removing DB fallback breaks local dev without env var** → Document in README that `DATABASE_URL` must be set. Add `.env.example`.
- **[Trade-off] Extra container in docker-compose** → Minimal overhead; nginx is ~25MB. Worth the clean separation.
