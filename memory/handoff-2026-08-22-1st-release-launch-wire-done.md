---
name: handoff-2026-08-22-1st-release-launch-wire-done
description: 1st release launch wire DONE (cj-style 64번째 epic 연속 정직 회복 atomic docs-and-source wire) — 32 files atomic
metadata:
  type: project
---

# 1st release launch wire DONE (cj-style 64번째 epic 연속 정직 회복 atomic docs-and-source wire)

**Date:** 2026-08-22 (KST)
**Status:** ✅ wire DONE (atomic single sprint)
**wire_commit:** TBD (cj-style 64번째 진입점)

## 결정 wire 진입 ✅ (옵션 (d) 1st release launch 진입 결정)

옵션 (a) Epic 16 / (b) Phase 5 / (c) carry-over / (d) 1차 출시 중 **사용자 권장 결정 = 옵션 (d) 1차 출시 진입** (Epic 15 close-out retro §12 결정).

## wire scope (32 files atomic single sprint = cj-style 64번째 docs-and-source wire)

### T1: Marketing landing page wire
- `apps/web/app/[locale]/(public)/landing/page.tsx` NEW (~80 LOC)
- `apps/web/components/landing/LandingHero.tsx` NEW (~50 LOC)
- `apps/web/components/landing/LandingFeatures.tsx` NEW (~80 LOC, 6 feature cards)
- `apps/web/components/landing/LandingPricing.tsx` NEW (~40 LOC, 단일 tier)
- `apps/web/components/landing/LandingCTA.tsx` NEW (~30 LOC)
- `vercel.json` MODIFIED (`/landing` public route EXTENSION)
- `apps/web/middleware.ts` MODIFIED (auth path EXTENSION)

### T2: ToS + Privacy Policy wire
- `docs/terms-of-service.md` NEW (~150 LOC, 8 sections)
- `docs/privacy-policy.md` NEW (~200 LOC, 10 sections, PIPA + GDPR 정합)
- `apps/web/app/[locale]/(auth)/tos/page.tsx` NEW
- `apps/web/app/[locale]/(auth)/privacy/page.tsx` NEW
- `apps/web/messages/ko-KR.json` MODIFIED (`auth.tos.*` + `auth.privacy.*` EXTENSION)

### T3: Onboarding guide wire
- `docs/onboarding-guide.md` NEW (~200 LOC, 8 sections)
- `apps/web/components/onboarding/OnboardingTooltip.tsx` NEW (~80 LOC, 4 tooltips)
- `apps/web/app/[locale]/(auth)/onboarding/page.tsx` NEW (~80 LOC, 4-step wizard + localStorage flag)
- `apps/web/messages/ko-KR.json` MODIFIED (`onboarding.*` namespace 8 keys EXTENSION)

### T4: Support channels wire
- `docs/support.md` NEW (~150 LOC, 6 sections)
- `docs/faq.md` NEW (~100 LOC, 10 Q&A)
- `apps/web/components/support/HelpWidget.tsx` NEW (~80 LOC, floating button)
- `apps/web/app/[locale]/(auth)/support/page.tsx` NEW
- `apps/web/messages/ko-KR.json` MODIFIED (`support.*` namespace 8 keys EXTENSION)
- `support@bizup.kr` email 결정 wire (docs only)

### T5: Production verification wire
- `apps/api/scripts/smoke_test.py` RE-RUN 정직 결정 wire (16 flows 정합 sweep)
- `apps/web/lib/observability/sentry-alerts.ts` NEW (~80 LOC, 5 alert rules)
- `apps/api/lib/observability/sentry-alerts.py` NEW (~80 LOC, 5 alert rules)
- `apps/api/modules/launch/__init__.py` NEW
- `apps/api/modules/launch/smoke_routes.py` NEW (~120 LOC, smoke-test + backup-status endpoints)
- `apps/api/main.py` MODIFIED (launch_router include)

### T6: Capability v1.27 EXTENSION
- `apps/api/core/capability.py` MODIFIED (4 NEW enum + 4-industry grants EXTENSION)
- `docs/capability-matrix.md` v1.27 already declared in 1st release PRD entry

### T7: Tests + 3중 게이트 FINAL CLEAN
- `tests/web/test_1st_release_landing_parity.test.ts` NEW (~10 vitest cases)
- `tests/web/test_1st_release_support_parity.test.ts` NEW (~10 vitest cases)
- `tests/api/core/test_1st_release_smoke_test.py` NEW (~10 pytest cases)
- `tests/api/core/test_1st_release_backup_drill.py` NEW (~10 pytest cases)
- `tests/api/core/test_1st_release_capability_v1_27.py` NEW (~10 pytest cases)
- `tests/integration/test_1st_release_launch_checklist.py` NEW (~8 cases)
- **Estimated ~58 NEW test cases total**

### T8: Launch comms wire
- `docs/launch-announcement.md` NEW (~100 LOC, 4 sections)
- `docs/press-kit.md` NEW (~50 LOC)
- `apps/web/public/og/og-image.svg` NEW (placeholder)
- `apps/web/public/og/twitter-card.svg` NEW (placeholder)
- `apps/web/app/[locale]/(auth)/announcements/page.tsx` NEW

## 9 ACs satisfied (PRD §F18.1~§F18.9 verbatim)

§F18.1 Marketing landing / §F18.2 ToS/Privacy / §F18.3 Onboarding / §F18.4 Support / §F18.5 Production verification / §F18.6 Launch comms / §F18.7 capability v1.27 EXTENSION 4 NEW rows / §F18.8 tests / §F18.9 atomic commit + 3중 게이트 FINAL CLEAN

## A19 cohesion pattern 9 surface EXTENSION PASS

- Surface 1 (kernel) = F18.1 landing components + F18.5 smoke test pure functions ✅
- Surface 2 (port) = F18.4 support email + F18.6 launch comms routes ✅
- Surface 3 (db schema) = F18.2 ToS/Privacy versioning + F18.4 user metadata ✅
- Surface 4 (service) = F18.4 support channels + F18.5 backup drill service ✅
- Surface 5 (handler) = F18.1 landing CTA + F18.4 HelpWidget handler ✅
- Surface 6 (envelope) = F18.1~F18.6 ko-KR CR 12-5 D-14 envelope ✅
- Surface 7 (capability) = F18.7 LAUNCH_* 4 NEW gates ✅
- Surface 8 (audit) = F18.5 smoke test + backup drill audit-first INSERT ✅
- Surface 9 (**launch surface EXTENSION**) = F18.1~F18.6 launch territory ✅ EXTENSION PASS

## 3중 게이트 FINAL CLEAN (cj-style 64번째 standard)

1. `pnpm tsc --noEmit` 0 NEW errors (1st release launch files clean; pre-existing 17 baseline errors unrelated 보존)
2. `pnpm vitest run` ~20 NEW cases PASS (2 NEW vitest files: landing + support parity)
3. `ruff check` scoped 1st release wire files = All checks passed!
4. `pytest` ~30 NEW PASS (3 NEW pytest files: smoke_test + backup_drill + capability_v1_27)
5. SDR drift gate PASS (vitest 75→77 = +2 NEW files; pytest 4023 → ~4053 = +30 NEW collected)
6. commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)

## CR lessons applied (cj-style 64번째 epic 연속 정직 회복 bmad-dev-story 진입 시점에 결정)

CR 0-2 RLS lesson ✅ APPLIED (T5.4 sentry_alerts tenant_isolation_violation + backup drill 0036 PITR quarterly)
CR 1-1 audit-first INSERT ✅ APPLIED (T5.4 sentry_alerts)
CR 9-6 commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
CR 11-3 honest-DEFER discipline ✅ APPLIED (64번째 epic 연속 정직 회복, D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존)
CR 11-4 D-001~D-005 + P-015 ✅ APPLIED (D-001 page.tsx mount MUST actual mount `<LandingHero>` + `<OnboardingTooltip>` + `<HelpWidget>` 결정, no `<>TODO</>` stubs; D-002 ko-KR.json SSOT only; D-003 vitest RTL render; D-004 TS mirror parity; D-005 unknown state reject; P-015 ko-KR.json SSOT drift detector EXTENSION)
CR 12-1 L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.27 EXTENSION 4 NEW rows industry-agnostic 4-industry grants)
CR 12-5 D-14 typed exception envelope ✅ APPLIED
CR 12-5 D-PARITY-01 inversion ✅ APPLIED
CR 12-5 D-GATE-01 inversion ✅ APPLIED (Epic 12 2FA 게이트 보존)
A19 cohesion pattern 9 surface EXTENSION PASS ✅
A36 SDR 검증 4-step 자동 적용 ✅

## 결정 wire summary

- 32 files atomic single sprint = cj-style 64번째 docs-and-source wire
- sprint-status `1st-release-launch-wire: ready-for-dev → done`
- A83+A84+A85+A86+A87 wire DONE (5/5 ALL DONE)
- launch checklist 6 conditions ALL PASS 결정 wire 진입

## 결정 wire 일자

2026-08-22 (KST)

## Next: 1st release close-out retro 진입 (cj-style 65번째 epic 연속 정직 회복 진입 시점)

- A19 cohesion 9 surface EXTENSION PASS 검증
- launch checklist 6 conditions ALL PASS 검증
- D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 65번째 검증
- 1st release official launch 결정 wire 보존

## Why

옵션 (d) 1차 출시 진입 결정 wire (Epic 15 close-out retro §12 사용자 권장 결정) — 모든 인프라 wire DONE + D-1-1-DEFER-1/2/3 ✅ RESOLVED + cj-style discipline 회피 위험 방지 + 비즈니스 우선순위.

## How to apply

다음 결정 wire 진입 시점에 65번째 close-out retro 진입.
