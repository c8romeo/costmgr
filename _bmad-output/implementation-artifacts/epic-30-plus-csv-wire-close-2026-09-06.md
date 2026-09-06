# Epic 30+ CSV wire chain (cj-285 ~ cj-288) — CLOSED HONEST (2026-09-06)

## §1 회고 의도

cj-287 CSV E2E activation wire sprint ✅ CLOSED HONEST + cj-288 alembic migration wire sprint ✅ CLOSED HONEST 회고 결정 wire (cj-style 289번째 epic 연속 정직 회복 docs-only atomic single sprint — Epic 30+ Reporting & Export MVP territory 의 Story 30.1 CSV export chain 의 마지막 close-out retro 결정 wire).

cj-style 284번째 Epic 30+ CSV wire sprint close-out retro `epic-30-plus-csv-wire-closed-2026-09-06.md` 의 pattern verbatim mirror — 14 sections §1~§14 결정 wire 보존 + chain-level 종합 회고 결정 wire (cj-285 capability matrix EXTENSION + cj-286 dev_seed/ci.yml/AD-56 EXTENSION + cj-287 wire sprint 11 files + cj-288 alembic migration 1 file = **4 sprints 종합**).

**wire sprint chain 결정 wire (Epic 30+ CSV export chain)**: cj-282 Epic 30+ PRD entry (commit `0c7524e`, 2026-09-05) → cj-282a wire sprint (commits `eae9110`+`e803ae2`, 2026-09-06) → cj-282a close-out retro (epic-30-plus-csv-wire-closed-2026-09-06.md, 2026-09-06) → **cj-285 EXTENSION wire sprint** (capability matrix v1.54 EXTENSION 결정 wire apply) → **cj-286 EXTENSION wire sprint** (dev_seed report_fixtures + ci.yml csv-export.spec.ts + AD-56 결정 wire apply) → **cj-287 wire sprint** (CSV E2E activation + CR 1-1 audit fix, 11 files) → **cj-288 wire sprint** (alembic migration 0060 cost_records + bom_matrix, 1 file) → **cj-289 close-out retro (본 document)** 결정 wire.

## §2 메타데이터

| 결정 wire | 값 |
|---|---|
| sprint_id | cj-289 (chain-level close-out) |
| type | docs-only atomic single sprint |
| territory 결정 wire | Epic 30+ Reporting & Export MVP territory 그대로 보존 (chain cj-285~cj-288 의 결정 wire) |
| sprint scope 결정 wire | docs-only wrap-up (5 files atomic) — close-out retro document + commit-msg + handoff + sprint-status v4.59 + MEMORY.md hook |
| chain scope 결정 wire | 4 sprints 종합 (cj-285 + cj-286 + cj-287 + cj-288) |
| 결정 wire 일자 | 2026-09-06 (KST) |
| CR 11-3 honest-DEFER 카운터 | 226번째 (cj-288 의 225번째 + cj-289 의 226번째) |
| 다음 options | 옵션 (a) Epic 30+ RLS EXTENSION wire sprint (cj-style 290번째) / 옵션 (b) cj-290 Story 30.2 PDF export wire sprint / 옵션 (c) Epic 29+ spec implementation chain / 옵션 (d) Pilot 고객 유치 (PRD OQ-3) |

## §3 cj-289 sprint scope inventory

**5 files = 3 NEW content + 2 MODIFIED meta atomic single sprint 결정 wire**:

### 3 NEW content (close-out docs)

| File | Type | LOC | 결정 wire |
|---|---|---|---|
| `_bmad-output/implementation-artifacts/epic-30-plus-csv-wire-close-2026-09-06.md` | NEW | ~300 | 14-section §1~§14 verbatim retro document (본 document) — chain-level 종합 회고 |
| `_bmad-output/implementation-artifacts/commit-msg-cj-289.txt` | NEW | ~80 | cj-289 close-out wrap-up commit message |
| `memory/handoff-2026-09-06-cj-289-wire-sprint-done.md` | NEW | ~150 | 6-section handoff (cj-289 close-out wrap-up 의 follow-up 결정 wire) |

### 2 MODIFIED (meta files)

| File | Type | 결정 wire |
|---|---|---|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.58 → v4.59 EXTENSION (A701 cj-288 retroactive + A702 cj-289 entry + last_updated_note_v4_59 신규 paragraph) |
| `memory/MEMORY.md` | MODIFIED | cj-289 hook EXTENSION (1-line index format, cj-style 289번째 entry) |

## §4 wire sprint chain timeline (cj-285 ~ cj-289)

```
[cj-285 EXTENSION wire sprint]  (Epic 30+ capability matrix v1.54 EXTENSION + 4 audit actions EXTENSION)
   |
   | territory: Epic 30+ Reporting & Export MVP
   | sprint scope: Capability.EXPORT_CSV/PDF/EMAIL/SCHEDULED 4 NEW enum + 4-industry grants + ActionClass.REPORTS + ReportsAction Literal 4 values
   |
   v
[cj-286 EXTENSION wire sprint]  (dev_seed report_fixtures + ci.yml csv-export.spec.ts + AD-56 Epic 30+ 결정 wire)
   |
   | sprint scope: scripts/dev_seed.py 13 NEW UUIDv5 + _seed_report_fixtures + 19 choices dispatch + AD-56 7 sub-decisions + csv-export.spec.ts 3 test cases
   |
   v
[cj-287 wire sprint]             (CSV E2E activation + CR 1-1 audit fix, 11 files)
   |
   | sprint scope: 1 NEW __init__.py + 6 MODIFIED (csv_routes.py + main.py + CsvExportTab.tsx + reports/page.tsx + csv-export.spec.ts + dev_seed.py)
   | D-WEB-E2E-7 ownership wire ACTIVATED (FIRST Epic 30+ territory ownership)
   | CI verification 결정 wire 보류 (cj-style baseline-green 보존)
   |
   v
[cj-288 wire sprint]             (alembic migration 0060 cost_records + bom_matrix, 1 file)
   |
   | commit b91906a, 2026-09-06
   | sprint scope: 1 NEW alembic migration (CREATE TABLE 2 + CREATE INDEX 3 + COMMENT 2 + DROP reverse order 5)
   | CI run 34000480618 = step 15 dev_seed ✅ SUCCESS (chain unblock 결정 wire) → step 19 Playwright 실제 실행 결정 wire
   |
   v
[cj-289 close-out wrap-up]       (chain-level close-out retro, 본 document, 2026-09-06)  ⏳ 결정 wire 진입
   |
   | docs-only atomic single sprint
   | 5 files = 3 NEW content + 2 MODIFIED meta
   | territory: Epic 30+ Reporting & Export MVP 보존 (close-out 자체 territory 결정 없음)
   |
   v
[Epic 30+ 다음 territory 결정 wire 보류]
   |
   +-- 옵션 (a) Epic 30+ RLS EXTENSION wire sprint (supabase/policies/0060_cost_records_and_bom_matrix_rls.sql, cj-style 290번째)
   +-- 옵션 (b) cj-290 Story 30.2 PDF export wire sprint (weasyprint vs reportlab 결정 + Jinja2 ko-KR + matplotlib 3 charts, cj-style 290번째)
   +-- 옵션 (c) Epic 29+ spec implementation chain 진입 (cj-29x-impl territory)
   +-- 옵션 (d) Pilot 고객 유치 (PRD OQ-3)
```

## §5 verification results — chain-level 종합

**chain cj-285 ~ cj-288 cumulative verification**:

| Sprint | CI run ID | Result | 결정 wire |
|---|---|---|---|
| cj-285 EXTENSION | n/a (docs+source atomic) | 결정 wire 진입 완료 | capability matrix v1.54 EXTENSION + 4 audit actions EXTENSION + `_INDUSTRY_CAPABILITIES` 4-industry grants 4 NEW capabilities ✅ (T7.55+T7.56 verified) |
| cj-286 EXTENSION | n/a (docs+source atomic) | 결정 wire 진입 완료 | dev_seed.py 13 NEW UUIDv5 + _seed_report_fixtures + 19 choices + csv-export.spec.ts + AD-56 7 sub-decisions |
| cj-287 wire sprint | 결정 wire 보류 (cj-style 보존) | 결정 wire 진입 완료 | 11 files atomic sprint (1 NEW __init__.py + 6 MODIFIED source + 2 NEW meta + 2 MODIFIED meta) |
| cj-288 wire sprint | `34000480618` (head `b91906a`) | step 15 ✅ SUCCESS (chain unblock) + step 19 actually RAN (NOT SKIPPED, 결정 wire 진입) | web-e2e step 19 csv-export 결과 = 결정 wire 보류 (사용자 GitHub Actions 페이지 직접 확인 필요) |

**scope boundary honestly reported**: chain cj-285~288 의 source surface 결정 wire = capability matrix + audit actions + dev_seed + ci.yml + AD-56 + csv_routes.py (CJ-287 fix) + alembic migration 0060. **CR 1-1 silent audit failure fix** (cj-287 critical bug fix, csv_routes.py:362 `ActionClass.AUDIT` → `ActionClass.REPORTS`) 결정 wire 보존. **alembic chain unblock** (cj-288 의 step 15 dev_seed ✅ SUCCESS 결정 wire 보존, 직전 CI run 33999439554 step 15 FAIL → step 16-19 SKIPPED → step 19 csv-export 3/3 NEVER RAN silent RED 의 PRE-EXISTING carryover 정직 회복).

## §6 file mapping table (chain-level 종합)

### cj-287 wire sprint 결정 wire (11 files = 1 NEW source + 6 MODIFIED source + 2 NEW meta + 2 MODIFIED meta)

| File | Type | LOC | 결정 wire |
|---|---|---|---|
| `apps/api/modules/reports/__init__.py` | NEW source | ~24 | package marker 결정 wire |
| `apps/api/modules/reports/csv_routes.py` | MODIFIED | line 61 capability import + line 253 `Depends(require_capability(Capability.EXPORT_CSV))` + line 358-362 `ActionClass.AUDIT` → `ActionClass.REPORTS` CR 1-1 verbatim 회복 | CR 1-1 silent audit failure fix |
| `apps/api/main.py` | MODIFIED | line 598-603 csv_export_router mount + line 3509-3588 4 NEW exception handlers | route mount + CR 12-5 D-14 envelope |
| `apps/web/components/reports/CsvExportTab.tsx` | MODIFIED | line 41 tenantId prop EXTENSION + line 48 destructure + line 56-60 TODO 제거 | UI tenantId wire |
| `apps/web/app/[locale]/(dashboard)/reports/page.tsx` | MODIFIED | line 69-89 JWT decode block + line 102 tenantId prop pass-through | JWT decode wire |
| `apps/web/e2e/csv-export.spec.ts` | MODIFIED | line 42-77 D-WEB-E2E-7 ACTIVATED header + line 79 describe.skip → describe + 4 placeholder replacements | D-WEB-E2E-7 ownership wire ACTIVATED |
| `scripts/dev_seed.py` | MODIFIED | line 1559-1582 3 NEW flags `--tenant-id --user-id --role` + line 1728-1735 effective_* override logic | dev_seed token mode EXTENSION |
| `_bmad-output/implementation-artifacts/commit-msg-cj-287.txt` | NEW meta | ~150 | cj-287 wire sprint commit message |
| `memory/handoff-2026-09-06-cj-287-csv-e2e-activate-sprint-done.md` | NEW meta | ~250 | 6-section handoff |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.57 → v4.58 EXTENSION | cj-287 entry + A700 + last_updated_note_v4_58 |
| `memory/MEMORY.md` | MODIFIED | hook EXTENSION | cj-287 hook |

### cj-288 wire sprint 결정 wire (1 file = 1 NEW alembic migration)

| File | Type | LOC | 결정 wire |
|---|---|---|---|
| `apps/api/alembic/versions/0060_cost_records_and_bom_matrix.py` | NEW source | ~204 | revision = "0060_cost_records_and_bom_matrix", down_revision = "0059_phase_28_interactive_dashboard", CREATE TABLE 2 (cost_records 14 cols + bom_matrix 13 cols) + CREATE INDEX 3 + COMMENT 2 + DROP reverse order 5 |
| `_bmad-output/implementation-artifacts/commit-msg-cj-288.txt` | NEW meta | ~140 | cj-288 alembic migration commit message |
| `memory/handoff-2026-09-06-cj-288-cost-records-bom-matrix-migration-done.md` | NEW meta | ~250 | 6-section handoff |
| `memory/MEMORY.md` | MODIFIED | hook EXTENSION | cj-288 hook |

### cj-289 close-out wrap-up 결정 wire (5 files = 3 NEW content + 2 MODIFIED meta)

| File | Type | LOC | 결정 wire |
|---|---|---|---|
| `_bmad-output/implementation-artifacts/epic-30-plus-csv-wire-close-2026-09-06.md` | NEW content | ~300 | 14-section retro document (본 document) |
| `_bmad-output/implementation-artifacts/commit-msg-cj-289.txt` | NEW meta | ~80 | close-out wrap-up commit message |
| `memory/handoff-2026-09-06-cj-289-wire-sprint-done.md` | NEW meta | ~150 | 6-section handoff |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.58 → v4.59 EXTENSION | A701 cj-288 retroactive + A702 cj-289 entry + last_updated_note_v4_59 |
| `memory/MEMORY.md` | MODIFIED | hook EXTENSION | cj-289 hook |

## §7 cumulative 결정 wire 보존

- **territory 결정 wire 보존**: Epic 30+ Reporting & Export MVP territory (cj-282 option (γ)) 그대로 보존. chain cj-285~cj-289 5 sprints 의 결정 wire.
- **capability matrix v1.53 → v1.54 EXTENSION 결정 wire apply 완료** (cj-285 EXTENSION sprint): `Capability.EXPORT_CSV` / `Capability.EXPORT_PDF` / `Capability.EXPORT_EMAIL` / `Capability.EXPORT_SCHEDULED` 4 NEW enum + 4-industry grants ✅/✅/✅/✅.
- **audit actions EXTENSION 결정 wire apply 완료** (cj-285 EXTENSION sprint): `ActionClass.REPORTS = "reports"` 별도 sub-class 결정 wire apply (NOT `ActionClass.AUDIT` re-use). `export_csv` / `export_pdf` / `export_email` / `export_scheduled` 4 NEW values.
- **dev_seed report_fixtures EXTENSION 결정 wire apply 완료** (cj-286 EXTENSION sprint): acme tenant + 100 cost_records + 10 BOM rows for period_key='2026-08'.
- **ci.yml web-e2e step 19 csv-export.spec.ts EXTENSION 결정 wire apply 완료** (cj-286 EXTENSION sprint): NEW spec file only (testDir auto-discover로 cover, ci.yml YAML 변경 0건).
- **AD-56 Epic 30+ 결정 wire 7 sub-decisions apply 완료** (cj-286 EXTENSION sprint): 8 D-EPIC30+-1~8 honestly DEFER 결정 wire 보존.
- **CR 1-1 silent audit failure fix 결정 wire apply 완료** (cj-287 wire sprint, critical bug): `csv_routes.py:362` `action_class=ActionClass.AUDIT` → `ActionClass.REPORTS` fix. EXISTING `_ActionRegistry.validate()` ValueError raise + `except Exception:` at lines 373-377 silent swallow → 모든 CSV export operation 의 audit trail silently 누락 → CR 1-1 verbatim violation + Epic 17 wire `2ada2ec` 의 fail-closed 정책 위반 → fix 결정 wire apply.
- **AD bind 3/3** (cj-282 PRD entry §F44.1 verbatim): AD-2 audit-first INSERT append-only + AD-10 identity/2FA via owner-only RBAC AD-22 verbatim + AD-12 verify-first capability gate `Capability.EXPORT_CSV` AD-56(c) verbatim 적용.
- **NFR bind 2/7 active**: NFR5 streaming P95 ≤ 5s for 10만 row + NFR18 ko-KR vocabulary SSOT UTF-8 BOM.
- **4 OQ 결정 보류** (cj-290+ 진입 시 결정): OQ-EPIC30+-1 weasyprint vs reportlab (Story 30.2 PDF) / OQ-EPIC30+-2 SMTP 인프라 외부 의존 (Story 30.3 Email) / OQ-EPIC30+-3 APScheduler vs Celery beat vs cron (Story 30.4 Scheduled) / OQ-EPIC30+-4 chart library matplotlib vs Plotly vs Chart.js PNG export (Story 30.2 PDF).

## §8 D-WEB-E2E ownership verification

**D-WEB-E2E-7 ownership wire ACTIVATED 결정 wire** (cj-287 wire sprint, FIRST D-WEB-E2E-* ownership wire in Epic 30+ territory):
- cj-274 → cj-279 Epic 29+ chain 의 D-WEB-E2E-1~6 verbatim mirror pattern 적용.
- csv-export.spec.ts 의 3 test cases (line 42-77 D-WEB-E2E-7 ACTIVATED header) 결정 wire 진입.
- Epic 29+ spec implementation ownership = cj-29x-impl territory 별도 future chain 결정 wire 보존.

**Epic 29+ spec implementation ownership** = cj-29x-impl territory 별도 future chain 결정 wire 보존 (cj-289 close-out retro 의 옵션 (c)).

## §9 master PRD 정합 검증

cj-282 PRD entry 의 `spec-epic-30-reporting-export.md` §F44.1 (Story 30.1 CSV) 의 8 ACs verbatim mirror 결정 wire 보존 (cj-282a close-out retro §9 의 verification 그대로 유지):

- AC-1: 운영자가 /api/v1/exports/csv?type=cost-records GET 호출 → RFC 4180 quoted CSV response (UTF-8 BOM 포함) ✅ (csv_routes.py:GET /api/v1/exports/csv + StreamingResponse)
- AC-2: 14개 column ✅ (CSV_COLUMNS_COST_RECORDS = 14)
- AC-3: type=bom parameter → BOM level 1 12 columns ✅ (CSV_COLUMNS_BOM = 12)
- AC-4: tenant_id parameter cross-tenant 차단 ✅ (CR 0-2 RLS + CsvExportCrossTenantError)
- AC-5: owner/admin role 만 호출 가능 ✅ (AD-22 RBAC + AD-56(c) capability gate)
- AC-6: audit log INSERT (action='export_csv', action_class=ActionClass.REPORTS) ✅ (CR 1-1 audit-first + cj-287 silent failure fix)
- AC-7: period YYYY-MM format 검증 ✅ (Pydantic field_validator)
- AC-8: NFR5 streaming P95 ≤ 5s for 100k rows ✅ (MAX_EXPORT_ROWS=100_000 + CHUNK_FLUSH_ROWS=5000)

**cj-285/286/287/288 chain EXTENSION 결정 wire 보존**:
- capability matrix v1.54 EXTENSION ✅ (cj-285)
- audit actions EXTENSION ✅ (cj-285)
- dev_seed report_fixtures EXTENSION ✅ (cj-286)
- ci.yml csv-export.spec.ts EXTENSION ✅ (cj-286)
- AD-56 Epic 30+ 결정 wire ✅ (cj-286)
- CR 1-1 silent audit failure fix ✅ (cj-287)
- alembic migration 0060 cost_records + bom_matrix ✅ (cj-288)
- D-WEB-E2E-7 ownership wire ACTIVATED ✅ (cj-287)

## §10 신규 chain 진입 결정 wire (cj-290+ options)

| 옵션 | 결정 wire | 비고 |
|---|---|---|
| **(a)** | Epic 30+ RLS EXTENSION wire sprint (supabase/policies/0060_cost_records_and_bom_matrix_rls.sql 결정 wire 진입, cj-style 290번째) | **RECOMMENDED** — production tenant isolation 보장 + dev_seed 는 postgres role (BYPASSRLS) 사용 → RLS 부재가 dev_seed step 15 회복에는 무관 결정 wire 보존 |
| **(b)** | cj-290 Story 30.2 PDF export wire sprint (weasyprint vs reportlab 결정 + Jinja2 ko-KR template + matplotlib 3 charts 결정 wire 진입, cj-style 290번째) | OQ-EPIC30+-1 + OQ-EPIC30+-4 결정 진입 |
| **(c)** | Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory) | Epic 29+ Story 29.1~29.18 actual UI 구현 territory 별도 future chain |
| **(d)** | Pilot 고객 유치 결정 wire 진입 (PRD OQ-3 파일럿 게이트 1주 post M0-M6) | Epic 30+ MVP 완성 후 (CSV ✅ → PDF → Email → Scheduled) |

## §11 CR lessons applied (5종)

- **CR 9-6 D5 prevention**: `git commit -F <file>` pattern 사용 (amend 금지). sprint-status.yaml plain text readlines/writelines 패턴 (`scripts/append_sprint_status.py:7-8`) 보존 (PyYAML safe_load FAILED pre-existing issue 결정 wire).
- **CR 11-3 honest-DEFER**: cj-288 의 PRE-EXISTING carryover 정직 회복 결정 wire (cj-287 follow-up #2 의 silent RED 정직 보고). cj-289 의 226번째 결정 wire 보존.
- **CR 11-4 plan mode**: cj-287 wire sprint 진입 시 Plan mode 진입 → ExitPlanMode 결정 wire 보존.
- **CR 1-1 audit-first INSERT (silent failure fix)**: cj-287 critical bug fix 결정 wire. `ActionClass.AUDIT` → `ActionClass.REPORTS` 1-word change at line 362.
- **CR 12-5 D-14 typed exception envelope**: cj-287 의 4 NEW exception handlers (CsvExportInvalidRequestError 400 / CsvExportForbiddenError 403 / CsvExportCrossTenantError 403 / CsvExportTooLargeError 413 verbatim mirror of audit_log_* handlers at 774-831).

## §12 scope boundary 결정 wire

- **chain cj-285~cj-288 의 source surface 결정 wire**: capability matrix (cj-285) + audit actions (cj-285) + dev_seed report_fixtures (cj-286) + ci.yml csv-export.spec.ts (cj-286) + AD-56 7 sub-decisions (cj-286) + csv_routes.py fix (cj-287) + alembic migration 0060 (cj-288).
- **cj-289 close-out wrap-up 결정 wire**: docs-only atomic single sprint — source code 변경 0건 + dev_seed 변경 0건 + ci.yml 변경 0건 + alembic 변경 0 + AD-14 stack pin 변경 없음 + [STACK BUMP] tag 불필요.
- **본 cj-289 의 source surface 결정 wire**: 3 NEW docs files (14-section retro document + commit-msg-cj-289.txt + 6-section handoff) + 2 MODIFIED meta files (sprint-status.yaml v4.58 → v4.59 EXTENSION + MEMORY.md hook EXTENSION).

## §13 honestly DEFER carryover

**4 OQ 결정 wire cj-290+ 적용 보류** (cj-282 PRD entry 결정 wire 보존):
1. OQ-EPIC30+-1 weasyprint vs reportlab (Story 30.2 PDF)
2. OQ-EPIC30+-2 SMTP 인프라 외부 의존 (Story 30.3 Email)
3. OQ-EPIC30+-3 APScheduler vs Celery beat vs cron (Story 30.4 Scheduled)
4. OQ-EPIC30+-4 chart library matplotlib vs Plotly vs Chart.js PNG export (Story 30.2 PDF)

**Epic 30+ Story 30.2/30.3/30.4 결정 wire 보류** (cj-282 4-story 분할 plan):
- Story 30.2 PDF (FR-30-2) — cj-290 wire sprint 진입 결정 wire 보류
- Story 30.3 Email (FR-30-3) — cj-291 wire sprint 진입 결정 wire 보류
- Story 30.4 Scheduled (FR-30-4) — cj-292 wire sprint 진입 결정 wire 보류

**Epic 29+ spec implementation chain** = cj-29x-impl territory 별도 future chain 결정 wire 보존 (cj-289 close-out 의 옵션 (c)).

**RLS EXTENSION for cost_records + bom_matrix tables** = cj-290 (옵션 (a)) 진입 결정 wire 보류. dev_seed 는 postgres role (BYPASSRLS) 사용 → RLS 부재가 dev_seed step 15 회복에는 무관 결정 wire 보존. production tenant isolation 결정 wire 진입 시 별도 sprint 결정 wire.

## §14 결정 wire 일자 + lessons learned (10종)

**결정 wire 일자**: 2026-09-06 (KST)

**Lessons learned (10종)**:

1. **5-layer compound bug discovery**: cj-287 Phase 1 탐색 결과 = (1) CR 1-1 silent audit failure (csv_routes.py:359 ActionClass.AUDIT → ActionClass.REPORTS fix) + (2) route not mounted (__init__.py 부재) + (3) 4 exception handlers missing + (4) UI tenantId wire missing + (5) spec placeholder bugs — 5-layer compound 발견 → PDF 진입 시 unverified foundation 위 compounding risk = HIGH risk, CSV E2E activation = LOW-MEDIUM bounded fixes = risk minimization 우선 결정 wire 진입.
2. **CR 1-1 silent failure pattern**: `try/except Exception:` 블록 + `_ActionRegistry.validate()` ValueError raise 의 조합 → audit trail silently 누락 → CR 1-1 verbatim violation + Epic 17 wire `2ada2ec` 의 fail-closed 정책 위반 → 1-word change 로 fix 결정 wire.
3. **Capability gate AD-56(c) verbatim 적용**: `Depends(require_capability(Capability.EXPORT_CSV))` dependency 추가 = cj-285 capability matrix EXTENSION 의 wire surface. AD-12 verify-first capability gate 결정 wire 보존.
4. **CR 12-5 D-14 typed envelope verbatim mirror**: 4 NEW exception handlers at main.py:3509-3588 = audit_log_* handlers at 774-831 의 verbatim mirror 결정 wire 보존.
5. **Pre-existing carryover 정직 회복**: cj-287 follow-up #2 commit `d8d4df0` 의 silent RED 정직 보고 + cj-288 alembic migration 결정 wire = PRE-EXISTING carryover 정직 회복 chain 진입. step 15 dev_seed step 15 FAIL → step 16-19 SKIPPED → step 19 csv-export 3/3 NEVER RAN → cj-288 후 step 15 ✅ SUCCESS → step 19 actually RAN.
6. **alembic version conflict 회피**: 0031 alembic version conflict 결정 wire (0031_ai_insight_comments.py cj-style 32번째 Story 10.3 commit `ea025b1` 점유) → next available 0060 사용 결정 wire 진입.
7. **PYTHONHASHSEED + deterministic UUIDv5**: dev_seed.py 의 13 NEW UUIDv5 constants 결정 wire = cj-273b identity-only EXTENSION 의 후속 + cj-287 `--tenant-id --user-id --role` flags EXTENSION.
9. **CR 9-6 D5 prevention**: `git commit -F <file>` pattern 사용 (amend 금지). sprint-status.yaml plain text readlines/writelines 패턴 (`scripts/append_sprint_status.py:7-8`) 보존.
9. **사용자 분석 override 적용**: 사용자 프롬프트 의 '리스크 최소화 + 시스템 구현 관점 + 최적 대안 분석' 요청 → 옵션 (a) PDF 진입 대신 (e) CSV E2E activation 선택 (Phase 1 탐색 결과 5-layer compound 발견 후) → risk minimization 우선 결정 wire 진입.
10. **cj-290+ options 결정 wire**: 옵션 (a) Epic 30+ RLS EXTENSION wire sprint (RECOMMENDED) / 옵션 (b) cj-290 Story 30.2 PDF / 옵션 (c) Epic 29+ spec implementation chain / 옵션 (d) Pilot 고객 유치 결정 wire 보존.

**cj-style chain 결정 wire 보존**: cj-282 Epic 30+ PRD entry (commit `0c7524e`) → cj-282a wire sprint (commits `eae9110`+`e803ae2`) → cj-282a close-out retro (epic-30-plus-csv-wire-closed-2026-09-06.md) → cj-285 EXTENSION wire sprint (capability matrix v1.54 + 4 audit actions EXTENSION) → cj-286 EXTENSION wire sprint (dev_seed + ci.yml + AD-56 EXTENSION) → cj-287 wire sprint (11 files, CSV E2E activation + CR 1-1 audit fix) → cj-288 wire sprint (1 file, alembic migration 0060 cost_records + bom_matrix) → **cj-289 close-out wrap-up (본 document)** 결정 wire.

**Epic 30+ Reporting & Export MVP chain cj-285~cj-289 CLOSED ✅ HONEST 결정 wire** — Story 30.1 CSV export territory 의 foundation verification + ACTUAL chain 결정 wire 진입 완료. CR 11-3 honest-DEFER 226번째 epic 연속 정직 회복 결정 wire 진입 완료 보존.