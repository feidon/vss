## 1. Backend: Add /api prefix and remove SPA serving

- [x] 1.1 Add `prefix="/api"` to all router includes in `main.py`
- [x] 1.2 Remove `STATIC_DIR`, `serve_spa` catch-all, and `FileResponse` import from `main.py`
- [x] 1.3 Verify backend responds on `/api/blocks`, `/api/vehicles`, etc.

## 2. Backend: Environment-based DB config

- [x] 2.1 Remove hardcoded fallback from `session.py` — fail if `DATABASE_URL` not set
- [x] 2.2 Update `tests/pg_config.py` to read from `TEST_DATABASE_URL` / `TEST_DATABASE_URL_SYNC` env vars with localhost fallback

## 3. Frontend: Angular environment files

- [x] 3.1 Create `src/environments/environment.ts` with `apiBaseUrl: 'http://localhost:8000/api'`
- [x] 3.2 Create `src/environments/environment.production.ts` with `apiBaseUrl: '/api'`
- [x] 3.3 Configure `fileReplacements` in `angular.json` for production build
- [x] 3.4 Update `api.config.ts` to import from environment file instead of hardcoded constant

## 4. Nginx + Docker

- [x] 4.1 Create `nginx.conf` with SPA fallback (`try_files`) and `/api` reverse proxy
- [x] 4.2 Update `Dockerfile` to multi-stage: build Angular, copy into nginx image
- [x] 4.3 Update `docker-compose.yml`: add nginx service (port 80), make FastAPI internal-only
- [x] 4.4 Remove the `sed` hack from the Dockerfile

## 5. Documentation

- [x] 5.1 Create `.env.example` at repo root with all required env vars
- [x] 5.2 Update `CLAUDE.md` with new dev workflow and env setup

## 6. Verification

- [x] 6.1 Dev: run `ng serve` + backend with `DATABASE_URL` set, verify all routes and API calls
- [ ] 6.2 Docker: run `docker compose up`, verify SPA routing and API calls via nginx
- [x] 6.3 Verify page refresh on `/blocks`, `/editor`, `/viewer` all return the Angular app
