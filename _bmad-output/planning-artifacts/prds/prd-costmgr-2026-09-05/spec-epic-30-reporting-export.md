---
title: "Epic 30+ — Reporting & Export MVP PRD Entry (costmgr)"
status: draft
created: "2026-09-05"
finalized_by: "kjw (option (γ) approval — Reporting & Export MVP, 4-story atomic 분할)"
finalized_at: "2026-09-05T09:45:00+09:00"
rubric_verdict: "n/a (cj-style entry sprint — 7-dim review deferred to cj-282 close-out)"
polish_pass: "n/a (entry draft — wire sprint 결정 wire 진입 후 polish 결정 wire)"
parent_prd: "_bmad-output/planning-artifacts/prd.md v7.0 (final, 2026-08-26)"
epic: "30+"
entry_mode: "cj-style 282번째 epic 연속 정직 회복 = Epic 30+ 1번째 진입점 (option (γ) 신규 territory 결정 wire — cj-281 Epic 29+ chain FINAL CLOSED 직후 첫 product sprint)"
carries: "cj-style chain cj-229~281 CLOSED ✅ HONEST (cj-281 결정 wire). Epic 29+ chain cj-274~281 CLOSED ✅ HONEST (cj-281 결정 wire, 8 sprint). Epic 29+ 본 wire (Story 29.1~29.18 spec implementation) = 별도 future chain (cj-29x-impl territory, 보류 결정 wire)."
stakes: "internal tool (3~5 page PRD)"
working_mode: "Fast path — kjw review + iterate"
form_factor: "FastAPI endpoint (apps/api/modules/reports/) + minimal UI download trigger (apps/web/app/[locale]/(authenticated)/reports/)"
stakeholders: "kjw (PM/lead, 운영자/회계감사 contact) + Amelia (platform engineer)"
---

# Epic 30+ — Reporting & Export MVP PRD (costmgr)

> **Scope.** 본 문서는 master PRD v7.0 (`_bmad-output/planning-artifacts/prd.md`)를 보완하는 Epic 30+ PRD entry 이다. 본 Epic 30+ 의 territory 결정 wire = cj-281 Epic 29+ chain FINAL CLOSED 직후 option (γ) 신규 territory 진입 결정 (Reporting & Export MVP). cj-274 의 6 D-WEB-E2E-1~6 honestly DEFER items 의 Epic 29+ ownership 이전 결정 wire 와 별개 territory 이다.
>
> **cj-style chain 정합.** cj-281 cj-style chain CLOSED ✅ HONEST 결정 wire — cj-style chain (cj-229 ~ cj-281) = 본 chain 이전 53 sprint 진입 정합 보존. 본 Epic 30+ PRD entry = cj-style 282번째 진입점. Epic 29+ spec implementation 은 별도 future chain (cj-29x-impl territory, 보류 결정 wire) 으로 분리.
>
> **Master PRD 정합.** 본 PRD는 master PRD §F (ADs) / §M (modules) / §R (reports) 부분 EXTENSION 결정 wire — AD-2 + AD-10 + AD-12 보존 + REPORTING_CSV_EXPORT + REPORTING_PDF_EXPORT + REPORTING_EMAIL_DELIVERY + REPORTING_SCHEDULED 4 NEW capability row 결정 wire (master PRD §M capability matrix v1.47 → v1.48 EXTENSION 결정 wire). Epic 29+ (테스트 coverage extension) 와 본 Epic 30+ (user-facing feature) 의 명확한 territory 분리.

---

## 0. Document Purpose

본 PRD 는 Epic 30+ 본 wire sprint 진입 이전에 PRD-level acceptance criteria + architecture bind + capability matrix EXTENSION 을 확정한 Epic-level PRD extension 이다. 본 문서는 Epic 30+ spec entry 작성자 (`_bmad-output/implementation-artifacts/epic-30-*.md`) 와 Epic 30+ wire developer 양쪽이 single source 로 활용한다. 본 PRD 종결 후 `bmad-create-story` 4 진입 (cj-style Epic 30+ 2~5번째 진입점) → wire cycle 진입 (cj-style 283~286번째) → close-out retro 진입 (cj-style 287번째) 의 표준 cj-style chain pattern 적용.

---

## 1. Vision

**한 문장 정의:**

> **"회계감사용 CSV/Excel export + 월간 보고서 PDF 자동 생성 + 이메일 발송 + 스케줄링 = costmgr 운영자가 매월 말 회계감사 자료 준비 시간을 8h → 0.5h로 단축하는 자동 export pipeline"**

- **배경.** cj-style chain cj-229~281 (2026-08-04 ~ 2026-09-05) 53 sprint 의 인프라 결함 정직 회복 + Epic 29+ PRD/wire 진입 종료 (cj-274~281, 8 sprint). Epic 29+ spec implementation (Story 29.1~29.18 본 wire) 은 별도 future chain 으로 보류 결정. Epic 30+ = 운영자/회계감사용 user-facing export pipeline.
- **가치.** Epic 30+ 가 green 으로 종결되면 매월 회계감사용 자료 (CSV/Excel + PDF) 자동 생성 + 이메일 발송 → 운영자 수동 작업 8h → 0.5h. Pilot launch 시 회계감사 surface 신뢰도 +++. B2B SaaS 재무팀의 #1 요청 기능 = "export to Excel" (업계 표준).
- **out-of-band.** Epic 30+ 는 master PRD §F (ADs) 부분 EXTENSION (4 NEW capability row) + §M (modules) 부분 EXTENSION (apps/api/modules/reports/ NEW) + §R (reports) EXTENSION (보고서 카탈로그 +5 → +9). Epic 29+ (테스트 coverage extension only, capability 0) 와 명확한 territory 분리.

---

## 2. Target User

### 2.1 Jobs To Be Done

- **kjw (PM/lead, 운영자/회계감사 contact)**: "매월 말 회계감사용 CSV/Excel 자료를 8시간 안에 만들어야 하는데, 지금은 manual SQL query + Excel paste 로 진행 중" → 자동 export pipeline 필요. Pilot launch 시 회계감사 대응 능력 immediate.
- **재무팀 (외부, pilot 고객)**: "월간 보고서를 PDF 로 받아서 임원진에게 메일 forward" → PDF 자동 생성 + email 발송 필요.
- **세무사 (외부, pilot 고객)**: "분기별 cost detail 을 Excel 로 받아서 세무 신고" → CSV/Excel export 필요.

### 2.2 Non-Users (v1)

- **데이터 분석가 (외부)**: BI 도구 연동 (Looker, Metabase) = 별도 epic territory. Epic 30+ 는 file-based export 만.
- **모바일 native**: master PRD NFR20 (반응형 웹만). 모바일 native export = 별도 epic territory.
- **API consumer**: REST API public beta = 별도 epic territory (cj-282 PR FAQ 시점에 결정).

### 2.3 Key User Journeys

> UJ-30+ 는 회계감사용 export journey 만 캡처 (master PRD UJ-1~4 외부 user journey 와 별개).

- **UJ-30-1. kjw 가 월말 회계감사용 CSV export 한다.**
  - **Persona + context**: kjw (PM/lead), 매월 말 KST 17:00, 회계감사용 cost records CSV 필요.
  - **Entry state**: 로그인 후 [보고서] 페이지 진입.
  - **Path**: (1) [보고서] 페이지 → [CSV 내보내기] 탭 선택 (30초) → (2) period selector = `2026-08` 선택 (15초) → (3) type selector = `cost-records` 선택 (15초) → (4) [다운로드] 버튼 클릭 → backend GET `/api/v1/exports/csv` invocation → CSV file download (5초).
  - **Climax**: 35초 안에 cost records CSV 다운로드 완료.
  - **Resolution**: 회계감사용 CSV 확보, Excel paste 불필요.
  - **Edge case**: 10만 row 초과 → streaming response + gzip compression (NFR5 ≤ 5s 페이지 로드 보존).

- **UJ-30-2. kjw 가 월간 보고서 PDF 를 재무팀에 자동 발송한다.**
  - **Persona + context**: kjw (PM/lead), 매월 둘째 주 KST 10:00, 재무팀 monthly summary 보고서 발송.
  - **Entry state**: 보고서 페이지 진입, 직전 월 monthly summary PDF 미리보기.
  - **Path**: (1) [월간 보고서 PDF] 탭 선택 (30초) → (2) period = `2026-07` 선택 (15초) → (3) recipient email 입력 (`finance@customer.com`) (30초) → (4) [발송] 버튼 클릭 → POST `/api/v1/exports/email` invocation → 60초 안에 email 도착 + audit log row INSERT.
  - **Climax**: 1분 30초 안에 monthly summary PDF 이메일 발송 완료.
  - **Resolution**: 재무팀 monthly summary 자동 발송, kjw 수동 작업 0.
  - **Edge case**: SMTP failure → retry 3회 + audit log failure row + kjw Slack alert (NFR7 fail-safe 결정 wire).

- **UJ-30-3. 재무팀이 scheduled report 를 매월 자동 수신한다.**
  - **Persona + context**: 재무팀 (외부 pilot 고객), 매월 둘째 주 KST 09:00, scheduled monthly summary 도착.
  - **Entry state**: 이메일 inbox, 자동 발송된 monthly summary PDF 첨부.
  - **Path**: (1) email open → PDF 첨부 다운로드 → (2) PDF 내부: 회사 로고 + 월간 손익 요약 + 부문별 cost breakdown + chart 3개 (NFR18 ko-KR vocabulary) → (3) 임원진 forward.
  - **Climax**: 외부 재무팀이 0 클릭으로 monthly summary 수신.
  - **Resolution**: scheduled delivery 0 실패율 (NFR8 99.9% uptime).
  - **Edge case**: SMTP outage → scheduled job retry queue + 다음 cron cycle 까지 대기 (NFR7 fail-safe 결정 wire).

---

## 3. Glossary

- **EXPORT_CSV** — Epic 30+ Story 30.1 capability. apps/api/modules/reports/csv_routes.py.
- **EXPORT_PDF** — Epic 30+ Story 30.2 capability. apps/api/modules/reports/pdf_routes.py + weasyprint HTML→PDF.
- **EXPORT_EMAIL** — Epic 30+ Story 30.3 capability. apps/api/modules/reports/email_routes.py + SMTP delivery.
- **EXPORT_SCHEDULED** — Epic 30+ Story 30.4 capability. apps/api/jobs/scheduled_reports.py + APScheduler / cron.
- **dev_seed EXTENSION** — Epic 29+ 의 dev_seed.py (cj-275~278c 결정 wire) 와 별개. Epic 30+ dev_seed EXTENSION = `report_fixtures` scenario (회계감사용 sample data 1 set).
- **Master tenant** — `_bmad-output/planning-artifacts/prd.md` 의 `acme` tenant (Epic 29+ 의 DEV_TENANT_ID 와 별개, 동일 tenant_id 재사용 결정).
- **SMTP** — Simple Mail Transfer Protocol. 운영 SMTP server (예: SendGrid, AWS SES) = 외부 인프라, cj-29x+ provisioning 결정 wire.
- **streaming response** — FastAPI `StreamingResponse` + `csv.DictWriter` iterator pattern (10만 row 처리 시 NFR5 page load ≤ 5s 보존).
- **NFR18 ko-KR vocabulary** — master PRD §14 UI vocabulary. 본 Epic 30+ PDF/CSV header/footer 에 verbatim 적용.
- **AD-2 append-only** — audit-first INSERT only. CSV/PDF export 자체는 append-only 와 무관하나, export event 자체는 audit_logs 에 INSERT (Story 30.1~30.4 모두).
- **AD-12 verify-first** — capability matrix verify 통과 후 본 기능 진입. 본 Epic 30+ 의 4 NEW capability (EXPORT_CSV/EXPORT_PDF/EXPORT_EMAIL/EXPORT_SCHEDULED) 모두 verify-first gate 통과 결정 wire.

---

## 4. Features

> 각 subsection 은 coherent feature: behavioral description → FRs nested → optional feature-specific NFRs / notes. FRs are globally numbered FR-30-1 through FR-30-4 (4 stories = 4 FRs).

### 4.1 Feature 30.1 — D-REPORTS-1 CSV Export (Cost Records + BOM)

**Description:** 회계감사용 cost records + BOM 을 CSV 로 download. GET endpoint + streaming response + audit log. Bind: AD-2 (audit-first) + AD-12 (verify-first capability gate). Realizes UJ-30-1.

**Functional Requirements:**

#### FR-30-1: CSV Export Cost Records + BOM Download

[Backend endpoint] can [return] that [when authenticated operator GETs `/api/v1/exports/csv?type=cost-records&period=YYYY-MM&tenant_id={uuid}`, the response is `text/csv; charset=utf-8` with `Content-Disposition: attachment; filename=cost-records-{period_key}.csv` and body = CSV with columns `tenant_id, period_key, product_id, product_name, category, opening_qty, input_qty, output_qty, closing_qty, unit_cost, total_cost, currency, created_at, ledger_event_id` (RFC 4180 quoted, UTF-8 BOM for Excel ko-KR compatibility)]. AND [audit_logs has row `(actor_id, action='export_csv', target_type='cost_record', target_id=null, period_key, occurred_at, trace_id)`].

**Consequences (testable):**
- FastAPI route `apps/api/modules/reports/csv_routes.py` GET `/api/v1/exports/csv` + `apps/api/schemas/export_schemas.py` `CsvExportRequest(BaseModel)` + `StreamingResponse(media_type="text/csv")`.
- Audit log row INSERT 시 actor = JWT sub, target_type = `cost_record` (master PRD §14 audit vocabulary verbatim).
- CSV columns RFC 4180 quoted (double-quote escape), UTF-8 BOM `﻿` for Excel ko-KR compatibility (NFR18).
- 10만 row 처리 시 streaming response + gzip compression + NFR5 P95 ≤ 5s page load 보존.
- AD-2 bind verified: export event INSERT to `audit_logs` (append-only).
- AD-12 bind verified: EXPORT_CSV capability row (`capability_matrix` table) verify-first gate 통과 결정 wire (master PRD §M v1.48 EXTENSION).
- ko-KR UI: `[보고서] → [CSV 내보내기] → 기간 선택 → [다운로드]` (master PRD §14 vocabulary).
- data-testid: `reports-tab`, `csv-export-tab`, `period-selector-{YYYY-MM}`, `download-button`.

**Out of Scope:**
- Story 30.2 (PDF).
- Story 30.3 (Email).
- Story 30.4 (Scheduled).
- BOM 별도 export (Story 30.1 의 CSV columns 에 BOM level 1만 포함, full BOM tree export = 별도 epic territory 보류 결정 wire).

**Feature-specific NFRs:** *NFR5 streaming response (10만 row ≤ 5s page load). NFR18 UTF-8 BOM for Excel compatibility.*

---

### 4.2 Feature 30.2 — D-REPORTS-2 PDF Export (Monthly Summary Report)

**Description:** 월간 손익 요약 + 부문별 cost breakdown + chart 3개 PDF 자동 생성. HTML→PDF 변환 (weasyprint) + audit log. Bind: AD-2 + AD-12. Realizes UJ-30-2 step 1 (PDF 미리보기).

**Functional Requirements:**

#### FR-30-2: PDF Export Monthly Summary Report Download

[Backend endpoint] can [return] that [when authenticated operator GETs `/api/v1/exports/pdf?type=monthly-summary&period=YYYY-MM&tenant_id={uuid}`, the response is `application/pdf` with `Content-Disposition: attachment; filename=monthly-summary-{period_key}.pdf` and body = PDF with (1) cover page (tenant_name + period_key + generated_at), (2) 월간 손익 요약 table (총 매출 + 총 비용 + 영업이익 + 영업 이익률), (3) 부문별 cost breakdown table (제조/관리/영업/연구개발), (4) chart 3개 (월간 매출 추이 line chart + 부문별 비용 비중 pie chart + 전월 대비 증감 bar chart)]. AND [audit_logs has row `(actor_id, action='export_pdf', target_type='monthly_summary', period_key, occurred_at, trace_id)`].

**Consequences (testable):**
- FastAPI route `apps/api/modules/reports/pdf_routes.py` GET `/api/v1/exports/pdf` + `apps/api/services/pdf_generator.py` weasyprint HTML→PDF wrapper + `apps/api/templates/monthly_summary.html` Jinja2 template (ko-KR).
- Chart library: matplotlib (PNG) → embed via `<img src="data:image/png;base64,{...}">` (no external CDN, offline-safe).
- 10 page 이내 PDF (NFR12 page count limit).
- ko-KR vocabulary verbatim (master PRD §14): "월간 손익 요약", "총 매출", "총 비용", "영업이익", "영업 이익률", "부문별 비용 비중".
- AD-2 bind verified: audit_logs INSERT.
- AD-12 bind verified: EXPORT_PDF capability row verify-first gate 통과 결정 wire.
- ko-KR UI: `[월간 보고서 PDF] → 기간 선택 → [미리보기] → [다운로드]`.

**Out of Scope:**
- Story 30.1 (CSV).
- Story 30.3 (Email).
- Story 30.4 (Scheduled).
- Chart interactive (Plotly/Bokeh) = 별도 epic territory 보류 결정 wire (현재는 정적 PNG 결정 wire).

**Feature-specific NFRs:** *NFR12 PDF page count ≤ 10 (master PRD §14 PDF spec). NFR18 ko-KR vocabulary verbatim.*

---

### 4.3 Feature 30.3 — D-REPORTS-3 Email Delivery (Manual Trigger)

**Description:** Monthly summary PDF 를 재무팀/세무사/외부 stakeholder 에게 이메일 발송. SMTP + attachment + audit log. Bind: AD-10 (identity + auth) + AD-12. Realizes UJ-30-2 step 4 (이메일 발송).

**Functional Requirements:**

#### FR-30-3: Email Delivery with Attachment (PDF or CSV)

[Backend endpoint] can [deliver] that [when authenticated operator POSTs `/api/v1/exports/email` with body `{recipient_email, period_key, format: 'pdf'|'csv', tenant_id}`, the system (1) generates PDF or CSV (FR-30-1 or FR-30-2 reuse), (2) sends email via SMTP with attachment + ko-KR subject "월간 보고서 ({period_key})" + body "[{tenant_name}] 월간 보고서 ({period_key})을(를) 첨부하여 발송합니다.", (3) inserts audit_logs row `(actor_id, action='export_email', target_type='email', target_id={recipient_email}, period_key, occurred_at, trace_id)`, AND (4) returns HTTP 200 with `{delivery_id, status: 'sent', sent_at, recipient_email, period_key, format}`].

**Consequences (testable):**
- FastAPI route `apps/api/modules/reports/email_routes.py` POST `/api/v1/exports/email` + `apps/api/services/email_sender.py` SMTP wrapper (stdlib `smtplib` + `email.mime`).
- SMTP server: 환경변수 `SMTP_HOST` + `SMTP_PORT` + `SMTP_USER` + `SMTP_PASSWORD` + `SMTP_FROM` (apps/api/core/config.py 에 추가 결정 wire).
- Retry 정책: 3회 (NFR7 fail-safe) — 1차 즉시 실패 → 5분 후 retry → 30분 후 retry → 실패 시 audit_logs `status='failed'` + Slack alert (cj-29x+ 결정 wire).
- AD-10 bind verified: operator JWT 인증 + `export_email` action audit-first.
- AD-12 bind verified: EXPORT_EMAIL capability row verify-first gate 통과 결정 wire.
- NFR19 (PII redaction): recipient_email 에 tenant_id 마스킹 (`finance+{tenant_id_short}@customer.com` 패턴, 결정 wire 보류).
- ko-KR UI: `[이메일 발송] → 수신자 입력 → 기간 선택 → 포맷 선택 (PDF/CSV) → [발송] → 발송 완료 alert + delivery_id 표시`.

**Out of Scope:**
- Story 30.1 (CSV) 와 Story 30.2 (PDF) 자체.
- Story 30.4 (Scheduled).
- Bulk email (multiple recipient list) = 별도 epic territory 보류 결정 wire.

**Feature-specific NFRs:** *NFR7 retry 3회. NFR19 PII redaction recipient masking.*

---

### 4.4 Feature 30.4 — D-REPORTS-4 Scheduled Reports (Cron)

**Description:** 매월/매주/매일 scheduled report 자동 생성 + 이메일 발송. Background job (APScheduler / cron) + audit log. Bind: AD-12 + NFR4 (background jobs SLA). Realizes UJ-30-3.

**Functional Requirements:**

#### FR-30-4: Scheduled Report Cron + Delivery

[Background job] can [generate] that [when APScheduler / cron fires at `{cron_expression}` (e.g., `0 9 1 * *` = 매월 1일 09:00 KST), the system (1) iterates over all active tenants, (2) for each tenant generates monthly summary PDF (FR-30-2 reuse) for previous month, (3) sends email to tenant's `finance_contact_email` (tenant_metadata.finance_contact_email column, NEW column 추가 결정 wire) via FR-30-3 reuse, (4) inserts audit_logs row `(actor_id='system:scheduler', action='scheduled_report_sent', target_type='monthly_summary', target_id={tenant_id}, period_key, occurred_at, trace_id)`]. AND [GET `/api/v1/exports/scheduled` returns list of scheduled jobs with `{job_id, tenant_id, cron_expression, enabled, last_run_at, next_run_at, last_status}`].

**Consequences (testable):**
- APScheduler `BackgroundScheduler` + `apps/api/jobs/scheduled_reports.py` + `apps/api/main.py` startup hook.
- NEW alembic migration: `tenants.finance_contact_email VARCHAR(255) NULL` column EXTENSION.
- 99.9% uptime (NFR8): APScheduler restart on failure + `last_run_at` + `next_run_at` 결정 wire.
- AD-12 bind verified: EXPORT_SCHEDULED capability row verify-first gate 통과 결정 wire.
- ko-KR UI: `[스케줄 관리] → 새 스케줄 추가 → tenant 선택 + cron expression + enabled toggle → [저장]`. List view: `{job_id, tenant_name, cron, enabled, last_run_at, next_run_at, last_status}` table.

**Out of Scope:**
- Story 30.1 / 30.2 / 30.3 자체.
- Webhook / Slack delivery = 별도 epic territory 보류 결정 wire.

**Feature-specific NFRs:** *NFR4 background job SLA 99.9% uptime. NFR8 cron restart recovery.*

---

## 5. Architecture Bind

### 5.1 Capability Matrix EXTENSION (master PRD §M v1.47 → v1.48)

| Capability | Verify-first Gate | Description | Story |
|---|---|---|---|
| `EXPORT_CSV` | verify_first_export_csv | cost-records + BOM CSV export | 30.1 |
| `EXPORT_PDF` | verify_first_export_pdf | monthly summary PDF export | 30.2 |
| `EXPORT_EMAIL` | verify_first_export_email | email delivery with attachment | 30.3 |
| `EXPORT_SCHEDULED` | verify_first_export_scheduled | scheduled report cron | 30.4 |

### 5.2 AD Bind Coverage (3 master ADs)

| AD | bind FRs | Stories |
|---|---|---|
| AD-2 (append-only audit-first) | FR-30-1, FR-30-2, FR-30-3, FR-30-4 | 30.1, 30.2, 30.3, 30.4 (audit log INSERT) |
| AD-10 (identity + 2FA) | FR-30-3 | 30.3 (operator JWT auth) |
| AD-12 (verify-first capability) | FR-30-1, FR-30-2, FR-30-3, FR-30-4 | 30.1~30.4 (capability gate) |

### 5.3 NFR Bind Coverage (4 master NFRs)

| NFR | bind FRs | Stories |
|---|---|---|
| NFR4 (background job SLA) | FR-30-4 | 30.4 (APScheduler uptime) |
| NFR5 (page load P95 ≤ 5s) | FR-30-1 | 30.1 (streaming response) |
| NFR7 (retry fail-safe) | FR-30-3 | 30.3 (SMTP retry 3회) |
| NFR8 (background job 99.9% uptime) | FR-30-4 | 30.4 (cron restart) |
| NFR12 (PDF page count ≤ 10) | FR-30-2 | 30.2 (PDF spec) |
| NFR18 (ko-KR vocabulary) | FR-30-1, FR-30-2 | 30.1, 30.2 (ko-KR verbatim) |
| NFR19 (PII redaction) | FR-30-3 | 30.3 (recipient masking) |

---

## 6. Wire Sprint 분할 (cj-style 283~286 4 sprint 분할)

> cj-style atomic single sprint 원칙 = 1 sprint = 1 atomic deliverable. 4 stories → 4 sprints.

| Sprint | Story | Atomic Deliverable | Risk |
|---|---|---|---|
| **cj-282a** (P0 wire) | Story 30.1 CSV export | 1 endpoint + 1 UI tab + 1 test | ✅ Lowest (stdlib csv + StreamingResponse) |
| **cj-282b** (P1 wire) | Story 30.2 PDF export | 1 endpoint + weasyprint wrapper + 1 test | ⚠️ Medium (weasyprint dependency + Jinja2 template + matplotlib embed) |
| **cj-282c** (P1 wire) | Story 30.3 Email delivery | 1 endpoint + SMTP wrapper + 1 test | ⚠️ Medium (SMTP 인프라 외부 의존 + retry 정책) |
| **cj-282d** (P2 wire) | Story 30.4 Scheduled reports | 1 APScheduler job + 1 alembic migration + 1 UI list | ⚠️ Medium-High (cron + recovery + finance_contact_email column) |

### 6.1 cj-282a (Sprint 1, P0 minimum viable) — Story 30.1 CSV

- **Atomic scope**: `apps/api/modules/reports/csv_routes.py` NEW + `apps/api/schemas/export_schemas.py` NEW + `apps/web/app/[locale]/(authenticated)/reports/page.tsx` NEW + `apps/web/components/reports/CsvExportTab.tsx` NEW + audit log INSERT helper + 1 pytest + 1 vitest.
- **Wire verification**: pytest `tests/api/modules/reports/test_csv_routes.py` PASS + vitest `apps/web/components/reports/CsvExportTab.test.tsx` PASS.
- **Risk**: Low (all stdlib, no new infra).

### 6.2 cj-282b (Sprint 2, P1 PDF) — Story 30.2

- **Atomic scope**: `apps/api/modules/reports/pdf_routes.py` NEW + `apps/api/services/pdf_generator.py` NEW (weasyprint wrapper) + `apps/api/templates/monthly_summary.html` NEW (Jinja2 ko-KR) + `apps/api/services/chart_generator.py` NEW (matplotlib PNG) + `apps/web/components/reports/PdfExportTab.tsx` NEW + 1 pytest + 1 vitest + pyproject.toml `[STACK BUMP]` EXTENSION (weasyprint + matplotlib 결정 wire 보류).
- **Wire verification**: pytest PASS + vitest PASS + PDF preview rendering PASS.
- **Risk**: Medium — weasyprint system deps (libcairo, libpango) 결정 wire 보류. CI 환경 결정 wire 보류.

### 6.3 cj-282c (Sprint 3, P1 Email) — Story 30.3

- **Atomic scope**: `apps/api/modules/reports/email_routes.py` NEW + `apps/api/services/email_sender.py` NEW (smtplib wrapper + retry 3회) + `apps/web/components/reports/EmailSendDialog.tsx` NEW + 1 pytest + 1 vitest + apps/api/core/config.py EXTENSION (SMTP_HOST + SMTP_PORT + SMTP_USER + SMTP_PASSWORD + SMTP_FROM env vars).
- **Wire verification**: pytest PASS + vitest PASS + SMTP test server (aiosmtpd dev-only) integration test PASS.
- **Risk**: Medium — 외부 SMTP 인프라 결정 wire 보류. local dev = aiosmtpd fake server 결정 wire.

### 6.4 cj-282d (Sprint 4, P2 Scheduled) — Story 30.4

- **Atomic scope**: `apps/api/jobs/scheduled_reports.py` NEW (APScheduler) + `apps/api/main.py` EXTENSION (startup hook) + alembic migration NEW (`tenants.finance_contact_email VARCHAR(255) NULL`) + `apps/web/app/[locale]/(authenticated)/reports/scheduled/page.tsx` NEW + `apps/web/components/reports/ScheduledJobsList.tsx` NEW + 1 pytest + 1 vitest + pyproject.toml `[STACK BUMP]` EXTENSION (APScheduler 결정 wire 보류).
- **Wire verification**: pytest PASS + vitest PASS + alembic migration upgrade/downgrade round-trip PASS + APScheduler integration test PASS.
- **Risk**: Medium-High — finance_contact_email column 결정 wire 보류 + cron recovery 결정 wire 보류 + APScheduler vs Celery beat 결정 wire 보류.

---

## 7. Carry-over 정합

### 7.1 Epic 29+ 의 carry-over 보존

Epic 29+ spec implementation (Story 29.1~29.18) 은 cj-274 honestly DEFER → Epic 29+ ownership 이전 결정 wire + cj-275~278c P0/P1 dev_seed wire 결정 wire + cj-279 P2 service-only tenant wire 결정 wire + cj-280 Epic 29+ CLOSED retro 결정 wire + cj-281 Epic 29+ chain FINAL CLOSED 결정 wire (cj-style chain cj-229~281 정합 보존). Epic 30+ 은 Epic 29+ 의 spec implementation territory 와 **별개 territory** — Epic 29+ 본 wire (Story 29.1~29.18 본 구현) 은 별도 future chain (cj-29x-impl) 으로 보류 결정 wire.

### 7.2 Epic 30+ 의 Open Questions (OQ-EPIC30+)

본 Epic 30+ PRD entry 는 cj-style 결정 wire 진입 단계. 4 OQ 결정 보류 (cj-282a wire sprint 진입 시 결정 결정 wire):

- **OQ-EPIC30+-1**: weasyprint vs reportlab PDF library 결정 (cj-282b 진입 시 review)
- **OQ-EPIC30+-2**: SMTP 인프라 외부 의존 (SendGrid vs AWS SES vs on-prem Postfix) 결정 (cj-282c 진입 시 결정 wire)
- **OQ-EPIC30+-3**: APScheduler vs Celery beat vs cron 결정 (cj-282d 진입 시 결정 wire)
- **OQ-EPIC30+-4**: chart library (matplotlib vs Plotly vs Chart.js PNG export) 결정 (cj-282b 진입 시 결정 wire)

---

## 8. Next Steps (cj-style)

옵션 (a) **cj-282a wire sprint 진입 결정 wire** (cj-style 283번째 epic 연속 정직 회복) — Story 30.1 CSV export source+docs single sprint. option (b) **4 OQ 결정 wire 진입 후 cj-282a** — OQ-EPIC30+-1~4 결정 후 진입. option (c) **Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory)** — Epic 29+ Story 29.1~29.18 본 wire 진입 (Epic 30+ 보류).

**Recommended**: option (a) — cj-style discipline 회피 위험 방지 + Epic 30+ 의 lowest-risk story 먼저 진입 정합. 결정 wire 일자: 2026-09-05 (KST).

---

## 부록 A. Cross-references

- Master PRD: `_bmad-output/planning-artifacts/prd.md v7.0 (final, 2026-08-26)`
- Epic 30+ INDEX: (cj-282 entry sprint 결정 wire — 별도 파일 없음, 본 spec 이 INDEX 역할)
- Epic 30+ spec files (cj-282a wire 결정 시 작성): `apps/api/modules/reports/*.py` + `apps/web/components/reports/*.tsx`
- cj-style chain: cj-229 ~ cj-281 CLOSED ✅ HONEST
- Epic 29+ PRD: `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-09-05/prd.md`

## 부록 B. dev_seed EXTENSION 결정 wire (cj-282a 진입 시 보강)

Epic 30+ 의 dev_seed EXTENSION = `report_fixtures` scenario (cj-282a 진입 시 dev_seed.py 결정 wire):
- Scenario `report_fixtures`: 1 tenant (acme, Epic 29+ 의 DEV_TENANT_ID 재사용) + cost_records × 100 rows (period_key='2026-08') + BOM × 10 rows.
- Audit log: scenario invocation 자체 audit_logs 에 INSERT.
- Idempotency: ON CONFLICT (id) DO NOTHING (Epic 29+ cj-278b/c 패턴 verbatim 보존).
- D-REPORTS-EXTENSION ownership: Epic 30+ spec implementation owner (= Epic 30+ wire developer).
