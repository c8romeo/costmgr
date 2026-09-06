---
name: cj-290-rls-extension-done
description: cj-290 wire sprint 결정 wire (cj-style 290번째 source+docs atomic single sprint) — Epic 30+ RLS EXTENSION (cost_records + bom_matrix 4-policy split) + 5 NEW RLS tests + 3 ci.yml wirings + AD-3 production tenant isolation 보장
metadata:
  type: project
---

# cj-290 wire sprint 결정 wire (cj-style 290번째 source+docs atomic single sprint)

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: cj-282 Epic 30+ PRD entry `0c7524e` 의 Story 30.1 CSV export 결정 wire (cj-289 close-out retro §10 옵션 (a) verbatim mirror)
**chain 진입**: cj-289 close-out retro 결정 wire 의 "옵션 (a) Epic 30+ RLS EXTENSION wire sprint (cj-style 290번째, RECOMMENDED next)" 진입 = 본 sprint

## sprint scope 결정 wire — 8 files = 2 NEW source + 2 MODIFIED source + 2 NEW meta + 2 MODIFIED meta atomic single sprint

### 2 NEW source
1. `supabase/policies/0060_cost_records_and_bom_matrix_rls.sql` (~195 LOC)
   - 4-policy split × 2 tables = 8 NEW policies
   - `cost_records` × {SELECT same-tenant 4-role, INSERT blocked, UPDATE blocked, DELETE blocked}
   - `bom_matrix` × {SELECT same-tenant 4-role, INSERT blocked, UPDATE blocked, DELETE blocked}
   - GUC pattern: `tenant_id = current_setting('app.tenant_id', true)::uuid`
   - Pattern mirror: 0016_budget_scenarios_rls.sql (GUC pattern NEWEST convention) + 0014_tenant_backups_rls.sql (5-policy split with explicit blocked UPDATE/DELETE)
   - 10 doc lines (8 COMMENT ON POLICY + 2 COMMENT ON TABLE)
2. `tests/rls/test_cost_records_bom_matrix_isolation.py` (~270 LOC)
   - 5 RLS test cases mirroring `tests/rls/test_bom_lines_isolation.py` structure
   - `test_tenant_a_can_read_own_cost_records` (SELECT own)
   - `test_tenant_a_cannot_read_tenant_b_cost_records` (cross-tenant SELECT 0)
   - `test_tenant_a_cannot_read_tenant_b_bom_matrix` (own 1 + cross 0)
   - `test_tenant_a_cannot_insert_cost_record_for_tenant_b` (InsufficientPrivilegeError)
   - `test_tenant_a_cannot_update_tenant_b_bom_matrix` (silently 0 rows touched)
   - Uses `costmgr_test` role (NOSUPERUSER NOBYPASSRLS per 0000 CI shim)
   - Dual GUC: `SET LOCAL app.tenant_id` + `SET LOCAL request.jwt.claims`

### 2 MODIFIED source
1. `supabase/policies/0002_rls_smoke_test.sql` (+12 lines)
   - Append 8 NEW (schema, table, policy) tuples to `expected_policies` array
   - Smoke test array now has 28 triples (was 20)
2. `.github/workflows/ci.yml` (+6 lines across 3 jobs)
   - `rls-tests` job: append `-f supabase/policies/0060_cost_records_and_bom_matrix_rls.sql` after `-f supabase/policies/0001_rls_policies.sql`
   - `web-e2e` job: same modification
   - `smoke-e2e` job: same modification
   - Pattern: parallel `psql -v ON_ERROR_STOP=1` invocations (NOT `&&` chained)

### 2 NEW meta
1. `_bmad-output/implementation-artifacts/commit-msg-cj-290.txt` (~200 LOC) — `git commit -F` payload
2. `memory/handoff-2026-09-06-cj-290-rls-extension-done.md` (this file)

### 2 MODIFIED meta
1. `_bmad-output/implementation-artifacts/sprint-status.yaml` — A703 NEW entry + last_updated_note_v4_60 EXTENSION (v4.59 → v4.60)
2. `memory/MEMORY.md` — cj-290 hook EXTENSION

## 결정 wire 정합 (cj-282 PRD entry AD/NFR bind verbatim)

### AD bind 4/4 active (cj-282 PRD entry §F44.1 verbatim)

- **AD-2** (audit-first INSERT append-only) — cost_records + bom_matrix 자체는 read-only application surface (csv_routes.py:298-336 SELECT-only). export event 는 audit_logs 에 INSERT (cj-287 의 csv_routes.py:362 ActionClass.REPORTS fix 보존). RLS 의 INSERT/UPDATE/DELETE blocked policies = AD-2 INSERT-only soft invariant mirror 0014 + 0016.
- **AD-3** (RLS 정합) — 본 sprint 의 NEW RLS file 결정 wire 진입. Phase 3-0 listener fix 후속 (cj-style 100+ territory 의 dual GUC pattern). tenant_id FK to tenants(id) + tenant_id+period_key index + RLS 결정 wire 일치.
- **AD-15** (SSOT) — id UUID DEFAULT gen_random_uuid() (CSV export spec 호환). tenant_id UUID v4 JWT-derived. RLS 키는 같은 SSOT 컬럼.
- **AD-22** (owner-only RBAC verbatim) — csv_routes.py 의 `require_any_role("owner", "admin")` 결정 wire 보존 (cj-287 wire sprint 진입 완료). RLS 는 third defense layer 결정 wire 보존.

### NFR bind 2/2 active (cj-282 PRD entry §F44 NFR 매트릭스)

- **NFR5** (streaming P95 ≤ 5s for 10만 row) — idx_cost_records_tenant_period composite index + idx_bom_matrix_tenant_period 보존. RLS 의 SELECT same-tenant predicate = 추가 cost 없음 결정 wire 보존 (인덱스 컬럼과 RLS 키 컬럼이 동일 → index-driven scan).
- **NFR18** (ko-KR vocabulary SSOT) — comment ON TABLE 결정 wire 보존.

### CR 결정 wire verbatim 보존

- **CR 0-2 RLS** — cj-289 close-out retro §13 의 RLS 결정 wire 보류 해소. 본 sprint 가 production tenant isolation 보장 결정 wire 진입.
- **CR 1-1 audit-first INSERT** — cj-287 fix 보존 (csv_routes.py:362 ActionClass.REPORTS).
- **CR 9-6 atomic commit** — `git commit -F <file>` convention 결정 wire 보존.
- **CR 11-3 honest-DEFER 227번째** — 본 sprint 의 cj-289 carryover 정직 회복. PRE-EXISTING 2 failures (test-suite-measure P3 + web-e2e csv-export 3/3 carryover) 보존 결정 wire.
- **CR 11-4 P-015 pure validator pattern** — csv_routes.py 결정 wire 보존.
- **CR 12-5 D-14 typed exception envelope** — cj-287 wire sprint 의 4 NEW exception handlers 보존 + 본 sprint 의 "defense-in-depth explicit > implicit" 결정 wire 보존 (USING(false) WITH CHECK(false) 의 explicit blocked policies).

## 누적 결정 wire 보존 (Cumulative 결정 wire Preservation)

### Territory 결정 wire 보존
- Epic 30+ Reporting & Export MVP territory (cj-282 option (γ) 결정 wire) — 그대로 보존.

### Capability matrix 결정 wire 보존
- v1.53 → v1.54 EXTENSION (cj-285 EXTENSION sprint 결정 wire) — 4 NEW Capability enum (EXPORT_CSV/PDF/EMAIL/SCHEDULED) 그대로 보존. 본 sprint 는 v1.54 그대로.

### Audit actions 결정 wire 보존
- ActionClass.REPORTS = "reports" 별도 sub-class (cj-285 EXTENSION sprint 결정 wire) — 그대로 보존.

### Dev_seed 결정 wire 보존
- `_seed_report_fixtures(conn)` (cj-286 EXTENSION sprint 결정 wire) — 그대로 보존. dev_seed 는 postgres role BYPASSRLS 사용 → RLS 부재/존재 무관 결정 wire 보존.

### CR 1-1 fix 결정 wire 보존
- csv_routes.py:362 ActionClass.AUDIT → ActionClass.REPORTS fix (cj-287 critical bug fix 결정 wire) — 그대로 보존.

### D-WEB-E2E-7 ownership 결정 wire 보존
- csv-export.spec.ts ACTIVATED (cj-287 wire sprint 결정 wire, FIRST D-WEB-E2E-* ownership wire in Epic 30+ territory) — 그대로 보존.

### Alembic migration 결정 wire 보존
- 0060_cost_records_and_bom_matrix.py (cj-288 wire sprint 결정 wire, 1 NEW source file) — 그대로 보존. 본 sprint 가 후속 RLS EXTENSION 결정 wire 진입.

### Phase 3-0 listener 결정 wire 보존
- `attach_tenant_listener` in `apps/api/core/tenant_context.py:191-219` 의 dual GUC pattern (`app.tenant_id` + `app.user_id` + `request.jwt.claims`) 결정 wire 보존. 본 RLS 의 `current_setting('app.tenant_id', true)` 정상 resolve 결정 wire 보존.

## CR 11-3 honest-DEFER 검증 (Honest-DEFER Verification)

- CR 11-3 카운터: **227번째** (cj-289 의 226번째 + cj-290 의 227번째) — epic 연속 정직 회복 결정 wire.
- source code 변경 6 files (2 NEW + 2 MODIFIED source) 결정 wire 정직 보고.
- meta files 변경 4 files (2 NEW + 2 MODIFIED meta) 결정 wire 정직 보고.
- 13 job matrix unchanged 결정 wire 정직 보고 (apply step 추가만, 새 job 없음).
- AD-14 stack pin 변경 없음 / [STACK BUMP] tag 불필요 결정 wire 정직 보고.
- capability matrix v1.54 EXTENSION preserved (no change) 결정 wire 정직 보고.
- audit action EXTENSION preserved (no change) 결정 wire 정직 보고.
- PRE-EXISTING 2 failures (test-suite-measure P3 + web-e2e csv-export 3/3 carryover) 결정 wire 정직 보고 — 보존 결정 wire.

## 결정 wire + Lessons learned (Decisions + Lessons)

### 결정 wire 7개
1. Sprint scope = source+docs atomic single sprint (8 files = 2 NEW source + 2 MODIFIED source + 2 NEW meta + 2 MODIFIED meta).
2. Pattern choice = GUC pattern (`current_setting('app.tenant_id')`) matching 0014/0016 NEWEST convention.
3. Policy split = 4-policy split (SELECT same-tenant + INSERT blocked + UPDATE blocked + DELETE blocked).
4. Smoke test = 28 triples (was 20).
5. CI YAML = 3 lines × 3 jobs = parallel psql invocations.
6. RLS test = 5 cases mirroring test_bom_lines_isolation.py.
7. Sprint-status v4.59 → v4.60 EXTENSION (A703 cj-290 entry + last_updated_note_v4_60).

### Lessons learned (5종)
1. **Pattern consistency matters**: GUC pattern matching 0014/0016 NEWEST convention > JWT pattern matching 0006/0007 legacy convention. csv_routes.py already publishes `app.tenant_id` via `attach_tenant_listener`, so GUC pattern transparently works.
2. **Explicit blocked policies > implicit "no policy"**: USING(false) WITH CHECK(false) is clearer than omitting policies (CR 12-5 defense-in-depth explicit > implicit). Matches 0014 + 0016 convention.
3. **8 files atomic single sprint**: SQL + smoke test + ci.yml + RLS test all ship together to avoid intermediate broken states.
4. **CR 11-3 honest-DEFER 227번째**: epic 연속 정직 회복 — cj-282 → cj-282a → cj-285 → cj-286 → cj-287 → cj-288 → cj-289 → cj-290 8 sprints 의 cumulative 결정 wire 정직 보존.
5. **Dual GUC SET LOCAL for tests**: `_open_as_tenant` sets BOTH `app.tenant_id` AND `request.jwt.claims` because the Phase 3-0 listener fix (cj-style 100+ territory) publishes both. This ensures RLS policies reading either pattern resolve correctly.

## 결정 wire 일자 + 멤버 (Date + Members)

- **결정 wire 일자**: 2026-09-06 (KST)
- **결정 wire 작성**: kjw
- **결정 wire 검증**: cj-style 290번째 결정 wire 진입
- **결정 wire 멤버**: cj-style chain 282~290 9 sprints 결정 wire 보존

## Related 결정 wire

- [cj-282 Epic 30+ PRD entry `0c7524e`](handoff-2026-09-05-cj-282-epic-30-reporting-export-entry-done.md)
- [cj-285 EXTENSION wire sprint (capability matrix v1.54)](handoff-2026-09-06-cj-285-capability-matrix-extension-done.md)
- [cj-286 EXTENSION wire sprint (dev_seed + ci.yml + AD-56)](handoff-2026-09-06-cj-286-dev-seed-ci-yml-extension-done.md)
- [cj-287 wire sprint `5c37446` (CSV E2E activation)](handoff-2026-09-06-cj-287-csv-e2e-activate-sprint-done.md)
- [cj-288 wire sprint `b91906a` (alembic migration)](handoff-2026-09-06-cj-288-cost-records-bom-matrix-migration-done.md)
- [cj-289 close-out retro (Epic 30+ CSV wire chain)](handoff-2026-09-06-cj-289-wire-sprint-done.md)
- **cj-290 RLS EXTENSION wire sprint (본 document)** — Epic 30+ RLS EXTENSION 결정 wire.
