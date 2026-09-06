---
name: cj-288-cost-records-bom-matrix-migration-done
description: cj-288 wire sprint (cj-style 288번째 source-only atomic single sprint) — Epic 30+ cost_records + bom_matrix alembic migration 결정 wire + CI step 15 unblock + step 19 still failing
metadata:
  type: project
---

# cj-288 wire sprint 결정 wire (cj-style 288번째 source-only atomic single sprint)

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: cj-282 Epic 30+ PRD entry `0c7524e` 의 Story 30.1 CSV export territory (cj-287 follow-up #2 commit `d8d4df0` 의 PRE-EXISTING carryover 정직 회복)
**chain CLOSED 직후 진입**: cj-287 follow-up #2 `d8d4df0` 의 옵션 (a) cj-288 wire sprint 진입 = 본 sprint

## sprint scope 결정 wire — 1 file = 1 NEW alembic migration source-only atomic single sprint

### 1 NEW source
1. `apps/api/alembic/versions/0060_cost_records_and_bom_matrix.py` (~204 LOC)
   + revision = "0060_cost_records_and_bom_matrix"
   + down_revision = "0059_phase_28_interactive_dashboard"
   + CREATE TABLE IF NOT EXISTS `cost_records` (14 columns verbatim from
     `scripts/dev_seed.py:1455-1466` INSERT columns + `apps/api/modules/
     reports/csv_routes.py:300-303` SELECT columns 1:1 match)
   + CREATE INDEX `idx_cost_records_tenant_period` ON (tenant_id, period_key)
     — csv_routes.py:303 PRIMARY path (NFR5 streaming P95 ≤ 5s 결정 wire)
   + CREATE TABLE IF NOT EXISTS `bom_matrix` (13 columns verbatim from
     `scripts/dev_seed.py:1515-1522` INSERT columns + csv_routes.py:324-330
     SELECT columns 1:1 match, bom_level = 1 dev_seed 결정 wire 보존)
   + CREATE INDEX `idx_bom_matrix_tenant_period` ON (tenant_id, period_key)
   + CREATE INDEX `idx_bom_matrix_tenant_period_level` ON
     (tenant_id, period_key, bom_level) — bom_level=1 filter path
   + downgrade() — DROP INDEX/TABLE reverse order (FK dependents first)

### 1 NEW meta
1. `_bmad-output/implementation-artifacts/commit-msg-cj-288.txt` (~140 LOC)

## 0031 → 0060 번호 결정 wire 보존

cj-287 follow-up #2 commit `d8d4df0` 의 "0031_cost_records_and_bom_matrix.py
(or similar)" 권고 verbatim 보존. 0031 alembic version conflict (0031_ai_insight_
comments.py cj-style 32번째 Story 10.3 commit `ea025b1` 점유) → next available
0060 사용 결정 wire. Migration filename = 0060_cost_records_and_bom_matrix 결정
wire 보존.

## CI run 34000480618 결과 분석 (head `b91906a` cj-288)

### web-e2e job 27 steps 분석
- Step 13 "Apply Alembic migration" = **SUCCESS** (0060 적용 결정 wire 진입)
- Step 14 "Apply RLS policies" = SUCCESS
- Step 15 "Run dev seed --scenario all" = **SUCCESS** (relation does not
  exist error 해결 — cj-287 follow-up #2 의 honest-DEFER carryover 정직 회복)
- Step 16 "Boot uvicorn" = SUCCESS
- Step 17 "Playwright install chromium" = SUCCESS
- Step 18 "V8 fixture suite" = SUCCESS
- **Step 19 "playwright test --project=chromium" = FAILURE** (BUT actually
  RAN — not SKIPPED 결정 wire 진입)
- Step 20 "Upload Playwright report" = SUCCESS
- Step 21 "Upload uvicorn log" = SUCCESS

### 🎉 결정 wire milestone (cj-288 1차 정직 회복)

cj-287 follow-up #2 의 honest-DEFER 224번째 의 **PRE-EXISTING carryover 정직
회복** 결정 wire 진입:
- 직전 CI run 33999439554 (head `d8d4df0`): step 15 FAIL → step 16-19 모두
  SKIPPED → step 19 csv-export 3/3 NEVER RAN (silent RED)
- 본 sprint 후 CI run 34000480618 (head `b91906a`): step 15 SUCCESS →
  step 16-19 모두 ACTUAL EXECUTION → **step 19가 실제로 실행됨**

### web-e2e step 19 csv-export 3/3 passed 정직 보고

**3/3 passed 확인 결과: NOT YET** — step 19 여전히 exit code 1
(failure). 그러나 step 19가 실제로 실행된다는 사실 자체가 cj-287 의
D-WEB-E2E-7 ownership wire 의 verification milestone 진입 결정 wire 보존.

Job logs/artifacts fetch blocked:
- `GET /actions/runs/34000480618/jobs/101398374601/logs` → 403 (Must have
  admin rights to Repository)
- `GET /actions/artifacts/9979367275/zip` → 401 (Requires authentication)
- 사용자가 GitHub Actions 페이지 직접 확인 필요:
  `https://github.com/c8romeo/costmgr/actions/runs/34000480618/job/101398374601#step:19:1`

## 결정 wire 정합 (cj-282 PRD entry AD/NFR bind verbatim)

### AD bind 3/3 (cj-282 PRD entry §F44.1 verbatim)
- **AD-2** (audit-first INSERT append-only) — 본 table 자체는 append-only 와
  무관 (CSV export = read-only query against cost_records/bom_matrix).
  export event 자체는 audit_logs 에 INSERT (cj-287 wire sprint `5c37446` 의
  csv_routes.py:362 fix 보존).
- **AD-3** (RLS 정합) — tenant_id FK to tenants(id) ON DELETE CASCADE +
  tenant_id+period_key index 결정 wire 진입. RLS policies 는 별도 sprint
  (supabase/policies/0060_cost_records_and_bom_matrix_rls.sql 결정 wire)
  EXTENSION territory 보류 — dev_seed 는 postgres role (BYPASSRLS) 사용
  → RLS 부재가 dev_seed step 15 회복에는 무관 결정 wire.
- **AD-15** (SSOT) — id UUID DEFAULT gen_random_uuid() 결정 wire (CSV export
  spec 호환). tenant_id UUID v4 JWT-derived 결정 wire 보존.
- **AD-22** (owner-only RBAC verbatim) — csv_routes.py 의 `require_any_role
  ("owner", "admin")` 결정 wire 보존 (cj-287 wire sprint 진입 완료).

### NFR bind 2/7 active (cj-282 PRD entry §F44 NFR 매트릭스)
- **NFR5** (streaming P95 ≤ 5s for 10만 row) — idx_cost_records_tenant_period
  composite index 결정 wire 보존 + idx_bom_matrix_tenant_period 결정 wire
  보존.
- **NFR18** (ko-KR vocabulary SSOT) — comment ON TABLE 결정 wire 보존.

### CR 결정 wire verbatim 보존
- **CR 0-2 RLS** — tenant_id FK + index (RLS policies 별도 결정 wire).
- **CR 1-1 audit-first INSERT** — cj-287 fix 보존 (csv_routes.py:362
  ActionClass.REPORTS).
- **CR 9-6 atomic commit** — `git commit -F <file>` convention + commit-msg
  file verbatim 결정 wire 보존.
- **CR 11-3 honest-DEFER 225번째** — 본 sprint 의 cj-287 carryover 정직
  회복 결정 wire.
- **CR 11-4 P-015 pure validator pattern** — csv_routes.py 의 `_iter()`
  generator + `StreamingResponse` 결정 wire 보존.
- **CR 12-5 D-14 typed exception envelope** — cj-287 wire sprint 의 4 NEW
  exception handlers 보존.

## Pre-existing carryover 결정 wire 정직 회복

**HONEST reporting correction**: cj-287 follow-up #2 commit `d8d4df0`
본문 verbatim:
> "cj-288+ follow-up sprint 결정 wire 진입 필요: create Alembic
> migration `0031_cost_records_and_bom_matrix.py` (or similar) to
> create the missing tables + verify dev_seed `--scenario all`
> completes cleanly."

본 sprint 가 cj-287 의 PRE-EXISTING carryover 정직 회복 결정 wire 진입.
0031 alembic version conflict 결정 wire (0031_ai_insight_comments.py
cj-style 32번째 Story 10.3 commit `ea025b1` 점유) → next available
0060 사용 결정 wire. Migration filename = 0060_cost_records_and_
bom_matrix 결정 wire 보존.

## runtime 동작 변화 honestly reported

- source-only atomic single sprint — 1 file = 1 NEW alembic migration
  결정 wire 진입.
- apps/api/alembic/versions/0060_cost_records_and_bom_matrix.py: 204 LOC
  결정 wire 진입 (CREATE TABLE 2 + CREATE INDEX 3 + COMMENT 2 + DROP
  reverse order 5).
- ci.yml 변경 0 결정 wire 보존.
- dev_seed 변경 0 결정 wire 보존 (cj-286 EXTENSION 의 `_seed_report_
  fixtures` 보존).
- CSV export endpoint 변경 0 (csv_routes.py 보존).
- AD-14 stack pin (35 pins) 변경 없음 / [STACK BUMP] tag 불필요 결정
  wire 보존.
- 13 job matrix unchanged (cj-style baseline-green 보존).
- capability matrix v1.54 EXTENSION preserved from cj-285 EXTENSION wire
  sprint 결정 wire 보존 (no change at v1.55).
- audit action EXTENSION preserved from cj-285 EXTENSION wire sprint
  결정 wire 보존 (no change at v1.55).

## Lint 검증 결과 (CI 결정 wire 보존)

- `uv run ruff check apps/api packages` → All checks passed! 결정 wire.
- `uv run ruff format --check apps/api packages` → 386 files already
  formatted 결정 wire.
- `python scripts/check_money_types.py` → no errors 결정 wire.
- `python scripts/check_migration_money.py` → `[migration-money] OK
  apps\api\alembic\versions\0060_cost_records_and_bom_matrix.py` 결정 wire.
- `python scripts/check_migration_naming.py` → `[migration-naming] OK
  apps\api\alembic\versions\0060_cost_records_and_bom_matrix.py` 결정 wire.
- CI lint-conventions job (101398374506) → SUCCESS 결정 wire.

## Cross-References

- cj-282 Epic 30+ PRD entry: `0c7524e` (cj-style 220번째)
- cj-282a Story 30.1 CSV source+docs: `eae9110` (cj-style 283번째)
- cj-282a lint-conventions fix: `e803ae2` (cj-style 283 follow-up)
- cj-282a close-out retro: `7403920` (cj-style 284번째)
- cj-285 EXTENSION wire sprint (capability + audit): `215e963` (cj-style 285번째)
- cj-286 EXTENSION wire sprint (fixtures + spec + AD-56): `e408668` (cj-style 286번째)
- cj-287 wire sprint (CSV E2E activation + CR 1-1 fix): `5c37446` (cj-style 287번째)
- cj-287 follow-up #1: `c398d80` (ruff format + vitest tenantId)
- cj-287 follow-up #2: `d8d4df0` (ESLint unused vars + carryover doc)
- **cj-288 wire sprint** (cost_records + bom_matrix migration + step 15 unblock): `b91906a` (cj-style 288번째)
- CI run 34000480618: `b91906a` (in_progress at handoff 작성 시점)
- AD-56: `docs/architecture-decisions/AD-56-phase-30-epic-30-plus-reporting-export-decisions.md`

## Next (cj-289+ 결정 wire 보류)

cj-288 wire sprint 의 chain unblock 결정 wire 보존. **step 19 csv-export
3/3 passed 는 추가 sprint 진입 필요** (cj-289+ territory):
- 옵션 (a) cj-289 wire sprint (cj-style 289번째, RECOMMENDED next) — step 19
  failure root cause 분석 + fix. CSV API endpoint response, JWT decode
  tenantId, dev_seed fixture timing, UI testid visibility 등 결정 wire 진입.
- 옵션 (b) cj-288 close-out retro 결정 wire (cj-style 289번째) — 14-section
  §1~§14 verbatim retro document 진입.
- 옵션 (c) Epic 30+ RLS EXTENSION wire sprint (cj-style 290번째) —
  supabase/policies/0060_cost_records_and_bom_matrix_rls.sql 결정 wire
  진입 (production tenant isolation 보장).
- 옵션 (d) Epic 29+ spec implementation chain 진입 결정 wire (cj-29x
  territory) — 18 spec drifts unresolved + 18 stories × multi-sprint.
- 옵션 (e) Pilot 고객 유치 결정 wire 진입 (PRD OQ-3 파일럿 게이트 1주
  post M0-M6).
- 옵션 (f) cj-290 Story 30.2 PDF export wire sprint (cj-style 290번째)
  결정 wire — weasyprint vs reportlab 결정 + Jinja2 ko-KR template +
  matplotlib 3 charts 결정 wire 진입 (cj-282 PRD entry OQ-EPIC30+-1 +
  OQ-EPIC30+-4 결정 보류 해소).
- 옵션 (g) cj-291 Epic 30+ capability matrix sync EXTENSION (cj-style
  291번째) — capability matrix v1.54 EXTENSION 결정 wire 보완 + 4 audit
  actions sync (이미 cj-285 EXTENSION 결정 wire, close-out retro only
  결정).

**결정 wire 진입 완료** + **step 19 csv-export 3/3 passed follow-up 결정
wire 보류**.
