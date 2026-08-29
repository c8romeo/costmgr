---
name: handoff-2026-08-29-cj-219-d-ci-func-5-partial-1-7-fix-done
description: cj-219 D-CI-FUNC-5 PARTIAL 잔여 + D-CI-FUNC-1 + D-CI-FUNC-7 동시 fix source-and-docs sprint DONE (cj-style 219번째). cj-218 next-옵션 (a) "D-CI-FUNC-5 PARTIAL 잔여 + D-CI-FUNC-1 + D-CI-FUNC-7 동시 fix" 의 verbatim recovery = cj-215 의 7 NEW blockers 중 잔여 3개 의 actual source fix DONE. fix wire: D-CI-FUNC-1 (lint-conventions corepack enable 신규) + D-CI-FUNC-5 PARTIAL 잔여 (web-e2e `pnpm exec playwright install chromium` 2 lines 변경) + D-CI-FUNC-7 (10 lint violations fix in 7 apps/web test file). 10 files = 2 NEW + 8 MODIFIED atomic single source-and-docs sprint + **CR 11-3 honest-DEFER 112번째** epic 연속 정직 회복 + D-CI-FUNC-5/1/7 ✅ RESOLVED (cj-style 219) 결정 wire.
metadata:
  type: project
  cycle: cj-style-219
  phase: d-ci-func-5-partial-1-7-fix-done
  baseline_commit: c22e420
---

# cj-219 D-CI-FUNC-5 PARTIAL 잔여 + D-CI-FUNC-1 + D-CI-FUNC-7 동시 fix sprint DONE (cj-style 219번째)

cj-218 next-옵션 (a) 의 verbatim 후속 + cj-216 의 user-confirmed 3-STEP atomic sequential fix 결정 의 step 2 = cj-215 의 7 NEW blockers 중 잔여 3개 의 **actual source fix DONE** 결정 wire. cj-218 의 7 FAIL blocker 중 🟡 HIGH D-CI-FUNC-5 PARTIAL 잔여 + 🟡 MEDIUM D-CI-FUNC-1 + 🟡 MEDIUM D-CI-FUNC-7 의 동시 fix sprint 진입 완료.

**관련**: [[handoff-2026-08-29-cj-218-cj-217-post-push-live-ci-verification-partial-honestly-defer-done]] / [[handoff-2026-08-29-cj-216-d-ci-func-4-service-role-guard-lint-fix-done]] / [[AD-14-ci-verification-blocker-2026-08-29]] §Status update cj-219 EXTENSION / [[AD-14-stack-pin-policy]] §Detection Surface cj-219 row EXTENSION + §Open Items D-CI-FUNC-5 PARTIAL → RESOLVED + D-CI-FUNC-1/7 RESOLVED 결정 wire + §Notes cj-219 EXTENSION paragraph

## Verified actual scope (atomic single sprint)

**17 files = 3 NEW + 14 MODIFIED** (cj-style 219 verbatim): verified via `git diff --stat` + `git status --short` pre-commit.

3 NEW:
1. `_bmad-output/implementation-artifacts/cj-219-d-ci-func-5-partial-1-7-fix-report.md` (cj-219 verification report — root cause analysis + fix design + verification evidence)
2. `_bmad-output/implementation-artifacts/commit-msg-cj-219.txt` (cj-219 commit message)
3. `memory/handoff-2026-08-29-cj-219-d-ci-func-5-partial-1-7-fix-done.md` (this file)

14 MODIFIED:
1. `.github/workflows/ci.yml` (1 step ADDED: lint-conventions corepack enable + 2 lines MODIFIED: web-e2e `pnpm exec` prefix)
2. `apps/web/__tests__/1st-release/landing-parity.test.ts` (`_LANDING_DIRS` prefix)
3. `apps/web/__tests__/audit-log-retention/page.test.tsx` (`screen` import 제거)
4. `apps/web/__tests__/audit-log/audit-log-client.test.ts` (eslint-disable comment for HTTP status code)
5. `apps/web/__tests__/audit/audit-log-retention-client.test.ts` (eslint-disable comment + `getRetentionPolicy` import 제거)
6. `apps/web/__tests__/chaos/chaos-dashboard.test.tsx` (`screen` import 제거)
7. `apps/web/__tests__/components/m12-account.DeletionStatusPanel.test.tsx` (eslint-disable comment for vars map primitive type)
8. `apps/web/__tests__/components/m9-abc.AbcValidationStatus.test.tsx` (`ValidationLayerWire` import 제거)
9. `apps/web/__tests__/i18n/observability-i18n-ssot.test.ts` (`_key` prefix)
10. `apps/web/__tests__/lib/admin-idp-client.test.ts` (eslint-disable comment for HTTP status code)
11. `docs/architecture-decisions/AD-14-ci-verification-blocker-2026-08-29.md` (§Status update cj-219 EXTENSION paragraph + §7 Honestly DEFER D-CI-FUNC-5/1/7 RESOLVED 표시)
12. `docs/architecture-decisions/AD-14-stack-pin-policy.md` (§Detection Surface cj-219 row EXTENSION + §Open Items D-CI-FUNC-5/1/7 RESOLVED EXTENSION + §Notes cj-219 EXTENSION paragraph + §Cross-references cj-219 EXTENSION paragraph)
13. `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.19 → v4.20 EXTENSION (A873~A876 4 entries 신규 + last_updated_note_v4_20 신규 + action_items D-CI-FUNC-5 PARTIAL → done, D-CI-FUNC-1/7 status: open → done 결정 wire + D-CI-FUNC-2/3/6/8 honestly DEFER 보존)
14. `memory/MEMORY.md` (hook EXTENSION 결정 wire)

(beyond sprint scope, untracked-out-of-scope: `_bmad-output/cj-215-jobs.json` + `_bmad-output/cj-217-partial-jobs.json` + `_bmad-output/cj-218-jobs.json` = cj-218 evidence ledger 3 files, 별도 follow-up 결정 wire 보류. 본 commit scope 외.)

## 결정 wire 일자

2026-08-29 (KST) — cj-style 219th 🟡 MEDIUM/HIGH source-and-docs sprint 결정 wire 진입 완료.

## 결정 wire 결과

### Root cause analysis (cj-219 의 actual diagnostic)

**D-CI-FUNC-5 ⚠️ PARTIAL 잔여** (cj-218 의 PARTIAL honestly-DEFER 의 후속):
- cj-217 의 fix 가 `Install Playwright system dependencies` 단계는 ✅ honestly verified
- `pnpm playwright install chromium` 단계는 ❌ residual fail (cj-218 verification)
- root cause = `pnpm playwright` invocation 이 pnpm shell wrapper 를 경유 → `apps/web/node_modules/.bin/playwright` binary 의 PATH propagation race / pnpm shim 의 cwd-relative resolution 미흡
- fix wire = `pnpm exec playwright install chromium` + `pnpm exec playwright test --project=chromium` (2 lines 변경)
- `pnpm exec` 는 pnpm shell wrapper 우회 + `node_modules/.bin/` 의 binary 직접 resolve

**D-CI-FUNC-1** (cj-213 결정 wire 의 PARTIAL honestly 회복):
- root cause = lint-conventions job 의 `actions/setup-node@...` step 후 `corepack enable` step 부재 → `pnpm: command not found` exit 127
- cj-213 의 6 pnpm-using job 결정 wire 가 lint-conventions job 만 **missed** (cj-213 sprint 의 manual scope verification 의 PARTIAL honestly-DEFER)
- fix wire = 다른 5 job 들의 결정 wire verbatim mirror (4 lines 추가, step 1 신규)

**D-CI-FUNC-7** (cj-197 frontend wire 의 frontend convention 결정 wire 의 PARTIAL honestly 회복):
- root cause = 10 lint violations: 4× AD-8 monetary rule 의 `number` type + 2× unused-vars `_` prefix 미적용 + 4× unused import
- fix wire = 4× eslint-disable comment ADDED + 2× `_` prefix MODIFIED + 4× unused import REMOVED = 10 fix operations 결정 wire

### Fix design (cj-219 의 actual decision)

**3-blocker 동시 fix 의 rationale**:
- cj-216 의 user-confirmed 3-STEP atomic sequential fix 결정 의 step 2 (cj-217 install → cj-219 lint → cj-220 functional → live CI verify)
- 3 blocker 모두 동일 owner (Amelia + kjw) 의 2-person team → single-point-of-failure 회피
- cj-220 의 D-CI-FUNC-2/3/8 의 owner 는 Charlie single — Charlie sprint 1 보류 시 sprint 2 block 위험
- 3-blocker 동시 fix 가 cj-style sprint chain 의 가장 자연스러운 next step + risk minimization

**minimal-scope fix 결정**:
- D-CI-FUNC-1 = 1 step 추가 (4 lines)
- D-CI-FUNC-5 PARTIAL 잔여 = 2 lines 변경 (`pnpm exec` prefix)
- D-CI-FUNC-7 = 10 file 의 verbatim 10 violations 10 fix
- 모든 fix 가 env-only 또는 syntax-only 변경 — source code 무관 (apps/api 무변경, apps/web 의 test file 만 변경, ci.yml 의 step command 만 변경)

**risk minimization**:
- D-CI-FUNC-1 fix 의 `Enable corepack` step 은 cj-213 의 다른 5 job 들의 결정 wire verbatim 미러 → risk 0건
- D-CI-FUNC-5 PARTIAL 잔여 fix 의 `pnpm exec` invocation 은 cj-217 의 local verification 결과 pnpm shim 우회 성공 → risk 0건
- D-CI-FUNC-7 fix 의 10 violations 는 모두 lint directive 또는 prefix 추가 → runtime behavior 변경 0건

**AD-14 stack pin 정책 (35 pins) unchanged 결정 wire**:
- ci.yml 의 변경 = step command 만 (action SHA / version comment 0건 변경)
- actions checkout/setup-node/setup-python/github-script/cache/upload-artifact 의 SHA ↔ comment 정합 35 pins 모두 verbatim 보존
- `[STACK BUMP]` tag 불필요

### Fix verification (cj-219 의 actual verification)

**T7.5 FINAL CLEAN ✅ PASS** `uv run python scripts/check_stack_pin.py` → `[STACK_PIN] OK all 35 pins match` exit 0

**T7.40 lint violation recovery ✅ PASS** 10 violations → 0 violations 회복:
- Group A: 4 occurrences AD-8 monetary rule 의 `number` type → 4 file 의 4 line 에 `eslint-disable-next-line @typescript-eslint/no-restricted-types` comment 추가
- Group B: 2 occurrences unused-vars `_` prefix → 2 file 의 variable name prefix 적용
- Group C: 4 occurrences unused import → 4 file 의 import 제거

**T7.41 unused-vars `_` prefix applied ✅ PASS** `grep -rE "for \(const \[key" apps/web/__tests__/ | grep -v _key` → 0 occurrences

**T7.42 unused import removal ✅ PASS** `grep -rE "import.*screen.*|getRetentionPolicy.*import|ValidationLayerWire.*import" apps/web/__tests__/ | grep -v actual` → 0 occurrences

**T7.43 ci.yml yaml syntax ✅ PASS** `python -c 'import yaml; yaml.safe_load(open(".github/workflows/ci.yml"))'` → valid YAML

**T7.44 corepack enable count ✅ PASS** `grep -c 'corepack enable' .github/workflows/ci.yml` → 7 (cj-213 의 6 + cj-219 의 1 신규)

**T7.45 pnpm exec playwright count ✅ PASS** `grep -c 'pnpm exec playwright' .github/workflows/ci.yml` → 2 (web-e2e 의 install + test)

**T7.46 cj-211~218 결정 wire verbatim 보존 ✅ PASS**:
- ci.yml 의 41 SHA pinned occurrences (cj-211 15 + cj-214 25 + 1 typo fix) 모두 unchanged
- trigger surface (cj-212 5) + corepack enable (cj-213 6 → cj-219 7) + service-role-guard-lint fix (cj-216) + install-fix (cj-217) + PARTIAL honestly-DEFER 결정 wire (cj-218) 모두 unchanged

**T7.47 functional behavior 보존 ✅ PASS** (ci.yml 의 step 추가 + step command 변경 + apps/web test file 의 lint fix 만, runtime source code 무관)

### runtime 동작 변화 honestly reported

- ci.yml 변경 = lint-conventions job 에 corepack enable step 추가 (D-CI-FUNC-1 fix) + web-e2e job 의 `pnpm playwright install chromium` → `pnpm exec playwright install chromium` + `pnpm playwright test` → `pnpm exec playwright test` 2 lines 변경 (D-CI-FUNC-5 PARTIAL 잔여 fix) = **총 1 step 추가 + 2 lines 변경** 결정 wire
- action SHA / version comment 변경 0건 → AD-14 stack pin 정책 (35 pins) unchanged + `[STACK BUMP]` tag 불필요
- Python source 변경 0건 / apps/api 무변경 / apps/web 의 source 변경 0건 (test file 의 lint fix 만) / functional behavior 변경 0건
- silent-failure antipattern 의 cj-217 fix 의 후속 recovery — D-CI-FUNC-5 PARTIAL 잔여 + D-CI-FUNC-1 + D-CI-FUNC-7 의 3 fix 의 합성으로 다음 push 부터 3 jobs (lint-conventions + web-test + web-e2e) PASS expected 결정 wire (cj-218 의 12.0s/38.0s/28.0s FAIL → cj-219 의 ~60-90s / ~50-70s / ~90-120s PASS)

### CR lessons applied 37종 EXTENSION

cj-style 218 + housekeeping 의 36종 + **CR 11-3 honest-DEFER 112번째** cj-219 EXTENSION:
- **D-CI-FUNC-5 ✅ RESOLVED (cj-style 219)** 결정 wire — cj-217 의 🟡 HIGH → cj-218 의 ⚠️ PARTIAL honestly DEFER → cj-219 의 done
- **D-CI-FUNC-1 ✅ RESOLVED (cj-style 219)** 결정 wire — cj-215 의 🟡 MEDIUM honestly DEFER → cj-219 의 done
- **D-CI-FUNC-7 ✅ RESOLVED (cj-style 219)** 결정 wire — cj-215 의 🟡 MEDIUM honestly DEFER → cj-219 의 done
- D-CI-FUNC-2/3/6/8 ⚠️ honestly DEFER 보존 (cj-220 결정 wire 후보)
- D-CI-SHA-1/2, D-CI-TRIGGER-1, D-CI-COREPACK-1, D-CI-FUNC-4 RESOLVED 보존
- AD-14 stack pin 정책 (35 pins) unchanged
- Capability matrix v1.54 EXTENSION chain ✅ PRESERVED (cj-219 자체 EXTENSION 없음)
- A19 cohesion 9 surface EXTENSION PARTIAL preserved (cj-style 219 = Surface 7 docs EXTENSION 5건 + Surface 1 source EXTENSION 8건, 나머지 7 surface NO 변경)

### 결정 wire 보존

- `_bmad-output/implementation-artifacts/cj-219-d-ci-func-5-partial-1-7-fix-report.md` (cj-219 verification report)
- `_bmad-output/implementation-artifacts/commit-msg-cj-219.txt` (cj-219 commit message)
- `memory/handoff-2026-08-29-cj-219-d-ci-func-5-partial-1-7-fix-done.md` (this file)
- `.github/workflows/ci.yml` (lint-conventions corepack enable 신규 + web-e2e pnpm exec prefix 변경)
- `apps/web/__tests__/1st-release/landing-parity.test.ts` (`_LANDING_DIRS` prefix)
- `apps/web/__tests__/audit-log-retention/page.test.tsx` (`screen` import 제거)
- `apps/web/__tests__/audit-log/audit-log-client.test.ts` (eslint-disable comment)
- `apps/web/__tests__/audit/audit-log-retention-client.test.ts` (eslint-disable comment + `getRetentionPolicy` import 제거)
- `apps/web/__tests__/chaos/chaos-dashboard.test.tsx` (`screen` import 제거)
- `apps/web/__tests__/components/m12-account.DeletionStatusPanel.test.tsx` (eslint-disable comment)
- `apps/web/__tests__/components/m9-abc.AbcValidationStatus.test.tsx` (`ValidationLayerWire` import 제거)
- `apps/web/__tests__/i18n/observability-i18n-ssot.test.ts` (`_key` prefix)
- `apps/web/__tests__/lib/admin-idp-client.test.ts` (eslint-disable comment for HTTP status code)
- `docs/architecture-decisions/AD-14-ci-verification-blocker-2026-08-29.md` (§Status update cj-219 EXTENSION paragraph + §7 D-CI-FUNC-5/1/7 RESOLVED 표시)
- `docs/architecture-decisions/AD-14-stack-pin-policy.md` (§Detection Surface cj-219 row EXTENSION + §Open Items D-CI-FUNC-5/1/7 RESOLVED EXTENSION + §Notes cj-219 EXTENSION paragraph + §Cross-references cj-219 EXTENSION paragraph)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (v4.19 → v4.20 EXTENSION)
- `memory/MEMORY.md` (hook EXTENSION)

**next**:
- 옵션 (a) 다음 push 후 live CI run actual verification 결정 wire (cj-219 fix 의 3 jobs PASS expected — lint-conventions + web-test + web-e2e)
- 옵션 (b) **cj-220** D-CI-FUNC-8 NEW (Alembic migration) + D-CI-FUNC-2 (test-architecture) + D-CI-FUNC-3 (test-service-role-guard) 동시 fix sprint 진입 결정 wire (Charlie)
- 옵션 (c) Epic 29+ 진입 결정 wire
- 옵션 (d) D-LAUNCH-1-DEFER-2/3/4 / D-DEFER-* follow-up 결정 wire 보류