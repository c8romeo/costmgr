---
title: "cj-282 Epic 30+ Reporting & Export MVP PRD entry sprint ✅ DONE 결정 wire (cj-style 282번째 epic 연속 정직 회복)"
sprint_id: "cj-282"
date: "2026-09-05"
type: "epic-prd-entry"
carry_over: "cj-style chain cj-229~281 CLOSED ✅ HONEST (cj-281 결정 wire). Epic 29+ chain cj-274~281 CLOSED ✅ HONEST."
stakeholders: "kjw (PM/lead) + Amelia (platform engineer)"
---

# cj-282 Epic 30+ Reporting & Export MVP PRD entry sprint ✅ DONE 결정 wire

## 0. Sprint Identity

- **cj-style index**: cj-style 282번째 epic 연속 정직 회복 진입점 (option (γ) 신규 territory)
- **Date**: 2026-09-05 (KST)
- **Mode**: docs-only atomic single sprint (entry plan)
- **Carry-over**: cj-281 Epic 29+ chain FINAL CLOSED 결정 wire (1cf55ac) 의 'Epic 30+ entry 결정 wire' verbatim follow-up

## 1. Territory 결정 wire

### 1.1 3 옵션 분석

| 옵션 | User-facing value | Risk | Atomic? | Verdict |
|---|---|---|---|---|
| **(α) D-WEB-E2E-5 carryover** (3 specs verification only) | ❌ 0 (verification only) | ✅ Low | ✅ Yes | ⚠️ user-facing value 0 |
| **(β) Epic 29+ 18 spec UI 구현** | ✅✅✅ Max | ❌❌❌ **HUGE** (12 spec drifts + 18 stories × multi-sprint + web-e2e CI 38~42분/run fail) | ❌ No | ❌ atomic 원칙 위반 |
| **(γ) 신규 territory** | ✅✅ New value | ✅ Low~Medium | ✅ Yes | ✅ **SELECTED** |

### 1.2 결정 wire

**option (γ) Reporting & Export MVP** 선택.

**Rationale 5종**:

1. **cj-281 Epic 29+ chain FINAL CLOSED 직후 첫 NEW territory 진입 결정 wire** = chain CLOSED ✅ HONEST 의 자연스러운 후속 = 신규 territory 진입.
2. **option (γ) 신규 territory 선택** = (α) D-WEB-E2E-5 carryover = verification only (user-facing value 0) + (β) Epic 29+ 18 spec UI 구현 = 12 spec drifts unresolved + 18 stories × multi-sprint + web-e2e CI 38~42분/run fail + atomic 원칙 위반 = risk 🚨🚨🚨 → **option (γ) Reporting & Export MVP 선택** = greenfield + spec drift 0 + atomic 4-story 분할 가능 + Epic 29+ 의존 0 (기존 cost_records/BOM/tenant 모델 그대로 활용).
3. **B2B SaaS 재무팀 #1 요청 기능 = export to Excel** = 업계 표준, ROI 즉시, customer-facing 가치 즉시 전달 (회계감사용 자료 준비 8h → 0.5h 단축).
4. **cj-style atomic 4-sprint 분할 결정 wire** = cj-282a (Story 30.1 CSV P0) / cj-282b (Story 30.2 PDF P1) / cj-282c (Story 30.3 Email P1) / cj-282d (Story 30.4 Scheduled P2) = 1 sprint = 1 atomic deliverable 원칙 verbatim.
5. **master PRD §M capability matrix v1.47 → v1.48 EXTENSION** = 4 NEW capability row (EXPORT_CSV / EXPORT_PDF / EXPORT_EMAIL / EXPORT_SCHEDULED) 결정 wire (Epic 29+ 의 NEW capability 0 과 명확히 구분).

## 2. Epic 30+ Scope 결정 wire

### 2.1 한 문장 정의

> **"회계감사용 CSV/Excel export + 월간 보고서 PDF 자동 생성 + 이메일 발송 + 스케줄링 = costmgr 운영자가 매월 말 회계감사 자료 준비 시간을 8h → 0.5h로 단축하는 자동 export pipeline"**

### 2.2 4 stories 분할 (cj-style atomic 4-sprint 분할)

| Story | FR | Endpoint | Capability Row | Wire Sprint | Risk |
|---|---|---|---|---|---|
| **30.1** CSV export | FR-30-1 | GET `/api/v1/exports/csv` | EXPORT_CSV | **cj-282a P0** | ✅ Lowest (stdlib csv + StreamingResponse + UTF-8 BOM for Excel) |
| **30.2** PDF export | FR-30-2 | GET `/api/v1/exports/pdf` | EXPORT_PDF | cj-282b P1 | ⚠️ Medium (weasyprint + Jinja2 + matplotlib embed 3 charts) |
| **30.3** Email delivery | FR-30-3 | POST `/api/v1/exports/email` | EXPORT_EMAIL | cj-282c P1 | ⚠️ Medium (SMTP 인프라 외부 의존 + retry 3회 + PII redaction) |
| **30.4** Scheduled reports | FR-30-4 | GET `/api/v1/exports/scheduled` + APScheduler | EXPORT_SCHEDULED | cj-282d P2 | ⚠️ Medium-High (cron + recovery + `tenants.finance_contact_email` NEW column) |

### 2.3 AD/NFR Bind

- **AD bind**: AD-2 (append-only audit-first, 4 stories) + AD-10 (identity + 2FA, 30.3) + AD-12 (verify-first capability gate, 4 stories) = 3 master ADs
- **NFR bind**: NFR4 (background job SLA, 30.4) + NFR5 (page load P95 ≤ 5s, 30.1) + NFR7 (retry fail-safe, 30.3) + NFR8 (99.9% uptime, 30.4) + NFR12 (PDF page count ≤ 10, 30.2) + NFR18 (ko-KR vocabulary, 30.1+30.2) + NFR19 (PII redaction, 30.3) = 7 master NFRs

## 3. 산출물 결정 wire 진입 완료

| File | Type | LOC | Purpose |
|---|---|---|---|
| `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-09-05/spec-epic-30-reporting-export.md` | NEW | ~340 | PRD + 4 FRs + capability matrix EXTENSION + AD/NFR bind + wire sprint 분할 + 4 OQ + 부록 A/B |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | +1 entry + 1 note | A692 신규 entry + last_updated_note_v4_24 신규 (v4.23 → v4.24 EXTENSION) |
| `memory/handoff-2026-09-05-cj-282-epic-30-reporting-export-entry-done.md` | NEW | (this file) | handoff 결정 wire |
| `memory/MEMORY.md` | MODIFIED | +1 line | cj-282 hook EXTENSION |

**Total: 4 files = 2 NEW + 2 MODIFIED atomic single sprint 결정 wire 진입 완료**.

## 4. 4 OQ 결정 보류

본 Epic 30+ PRD entry 는 cj-style 결정 wire 진입 단계. 4 OQ 결정 보류 (cj-282a wire sprint 진입 시 결정 결정 wire):

- **OQ-EPIC30+-1**: weasyprint vs reportlab PDF library 결정 (cj-282b 진입 시 review)
- **OQ-EPIC30+-2**: SMTP 인프라 외부 의존 (SendGrid vs AWS SES vs on-prem Postfix) 결정 (cj-282c 진입 시 결정 wire)
- **OQ-EPIC30+-3**: APScheduler vs Celery beat vs cron 결정 (cj-282d 진입 시 결정 wire)
- **OQ-EPIC30+-4**: chart library (matplotlib vs Plotly vs Chart.js PNG export) 결정 (cj-282b 진입 시 결정 wire)

## 5. 검증 실측 (cj-282 docs-only atomic sprint)

- **T7.1 sprint-status v4.24 EXTENSION PASS** — A692 entry + last_updated_note_v4_24 신규 진입 완료 (6107 → 6109 lines, 1 entry + 1 note EXTENSION 결정)
- **T7.2 spec file structure PASS** — frontmatter (8 keys: title/status/created/finalized_by/finalized_at/rubric_verdict/polish_pass/parent_prd/epic/entry_mode/carries/stakes/working_mode/form_factor/stakeholders) + 8 sections (Purpose/Vision/Target User/Glossary/Features/Architecture Bind/Wire Sprint 분할/Carry-over 정합) + 2 부록 (Cross-references/dev_seed EXTENSION) 결정 wire
- **T7.3 MEMORY.md hook PASS** — cj-282 index line EXTENSION 결정 wire
- **T7.4 FR coverage 4/4 (100%)** — FR-30-1, FR-30-2, FR-30-3, FR-30-4 결정 wire
- **T7.5 AD bind coverage 3/25** — AD-2 + AD-10 + AD-12 결정 wire
- **T7.6 NFR bind coverage 7/20** — NFR4 + NFR5 + NFR7 + NFR8 + NFR12 + NFR18 + NFR19 결정 wire
- **T7.7 Capability matrix EXTENSION 4 NEW rows** — EXPORT_CSV / EXPORT_PDF / EXPORT_EMAIL / EXPORT_SCHEDULED 결정 wire
- **T7.8 FINAL CLEAN PASS** — 결정 wire 진입 단계 정리 완료

## 6. runtime 동작 변화 honestly reported

- **runtime source code 변경 0건** (docs-only atomic sprint)
- **AD-14 stack pin 정책 (35 pins) 변경 없음** — 결정 wire 진입 단계
- **[STACK BUMP] tag 불필요** — 결정 wire 진입 단계
- **capability matrix v1.47 → v1.48 EXTENSION 결정 wire** — 본 entry sprint 에서는 EXTENSION 결정만, 실제 cj-282a wire sprint 진입 시 적용
- **Epic 29+ spec implementation = 별도 future chain (cj-29x-impl territory, 보류 결정 wire)** — Epic 30+ 와 명확한 territory 분리

## 7. carry-over 정합

- cj-style chain cj-229~281 CLOSED ✅ HONEST (cj-281 결정 wire)
- Epic 29+ chain cj-274~281 CLOSED ✅ HONEST (cj-281 결정 wire)
- Epic 29+ spec implementation = 보류 (cj-29x-impl territory)
- Epic 30+ entry = cj-282 진입 완료
- Epic 30+ wire sprints = cj-282a~d 진입 대기

## 8. Next Steps (cj-style options)

**옵션 (a) cj-282a wire sprint 진입 결정 wire (cj-style 283번째, RECOMMENDED)**
- Story 30.1 CSV export source+docs single sprint
- 산출물: 7 files atomic (apps/api/modules/reports/csv_routes.py NEW + apps/api/schemas/export_schemas.py NEW + apps/web/app/[locale]/(authenticated)/reports/page.tsx NEW + apps/web/components/reports/CsvExportTab.tsx NEW + audit log INSERT helper + 1 pytest + 1 vitest)
- Risk: Lowest (all stdlib, no new infra)
- 권장: cj-style discipline 회피 위험 방지 + Epic 30+ 의 lowest-risk story 먼저 진입 정합

**옵션 (b) 4 OQ 결정 wire 진입 후 cj-282a**
- OQ-EPIC30+-1~4 결정 후 진입 (cj-282b/c/d OQ 선결정)

**옵션 (c) Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory)**
- Epic 29+ Story 29.1~29.18 본 wire 진입 (Epic 30+ 보류)
- 비권장: Epic 30+ 진입 결정 wire 보존 + 4 OQ 결정 보류로 wire 진입 가능 상태

## 9. 결정 wire 일자

2026-09-05 (KST)

**CR 11-3 honest-DEFER 220번째** (cj-281 의 219번째 + cj-282 의 220번째) epic 연속 정직 회복.
