# CI and Pre-commit Linter Design

## Overview

Add pre-commit hooks and a GitHub Actions CI pipeline to the VSS monorepo, covering Python (backend) and Angular (frontend) projects.

## Pre-commit Hooks

A single `.pre-commit-config.yaml` at the repo root using the `pre-commit` Python framework. Hooks are directory-scoped so backend changes only trigger Python hooks and frontend changes only trigger JS/TS hooks.

### Hooks

| Hook | Scope | Purpose |
|------|-------|---------|
| `ruff check` | `backend/**/*.py` | Python linting |
| `ruff format --check` | `backend/**/*.py` | Python format check |
| `lint-imports` | `backend/` | Architecture dependency enforcement |
| `eslint` | `frontend/src/**/*.{ts,html}` | Angular linting |
| `prettier --check` | `frontend/src/**/*.{ts,html,css}` | Format check |

`pre-commit` is installed as a backend dev dependency and configured at the repo root.

## CI Pipeline

Single GitHub Actions workflow at `.github/workflows/ci.yml`. Triggers on push to `main` and all pull requests. Five parallel jobs with path filters.

### Jobs

#### backend-lint
- **Trigger**: `backend/**` changes
- **Steps**: Checkout, setup Python 3.14, `uv sync`, `ruff check backend/`, `ruff format --check backend/`, `cd backend && lint-imports`

#### backend-test
- **Trigger**: `backend/**` changes
- **Services**: Postgres 17 container (`vss` user/password/db, plus `vss_test` db)
- **Steps**: Checkout, setup Python 3.14, `uv sync`, wait for Postgres health check, create `vss_test` database, `pytest -m ''` (all tests including Postgres integration)

#### frontend-lint
- **Trigger**: `frontend/**` changes
- **Steps**: Checkout, setup Node LTS, `npm ci`, `ng lint`, `npx prettier --check src/`

#### frontend-test
- **Trigger**: `frontend/**` changes
- **Steps**: Checkout, setup Node LTS, `npm ci`, `ng test`

#### frontend-build
- **Trigger**: `frontend/**` changes
- **Steps**: Checkout, setup Node LTS, `npm ci`, `ng build`

## New Dependencies and Config

| What | Where | Details |
|------|-------|---------|
| `pre-commit` | `backend/pyproject.toml` dev dep | `uv add --dev pre-commit` |
| `ruff` | `backend/pyproject.toml` dev dep | `uv add --dev ruff` |
| Ruff config | `backend/pyproject.toml` `[tool.ruff]` | Target Python 3.14, line length 88, src dirs |
| `angular-eslint` | `frontend/` | `ng add @angular-eslint/schematics` adds `eslint.config.js` and wires `ng lint` |
| `.pre-commit-config.yaml` | repo root | Pre-commit hook definitions |
| `.github/workflows/ci.yml` | repo root | CI workflow |

## What This Does NOT Change

- No modifications to existing application code
- No changes to existing test configuration defaults
- No additional formatting/style enforcement beyond ruff, eslint, and prettier
