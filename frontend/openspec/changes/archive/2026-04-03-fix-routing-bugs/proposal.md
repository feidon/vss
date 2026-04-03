## Why

The frontend is currently served by FastAPI's catch-all route on port 8000, causing three bugs:
1. FastAPI's `GET /blocks` API route takes priority over the SPA catch-all, so refreshing on `/blocks` returns raw JSON instead of the Angular app.
2. The SPA catch-all only registers when `static/` directory exists (`if STATIC_DIR.is_dir()`), making behavior inconsistent between dev and Docker.
3. The Dockerfile uses a `sed` hack to strip `http://localhost:8000` from built JS files — fragile and indicates the architecture needs fixing.

Additionally, URLs are hardcoded across the codebase: frontend API URL in `api.config.ts`, backend DB fallback in `session.py`, and test DB URLs in `pg_config.py`.

## What Changes

- **Add nginx** as the frontend web server in Docker, serving Angular static files with proper SPA fallback (`try_files $uri $uri/ /index.html`)
- **Prefix all FastAPI routes with `/api`** — separates API from SPA routes (`/api/blocks` vs `/blocks`)
- **Angular environment files** — `environment.ts` (dev: `http://localhost:8000/api`) and `environment.production.ts` (prod: `/api` relative, behind nginx)
- **Remove SPA serving from FastAPI** — delete the `serve_spa` catch-all and `STATIC_DIR` logic
- **Remove the Dockerfile `sed` hack** — no longer needed with environment-based URLs
- **Move all hardcoded URLs to env variables** — backend DB URL (remove fallback), test DB URLs (read from env with localhost fallback)

## Non-goals

- SSR or pre-rendering
- CDN or caching optimization
- Changing Angular routing structure

## Capabilities

### New Capabilities
- `nginx-spa`: Nginx configuration for serving Angular SPA with reverse proxy to FastAPI backend in Docker.
- `env-config`: Environment-based configuration for all URLs across frontend and backend.

### Modified Capabilities
_(none — no spec-level behavior changes, only infrastructure fix)_

## Impact

- **Frontend**: `api.config.ts`, new `environment.ts` / `environment.production.ts`, `angular.json` (file replacements)
- **Backend**: `main.py` (remove SPA serving, add `/api` prefix), `session.py` (remove fallback), `pg_config.py` (read from env)
- **Docker**: New nginx service in `docker-compose.yml`, new `nginx.conf`, updated `Dockerfile`
