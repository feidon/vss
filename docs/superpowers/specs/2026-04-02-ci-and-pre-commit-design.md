# CI and Pre-commit Linter Design

## Overview

Add pre-commit hooks and a GitHub Actions CI pipeline to the VSS monorepo, covering Python (backend) and Angular (frontend) projects.

## Pre-commit Hooks

A single `.pre-commit-config.yaml` at the repo root using the `pre-commit` Python framework. Hooks are directory-scoped so backend changes only trigger Python hooks and frontend changes only trigger JS/TS hooks.

### Hooks

| Hook | Scope | Purpose | Notes |
|------|-------|---------|-------|
| `ruff check` | `backend/**/*.py` | Python linting | Uses `ruff-pre-commit` mirror repo |
| `ruff format --check` | `backend/**/*.py` | Python format check | Uses `ruff-pre-commit` mirror repo |
| `lint-imports` | `backend/` | Architecture dependency enforcement | Local hook, `pass_filenames: false`, entry: `bash -c 'cd backend && lint-imports'` |
| `eslint` | `frontend/src/**/*.{ts,html}` | Angular linting | Local hook, `pass_filenames: false`, entry: `bash -c 'cd frontend && npx eslint src/'` |
| `prettier --check` | `frontend/src/**/*.{ts,html,css}` | Format check | Local hook, `pass_filenames: false`, entry: `bash -c 'cd frontend && npx prettier --check "src/**/*.{ts,html,css}"'` |

`pre-commit` is installed as a backend dev dependency and configured at the repo root.

### Developer Onboarding

After cloning the repo, developers must run:

```bash
cd backend && uv sync   # installs pre-commit
uv run pre-commit install   # activates git hooks
```

## CI Pipeline

Single GitHub Actions workflow at `.github/workflows/ci.yml`. Triggers on push to `main` and all pull requests. Five parallel jobs with path filters.

### Jobs

#### backend-lint
- **Trigger**: `backend/**` changes
- **Working directory**: `backend/`
- **Steps**: Checkout, setup Python 3.14, `uv sync`, `ruff check .`, `ruff format --check .`, `lint-imports`

#### backend-test
- **Trigger**: `backend/**` changes
- **Working directory**: `backend/`
- **Services**: Postgres 17 container (`POSTGRES_USER=vss`, `POSTGRES_PASSWORD=vss`, `POSTGRES_DB=vss`) with health check
- **Environment**: `DATABASE_URL=postgresql+asyncpg://vss:vss@localhost:5432/vss_test`
- **Steps**:
  1. Checkout, setup Python 3.14, `uv sync`
  2. Create test database: `PGPASSWORD=vss psql -h localhost -U vss -c "CREATE DATABASE vss_test;"`
  3. Run all tests: `uv run pytest -m ''` (test fixtures handle schema creation via `metadata.create_all()`, no Alembic migrations needed)

#### frontend-lint
- **Trigger**: `frontend/**` changes
- **Working directory**: `frontend/`
- **Steps**: Checkout, setup Node LTS, `npm ci`, `npx ng lint`, `npx prettier --check "src/**/*.{ts,html,css}"`

#### frontend-test
- **Trigger**: `frontend/**` changes
- **Working directory**: `frontend/`
- **Steps**: Checkout, setup Node LTS, `npm ci`, `npx ng test`

#### frontend-build
- **Trigger**: `frontend/**` changes
- **Working directory**: `frontend/`
- **Steps**: Checkout, setup Node LTS, `npm ci`, `npx ng build`

## New Dependencies and Config

| What | Where | Details |
|------|-------|---------|
| `pre-commit` | `backend/pyproject.toml` dev dep | `uv add --dev pre-commit` |
| `ruff` | `backend/pyproject.toml` dev dep | `uv add --dev ruff` |
| Ruff config | `backend/pyproject.toml` `[tool.ruff]` | Target Python 3.14, line length 88 (Python convention; frontend uses 100 via Prettier) |
| `angular-eslint` | `frontend/` | `ng add @angular-eslint/schematics` modifies `package.json`, `angular.json` (adds `lint` target), and creates `eslint.config.js` |
| `.pre-commit-config.yaml` | repo root | Pre-commit hook definitions |
| `.github/workflows/ci.yml` | repo root | CI workflow |

## What This Does NOT Change

- No modifications to existing application code
- No changes to existing test configuration defaults
- No additional formatting/style enforcement beyond ruff, eslint, and prettier
