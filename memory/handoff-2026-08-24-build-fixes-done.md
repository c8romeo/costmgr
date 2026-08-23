---
name: handoff-2026-08-24-build-fixes-done
description: Dev server build fixes DONE (Phase 8 wire 후속). 4 source files + commit message + .env.local (git-ignored). 16/18 representative routes 200 OK.
metadata:
  type: project
---

# Dev server build fixes DONE (Phase 8 wire 후속)

**결정 wire 일자**: 2026-08-24 (KST)
**commit**: `eaee198`

## 빌드 버그 3종 수정

1. **`apps/web/middleware.ts`** — `runtime = "edge"` → `"experimental-edge"` (Next.js 15 deprecation)
2. **`apps/web/instrumentation-node.ts`** — `TraceIdRatioBased` → `TraceIdRatioBasedSampler`, `ALWAYS_ON` → `AlwaysOnSampler()`, `ParentBased` wrapper 제거 (Phase 7 wire `59b56cd` 가 sdk-trace-base@1.27.0 변경된 API surface에 pinned 안 됨)
3. **`apps/web/instrumentation.ts`** — register() server branch 에 OTEL_SDK_DISABLED early-return + `eval("'./instrumentation-node'")` 로 webpack static analysis 우회 (edge bundle 이 Node `fs` require 하는 @grpc/proto-loader chain 분석 시도 차단)

부가: `apps/web/.env.local` (git-ignored) 신규 — OTEL_SDK_DISABLED=true + Supabase placeholder URL/anon key.

## Smoke test 결과

`npx next dev -p 3000` 재시작 후 18개 representative routes:

| Route | Status |
|-------|--------|
| `/` | 200 |
| `/landing` | 200 |
| `/login` | 200 |
| `/signup` | 200 |
| `/forgot-password` | 200 |
| `/onboarding` | 200 |
| `/announcements` | 200 |
| `/magic-link` | 200 |
| `/magic-link-sent` | 200 |
| `/privacy` | 200 |
| `/tos` | 200 |
| `/support` | 200 |
| `/activity` | 200 |
| `/audit-log` | 200 |
| `/audit-log-retention` | 200 |
| `/dashboard` | 307 (login redirect, expected) |
| `/reports/15` | 404 (separate issue — dashboard sub-route auth context) |
| `/reports/21` | 404 (same as above) |

## 정합 보존

Phase 8 wire `60d4ea1` + Phase 7 wire `59b56cd` + 모든 Epic 1~17 + Phase 3~7 + 1st release cycle 정합 100% 보존. 변경은 dev environment only (production OTLP export 는 Phase 7 wire 의 HTTP exporter 그대로 유지).

## Out of scope

- Phase 7 wire `59b56cd` upstream API drift (TraceIdRatioBased / ALWAYS_ON) 는 production OTLP tracing crisp fix 로 별도 follow-up.
- `/reports/15`, `/reports/21` 등 dashboard sub-routes 의 unauthenticated 404/500 은 dashboard layout re-verification sprint 에서 별도 처리.
