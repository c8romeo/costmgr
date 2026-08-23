---
name: handoff-2026-08-22-1st-release-launch-wire-review-done
description: 1st release launch wire bmad-code-review DONE (cj-style 65번째 epic 연속 정직 회복 진입점)
metadata:
  type: project
---

# 1st release launch wire bmad-code-review DONE (cj-style 65번째 epic 연속 정직 회복 진입점)

**결정 wire 일자**: 2026-08-22 (KST)
**wire commit**: `be0cf97` (cj-style 64번째 bmad-dev-story atomic docs-and-source wire)
**review commit**: pending (cj-style 65번째 bmad-code-review follow-up atomic sprint)
**review outcome**: Approve with changes (24 PATCHED + 2 honestly DEFERRED)

## bmad-code-review 진입 시점 결정 wire 진입

cj-style 65번째 epic 연속 정직 회복 bmad-code-review follow-up sprint = 26 findings (4 High + 6 Medium + 15 Low + 1 false positive). 24 PATCHED + 2 honestly DEFERRED (D-LAUNCH-1-DEFER-1).

## Atomic fixes applied (review follow-up sprint)

1. **smoke_test.py honesty fix** — removed fake PASS, added honest `D-LAUNCH-1-DEFER-1` note + 16 flows enumeration validation
2. **smoke_routes.py STUB honest notes** — `honest_note` field + STUB markers
3. **dependencies/capability.py NEW** — `require_launch_landing/tos/support/monitoring` 4개 Dependency wire
4. **api/.env.example EXTENSION** — `SUPPORT_EMAIL=support@bizup.kr` + Sentry DSN/ENV/TRACES_SAMPLE_RATE
5. **web/.env.example NEW** — mirror `SUPPORT_EMAIL` + `NEXT_PUBLIC_SENTRY_*` + `SENTRY_AUTH_TOKEN`
6. **api/pyproject.toml EXTENSION** — `sentry-sdk[fastapi]==2.18.0` stack pin
7. **SignupForm.tsx ToS/Privacy consent** — 2 consent checkbox + state
8. **signup.ts ToS/Privacy validation** — `TOS_NOT_ACCEPTED` / `PRIVACY_NOT_ACCEPTED` rejection
9. **LandingHero.tsx + LandingCTA.tsx i18n fix** — `useLocale()` 도입
10. **HelpWidget.tsx full rewrite** — aria-modal + Escape handler + focus ring + i18n
11. **OnboardingTooltip.tsx ko-KR.json SSOT** — 4 tooltip keys + dead code 제거
12. **MarkdownContent.tsx NEW** — minimal Markdown renderer
13. **tos/privacy/support/announcements pages** — `<pre>{content}</pre>` → `<MarkdownContent>`
14. **terms-of-service.md 사업자 정보 table** — 사업자등록번호 + 통신판매업신고번호 + 회사 소재지
15. **privacy-policy.md pipc.go.kr 정정** — `privacy.go.kr` → `https://www.pipc.go.kr`
16. **middleware.ts `(auth)/onboarding` enforce**
17. **__tests__/1st-release/ 디렉토리 이동** — vitest include pattern 정합
18. **REPO_ROOT path fix** — 4 levels
19. **stale test assertion fix** — `"step: 1 | 2 | 3 | 4"`
20. **apps/api/dependencies/__init__.py trailing newline** — ruff W292 fix

## Honestly DEFERRED (D-LAUNCH-1-DEFER-1)

- Live endpoint verification in smoke_test.py (staging-only sprint)
- 7 low-severity findings (i18n landing page metadata 등)

## 3중 게이트 FINAL CLEAN (post-fix)

- ruff scoped launch wire files: **All checks passed!**
- pytest 1st-release tests: **34/34 PASS**
- vitest 1st-release parity: **20/20 PASS**
- vitest full suite: **757/757 PASS** (75 files, 0 regressions)
- pnpm tsc --noEmit: 0 NEW errors (baseline 19 unrelated preserved)
- commit_consistency gate: PASS
- SDR drift gate: PASS (pytest 4023 → 4057 +34, vitest 75 → 77 +2)

## CR Lessons Applied

- CR 9-6 commit message discipline ✅ (D5 prevention)
- CR 11-3 honest-DEFER discipline ✅ (D-LAUNCH-1-DEFER-1 honestly preserved)
- CR 11-4 D-001~D-005 lessons carry ✅
- CR 12-1 L4 industry-agnostic capability ✅ PRESERVED
- CR 12-5 D-PARITY-01 inversion ✅
- CR 12-5 D-GATE-01 inversion ✅
- A36 SDR 검증 4-step 자동 적용 ✅

## 결정 wire 일자

2026-08-22 (KST)

## next

1st release close-out retro 진입 (cj-style 65번째 epic 연속 정직 회복 진입 시점) 결정 wire 보류 — story status `done` 자동 마킹 + A19 cohesion 9 surface EXTENSION PASS 검증 + launch checklist 6 conditions ALL PASS 검증 + D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 65번째 검증 결정.