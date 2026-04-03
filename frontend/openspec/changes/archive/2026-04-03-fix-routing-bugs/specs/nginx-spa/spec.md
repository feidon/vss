## ADDED Requirements

### Requirement: Nginx serves Angular SPA with fallback
Nginx SHALL serve the Angular build output as static files and return `index.html` for any path that does not match a static file.

#### Scenario: Serving a known static file
- **WHEN** the browser requests `/main-ABC123.js`
- **THEN** nginx SHALL serve the file from the static directory

#### Scenario: SPA fallback for Angular routes
- **WHEN** the browser requests `/blocks`, `/editor`, `/viewer`, or `/map`
- **THEN** nginx SHALL return `index.html`
- **THEN** Angular router SHALL handle the route client-side

#### Scenario: Page refresh on any Angular route
- **WHEN** the user refreshes the browser on any Angular route
- **THEN** nginx SHALL return `index.html` (not raw JSON)

### Requirement: Nginx reverse-proxies API requests to FastAPI
Nginx SHALL forward all requests matching `/api/*` to the FastAPI backend.

#### Scenario: API request through nginx
- **WHEN** the browser requests `GET /api/blocks`
- **THEN** nginx SHALL proxy the request to `http://fastapi:8000/api/blocks`

#### Scenario: API request with path parameters
- **WHEN** the browser requests `PATCH /api/services/101/route`
- **THEN** nginx SHALL proxy the request to `http://fastapi:8000/api/services/101/route`

### Requirement: FastAPI routes use /api prefix
All FastAPI routers SHALL be mounted under the `/api` prefix. The SPA catch-all route SHALL be removed.

#### Scenario: Block API endpoint
- **WHEN** a client requests `GET /api/blocks`
- **THEN** FastAPI SHALL return the list of blocks as JSON

#### Scenario: No SPA serving in FastAPI
- **WHEN** a client requests `GET /blocks` directly to FastAPI
- **THEN** FastAPI SHALL return 404

### Requirement: Docker compose runs nginx and FastAPI as separate services
Docker compose SHALL define nginx (port 80) and FastAPI (port 8000, internal) as separate services.

#### Scenario: Docker compose up
- **WHEN** a developer runs `docker compose up`
- **THEN** nginx SHALL be accessible on port 80
- **THEN** the Angular app SHALL load and route correctly
- **THEN** API calls SHALL reach FastAPI through nginx
