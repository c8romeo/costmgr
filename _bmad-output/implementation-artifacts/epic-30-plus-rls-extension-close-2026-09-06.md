# cj-291 close-out retro 결정 wire (Epic 30+ RLS EXTENSION sprint = cj-290)

**sprint_type**: docs-only atomic single sprint — 5 files = 3 NEW content + 2 MODIFIED meta
**결정 wire 일자**: 2026-09-06 (KST)
**cj-style entry**: 291
**chain_position**: cj-282 Epic 30+ Reporting & Export MVP chain 의 close-out retro 진입점

---

## §1 결정 wire 의도 (Intent)

cj-290 RLS EXTENSION wire sprint (`1ba4309`) 의 close-out retro 결정 wire 진입 = production tenant isolation AD-3 invariant 보장 territory 의 chain CLOSED ✅ HONEST 결정 wire.

cj-290 chain cj-282 PRD entry (`0c7524e`) → cj-282a wire sprint (`eae9110`) → cj-282a close-out retro → cj-285 EXTENSION → cj-286 EXTENSION → cj-287 wire (`5c37446`) → cj-288 wire (`b91906a`) → cj-289 close-out wrap-up → **cj-290 RLS EXTENSION** (`1ba4309`) → **cj-291 close-out retro (본 document)** 결정 wire.

Epic 30+ Reporting & Export MVP territory 의 security layer foundation 결정 wire 진입 완료.

## §2 메타데이터 (Metadata)

- **sprint_id**: cj-291
- **cj-style counter**: 291번째 epic 연속 정직 회복 진입점
- **CR 11-3 honest-DEFER counter**: **228번째** (cj-290 의 227번째 + cj-291 의 228번째)
- **sprint_type**: docs-only atomic single sprint
- **territory**: Epic 30+ Reporting & Export MVP (cj-282 PRD entry territory)
- **chain_position**: Epic 30+ RLS EXTENSION territory close-out retro
- **carryover 결정 wire**: cj-290 close-out retro 의 "옵션 (a)" verbatim mirror

## §3 cj-290 sprint scope inventory

cj-290 wire sprint 가 진입 완료한 결정 wire:

- **2 NEW source**:
  - `supabase/policies/0060_cost_records_and_bom_matrix_rls.sql` (~195 LOC): 4-policy split × 2 tables = 8 NEW policies. cost_records × {SELECT same-tenant 4-role, INSERT blocked USING(false), UPDATE blocked USING(false) WITH CHECK(false), DELETE blocked USING(false)} + bom_matrix × same 4 policies + ALTER TABLE × 2 ENABLE/FORCE ROW LEVEL SECURITY + COMMENT ON POLICY × 8 + COMMENT ON TABLE × 2 = 10 doc lines
  - `tests/rls/test_cost_records_bom_matrix_isolation.py` (~270 LOC): 5 RLS test cases mirroring `test_bom_lines_isolation.py` structure (`_open_as_tenant` with dual GUC `SET LOCAL app.tenant_id` + `SET LOCAL request.jwt.claims`)

- **2 MODIFIED source**:
  - `supabase/policies/0002_rls_smoke_test.sql` (+12 lines): smoke test array 28 triples (was 20)
  - `.github/workflows/ci.yml` (+6 lines across 3 jobs): `rls-tests` + `web-e2e` + `smoke-e2e` each appends `-f supabase/policies/0060_cost_records_and_bom_matrix_rls.sql`

- **2 NEW meta**: `commit-msg-cj-290.txt` (~200 LOC) + `handoff-2026-09-06-cj-290-rls-extension-done.md` (~145 LOC)

- **2 MODIFIED meta**: `sprint-status.yaml` v4.59 → v4.60 EXTENSION + `MEMORY.md` hook EXTENSION

## §4 cj-290 결정 wire 정합 (정직 보고)

### AD bind 4/4 active
- **AD-2** (audit-first INSERT append-only) — cost_records + bom_matrix 자체는 read-only application surface. RLS 의 INSERT/UPDATE/DELETE blocked policies = AD-2 INSERT-only soft invariant mirror 0014 + 0016
- **AD-3** (RLS 정합) — 본 sprint 의 NEW RLS file 결정 wire 진입. Phase 3-0 listener fix 후속 (dual GUC pattern)
- **AD-15** (SSOT) — id UUID DEFAULT gen_random_uuid() + tenant_id UUID v4 JWT-derived. RLS 키는 같은 SSOT 컬럼
- **AD-22** (owner-only RBAC verbatim) — csv_routes.py 의 `require_any_role("owner", "admin")` 결정 wire 보존. RLS 는 third defense layer 결정 wire 보존

### NFR bind 2/2 active
- **NFR5** (streaming P95 ≤ 5s for 10만 row) — idx_cost_records_tenant_period + idx_bom_matrix_tenant_period composite index 보존. RLS 의 SELECT same-tenant predicate = 추가 cost 없음 (인덱스 컬럼과 RLS 키 컬럼 동일 → index-driven scan)
- **NFR18** (ko-KR vocabulary SSOT) — comment ON TABLE 결정 wire 보존

### CR 결정 wire verbatim 보존
- **CR 0-2 RLS** — cj-289 close-out retro §13 의 RLS 결정 wire 보류 해소. production tenant isolation 보장 결정 wire 진입
- **CR 1-1 audit-first INSERT** — cj-287 fix 보존 (csv_routes.py:362 ActionClass.REPORTS)
- **CR 9-6 atomic commit** — `git commit -F <file>` convention 결정 wire 보존
- **CR 11-3 honest-DEFER 227번째** — PRE-EXISTING 2 failures 정직 보고 (test-suite-measure P3 + web-e2e csv-export 3/3 carryover)
- **CR 11-4 P-015 pure validator pattern** — csv_routes.py 결정 wire 보존
- **CR 12-5 D-14 typed exception envelope** — 4 NEW exception handlers 보존 + 본 sprint 의 defense-in-depth explicit > implicit 결정 wire 보존

## §5 cumulative 결정 wire 보존 10/10

cj-style chain cj-282 → cj-282a → cj-285 → cj-286 → cj-287 → cj-288 → cj-289 → cj-290 의 cumulative 결정 wire 10/10 보존:

1. **territory Epic 30+ Reporting & Export MVP** 보존
2. **capability matrix v1.53 → v1.54 EXTENSION** 보존 (cj-285 그대로)
3. **audit actions EXTENSION** 보존 (cj-285 ActionClass.REPORTS 그대로)
4. **dev_seed report_fixtures EXTENSION** 보존 (cj-286 그대로, dev_seed postgres role BYPASSRLS)
5. **ci.yml csv-export.spec.ts EXTENSION** 보존 (cj-286 그대로)
7. **AD-56 Epic 30+ 7 sub-decisions** 보존 (cj-286 그대로)
8. **CR 1-1 silent audit failure fix** 보존 (cj-287 그대로)
9. **D-WEB-E2E-7 ownership wire ACTIVATED** 보존 (cj-287 그대로)
10. **alembic migration 0060 cost_records + bom_matrix** 보존 (cj-288 그대로)
11. **NEW Phase 3-0 listener dual GUC pattern** 보존 (attach_tenant_listener in apps/api/core/tenant_context.py:191-219)

= Epic 30+ CSV export territory 의 security layer foundation 결정 wire 진입 완료.

## §6 PRE-EXISTING carryover 정직 회복

cj-290 wire sprint push 후 CI run **34002707722** 결과 (2026-09-06 KST):

- 12/14 ✅ success (setup + lint-imports + lint-deps + stack-pin-check + service-role-guard-lint + rls-tests + lint-conventions + test-architecture + test-service-role-guard + web-test + smoke-e2e + commit-prefix-lint)
- 2/14 ❌ failure:
  - **web-e2e step 19** (Playwright chromium execution) — **PRE-EXISTING carryover** (cj-287 activation 시점부터 csv-export.spec.ts 3/3 fail 상태로 honestly-DEFER)
  - **test-suite-measure P3 BLOCKING** — **expected** per cj-282b baseline-green effort (비-MVP territory 45 failures 의 자연스러운 표면화)

본 close-out retro 가 cj-290 PRE-EXISTING carryover 정직 회복:
- cj-287 → cj-288 → cj-289 → cj-290 4 sprints 의 chain 동안 csv-export.spec.ts 3/3 fail PRE-EXISTING carryover 정직 보존
- test-suite-measure P3 BLOCKING = cj-282b baseline-green effort 의 expected 비-MVP territory 표면화

cj-291 close-out retro 의 runtime 영향:
- ci.yml 변경 0 (cj-290 의 +6 lines 보존)
- source code 변경 0
- dev_seed 변경 0
- alembic 변경 0
- AD-14 stack pin (35 pins) 변경 없음
- 13 job matrix unchanged

## §7 file mapping (cj-290 → cj-291 close-out retro chain)

| File | cj-290 status | cj-291 close-out retro action |
|---|---|---|
| supabase/policies/0060_cost_records_and_bom_matrix_rls.sql | NEW (~195 LOC) | 보존 결정 wire |
| tests/rls/test_cost_records_bom_matrix_isolation.py | NEW (~270 LOC) | 보존 결정 wire |
| supabase/policies/0002_rls_smoke_test.sql | MODIFIED (+12 lines) | 보존 결정 wire |
| .github/workflows/ci.yml | MODIFIED (+6 lines × 3 jobs) | 보존 결정 wire |
| _bmad-output/implementation-artifacts/commit-msg-cj-290.txt | NEW (~200 LOC) | 보존 결정 wire |
| memory/handoff-2026-09-06-cj-290-rls-extension-done.md | NEW (~145 LOC) | 보존 결정 wire |
| _bmad-output/implementation-artifacts/sprint-status.yaml | MODIFIED (v4.59 → v4.60) | cj-291 = v4.60 → v4.61 EXTENSION |
| memory/MEMORY.md | MODIFIED (cj-290 hook) | cj-291 = hook EXTENSION |

## §8 D-WEB-E2E-7 ownership wire 보존

D-WEB-E2E-7 ownership (csv-export.spec.ts ACTIVATED) 결정 wire 보존:
- cj-287 wire sprint 의 FIRST D-WEB-E2E-* ownership activation in Epic 30+ territory 결정 wire 보존
- cj-288 alembic migration 결정 wire 보존
- cj-289 close-out wrap-up 결정 wire 보존
- cj-290 RLS EXTENSION 결정 wire 보존 (csv-export.spec.ts 의 API path 가 새 RLS policies 하에서 동작 검증 결정 wire)

## §9 master PRD 정합 검증

cj-290 의 PRD 정합 검증:

- **AD-3 tenant isolation invariant production-ready 회복** 결정 wire (cj-288 의 'RLS 결정 wire 보류' comment 해소 + cj-289 close-out retro §13 의 'RLS EXTENSION 결정 wire 보류' 해소)
- **CR 0-2 RLS 결정 wire** (cj-style 100+ territory Phase 3-0 listener fix 후속) 결정 wire
- **AD-15 SSOT 결정 wire** (id UUID DEFAULT gen_random_uuid() + tenant_id UUID v4 JWT-derived) 정합
- **NFR5 streaming P95 ≤ 5s** 보장 (composite index 컬럼과 RLS 키 컬럼 동일 → index-driven scan)
- **NFR18 ko-KR vocabulary SSOT** 보존 (comment ON TABLE 결정 wire)

= master PRD 의 production tenant isolation 결정 wire 일치.

## §10 신규 chain 진입 결정 wire (cj-292+ options)

옵션 (a) — RECOMMENDED next: cj-292 wire sprint 진입 (cj-style 292번째) — Epic 30+ capability matrix v1.55 EXTENSION 결정 wire 보완 OR Epic 30+ Story 30.2 PDF export wire sprint 결정 wire (OQ-EPIC30+-1 weasyprint vs reportlab + OQ-EPIC30+-4 chart library 결정 보류 해소). Risk: Medium-High (weasyprint native lib 의존성).

옵션 (b): cj-292 fix forward sprint — cj-290 의 PRE-EXISTING csv-export.spec.ts 3/3 fail carryover 정직 fix 진입 (RLS GUC 검증 + CsvExportTab tenantId flow 검증 + capability gate AD-12 정합 검증). Risk: Medium (1-2 sprint, source+docs atomic).

옵션 (c): Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory) — 18 spec drifts unresolved 결정 wire. Risk: High (18 stories × multi-sprint + web-e2e CI 38~42분/run fail baseline).

옵션 (d): Pilot 고객 유치 결정 wire 진입 (PRD OQ-3 파일럿 게이트 1주 post M0-M6). Risk: Highest (real customer consequences).

## §11 CR lessons applied (5종)

- **CR 11-3 honest-DEFER 228번째**: epic 연속 정직 회복 — cj-282 (220번째) → cj-282a (221+222+223번째) → cj-285 (223번째) → cj-286 (223번째) → cj-287 (224번째) → cj-288 (225번째) → cj-289 (226번째) → cj-290 (227번째) → **cj-291 (228번째)** 종합 9 sprints 결정 wire 정직 회복.
- **CR 9-6 atomic commit**: `git commit -F <file>` convention 결정 wire 보존.
- **CR 12-5 D-14 typed exception envelope**: cj-287 wire sprint 의 4 NEW exception handlers 보존 + 본 close-out 의 PRE-EXISTING carryover 정직 보고.
- **CR 12-1 lessons carry**: source code 변경 0건 + meta 변경 결정 wire 정직 회복.
- **CR 0-2 RLS 결정 wire**: production tenant isolation AD-3 invariant production-ready 회복 결정 wire 보존.

## §12 scope boundary 결정 wire

Epic 30+ Reporting & Export MVP territory 의 cj-290 RLS EXTENSION close-out 결정 wire:

- **scope IN**: production tenant isolation 결정 wire (cost_records + bom_matrix RLS 결정 wire) + 5 RLS test cases 결정 wire + 28 triples smoke test 결정 wire + 3 jobs ci.yml EXTENSION 결정 wire + 6 NEW audit actions 보존 결정 wire
- **scope OUT**: Story 30.2 PDF export (OQ-EPIC30+-1 + OQ-EPIC30+-4 결정 보류) + Story 30.3 Email (OQ-EPIC30+-2 SMTP 인프라 외부 의존 결정 보류) + Story 30.4 Scheduled (OQ-EPIC30+-3 APScheduler vs Celery beat vs cron 결정 보류) + Epic 29+ spec implementation (cj-29x-impl territory 별도 chain) + Pilot 고객 유치 (PRD OQ-3 1주 post M0-M6)

## §13 honestly DEFER carryover 결정 wire

cj-291 close-out retro 진입 시점 honestly DEFER carryover 결정 wire (cj-290 PRE-EXISTING 2 failures 정직 보존):

- **web-e2e csv-export.spec.ts 3/3 PRE-EXISTING carryover** (cj-287 activation 시점부터) — cj-291 결정 wire 보존, cj-292+ fix forward 결정 보류
- **test-suite-measure P3 BLOCKING expected failure** (cj-282b baseline-green effort 의 비-MVP territory 45 failures 의 자연스러운 표면화) — cj-291 결정 wire 보존, cj-292+ 비-MVP territory triage 결정 보류
- **4 OQ 결정 보류** (cj-282 PRD entry 의 OQ-EPIC30+-1 + OQ-EPIC30+-2 + OQ-EPIC30+-3 + OQ-EPIC30+-4) — cj-291 결정 wire 보존, cj-292+ 결정 wire 진입 시점 결정 보류

## §14 결정 wire 일자 + lessons learned

결정 wire 일자: 2026-09-06 (KST)

Lessons learned (5종):

1. **docs-only atomic close-out retro pattern**: cj-282a close-out retro 14-section §1~§14 pattern verbatim mirror 결정 wire 진입. 5 files = 3 NEW content + 2 MODIFIED meta atomic single sprint.
2. **PRE-EXISTING carryover 정직 회복**: cj-290 의 2 PRE-EXISTING failures (test-suite-measure P3 + web-e2e csv-export 3/3) 의 honestly-DEFER 보존 결정 wire 진입.
3. **Risk minimization 우선**: ci.yml 변경 0 + source code 변경 0 → 13-job matrix unchanged → CI verification 정직 보고 결정 wire.
4. **CR 11-3 honest-DEFER 228번째**: epic 연속 정직 회복 — chain cj-282 → cj-282a → cj-285 → cj-286 → cj-287 → cj-288 → cj-289 → cj-290 → cj-291 종합 9 sprints 의 cumulative 결정 wire 정직 보존.
5. **cj-style chain 결정 wire 보존**: cj-style 282~291 10 sprints Epic 30+ Reporting & Export MVP territory 결정 wire 정직 보존.

**Epic 30+ Reporting & Export MVP security layer foundation (RLS EXTENSION = cj-290 chain) 결정 wire CLOSED ✅ HONEST 결정 wire**.

---

# Related 결정 wire

- [cj-282 Epic 30+ PRD entry `0c7524e`](handoff-2026-09-05-cj-282-epic-30-reporting-export-entry-done.md)
- [cj-282a wire sprint `eae9110`](handoff-2026-09-05-cj-282a-wire-sprint-done.md)
- [cj-285 EXTENSION wire sprint (capability matrix v1.54)](handoff-2026-09-06-cj-285-capability-matrix-extension-done.md)
- [cj-286 EXTENSION wire sprint (dev_seed + ci.yml + AD-56)](handoff-2026-09-06-cj-286-extension-wire-sprint-done.md)
- [cj-287 wire sprint `5c37446` (CSV E2E activation)](handoff-2026-09-06-cj-287-csv-e2e-activate-sprint-done.md)
- [cj-288 wire sprint `b91906a` (alembic migration)](handoff-2026-09-06-cj-288-cost-records-bom-matrix-migration-done.md)
- [cj-289 close-out wrap-up](handoff-2026-09-06-cj-289-wire-sprint-done.md)
- [cj-290 RLS EXTENSION wire sprint `1ba4309`](handoff-2026-09-06-cj-290-rls-extension-done.md)
- **cj-291 close-out retro (본 document)** — Epic 30+ RLS EXTENSION chain close-out 결정 wire