## ADDED Requirements

### Requirement: Frontend API base URL from Angular environment files
The Angular app SHALL read the API base URL from environment files, not a hardcoded constant.

#### Scenario: Development environment
- **WHEN** the app runs via `ng serve`
- **THEN** `API_BASE_URL` SHALL be `http://localhost:8000/api`

#### Scenario: Production build
- **WHEN** the app is built with `ng build`
- **THEN** `API_BASE_URL` SHALL be `/api` (relative)

#### Scenario: No hardcoded localhost in production bundle
- **WHEN** the Angular app is built for production
- **THEN** the output SHALL NOT contain `http://localhost:8000`

### Requirement: Backend DATABASE_URL has no hardcoded fallback
The backend SHALL read `DATABASE_URL` from the environment and fail immediately if it is not set.

#### Scenario: DATABASE_URL is set
- **WHEN** `DATABASE_URL` environment variable is set
- **THEN** the backend SHALL use it to connect to the database

#### Scenario: DATABASE_URL is missing
- **WHEN** `DATABASE_URL` environment variable is not set
- **THEN** the backend SHALL fail to start with a clear error message

### Requirement: Test DB URLs from environment with localhost fallback
Test configuration SHALL read database URLs from environment variables with localhost defaults.

#### Scenario: Test env vars not set
- **WHEN** `TEST_DATABASE_URL` is not set
- **THEN** tests SHALL use `postgresql+asyncpg://vss:vss@localhost:5432/vss_test`

#### Scenario: Test env vars set (CI)
- **WHEN** `TEST_DATABASE_URL` is set to a custom value
- **THEN** tests SHALL use that value

### Requirement: .env.example documents all required variables
A `.env.example` file SHALL list all environment variables with example values.

#### Scenario: Developer onboarding
- **WHEN** a new developer clones the repo
- **THEN** `.env.example` SHALL show all required and optional env vars with descriptions
