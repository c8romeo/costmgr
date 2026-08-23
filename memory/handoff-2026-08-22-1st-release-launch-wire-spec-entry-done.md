---
name: handoff-2026-08-22-1st-release-launch-wire-spec-entry-done
description: 1st release launch wire bmad-create-story spec entry DONE (cj-style 1st release launch 2번째 진입점 = cj-style 63번째 epic 연속 정직 회복 atomic docs-only wire).
metadata:
  type: project
---

# 1st release launch wire bmad-create-story spec entry DONE (2026-08-22)

**Why:** Epic 15 close-out retro `729b223` §12 옵션 (d) 1차 출시 진입 결정 + 1st release PRD entry `e48db06` (cj-style 62번째 epic 연속 정직 회복) 진입 후속. PRD §F18 (F18.1~F18.8 verbatim) + AD-29 + A83+A84+A85+A86+A87 결정 wire 진입 시점에 bmad-create-story spec 결정.

**How to apply:** cj-style 63번째 진입점 (1st release launch 2번째 진입점) = atomic docs-only wire. 5 files atomic single sprint:
1. `_bmad-output/implementation-artifacts/1st-release-launch-wire.md` NEW (~237 lines, 9 ACs PRD §F18.1~§F18.9 verbatim + 8 tasks T1~T8 + 23 subtasks)
2. `_bmad-output/implementation-artifacts/sprint-status.yaml` MODIFIED (`1st-release-launch-wire: backlog → ready-for-dev` + last_updated_note v3.3 entry 신규 prepend)
3. `memory/handoff-2026-08-22-1st-release-launch-wire-spec-entry-done.md` NEW (THIS auto-memory handoff)
4. `MEMORY.md` MODIFIED (1st release spec entry handoff hook 신규)
5. `_bmad-output/implementation-artifacts/commit-msg-1st-release-launch-wire-spec-entry.txt` NEW (THIS commit message)

**baseline_commit = `e48db06`** (1st release PRD entry tip = cj-style 62번째 wire DONE 진입 시점).
**sprint-status transition:** `1st-release-launch-wire: backlog → ready-for-dev`.

## 9 ACs satisfied (PRD §F18.1~§F18.9 verbatim)

- **§F18.1 Marketing landing page** (`/landing` route + LandingHero + LandingFeatures + LandingPricing + LandingCTA + ko-KR inline copy EXTENSION + vercel.json public route EXTENSION, (public) route group 신규, capability gate `LAUNCH_LANDING`)
- **§F18.2 ToS + Privacy Policy** (`docs/terms-of-service.md` 8 sections + `docs/privacy-policy.md` 한국 PIPA + GDPR 정합 10 sections + versioning + signup flow EXTENSION (auth)/tos + (auth)/privacy, capability gate `LAUNCH_TOS`)
- **§F18.3 Onboarding user guide** (`docs/onboarding-guide.md` 8 sections + OnboardingTooltip (4 tooltips) + first-run wizard 4-step + localStorage `costmgr.onboarding.completed` flag, Epic 1 partial scaffold `d182d7d` 정합)
- **§F18.4 Customer support channels** (`docs/support.md` 6 sections + email `support@bizup.kr` + HelpWidget + `(auth)/support/page.tsx` + `docs/faq.md` 10 Q&A, capability gate `LAUNCH_SUPPORT`)
- **§F18.5 Production launch verification** (smoke test RE-RUN 정직 결정 `apps/api/scripts/smoke_test.py` + 0036 PITR drill quarterly + Sentry alert wiring production environment + RPO 4h/RTO 24h SLA verification, capability gate `LAUNCH_MONITORING`)
- **§F18.6 Public launch communications** (`docs/launch-announcement.md` 4 sections + `docs/press-kit.md` 회사/제품/로고/팩트시트 + `apps/web/public/og/` og:image + twitter:card + `(auth)/announcements/page.tsx` in-app banner)
- **§F18.7 Capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows** (`LAUNCH_LANDING` + `LAUNCH_TOS` + `LAUNCH_SUPPORT` + `LAUNCH_MONITORING` industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)
- **§F18.8 tests + wire scope T1~T8 결정** (~+30 NEW pytest PASS + ~+20 NEW vitest PASS + 0 NEW ruff + 0 regressions, pytest 4023 → ~4053, vitest 75 → 77)
- **§F18.9 atomic commit + 3중 게이트 FINAL CLEAN** (tsc 0 NEW + vitest ~95/95 + ruff All checks passed! + pytest ~4053/4053 + SDR drift gate PASS + commit_consistency PASS) + A36 SDR 검증 4-step 자동 적용

## A19 cohesion pattern 9 surface EXTENSION PASS

(kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅ + **launch surface EXTENSION** = F18.1~F18.6 launch territory)

- Surface 1 (kernel) = F18.1 landing components + F18.5 smoke test pure functions ✅
- Surface 2 (port) = F18.4 support email + F18.6 launch comms routes ✅
- Surface 3 (db schema) = F18.2 ToS/Privacy versioning (changelog) + F18.4 user metadata (`tos_accepted_at` + `privacy_accepted_at`) ✅
- Surface 4 (service) = F18.4 support channels + F18.5 backup drill service ✅
- Surface 5 (handler) = F18.1 landing CTA + F18.4 HelpWidget handler ✅
- Surface 6 (envelope) = F18.1~F18.6 ko-KR CR 12-5 D-14 envelope ✅
- Surface 7 (capability) = F18.7 LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING 4 NEW gates ✅
- Surface 8 (audit) = F18.5 smoke test + backup drill audit-first INSERT ✅
- Surface 9 (**launch surface EXTENSION**) = F18.1~F18.6 launch territory ✅ EXTENSION PASS

## CR lessons applied (cj-style 63번째 epic 연속 정직 회복 진입 시점에)

- CR 0-2 RLS lesson ✅ APPLIED (F18.5 production verification — 0036 PITR drill quarterly + RLS violation Sentry alert 결정 wire 진입)
- CR 1-1 audit-first INSERT ✅ APPLIED (F18.5 production verification — backup_drill audit-first INSERT 결정 wire 진입)
- CR 9-6 commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire 진입)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (63번째 epic 연속 정직 회복, D-1-1-DEFER-1/2/3 ✅ honestly RESOLVE 보존)
- CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED (D-001 page.tsx mount MUST actual mount `<LandingHero>` + `<OnboardingTooltip>` + `<HelpWidget>` + D-002 ko-KR.json SSOT only + D-003 vitest RTL render + D-004 TS mirror parity mandatory + D-005 unknown state reject + P-015 ko-KR.json SSOT drift detector)
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (F18.7 capability matrix v1.27 EXTENSION 4 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire 진입)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (F18.1~F18.6 ko-KR envelope `{code, message_ko, details, trace_id}` 결정 wire 진입)
- CR 12-5 D-PARITY-01 inversion ✅ APPLIED (smoke test RE-RUN 정직 결정 + Sentry alert parity 결정 wire 진입)
- CR 12-5 D-GATE-01 inversion ✅ APPLIED (Epic 12 2FA 게이트 보존 + launch checklist 6 conditions capability gate 진입 결정 wire)
- A19 cohesion pattern 9 surface EXTENSION PASS ✅ (launch surface EXTENSION = F18.1~F18.6 launch territory 결정 wire)
- A36 SDR 검증 4-step 자동 적용 ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정)

## D-1-1-DEFER-* honestly ✅ RESOLVED 보존 (CR 11-3 63번째 epic 연속 정직 회복)

D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth (Google/Naver/Kakao) + D-1-1-DEFER-3 SSO enterprise SAML 모두 ✅ RESOLVED 보존 (Epic 15 wire `5f9e37f` 진입 시점에 모두 정직 회복 결정 wire 완료 + 60번째 epic 연속 정직 회복 검증 + 63번째 진입 시점에 grep guard INVERSION 또는 test rename 결정 wire 보존).

## Epic 15 + Phase 3 + Phase 4 cycle 정합 보존

✅ 1st release PRD entry commit `e48db06` 진입 시점에 결정 wire 모두 보존 (master PRD v3.3 §F18 신규 + AD-29 신규 결정 + capability matrix v1.27 EXTENSION 4 NEW rows + D-1-1-DEFER-1/2/3 ✅ RESOLVED 62번째)
✅ Epic 15 wire DONE 진입 시점에 cj-style 58~61번째 epic 연속 wire DONE 모두 보존 (Epic 15 PRD entry `dd218fa` + Epic 15 spec entry `9ba92dd` + Epic 15 atomic wire T1~T8 `5f9e37f` + Epic 15 close-out retro `729b223`)
✅ Phase 4 wire DONE 진입 시점에 cj-style 53~57번째 epic 연속 wire DONE 모두 보존 (Phase 4 PRD entry `8e046df` + Phase 4 spec entry + Phase 4 atomic wire T1~T8 `71a033a` + Phase 4 close-out retro `934b35e`)
✅ Phase 3 cycle close-out 완료 (Phase 3 PRD entry `9085a03` + Phase 3-0 atomic sprint `1db21d2` + Phase 3-1 atomic sprint `d3e7454` + Phase 3 close-out retro = cj-style 49~52번째 epic 연속 정직 회복 wire DONE)
✅ Epic 12 2FA 게이트 보존
✅ Epic 14 LISTEN/NOTIFY multi-process coordination 결정 wire 보존
✅ Epic 13 LISTEN/NOTIFY consume 결정 wire 보존
✅ Epic 11 close-out retro
✅ Phase 2 close-out baseline 599 passed 정합
✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존 (F18.3 onboarding guide 정합 결정)

## partial wire 시도 0건 + single sprint atomic wire 1 진입점 결정

(cj-style 63번째 epic 연속 정직 회복 bmad-create-story spec atomic docs-only wire). 결정 wire 일자: 2026-08-22 (KST).

## next (cj-style 64번째 + 65번째 진입점 결정 wire 보존)

- **1st release bmad-dev-story atomic wire T1~T8 진입** (cj-style 1st release launch 3번째 진입점 = cj-style 64번째 epic 연속 정직 회복 wire 진입 시점) — T1 Marketing landing + T2 ToS/Privacy + T3 Onboarding guide + T4 Support channels + T5 Production verification + T6 Capability v1.27 EXTENSION + T7 Tests + T8 Launch comms + 3중 게이트 FINAL CLEAN atomic single sprint wire 진입 결정 wire 보존.
- **1st release close-out retro 진입** (cj-style 1st release launch 4번째 진입점 = cj-style 65번째 epic 연속 정직 회복 진입 시점) — A19 cohesion 9 surface EXTENSION PASS 검증 (launch surface EXTENSION) + launch checklist 6 conditions ALL PASS 검증 + D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 65번째 검증 결정 wire 보류.

## Cross-references

- master PRD v3.3 §F18 (F18.1~F18.8 verbatim) — `_bmad-output/planning-artifacts/prd.md` lines 963-1068
- master PRD v3.3 §8.1 M0-(k) 1st release launch AC — `_bmad-output/planning-artifacts/prd.md` line 452
- master PRD v3.3 §부록 A A83+A84+A85+A86+A87 — `_bmad-output/planning-artifacts/prd.md` lines 1369-1373
- master PRD v3.3 §15 로드맵 1st release row — `_bmad-output/planning-artifacts/prd.md` line 1202
- AD-29 1st release launch 신규 결정 — `_bmad-output/planning-artifacts/prd.md` line 1386
- capability matrix v1.27 EXTENSION 4 NEW rows — `docs/capability-matrix.md`
- 1st release PRD entry handoff — [[handoff-2026-08-22-1st-release-prd-entry-done]]
- 1st release PRD entry commit — `e48db06`
- Epic 15 close-out retro 결정 wire 보존 진입 — [[handoff-2026-08-22-epic-15-close-out-done]]
- Epic 15 atomic wire 결정 wire 보존 진입 — [[handoff-2026-08-22-epic-15-sso-magic-oauth-wire-done]]
- Phase 4 deployment wire 결정 wire 보존 진입 — [[handoff-2026-08-22-phase-4-deployment-wire-done]]
- Phase 3 close-out retro 결정 wire 보존 진입 — [[handoff-2026-08-22-phase-3-close-out-done]]
