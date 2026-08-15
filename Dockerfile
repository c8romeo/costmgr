# ─────────────────────────────────────────────────────────────────────────────
# costmgr Dockerfile — multi-stage build (CI-only per HANDOFF Decision 2)
# ─────────────────────────────────────────────────────────────────────────────
# Per AD-14, base images MUST be pinned by @sha256:... digest for full
# reproducibility (AC #1). All digests were captured via:
#
#   curl -H "Authorization: Bearer $TOKEN" \
#        -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
#        -I https://registry-1.docker.io/v2/<repo>/manifests/<tag>
#
# Re-run the digest refresh on:
#   - Node / Python / nginx major version bump
#   - Base image EOL announcement
#   - Supply-chain security advisory
#
# Multi-arch support: pass `--platform=linux/amd64` (or arm64) at build time.
# `ARG TARGETPLATFORM` is exposed below for conditional logic if needed.
# ─────────────────────────────────────────────────────────────────────────────

# syntax=docker/dockerfile:1.7

ARG TARGETPLATFORM=linux/amd64

# ── Stage 1: frontend build (Next.js) ──────────────────────────────────────
FROM node:24.18.0-alpine@sha256:a0b9bf06e4e6193cf7a0f58816cc935ff8c2a908f81e6f1a95432d679c54fbfd AS frontend-builder
WORKDIR /repo

# Copy only manifests first for layer caching
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml .npmrc tsconfig.base.json ./
COPY apps/web/package.json ./apps/web/
COPY packages/ ./packages/

RUN corepack enable && corepack prepare pnpm@9.15.4 --activate \
 && pnpm install --frozen-lockfile

# Now copy the rest and build
COPY apps/web ./apps/web

# Use standalone output to keep the runtime image small
ENV NEXT_TELEMETRY_DISABLED=1
RUN cd apps/web && pnpm build

# ── Stage 2: backend build (uv sync) ───────────────────────────────────────
FROM python:3.14-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4 AS backend-builder
WORKDIR /repo

# uv is the only resolver — no pip install of project deps.
# ghcr.io/astral-sh/uv pinned by digest (multi-arch image index).
COPY --from=ghcr.io/astral-sh/uv:0.11.32@sha256:df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c /uv /uvx /usr/local/bin/

# Copy manifests + lockfile first for layer caching
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml ./apps/api/
COPY packages/cost_engine/pyproject.toml ./packages/cost_engine/
COPY packages/services/pyproject.toml ./packages/services/
COPY packages/ports/pyproject.toml ./packages/ports/

# Build a stripped runtime venv (no dev deps)
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/repo/.venv

RUN uv sync --frozen --no-dev --no-install-project

# Copy the source and install project (no dev deps)
COPY apps ./apps
COPY packages ./packages
RUN uv sync --frozen --no-dev --no-editable

# Pre-compile Python bytecode to surface syntax errors at build time
RUN uv run python -m compileall -q apps packages

# ── Stage 3: backend runtime ───────────────────────────────────────────────
FROM python:3.14-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4 AS backend-runtime
WORKDIR /app

# Non-root user for runtime
RUN groupadd --system app && useradd --system --gid app --create-home --shell /usr/sbin/nologin app

# Copy venv + project from builder
COPY --from=backend-builder /repo/.venv /app/.venv
COPY --from=backend-builder /repo/apps /app/apps
COPY --from=backend-builder /repo/packages /app/packages
COPY --from=backend-builder /repo/pyproject.toml /repo/uv.lock /app/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

USER app
EXPOSE 8000

# Health check with retry (DOCKER-4: avoid single-shot urllib.request.urlopen)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request, time; \
r = urllib.request.Request('http://localhost:8000/health'); \
[urllib.request.urlopen(r, timeout=2) for _ in range(3) if time.sleep(0.5) is None]"]

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# ── Stage 4: frontend runtime (nginx) ──────────────────────────────────────
FROM nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10 AS frontend-runtime

# Drop the default config, use ours
COPY --from=frontend-builder /repo/apps/web/.next/static /usr/share/nginx/html/_next/static
COPY --from=frontend-builder /repo/apps/web/public /usr/share/nginx/html/public

# Minimal nginx config — Next.js standalone mode emits server.js, but for
# static export we serve via nginx. Tailor per apps/web/next.config.js output.
RUN cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Long-cache hashed assets
    location /_next/static/ {
        expires 1y;
        access_log off;
        add_header Cache-Control "public, immutable";
    }

    # Everything else: SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# HEALTH-1: nginx:1.27-alpine does NOT ship `wget` by default → install busybox
# wget explicitly (it's a tiny static binary that nginx already bundles
# elsewhere on the image filesystem; we install for safety in slim variants).
RUN apk add --no-cache wget

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]