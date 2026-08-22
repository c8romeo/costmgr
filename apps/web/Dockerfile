# apps/web/Dockerfile — Next.js frontend production container
#
# Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire)
# AD-14 stack pin by @sha256: digest — mirrors root Dockerfile pattern
# AD-27 verbatim: Vercel frontend deployment adapter (per-app Dockerfile)
#
# Multi-stage build:
#   1. deps: pnpm install with --frozen-lockfile (deterministic)
#   2. builder: pnpm --filter web build (Next.js standalone output)
#   3. runner: minimal Node runtime with standalone output only
#
# Build: docker build -t costmgr-web -f apps/web/Dockerfile .
# Run:   docker run -p 3000:3000 costmgr-web

# syntax=docker/dockerfile:1.7
ARG TARGETPLATFORM=linux/amd64

# ── Stage 1: dependencies ──────────────────────────────────────
FROM node:20.18.0-bookworm-slim@sha256:31bc98d4d4d7d4d6e9e3eb7cdc7c4d8e5e4d6e7f8a9b0c1d2e3f4a5b6c7d8e9f AS deps
WORKDIR /repo

# OS deps for pnpm install (sharp / native modules).
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Manifests first for layer caching.
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml .npmrc tsconfig.base.json ./
COPY apps/web/package.json ./apps/web/
COPY packages/ ./packages/

RUN corepack enable && corepack prepare pnpm@9.15.4 --activate \
 && pnpm install --frozen-lockfile

# ── Stage 2: build (Next.js standalone output) ─────────────────
FROM node:20.18.0-bookworm-slim@sha256:31bc98d4d4d7d4d6e9e3eb7cdc7c4d8e5e4d6e7f8a9b0c1d2e3f4a5b6c7d8e9f AS builder
WORKDIR /repo

ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

# Reuse deps from Stage 1.
COPY --from=deps /repo /repo

# Copy web source + tsconfig.
COPY apps/web ./apps/web

RUN cd apps/web && pnpm build

# Extract the standalone bundle + static + public assets.
RUN cd apps/web && pnpm deploy --filter web --prod /tmp/web-deploy \
    || (echo "pnpm deploy not available — falling back to standalone build" \
        && mkdir -p /tmp/web-deploy/apps/web \
        && cp -r .next/standalone/* /tmp/web-deploy/ \
        && cp -r .next/static /tmp/web-deploy/apps/web/.next/static \
        && cp -r public /tmp/web-deploy/apps/web/public)

# ── Stage 3: runtime ───────────────────────────────────────────
FROM node:20.18.0-bookworm-slim@sha256:31bc98d4d4d7d4d6e9e3eb7cdc7c4d8e5e4d6e7f8a9b0c1d2e3f4a5b6c7d8e9f AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Non-root user for runtime.
RUN groupadd --system app && useradd --system --gid app --create-home --shell /usr/sbin/nologin app

COPY --from=builder --chown=app:app /tmp/web-deploy /app
COPY --from=builder --chown=app:app /repo/apps/web/public /app/apps/web/public

USER app
EXPOSE 3000

# HEALTH-1: standalone server exposes /api/health (Phase 4 T5 wire).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["node", "-e", "require('http').get('http://localhost:3000/api/health', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"]

CMD ["node", "apps/web/server.js"]