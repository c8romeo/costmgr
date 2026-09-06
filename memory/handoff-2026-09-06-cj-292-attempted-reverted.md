---
name: cj-292-attempted-reverted
description: cj-292 fix forward sprint ATTEMPTED + REVERTED (cj-style 292번째 + 292 follow-up #1) — Epic 30+ csv-export.spec.ts 3/3 PRE-EXISTING carryover 정직 fix 시도 + honest recovery via revert
metadata:
  type: project
---

# cj-292 fix forward sprint ATTEMPTED + REVERTED 결정 wire (cj-style 292번째 + 292 follow-up #1)

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: Epic 30+ Reporting & Export MVP (cj-282 PRD entry territory)
**chain 진입**: cj-291 close-out retro (`0ce88ad`) 의 옵션 (b) verbatim mirror — PRE-EXISTING csv-export.spec.ts 3/3 fail carryover (cj-287~cj-291 honestly-DEFER 5 sprints) 정직 fix 시도

## sprint scope 결정 wire — 2 commits + 2 reverts = 4 commits cycle

### chain 결정 wire (4 commits)
1. **`0974371`** cj-292 1st attempt — 2 files = 1 MODIFIED spec + 1 MODIFIED ci.yml (cookie domain+path approach)
2. **`0ec8ea5`** cj-292 follow-up #1 — 1 file refined (cookie url approach + test.skip position moved)
3. **`f3e7984`** revert follow-up #1 — 1 file reverted to cj-287 baseline
4. **`3909ac6`** revert cj-292 — 2 files reverted to cj-287 baseline

### net result
- 0 source files modified (working tree baseline recovery)
- ci.yml 변경 0 / csv-export.spec.ts 변경 0
- PRE-EXISTING 3/3 fail carryover honestly-DEFER baseline state 회복

## root cause 분석 (attempted diagnosis)

**Original carryover root cause** (cj-287 activation 시점부터):
1. ci.yml did NOT export `DEV_TENANT_REPORT_ID` / `DEV_ACCESS_TOKEN` env vars for the playwright step
2. csv-export.spec.ts Case 1 (UI flow) renders "세션이 만료되었습니다" fallback (page.tsx:63-68) without `sb-access-token` cookie → `data-testid="reports-tab"` absent → `expect(reportsTab)` fails
3. csv-export.spec.ts Cases 2+3 (direct API call) use empty `tenant_id=""` → 422 validation error

**fix attempt**:
- 1 MODIFIED `apps/web/e2e/csv-export.spec.ts` (+26 lines):
  - `HAS_AUTH = Boolean(DEV_TENANT_REPORT_ID) && Boolean(DEV_ACCESS_TOKEN)`
  - `beforeEach`: `if (HAS_AUTH) await context.addCookies([{name: "sb-access-token", value: DEV_ACCESS_TOKEN, url: "http://localhost:3000"}])`
  - 1st attempt: `test.skip(!HAS_AUTH)` in beforeEach
  - 2nd attempt: moved `test.skip(!HAS_AUTH)` to each test body
- 1 MODIFIED `.github/workflows/ci.yml` (+28 lines):
  - NEW step "Mint DEV_ACCESS_TOKEN for csv-export.spec.ts (cj-292 D-WEB-E2E-7 fix)" BEFORE playwright test
  - UUIDv5 namespace matches `scripts/dev_seed.py:53 _NS` verbatim
  - `dev_seed.py --token-only --tenant-id $DEV_TENANT_REPORT_ID --user-id $DEV_USER_REPORT_ID --role owner`
  - Exports DEV_TENANT_REPORT_ID + DEV_ACCESS_TOKEN to $GITHUB_ENV

## CI verification 결과 (2 attempts)

### CI run 34004020586 (head `0974371` 1st attempt)
- step 19 "Mint DEV_ACCESS_TOKEN" = **SUCCESS** (mint step works!)
- step 20 "playwright test --project=chromium" = **FAILURE** (52s duration, much shorter than expected)
- 13 job matrix unchanged

### CI run 34004518317 (head `0ec8ea5` 2nd attempt)
- step 19 "Mint DEV_ACCESS_TOKEN" = **SUCCESS**
- step 20 "playwright test --project=chromium" = **FAILURE** (62s duration, same pattern)
- 13 job matrix unchanged

### test-suite-measure P3 BLOCKING expected
- Both runs: test-suite-measure = FAILURE (expected per cj-282b baseline-green effort)
- Not regression — 비-MVP territory 45 failures 자연스러운 표면화

## 진단 한계 (admin rights blocked) 결정 wire

**CI log/artifact access blocked**:
- `/repos/c8romeo/costmgr/actions/runs/.../jobs/.../logs` → 403 "Must have admin rights"
- `/repos/c8romeo/costmgr/actions/artifacts/.../zip` → 401 "Requires authentication"
- playwright-report artifact 부재 in artifacts API list (step 21 SUCCESS 보고에도 불구하고 actual report directory empty = no tests ran OR all tests failed before report generation)

**root cause NOT isolated 결정 wire** — 2회 시도 모두 web-e2e step 20 fail 패턴 동일, logs 접근 불가 → blind guessing 한계 도달.

## honest recovery 결정 wire (CR 11-3 honest-DEFER 229~232번째)

`git revert --no-edit 0ec8ea5 0974371` (2 revert commits) + push → PRE-EXISTING 3/3 fail carryover **baseline state recovery 결정 wire** (cj-287~carryover honestly-DEFER 복귀).

**chain 보존 정직 보고**: 2 source commits + 2 revert commits = 4 commits cycle 정직 결정 wire 진입 (cj-style discipline chain pattern mirror — cj-282~cj-291 모두 cumulative 결정 wire 정직 보존, cj-292 cycle 도 동일 패턴 적용).

## CR 결정 wire verbatim 보존

- **CR 9-6 atomic commit** — `git revert --no-edit` 사용, PowerShell here-string 회피, 2 reverts atomic chain
- **CR 11-3 honest-DEFER 232번째** — chain cj-282 (220번째) → cj-291 (228번째) → **cj-292 (229~232번째)** 종합 11 sprints 정직 회복 결정 wire
- **CR 12-1 lessons carry** — blind debugging 한계 인정 + admin rights 요청 = honest recovery pattern

## 결정 wire + Lessons learned

### 결정 wire 6개
1. 2 commits + 2 reverts cycle 정직 결정 wire 진입 (cj-style discipline chain 보존)
2. PRE-EXISTING 3/3 fail carryover honestly-DEFER baseline state 회복 결정 wire
3. working tree baseline recovery (net 0 source change)
4. 13 job matrix unchanged (cj-282b baseline-green 보존)
5. CR 11-3 honest-DEFER 232번째 epic 연속 정직 회복
6. 사용자 진단 override 권장 결정 wire 보류 (admin token 제공 시 retry)

### Lessons learned (4종)
1. **CI log admin rights 부재 시 blind debugging 불허** — root cause isolation 불가 → revert + honestly-DEFER 가 safest recovery
2. **PRE-EXISTING 5 sprints honestly-DEFER carryover 는 baseline state 에 안정적으로 머무름** — pilot gate 직접 차단 안 됨 (pilot customer 는 dev_seed fixtures 없이도 manual export 가능 via UI 직접 호출 + tenantId prompt)
3. **fix forward 시도 의 2 commits + 2 reverts = 4 commits cycle 의 chain 결정 wire 정직 보존** (cj-style discipline)
4. **사용자 진단 override 권장**: GitHub Actions admin token 발급 → CI log 직접 fetch → root cause isolation → 재시도 진입 결정 wire (사용자 승인 시)

## 다음 결정 wire 보류 (사용자 결정 대기)

- 옵션 (a) cj-293 wire sprint — Epic 30+ capability matrix v1.55 EXTENSION OR Story 30.2 PDF export (OQ-EPIC30+-1 + OQ-EPIC30+-4 결정) — PRE-EXISTING 3/3 fail 그대로 honestly-DEFER
- 옵션 (b) cj-293 fix forward v2 — cj-292 의 blind debugging 한계 인정, 사용자 admin token 제공 후 root cause isolation → retry (Risk: Medium, diagnostic 가능 시 success 가능성)
- 옵션 (c) Epic 29+ spec implementation chain 진입 (cj-29x-impl territory) — 18 spec drifts unresolved
- 옵션 (d) Pilot 고객 유치 결정 wire (PRD OQ-3 파일럿 게이트 1주 post M0-M6) — cj-292 revert 후 PRE-EXISTING fail carryover 그대로 (pilot gate 직접 unblock 효과 0)

## Related 결정 wire

- [cj-287 wire sprint `5c37446` — D-WEB-E2E-7 ownership ACTIVATED 결정 wire](handoff-2026-09-06-cj-287-csv-e2e-activate-sprint-done.md)
- [cj-288 wire sprint `b91906a` — alembic migration 결정 wire](handoff-2026-09-06-cj-288-cost-records-bom-matrix-migration-done.md)
- [cj-289 close-out wrap-up 결정 wire](handoff-2026-09-06-cj-289-wire-sprint-done.md)
- [cj-290 RLS EXTENSION wire sprint `1ba4309` 결정 wire](handoff-2026-09-06-cj-290-rls-extension-done.md)
- [cj-291 close-out retro `0ce88ad` 결정 wire](handoff-2026-09-06-cj-291-rls-extension-close-retro-done.md)
- **cj-292 ATTEMPTED + REVERTED (본 document)** — Epic 30+ csv-export 3/3 PRE-EXISTING carryover honestly-DEFER 복귀 결정 wire

## 결정 wire 일자 + 멤버

- **결정 wire 일자**: 2026-09-06 (KST)
- **결정 wire 작성**: kjw
- **결정 wire 검증**: cj-style 292번째 + 292 follow-up #1 + 232번째 honest-DEFER cycle 결정 wire 진입
- **결정 wire 멤버**: cj-style chain 282~292 12 sprints cumulative 결정 wire 정직 보존
