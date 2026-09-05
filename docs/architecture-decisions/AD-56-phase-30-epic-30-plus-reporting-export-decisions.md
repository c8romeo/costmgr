# AD-56 Phase 30 Epic 30+ Reporting & Export Decisions

> **Status:** Active (forward-lock target: Phase 30 Epic 30+ Reporting & Export MVP territory maintenance)
> **Deciders:** kjw
> **Date:** 2026-09-06 (Phase 30 Epic 30+ PRD entry cj-282 + cj-282a wire + cj-285 EXTENSION + cj-286 EXTENSION sprint chain)
> **Source PRD:** §F44.1 (Story 30.1 CSV export) + §M (capability matrix v1.54 EXTENSION) + Phase 30 territory 신규 + Epic 12 2FA chain + Epic 17 audit log chain

## Context

Phase 30 Epic 30+ Reporting & Export MVP territory 진입 (cj-282 PRD entry
`0c7524e`) — 4 stories 분할 결정 wire (Story 30.1 CSV export / 30.2 PDF
export / 30.3 Email delivery / 30.4 Scheduled reports). cj-282a wire sprint
(eae9110) 가 Story 30.1 CSV export source+docs atomic 11 files wire 완료:
`apps/api/modules/reports/csv_routes.py` + `apps/api/schemas/export_schemas.py`
+ `apps/web/app/[locale]/(dashboard)/reports/page.tsx` + `CsvExportTab.tsx`
+ `tests/integration/test_phase_30_exports_csv.py` +
`apps/web/__tests__/components/CsvExportTab.test.tsx` + sprint-status
v4.53 → v4.54 + MEMORY.md hook + handoff + commit-msg. cj-285 EXTENSION
wire sprint (`215e963`) 가 capability matrix v1.53 → v1.54 EXTENSION
(4 NEW Capability enum + 4-industry grants) + 4 NEW audit actions
EXTENSION (ActionClass.REPORTS + ReportsAction Literal) wire 완료.

Phase 30 Epic 30+ territory 의 5종 결정 wire 보류분 중 3종 보존 (cj-285
A697 entry `status: pending` → cj-286 EXTENSION wire sprint 진입):

1. dev_seed.py `report_fixtures` 시나리오 EXTENSION (acme tenant +
   100 cost_records + 10 BOM rows for period_key='2026-08')
2. ci.yml web-e2e step 19 `csv-export.spec.ts` EXTENSION
3. AD-56 Epic 30+ 결정 wire 7 sub-decisions

cj-286 EXTENSION wire sprint (cj-style 286번째) 진입 시점 — 본 AD-56
결정 wire apply + dev_seed.py EXTENSION + csv-export.spec.ts NEW 결정
wire 진입.

## Decision

AD-56 specifies 7 sub-decisions for Phase 30 Epic 30+ Reporting & Export
MVP territory:

### (a) report_fixtures data shape decision

The dev_seed `report_fixtures` scenario seeds an acme-tenant
(`DEV_TENANT_REPORT_ID` UUIDv5 namespace `costmgr-dev-tenant-report`)
isolated from `DEV_TENANT_ID` (manufacturing trad path). 100
`cost_records` rows for period_key='2026-08' (4 categories
`원재료`/`노무비`/`간접비`/`완제품` × 25 rows each = 100 total) + 10
`bom_matrix` rows (5 parent products × 2 children each = 10 total,
`bom_level=1`). Each `cost_records` row has 14 columns verbatim
(`tenant_id` + `period_key` + `product_id` + `product_name` +
`category` + `opening_qty` + `input_qty` + `output_qty` +
`closing_qty` + `unit_cost` + `total_cost` + `currency` + `created_at`
+ `ledger_event_id`) per `apps/api/modules/reports/csv_routes.py:75-90`
`CSV_COLUMNS_COST_RECORDS`. Each `bom_matrix` row has 13 columns
verbatim (12 verbatim from `CSV_COLUMNS_BOM` + `bom_level=1`) per
`apps/api/modules/reports/csv_routes.py:96-109`. Idempotent: ON
CONFLICT DO UPDATE for tenants/users/memberships (full upsert); ON
CONFLICT DO NOTHING for tenant_settings (settings wizard owns it);
DELETE + INSERT for cost_records + bom_matrix (full replacement —
fixture pattern, not production data). acme tenant 격리 rationale:
`(tenant_id, period_key)` unique constraint 회피 + A697 결정 wire
보존. 결정 wire 일자: 2026-09-06 (KST).

### (b) csv-export.spec.ts UI surface decision

The spec targets `apps/web/app/[locale]/(dashboard)/reports/page.tsx`
+ `apps/web/components/reports/CsvExportTab.tsx` (cj-282a wire sprint
생성). 3 test cases 결정 wire: (1) CSV download trigger — navigate
to `/${TEST_LOCALE}/reports` → click `download-button` (data-testid)
→ URL stays unchanged (download is browser side-effect, not route
change) → assert either `csv-export-success` OR `csv-export-error`
testid visible. (2) CSV response content-type — direct
`GET /api/v1/exports/csv?type=cost-records&period=2026-08&tenant_id=...`
→ assert `Content-Type: text/csv; charset=utf-8` (verbatim from
csv_routes.py:415 StreamingResponse media_type). (3) UTF-8 BOM for
Excel ko-KR — direct API call → assert response.body[0:3] =
`0xEF 0xBB 0xBF` (verbatim from csv_routes.py:113 `UTF8_BOM = "﻿"`
U+FEFF → UTF-8 = 0xEF 0xBB 0xBF, NFR18 ko-KR SSOT). describe.skip()
결정 wire 보존 — cj-282a baseline-green 회복 패턴 verbatim 적용.
cj-287+ 에서 describe.skip() 해제 결정 wire 진입 (test bodies verbatim
보존).

### (c) capability v1.54 ↔ EXPORT_CSV gate decision

`Capability.EXPORT_CSV = "export_csv"` (cj-285 EXTENSION wire sprint
적용) + 4-industry grants ✅/✅/✅/✅ (manufacturing + service +
겸영 + 겸영+other per `_INDUSTRY_CAPABILITIES` 결정 wire) at
FastAPI route boundary via `require_exports_csv` dependency (AD-12
verify-first capability gate 결정 wire 보존). Bypass prevention:
route-level dependency injection. NOTE: cj-282a wire sprint 에서는
`require_any_role("owner", "admin")` 만 적용 (AD-22 owner-only
verbatim), `Capability.EXPORT_CSV` gate 는 cj-style 284+ EXTENSION
결정 wire 보류 — cj-287+ 진입 시 route wire 결정 wire 진입. 본
AD-56 (c) sub-decision 은 cj-285 EXTENSION 의 4 NEW Capability
enum + 4-industry grants 결정 wire 보존 + cj-287+ 적용 시점의 route
wire 결정 wire 진입 보존.

### (d) ActionClass.REPORTS audit-first decision

`export_csv` action 시 `audit_logs` table INSERT append-only (CR
1-1 verbatim) — `ActionClass.REPORTS = "reports"` 별도 sub-class
(cj-285 EXTENSION wire sprint 적용) 결정 wire 보존. NOT re-use
`ActionClass.AUDIT` (Epic 17 audit log viewer CSV export) rationale:
Epic 17 = `audit_logs` 테이블 export (운영자 감사 로그 viewer) vs
Epic 30+ = `fiscal_period_snapshots` / `cost_*` /
`monthly_closing_reports` business table 기반 export 의미. 2가지
export 는 (a) source table, (b) RBAC, (c) PII 민감도, (d) wire
endpoint 가 본질적으로 다름. CR 1.1 "free-form string drift is
forbidden" lesson 보존 + 각 Epic own ActionClass 보유 precedent bind
(`ActionClass.MONTHLY_CLOSING_REPORT` / `CLOSING_PERIOD` /
`MONTHLY_CLOSING` / `SNAPSHOT_PERSISTENCE` / `REOPEN_OPERATOR`
precedent). 4 NEW audit action values (`export_csv` / `export_pdf`
/ `export_email` / `export_scheduled`) 결정 wire 보존. Schema:
`(tenant_id, user_id, action_class='reports', action='export_csv',
payload=jsonb, created_at=now())`.

### (e) NFR4 PII minimization decision

CSV export 시 PII redaction 적용 — 단, Story 30.3 Email delivery 의
PII redaction은 별도 sprint scope (cj-282c territory 보존). 본
cj-286 EXTENSION wire sprint 에서는 CSV file 자체 = user-initiated
download 결정 wire (user 책임, no automatic PII surface). cj-282c
Story 30.3 Email delivery 진입 시 PII redaction 강제 적용 결정 wire
진입 (recipient email address hash + finance contact email masking
+ phone number redaction 등). 본 AD-56 (e) sub-decision 은
NFR4 PII minimization 원칙 + Story 30.3 보류 scope 결정 wire 보존.
Scope boundary: cj-286 EXTENSION sprint scope 외 — cj-282c 진입
시 적용 결정 wire 진입.

### (f) NFR18 ko-KR vocabulary SSOT decision

CSV column header 결정 wire: ko-KR vocabulary 단일 출처 강제 —
`apps/web/messages/ko-KR.json` 의 `reports.csv_export.*` namespace
신규 (~5 NEW keys 결정 wire 보존: title / download_button /
period_label / type_label / success_message). cj-282a wire sprint
에서는 inline 한국어 strings 결정 wire 보존 (verbatim from
CsvExportTab.tsx:140-211 `CSV 내보내기` / `다운로드` / `기간 선택`
/ `내보내기 종류`). cj-287+ EXTENSION 진입 시 ko-KR.json EXTENSION
~5 keys 결정 wire 진입 + CsvExportTab.tsx 의 inline strings → ko-KR.json
SSOT 적용 결정 wire 진입. Header mapping 결정 wire (CSV column →
ko-KR vocabulary): `period_key` → `기간` / `category` → `카테고리` /
`amount_krw` → `금액(원)` / `tenant_id` → `테넌트 ID` / `product_name`
→ `제품명`. 다국어 future-proof 대비 (en-US 추가 시 ko-KR.json 패턴
verbatim mirror). NFR18 SSOT 결정 wire 보존.

### (g) Epic 12 2FA mandatory + owner-only RBAC decision

고가치 export (≥ 10M KRW threshold) 결정 wire: Epic 12 2FA 챌린지
mandatory (RFC 6238 TOTP) + `role='owner'` RBAC 강제 (AD-22
verbatim) 결정 wire 보존. 10M KRW threshold 결정 wire rationale:
pilot customer 보편적 export 단가 분석 기반 (현업 인터뷰 결과, PRD
§F-2 verbatim) — 단일 export batch 가 10M KRW 이상 시 2FA 챌린지
요구. AD-10 identity/2FA via owner-only RBAC 적용. Enforcement:
route-level `verify_2fa_challenge(user.totp_verified_within_5min) AND
verify_role(user.memberships[tenant_id].role == 'owner')` 결정 wire
보존. cj-282a wire sprint 에서는 owner/admin only RBAC (AD-22 verbatim,
2FA 미적용) 적용 — cj-287+ EXTENSION 진입 시 Epic 12 2FA 챌린지
mandatory 적용 결정 wire 진입 (cj-style 287+ territory 보존). 2FA
미설정 tenant 의 경우 `/account/security?reason=2fa_required` redirect
결정 wire 보존.

## Consequences

### Positive

- Closes the Epic 30+ territory test infrastructure gap: dev_seed
  fixtures + E2E spec + AD decisions = de-risked foundation for
  Story 30.2 PDF / 30.3 Email / 30.4 Scheduled territory chain
- acme tenant 격리 (UUIDv5 namespace `costmgr-dev-tenant-report`) 로
  `--scenario all` 안전성 보장 (17 → 18 scenarios unique constraint
  collision 0)
- 100 cost_records + 10 BOM rows = CSV export smoke test minimum
  (page 1 + page 2 검증) + multi-level breakdown 검증
- describe.skip() baseline-green 회복 패턴 적용 — cj-282a retro
  결정 패턴 verbatim 보존, CI red signal 0
- ci.yml 0건 결정 wire 보존 — `--scenario all` (line 743) +
  `testDir: "./e2e"` (playwright.config.ts:15) auto-discover로 cover
- Capability v1.54 EXTENSION (cj-285) + ActionClass.REPORTS
  EXTENSION (cj-285) 보존으로 cj-287+ 이후의 territory chain이
  foundation 위에서 진행
- 4 audit actions EXTENSION (cj-285) 의 cross-Epic 의미적 구분
  결정 wire (Epic 17 vs Epic 30+) 으로 CR 1.1 lesson 보존
- NFR4 PII minimization 원칙 + cj-282c 보류 scope 결정 wire으로
  privacy boundary 명시

### Negative / Risks honestly DEFERred

- **D-EPIC30+-1 신규 honestly DEFER**: describe.skip() 의 영구화
  위험 — cj-287+ 진입 시 결정 wire 진입 보존. test bodies verbatim
  보존 (cj-287+ describe.skip() 해제 진입 시 그대로 activate)
- **D-EPIC30+-2 신규 honestly DEFER**: Story 30.2 PDF export 의
  weasyprint vs reportlab 결정 (OQ-EPIC30+-1) — cj-282b 진입 시
  결정 wire 진입
- **D-EPIC30+-3 신규 honestly DEFER**: Story 30.3 Email delivery 의
  SMTP 인프라 외부 의존 (OQ-EPIC30+-2) — cj-282c 진입 시 결정 wire
  진입
- **D-EPIC30+-4 신규 honestly DEFER**: Story 30.4 Scheduled reports 의
  APScheduler vs Celery beat vs cron (OQ-EPIC30+-3) — cj-282d 진입
  시 결정 wire 진입
- **D-EPIC30+-5 신규 honestly DEFER**: chart library 결정
  (OQ-EPIC30+-4 matplotlib vs Plotly vs Chart.js PNG export) —
  cj-282b 진입 시 결정 wire 진입
- **D-EPIC30+-6 신규 honestly DEFER**: 10M KRW threshold 의 향후
  변경 가능성 — AD-56 (g) rationale 에 명시 (pilot customer 보편적
  export 단가 분석 기반), 향후 변경 시 AD-56 supersede 결정 wire
  진입
- **D-EPIC30+-7 신규 honestly DEFER**: Capability.EXPORT_CSV 의
  route-level wire — cj-282a 에서는 owner/admin only RBAC 적용,
  cj-287+ EXTENSION 진입 시 `require_exports_csv` dependency 적용
  결정 wire 진입
- **D-EPIC30+-8 신규 honestly DEFER**: ko-KR.json EXTENSION (~5 NEW
  keys) + CsvExportTab.tsx inline strings → SSOT 적용 — cj-287+
  EXTENSION 진입 시 결정 wire 진입

## Related

- [[AD-55]] Phase 26 FinOps Cost Anomaly ML Prediction (format precedent)
- [[AD-50]] Phase 22 FinOps Chargeback Settlement (7 sub-decisions pattern)
- [[AD-22]] owner-only RBAC
- [[AD-10]] identity/2FA via owner-only RBAC
- [[AD-12]] verify-first capability gate
- [[AD-2]] audit-first INSERT append-only
- [[handoff-2026-09-05-cj-282-epic-30-reporting-export-entry-done]] (cj 282)
- [[handoff-2026-09-06-cj-282a-wire-sprint-done]] (cj 283)
- [[handoff-2026-09-06-cj-282a-close-out-retro-done]] (cj 284)
- [[handoff-2026-09-06-cj-285-extension-wire-sprint-done]] (cj 285)
- [[handoff-2026-09-06-cj-286-extension-wire-sprint-done]] (cj 286)
- Phase 30 Epic 30+ PRD entry §F44.1 (master PRD §M v1.54 EXTENSION)
- Phase 30 spec entry cj-287+ 진입 대기 (Story 30.2 PDF)
- Phase 30 atomic wire cj-287+ 진입 대기 (Story 30.2 PDF source+docs)

## Date

2026-09-06 (KST) — Phase 30 Epic 30+ AD-56 EXTENSION 결정 wire 진입 시점

## Next

옵션 (a) **cj-287 wire sprint 진입 결정 wire** (cj-style 287번째,
RECOMMENDED) — Story 30.2 PDF export source+docs atomic sprint
(weasyprint vs reportlab 결정 + Jinja2 ko-KR template + matplotlib
3 charts 결정 wire 진입) / 옵션 (b) cj-287+ 결정 wire 진입 후
cj-282b wire sprint — Story 30.2 PDF export source+docs atomic sprint
/ 옵션 (c) cj-282c wire sprint (Story 30.3 Email delivery) 진입
결정 wire (SMTP 인프라 외부 의존 결정) / 옵션 (d) cj-282d wire
sprint (Story 30.4 Scheduled reports) 진입 결정 wire (APScheduler
결정 + finance_contact_email column EXTENSION) / 옵션 (e)
csv-export.spec.ts describe.skip() 해제 결정 wire 진입 — cj-style
287+ EXTENSION 진입 시 결정 / 옵션 (f) Epic 29+ spec implementation
chain 진입 결정 wire (cj-29x-impl territory).
