# syntax=docker/dockerfile:1
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .

EXPOSE 8000
CMD ["/bin/sh", "-c", ".venv/bin/alembic upgrade head && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000"]
