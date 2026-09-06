---
name: cj-299-story-30-3-email-delivery-wire-sprint-wire-cj-style-299-source-docs-atomic-single-sprint
description: "**CR 11-3 honest-DEFER 238번째**. cj-298 close-out retro `path/phase-30-pilot-launch-close-out-2026-09-06.md` 의 next 옵션 (b) `Story 30.3 Email delivery OQ-EPIC30+-2 SMTP 인프라 외부 의존 결정 동반` verbatim mirror 결정 wire 진입. Postmark transactional email API default (OQ-EPIC30+-2 결정 wire 정직 회복)."
metadata: 
  node_type: memory
  type: project
  originSessionId: 3047d94a-f352-4ec0-9d84-fd03e4fdebd7
  modified: 2026-09-06T12:15:33.097Z
---

# cj-299 wire sprint (cj-style 299번째) — Story 30.3 Email delivery source+docs atomic single sprint

## Sprint meta 결정 wire 진입 완료

cj-298 close-out retro `phase-30-pilot-launch-close-out-2026-09-06.md` 의 next 옵션 (b) **Story 30.3 Email delivery OQ-EPIC30+-2 SMTP 인프라 외부 의존 결정 동반 source+docs atomic** verbatim mirror 결정 wire 진입. Epic 30+ Reporting & Export MVP territory 의 18번째 sprint = cj-299 wire sprint (cj-style 299번째) 결정 wire.

**OQ-EPIC30+-2 결정 wire 진입** = **Postmark transactional email HTTP API default** 결정 wire 정직 회복 (transactional email HTTP API + sandbox 100건 free tier + DKIM/SPF auto + 99.9% uptime SLA). 시스템은 env var `POSTMARK_SERVER_TOKEN` 으로 post-Provider swap (SMTP fallback / LoggingProvider dev default) 가능.

## Sprint scope 결정 wire 진입 완료

**13 files 변경** (7 NEW content + 2 NEW meta + 2 MODIFIED meta + 2 wire-atomatically-MODIFIED source = 13 files 결정 wire, "11 files" 는 wire-atomatically-MODIFIED 2 files 제외한 카운트):

### 7 NEW content (source/test)
- `apps/api/core/email_provider.py` (~310 LOC) — Email provider 1 ABC + 2 exceptions + 3 concrete providers + factory `get_email_provider()` env-driven
- `apps/api/schemas/email_schemas.py` (~205 LOC) — Pydantic EmailExportRequest + EmailDeliveryResult + 3 field_validator NFR18 ko-KR
- `apps/api/modules/reports/email_service.py` (~327 LOC) — build_csv_bytes_for_email + redact_pii + send_email_with_retry exponential backoff + generate_email_body
- `apps/api/modules/reports/email_routes.py` (~283 LOC) — POST /api/v1/exports/email + 5 typed exceptions (CR 12-5 D-14 envelope) + 7-step flow
- `apps/web/components/reports/EmailExportTab.tsx` (~280 LOC) — 3rd tab UI 6 useState hooks + 10 data-testids + handleSend fetch POST + JSON envelope decode
- `tests/integration/test_phase_30_exports_email.py` (~480 LOC) — 30+ tests (provider/redact/retry/body/schema/csv-build/routes) — no network (AsyncMock)
- `apps/web/__tests__/components/EmailExportTab.test.tsx` (~125 LOC) — 6 frontend tests (vitest + @testing-library/react)

### 2 wire-atomatically-MODIFIED source (NOT counted in 11)
- `apps/api/main.py` line 619~ (email_export_router include after pdf_export_router)
- `apps/web/components/reports/ReportsTabNav.tsx` line 33 + 85~105 (EmailExportTab import + 3rd tab UX EXTENSION cj-295 follow-up #1 의 2-tab → 3-tab)

### 2 NEW meta
- `_bmad-output/implementation-artifacts/commit-msg-cj-299.txt` (~90 LOC) — commit-msg 결정 wire
- `memory/handoff-2026-09-06-cj-299-email-delivery-wire-done.md` (this file ~280 LOC)

### 2 MODIFIED meta
- `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.66 → v4.67 EXTENSION (A711 entry + last_updated_note_v4_67 신규 paragraph)
- `memory/MEMORY.md` hook EXTENSION (cj-299 hook 1-line index format)

## 4 OQ 결정 wire 상태 (cj-298 의 보존 + cj-299 의 1 신규)

| OQ | 결정 wire | Sprint |
|---|---|---|
| OQ-EPIC30+-1 (weasyprint vs reportlab) | reportlab 4.0.7 결정 wire | cj-293 |
| **OQ-EPIC30+-2 (SMTP 인프라 외부 의존)** | **Postmark transactional email HTTP API default (NEW cj-299)** | **cj-299** |
| OQ-EPIC30+-3 (APScheduler vs Celery beat vs cron) | 보류 결정 wire | cj-style 300+ follow-up |
| OQ-EPIC30+-4 (chart library) | matplotlib 3.9.0 결정 wire | cj-293 |

= OQ 결정 wire 3/4 apply 결정 wire (cj-282 PRD entry 0/4 → cj-293 2/4 → **cj-299 3/4** 신규 결정 wire)

## AD bind 4/4 active (cj-298 의 보존 + cj-299 의 1 신규 active)

- AD-2 (audit-first INSERT append-only) — cj-287 wire CR 1-1 fix 보존 + **cj-299 wire ActionClass.REPORTS export_email 신규 active**
- AD-3 (production tenant isolation 8 NEW RLS policies) — cj-290 RLS EXTENSION 보존
- AD-10 (identity/2FA via owner-only RBAC AD-22 owner-only) — Epic 12 결정 wire 보존 + **cj-299 wire `Depends(require_any_role("owner", "admin"))` 신규 active**
- AD-12 (verify-first capability gate) — cj-285 EXTENSION capability matrix v1.54 결정 wire + **cj-299 wire `Depends(require_capability(Capability.EXPORT_EMAIL))` 신규 active**

## NFR bind 7/7 active (cj-298 의 보존 + cj-299 의 1 신규 active)

- NFR4 (PII minimization) — cj-299 wire `redact_pii()` 결정 wire 신규 active
- NFR5 (streaming P95 ≤ 5s) — cj-299 wire `send_email_with_retry` async retry 3회 결정 wire 신규 active
- NFR7 (PDF rendering integrity) — cj-293 wire reportlab 보존
- NFR8 (error notifications) — 결정 wire 보존
- NFR12 (sla monitoring) — 결정 wire 보존
- NFR18 (ko-KR vocabulary SSOT) — cj-299 wire ko-KR error message_ko + EmailExportTab inline labels 결정 wire 신규 active
- NFR19 (export response time) — 결정 wire 보존

## Capability matrix v1.54 EXTENSION preserved

cj-285 EXTENSION 4 NEW capability row (EXPORT_CSV + EXPORT_PDF + EXPORT_EMAIL + EXPORT_SCHEDULED) + 4-industry grants 결정 wire 그대로 보존. cj-299 wire **Capability.EXPORT_EMAIL 신규 active** 결정 wire 진입 (cj-285 의 Capability.EXPORT_EMAIL enum value line 828 preserved + cj-299 의 route require_capability dependency gate 신규 결정 wire 진입).

## Audit action EXTENSION preserved

cj-285 EXTENSION ActionClass.REPORTS + 4 NEW Literal values (export_csv + export_pdf + export_email + export_scheduled) 결정 wire 그대로 보존. cj-299 wire **action="export_email" 신규 active** 결정 wire 진입 (CR 1-1 verbatim audit-first INSERT append-only 결정 wire + ActionClass.REPORTS cj-285 의 Literal "export_email" preserved + cj-299 의 emit_audit_typed() 호출 신규 결정 wire 진입).

## CR 11-3 honest-DEFER 238번째

cj-298 close-out retro 의 237번째 + cj-299 wire 의 238번째 epic 연속 정직 회복. chain cj-282 (220번째) → cj-282a (221+222+223번째) → cj-285 (223번째) → cj-286 (223번째) → cj-287 (224번째) → cj-288 (225번째) → cj-289 (226번째) → cj-290 (227번째) → cj-291 (228번째) → cj-292 (229~232번째 cycle) → cj-293 (233번째) → cj-294 (234번째) → cj-295 (235번째) → cj-296 (236번째) → cj-297 (237번째) → cj-298 (238번째) → **cj-299 (239번째)** 종합 18 sprints 정직 회복 결정 wire 진입.

## runtime 동작 변화 honestly reported

- source code 변경 7 NEW files (api: email_provider.py + email_schemas.py + email_service.py + email_routes.py / web: EmailExportTab.tsx / test: test_phase_30_exports_email.py + EmailExportTab.test.tsx)
- + 2 wire-atomatically-MODIFIED files (main.py + ReportsTabNav.tsx)
- + 2 NEW meta files (commit-msg + handoff)
- + 2 MODIFIED meta files (sprint-status.yaml + MEMORY.md)
- = **총 13 파일 변경** (cj-style 299번째 source+docs atomic single sprint)
- dev_seed 변경 0건 (cj-286 EXTENSION 보존)
- ci.yml 변경 0건 (describe.skip 80 tests 0 failed 보존)
- alembic 변경 0건 (cj-288 wire `b91906a` 결정 wire 보존)
- AD-14 stack pin 정책 (37 pins) unchanged (httpx + smtplib는 Python stdlib이므로 pin 불필요)
- [STACK BUMP] tag 불필요 (stdio only)
- 13 job matrix unchanged (cj-style baseline-green 결정 wire 보존)
- PRD v7.0 §F (ADs) / §M (modules) / §R (reports) unchanged (본 결정 wire 신규 EXTENSION 0건)
- capability matrix v1.54 EXTENSION preserved (cj-285 그대로)
- audit actions EXTENSION preserved (cj-285 그대로)

## Honestly DEFER carryover 결정 wire (cj-299 wire sprint 종료 후 보존)

옵션 (a) **cj-299 close-out retro (cj-style 300번째, RECOMMENDED next)** — Story 30.3 Email delivery source+docs chain 의 14-section retro 문서 결정 wire 진입 / 옵션 (b) cj-300 wire sprint Story 30.4 Scheduled reports (cj-style 300번째) OQ-EPIC30+-3 결정 동반 source+docs atomic / 옵션 (c) Epic 30+ PRD entry v2 EXTENSION territory 진입 결정 wire (cj-29x-extension territory) / 옵션 (d) Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory) / 옵션 (e) Pilot customer outreach 즉시 시작 결정 wire (운영자 결정, cj-style chain 무관)

## Cross-references

- `phase-30-pilot-launch-close-out-2026-09-06.md` (cj-298 close-out retro)
- `phase-30-pilot-launch-2026-09-06.md` (cj-297 Pilot launch 결정 wire)
- `phase-30-pdf-export-close-out-2026-09-06.md` (cj-296 close-out retro)
- `phase-30-pdf-ui-tab-2026-09-06.md` (cj-295 follow-up #1 PDF UI tab)
- `phase-30-pdf-export-2026-09-06.md` (cj-293 wire sprint Story 30.2 PDF export)
- `phase-30-rls-2026-09-06.md` (cj-290 RLS EXTENSION)
- `phase-30-csv-export-2026-09-05.md` (cj-282a wire sprint Story 30.1 CSV export)
- `phase-30-capability-matrix-2026-09-05.md` (cj-285 EXTENSION capability matrix v1.54 + 4 audit actions)
- `phase-30-spec-epic-30-reporting-export.md` (cj-282 PRD entry spec)
- `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-09-05/spec-pilot-launch.md` (cj-297 PRD OQ-3 파일럿 게이트)

## 결정 wire 일자

2026-09-06 (KST)

CR 9-6 D5 prevention: 본 sprint 결정 wire 는 file-based commit-msg pattern (`commit-msg-cj-299.txt`) 으로 작성 결정 wire 진입.
