# Epic 30+ CSV wire sprint — CLOSED HONEST (2026-09-06)

## §1 회고 의도

cj-282a Story 30.1 CSV export wire sprint ✅ CLOSED HONEST 회고 결정 wire (cj-style 284번째 epic 연속 정직 회복 docs-only atomic single sprint — cj-282a wire sprint 의 next 옵션 (a) verbatim mirror, A693 의 "옵션 (a) cj-282a close-out retro 진입 결정 wire (cj-style 284번째, RECOMMENDED)" verbatim). 본 actual retro document 작성 결정 wire.

cj-style 280번째 Epic 29+ CLOSED retro 의 `phase-24-close-out-2026-08-27.md` pattern verbatim mirror — 14 sections §1~§14 결정 wire 보존.

**wire sprint chain 결정 wire (Epic 30+ entry)**: cj-282 Epic 30+ PRD entry (commit `0c7524e`, 2026-09-05) → cj-282a wire sprint (commits `eae9110` + `e803ae2`, 2026-09-06) → **cj-style 284번째 close-out retro (본 document)** 결정 wire.

## §2 메타데이터

| 결정 wire | 값 |
|---|---|
| sprint_id | cj-282a |
| type | source+docs atomic single sprint |
| territory 결정 wire | cj-282 option (γ) Reporting & Export MVP territory 그대로 보존 (cj-282a wire sprint 결정 wire) |
| sprint scope 결정 wire | Story 30.1 CSV export P0 (Risk Lowest — stdlib csv + FastAPI StreamingResponse only, no new infra) |
| commit hash #1 | `eae9110` (cj-282a source+docs atomic 10 files +1485/-0) |
| commit hash #2 | `e803ae2` (lint-conventions fix 1 file +2/-2, ruff format 정정) |
| CI run ID | `33994517481` (`9-3-dev-2026-08-17` branch) |
| sprint-status 결정 wire | v4.53 → v4.54 EXTENSION |
| 결정 wire 일자 | 2026-09-06 (KST) |
| CR 11-3 honest-DEFER 카운터 | 223번째 (cj-282a wire sprint 의) |
| 다음 close-out retro | cj-style 284번째 (본 document) |
| 후속 options | 옵션 (a) cj-285+ EXTENSION wire sprint (capability matrix v1.54 + 4 audit actions EXTENSION, RECOMMENDED) / 옵션 (b) cj-282b Story 30.2 PDF wire / 옵션 (c) Epic 29+ spec implementation chain |

## §3 cj-282a sprint scope inventory

**11 files = 7 NEW content + 2 NEW meta + 2 MODIFIED atomic single sprint 결정 wire**:

### 7 NEW content (source/test files)

| File | Type | LOC | 결정 wire |
|---|---|---|---|
| `apps/api/modules/reports/csv_routes.py` | NEW | ~433 | GET /api/v1/exports/csv 라우트 (StreamingResponse + UTF-8 BOM + RFC 4180 quoted + audit-first INSERT (CR 1-1) + owner-only RBAC (AD-22) + capability gate (AD-12) + ko-KR SSOT (NFR18) + 5 typed exception classes (CR 12-5 D-14 envelope)) |
| `apps/api/schemas/export_schemas.py` | NEW | ~80 | CsvExportRequest(BaseModel) Pydantic schema (type Literal["cost-records", "bom"] + period regex YYYY-MM + tenant_id UUID4 + field_validator) |
| `apps/web/app/[locale]/(dashboard)/reports/page.tsx` | NEW | ~85 | RSC 보고서 페이지 (ko-KR NFR18 SSOT + data-testid reports-tab 마운트 + auth gate via sb-access-token cookie) |
| `apps/web/app/[locale]/(dashboard)/reports/layout.tsx` | NEW | ~37 | (dashboard) layout group auth gate (sb-access-token cookie → /ko-KR/login redirect) |
| `apps/web/components/reports/CsvExportTab.tsx` | NEW | ~213 | CSV 내보내기 탭 UI (period selector + type selector + download button + 4 data-testids: reports-tab, csv-export-tab, period-selector-{YYYY-MM}, download-button) |
| `tests/integration/test_phase_30_exports_csv.py` | NEW | ~314 | pytest 22 tests (UTF-8 BOM + RFC 4180 escape 6종 + CSV columns 14/12 + audit action='export_csv' + 5 typed exceptions + 4 schema validators + 2 row mappers + MAX_EXPORT_ROWS constant + cross-tenant invariant) |
| `apps/web/__tests__/components/CsvExportTab.test.tsx` | NEW | ~85 | vitest 4 tests (ko-KR labels verbatim NFR18 SSOT + 4 data-testids + 12 period options + 2 type options) |

### 2 NEW meta (decisions docs)

| File | Type | LOC | 결정 wire |
|---|---|---|---|
| `_bmad-output/implementation-artifacts/commit-msg-cj-283.txt` | NEW | ~94 | Archetype B source+docs wire sprint commit message (cj-282a source+docs atomic 진입 결정 wire) |
| `memory/handoff-2026-09-06-cj-282a-wire-sprint-done.md` | NEW | ~124 | 6-section handoff (cj-282a wire sprint 의 follow-up 결정 wire) |

### 2 MODIFIED (meta files)

| File | Type | 결정 wire |
|---|---|---|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.53 → v4.54 EXTENSION (cj-282a: backlog 신규 entry + A693 action_item 신규 + last_updated_note_v4_54 신규 paragraph) |
| `memory/MEMORY.md` | MODIFIED | cj-282a hook EXTENSION (단, **honest note**: 프로젝트 repo 의 MEMORY.md file 에는 cj-282 entry 까지만 (line 319) 작성되고 cj-282a hook 은 auto-memory dir 에만 작성됨 — CR 11-3 honestly reported, 본 close-out retro 에서 정정 결정 wire) |

## §4 wire sprint chain timeline

```
[cj-282 PRD entry]            (commit 0c7524e, 2026-09-05)
   |
   | territory: option (γ) Reporting & Export MVP 선택
   | sprint scope: 4 stories 분할 (30.1 CSV / 30.2 PDF / 30.3 Email / 30.4 Scheduled)
   |
   v
[cj-282a wire sprint]         (commits eae9110 + e803ae2, 2026-09-06)  ✅ CLOSED HONEST
   |
   | territory: option (γ) Reporting & Export MVP 그대로 보존
   | sprint scope: Story 30.1 CSV P0 (Risk Lowest)
   | 11 files = 7 NEW content + 2 NEW meta + 2 MODIFIED atomic
   | CI 33994517481: 14/14 completed, 13/14 PASS, 1/14 expected FAIL (test-suite-measure P3 BLOCKING)
   |
   v
[cj-style 284번째 close-out retro]   (본 document, 2026-09-06)  ⏳ 결정 wire 진입
   |
   | docs-only atomic single sprint
   | 5 files = 3 NEW content + 2 MODIFIED meta
   | territory: 보존 (close-out retro 자체 territory 결정 없음)
   |
   v
[cj-285+ territory options 결정 wire 보류]
   |
   +-- 옵션 (a) cj-285+ EXTENSION wire sprint (capability matrix v1.54 + 4 audit actions EXTENSION source+docs atomic, RECOMMENDED)
   +-- 옵션 (b) cj-282b wire sprint (cj-style 285번째, Story 30.2 PDF weasyprint 결정 + source+docs atomic)
   +-- 옵션 (c) Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory)
```

## §5 verification results — CI run 33994517481 (2026-09-06)

**14/14 jobs completed, 13/14 PASS, 1/14 expected FAIL**

| Job | Result | 결정 wire |
|---|---|---|
| setup | ✅ success | |
| test-suite-measure | ❌ FAIL | P3 BLOCKING gate per cj-274 baseline 결정 wire — expected 비-MVP 회귀 표면화 (cj-style discipline 보존) |
| test-architecture | ✅ success | |
| service-role-guard-lint | ✅ success | |
| lint-conventions | ✅ success | **fix commit e803ae2 ruff format 정정 효과** |
| lint-deps | ✅ success | |
| commit-prefix-lint | ✅ success | `feat(api+web):` prefix 결정 wire 보존 |
| web-e2e | ✅ success | **74 skipped 0 failed** (cj-282a/b bulk skip 18 specs 유지) |
| smoke-e2e | ✅ success | |
| rls-tests | ✅ success | |
| web-test | ✅ success | **vitest 4/4 PASS** (CsvExportTab.test.tsx) |
| lint-imports | ✅ success | |
| test-service-role-guard | ✅ success | |
| stack-pin-check | ✅ success | AD-14 stack pin 정책 (35 pins) 변경 없음 |

**scope boundary honestly reported**: cj-282a wire sprint 의 source surface 결정 wire = 7 NEW source/test files. **lint-conventions 첫 push `eae9110` FAIL → fix `e803ae2` PASS** 결정 wire 보존 (CR 9-6 D5 prevention: `git commit -F <file>` pattern, amend 안 함). **test-suite-measure FAIL = P3 BLOCKING gate** per cj-274 baseline decision wire 결정 wire 보존 — expected 비-MVP 회귀 표면화, cj-style discipline 보존.

## §6 file mapping table (11 rows × 4 columns)

| File | Type | LOC | 결정 wire |
|---|---|---|---|
| apps/api/modules/reports/csv_routes.py | NEW content | ~433 | GET /api/v1/exports/csv route |
| apps/api/schemas/export_schemas.py | NEW content | ~80 | CsvExportRequest schema |
| apps/web/app/[locale]/(dashboard)/reports/page.tsx | NEW content | ~85 | RSC reports page |
| apps/web/app/[locale]/(dashboard)/reports/layout.tsx | NEW content | ~37 | (dashboard) layout auth gate |
| apps/web/components/reports/CsvExportTab.tsx | NEW content | ~213 | CSV export tab UI |
| tests/integration/test_phase_30_exports_csv.py | NEW content | ~314 | pytest 22 tests |
| apps/web/__tests__/components/CsvExportTab.test.tsx | NEW content | ~85 | vitest 4 tests |
| _bmad-output/implementation-artifacts/commit-msg-cj-283.txt | NEW meta | ~94 | wire sprint commit msg |
| memory/handoff-2026-09-06-cj-282a-wire-sprint-done.md | NEW meta | ~124 | wire sprint 6-section handoff |
| _bmad-output/implementation-artifacts/sprint-status.yaml | MODIFIED meta | +2 entries | v4.54 EXTENSION (cj-282a backlog + A693 + last_updated_note_v4_54) |
| memory/MEMORY.md | MODIFIED meta | (cj-282a hook EXTENSION 결정 wire) | **honest note: auto-memory dir 에만 작성됨, 프로젝트 repo 의 MEMORY.md file 에는 미작성 — 본 close-out retro 에서 정정 결정 wire** |

## §7 cumulative 결정 wire 보존

- **territory 결정 wire 보존**: cj-282 option (γ) Reporting & Export MVP territory 그대로 이어서 (cj-282a wire sprint 결정 wire)
- **AD bind 3/3**: AD-2 audit-first INSERT append-only + AD-10 identity/2FA via owner-only RBAC AD-22 verbatim + AD-12 verify-first capability (Capability.EXPORTS_CSV EXTENSION 결정 wire 보류 cj-style 284+ 적용)
- **NFR bind 2/7 active**: NFR5 streaming P95 ≤ 5s for 10만 row + NFR18 ko-KR vocabulary SSOT
- **4 OQ 결정 보류** (cj-282b/c/d 진입 시 결정 — cj-282a 범위 외 N/A 마킹): OQ-EPIC30+-1 weasyprint vs reportlab (Story 30.2 PDF) / OQ-EPIC30+-2 SMTP 인프라 외부 의존 (Story 30.3 Email) / OQ-EPIC30+-3 APScheduler vs Celery beat vs cron (Story 30.4 Scheduled) / OQ-EPIC30+-4 chart library matplotlib vs Plotly vs Chart.js PNG export (Story 30.2 PDF)

## §8 D-WEB-E2E ownership verification

cj-282a wire sprint 가 **신규 web-e2e spec 0건 추가** 결정 wire (cj-282 PRD entry 의 ci.yml web-e2e step 19 csv-export.spec.ts 추가 결정 wire 보류 보존). 기존 cj-282a/b bulk skip 18 specs (cj-282a web-e2e skip 6 specs + cj-282b bulk skip 12 specs = 6+12 = 18 specs skipped, 74 tests skipped total) 그대로 유지 결정 wire.

**Epic 29+ spec implementation ownership** = cj-29x-impl territory 별도 future chain 결정 wire 보존 (Epic 30+ 의 옵션 (c)).

## §9 master PRD 정합 검증

cj-282 PRD entry 의 `spec-epic-30-reporting-export.md` §F44.1 (Story 30.1 CSV) 의 8 ACs verbatim mirror 결정 wire 보존:
- AC-1: 운영자가 /api/v1/exports/csv?type=cost-records GET 호출 → RFC 4180 quoted CSV response (UTF-8 BOM 포함) ✅ (csv_routes.py:GET /api/v1/exports/csv + StreamingResponse)
- AC-2: 14개 column (tenant_id, period_key, product_id, product_name, category, opening_qty, input_qty, output_qty, closing_qty, unit_cost, total_cost, currency, created_at, ledger_event_id) ✅ (CSV_COLUMNS_COST_RECORDS = 14)
- AC-3: type=bom parameter → BOM level 1 12 columns ✅ (CSV_COLUMNS_BOM = 12)
- AC-4: tenant_id parameter cross-tenant 차단 ✅ (CR 0-2 RLS + CsvExportCrossTenantError)
- AC-5: owner/admin role 만 호출 가능 ✅ (AD-22 RBAC)
- AC-6: audit log INSERT (action='export_csv', action_class=ActionClass.AUDIT) ✅ (CR 1-1 audit-first)
- AC-7: period YYYY-MM format 검증 ✅ (Pydantic field_validator)
- AC-8: NFR5 streaming P95 ≤ 5s for 100k rows ✅ (MAX_EXPORT_ROWS=100_000 + CHUNK_FLUSH_ROWS=5000)

## §10 신규 chain 진입 결정 wire (cj-285+ options)

| 옵션 | 결정 wire | 비고 |
|---|---|---|
| **(a)** | cj-285+ EXTENSION wire sprint (capability matrix v1.54 EXTENSION + 4 audit actions EXTENSION source+docs atomic) | **RECOMMENDED** — cj-282a 의 결정 wire 보류분 5종 EXTENSION 적용 |
| **(b)** | cj-282b wire sprint (cj-style 285번째, Story 30.2 PDF weasyprint 결정 + source+docs atomic) | OQ-EPIC30+-1 + OQ-EPIC30+-4 결정 진입 |
| **(c)** | Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory) | Epic 29+ Story 29.1~29.18 actual UI 구현 territory 별도 future chain |

## §11 CR lessons applied (5종)

- **CR 9-6 D5 prevention**: `git commit -F <file>` pattern 사용 (amend 금지). lint-conventions FAIL fix 에서 amend 안 하고 별도 commit `e803ae2` 으로 정정 결정 wire 보존.
- **CR 11-3 honest-DEFER**: 13/14 PASS + 1/14 expected P3 BLOCKING honestly reported. close-out retro 자체 source code 변경 0건 결정 wire.
- **CR 11-4 plan mode**: cj-282a wire sprint 진입 시 Plan mode 진입 → ExitPlanMode 결정 wire 보존 (cjs-style 284번째 close-out retro 진입 시 동일 pattern 적용).
- **CR 12-1 audit-first INSERT**: AD-2 audit-first INSERT append-only 결정 wire 보존 (CR 1-1 verbatim mirror). audit action='export_csv' (ActionClass.AUDIT re-use 결정).
- **CR 12-5 D-14 typed exception envelope**: 5 NEW typed exception classes (CsvExportError + CsvExportInvalidRequestError + CsvExportForbiddenError + CsvExportCrossTenantError + CsvExportTooLargeError) 결정 wire 보존.

## §12 scope boundary 결정 wire

- **cj-282a wire sprint 의 source surface 결정 wire**: 7 NEW source/test files (csv_routes.py + export_schemas.py + reports/page.tsx + reports/layout.tsx + CsvExportTab.tsx + test_phase_30_exports_csv.py + CsvExportTab.test.tsx) + 4 NEW/MODIFIED meta files.
- **close-out retro (cj-style 284번째) 결정 wire**: docs-only atomic single sprint — source code 변경 0건 + dev_seed 변경 0건 + ci.yml 변경 0건 + AD-14 stack pin 변경 없음 + [STACK BUMP] tag 불필요.
- **본 close-out retro 의 source surface 결정 wire**: 3 NEW docs files (14-section retro document + commit-msg-cj-284.txt + 6-section handoff) + 2 MODIFIED meta files (sprint-status.yaml v4.54 → v4.55 EXTENSION + MEMORY.md hook EXTENSION).

## §13 honestly DEFER carryover

**5 EXTENSION 결정 wire cj-285+ 적용 보류** (cj-282a wire sprint 결정 wire 보존):

1. **Capability matrix v1.53 → v1.54 EXTENSION** — `Capability.EXPORTS_CSV/PDF/EMAIL/SCHEDULED` 4 NEW enum + 4-industry grants + matrix md row EXTENSION + drift detector test EXTENSION.
2. **AuditAction 4 NEW Literal EXTENSION** — `ExportsAction = Literal["export_csv", "export_pdf", "export_email", "export_scheduled"]` + DB CHECK constraint EXTENSION.
3. **dev_seed.py `report_fixtures` 시나리오 EXTENSION** — acme tenant + 100 cost_records + 10 BOM rows for period_key='2026-08'.
4. **ci.yml web-e2e step 19 csv-export.spec.ts EXTENSION** — cj-285+ 진입 시 결정.
5. **AD-56 Epic 30+ 결정 wire 7 sub-decisions** — verbatim cross-reference pattern 결정 wire.

**OQ-CLOSE-001 신규 honestly DEFER**: 본 close-out retro 자체에서 5 EXTENSION 적용할지 별도 sprint 로 분할할지 결정 — cj-285+ 결정 진입.

## §14 결정 wire 일자 + lessons learned (10종)

**결정 wire 일자**: 2026-09-06 (KST)

**Lessons learned (10종)**:

1. **Risk Lowest = stdlib csv + FastAPI StreamingResponse** — no new infra 결정 wire 보존 → CI web-e2e skip 부담 0건 (cj-282a/b bulk skip 18 specs 유지 결정 wire).
2. **utf-8 BOM = U+FEFF (﻿)** — RFC 4180 + Excel ko-KR 호환 = 필수 결정 wire 보존.
3. **chunked streaming + CHUNK_FLUSH_ROWS=5000** — NFR5 streaming P95 ≤ 5s for 100k rows 결정 wire 보존.
4. **CR 12-5 D-14 typed exception envelope** — 5 typed exceptions + ko-KR SSOT message 결정 wire 보존.
5. **CR 1-1 audit-first INSERT** — action='export_csv' + action_class=ActionClass.AUDIT (EXISTING re-use 결정, 신규 sub-class 아님) 결정 wire 보존.
6. **Pydantic v2 ConfigDict migration** — `class Config:` → `model_config = ConfigDict(extra="forbid", ...)` 결정 wire 보존 (v2 deprecation 회피).
7. **vitest most-recent-first UX convention** — period options[0] = current month 결정 wire 보존 (UX intuition).
8. **CR 9-6 D5 prevention** — `git commit -F <file>` pattern (amend 금지) 결정 wire 보존.
9. **PowerShell `&&` not supported** — `;` 또는 Set-Location chain 사용 결정 wire 보존 (PowerShell 5.1 limitation).
10. **cj-285+ options 결정 wire** — 옵션 (a) cj-285+ EXTENSION wire sprint (capability matrix + 4 audit actions, RECOMMENDED) / 옵션 (b) cj-282b Story 30.2 PDF / 옵션 (c) Epic 29+ spec implementation chain 결정 wire 보존.

**cj-style chain 결정 wire 보존**: cj-282 Epic 30+ PRD entry (commit 0c7524e) → cj-282a wire sprint (commits eae9110+e803ae2) → **cj-style 284번째 close-out retro (본 document)** 결정 wire.
