# apps/api/Dockerfile — FastAPI backend production container
#
# Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire)
# AD-14 stack pin by @sha256: digest — mirrors root Dockerfile pattern
# AD-27 verbatim: Railway backend deployment adapter (per-app Dockerfile)
#
# Multi-stage build:
#   1. builder: uv sync with --no-dev (FastAPI + deps)
#   2. runtime: minimal Python 3.12-slim + uvicorn production server
#
# Build: docker build -t costmgr-api -f apps/api/Dockerfile .
# Run:   docker run -p 8000:8000 --env-file .env costmgr-api

# syntax=docker/dockerfile:1.7
ARG TARGETPLATFORM=linux/amd64

# ── Stage 1: builder ───────────────────────────────────────────
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS builder
WORKDIR /repo

# uv is the only resolver — no pip install of project deps.
# ghcr.io/astral-sh/uv pinned by digest (multi-arch image index).
COPY --from=ghcr.io/astral-sh/uv:0.11.32@sha256:df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c /uv /uvx /usr/local/bin/

# OS deps for building Python packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Manifests + lockfile first for layer caching.
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml ./apps/api/
COPY packages/cost_engine/pyproject.toml ./packages/cost_engine/
COPY packages/services/pyproject.toml ./packages/services/
COPY packages/ports/pyproject.toml ./packages/ports/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/repo/.venv

# Build a stripped runtime venv (no dev deps).
RUN uv sync --frozen --no-dev --no-install-project

# Copy the source and install project (no dev deps).
COPY apps ./apps
COPY packages ./packages
RUN uv sync --frozen --no-dev --no-editable

# Pre-compile Python bytecode to surface syntax errors at build time.
RUN uv run python -m compileall -q apps packages

# ── Stage 2: runtime ───────────────────────────────────────────
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS runner
WORKDIR /app

# Non-root user for runtime.
RUN groupadd --system app && useradd --system --gid app --create-home --shell /usr/sbin/nologin app

# Copy venv + project from builder.
COPY --from=builder /repo/.venv /app/.venv
COPY --from=builder /repo/apps /app/apps
COPY --from=builder /repo/packages /app/packages
COPY --from=builder /repo/pyproject.toml /repo/uv.lock /app/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

USER app
EXPOSE 8000

# Health check uses the FastAPI endpoint at /api/v1/health (Phase 4 T5 wire).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; \
r = urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=2); \
exit(0 if r.status == 200 else 1)"]

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]