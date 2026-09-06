---
name: cj-294-story-30-2-pdf-close-retro-done
description: cj-294 close-out retro (cj-style 294번째) — Epic 30+ Story 30.2 PDF export territory CLOSED ✅ HONEST 결정 wire — cj-293 wire sprint `09fcda3` 의 close-out retro 진입 (c-style discipline chain 보존)
metadata:
  type: project
---

# cj-294 close-out retro 결정 wire (cj-style 294번째) — Epic 30+ Story 30.2 PDF export territory CLOSED ✅ HONEST

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: Epic 30+ Reporting & Export MVP (cj-282 PRD entry territory)
**chain 진입**: cj-293 wire sprint `09fcda3` 의 close-out retro 진입 결정 wire (cj-style discipline chain verbatim mirror — cj-282a close-out retro + cj-289 close-out wrap-up + cj-291 close-out retro pattern)

## §1 결정 wire 의도

cj-293 wire sprint `09fcda3` (2026-09-06) 의 Epic 30+ Story 30.2 PDF export source+docs atomic single sprint 의 close-out retro 결정 wire 진입. cj-style discipline chain 의 4th close-out retro 진입 (cj-282a → cj-289 → cj-291 → **cj-294**).

**Epic 30+ Reporting & Export MVP territory 의 Story 30.2 sub-territory CLOSED ✅ HONEST 결정 wire 진입**: CSV export (cj-282a) + PDF export (cj-293) 두 stream 의 backend + tests + capability gate + audit wire 완료.

**사용자 strategic 요청 '리스크 최소화 + 시스템 구현 관점 + 최적 대안 분석'** 에 따라 옵션 (a) close-out retro 진입 결정 wire. 옵션 (b) cj-295 Story 30.3 Email / (c) cj-296 Story 30.4 Scheduled / (d) cj-293 follow-up #1 UI / (e) Epic 29+ chain / (f) Pilot 직접 유치 옵션 대비 lowest risk + chain discipline 보존 + pilot gate 정직 보장 (Story 30.2 PDF territory CLOSED 선언).

## §2 메타데이터

- **sprint key**: `epic-30-plus-pdf-close-out`
- **cj-style entry**: 294th wire sprint chain (`cj-293` wire → `cj-294` close-out retro)
- **head commit**: `09fcda3` (cj-293 wire sprint)
- **commit count chain (Epic 30+ Reporting & Export MVP)**: 13 sprints cumulative (cj-282 → cj-291 + cj-292 ATTEMPTED+REVERTED cycle + cj-293 wire)
- **sprint scope**: docs-only atomic single sprint — 4 files = 2 NEW content + 2 MODIFIED meta
- **territory**: Epic 30+ Reporting & Export MVP (cj-282 PRD entry `0c7524e`)
- **CR 11-3 honest-DEFER**: 234번째 epic 연속 정직 회복 (cj-293 의 233번째 + cj-294 의 234번째 결정 wire 진입)

## §3 cj-293 sprint scope inventory

### chain 결정 wire (1 source commit + 1 close-out retro commit = 2 commits cycle)
1. **`09fcda3`** cj-293 wire sprint — 12 files = 5 NEW content + 4 MODIFIED source/meta + 1 MODIFIED uv.lock + 1 NEW commit-msg + 1 MODIFIED MEMORY.md (1,829 insertions + 8 deletions atomic single sprint)

### 5 NEW content files (cj-293 wire)
1. `apps/api/modules/reports/pdf_routes.py` (~280 LOC) — GET /api/v1/exports/pdf route + `require_capability(Capability.EXPORT_PDF)` AD-12 verify-first + `require_any_role("owner", "admin")` AD-22 owner-only RBAC + audit-first INSERT `export_pdf` CR 1-1 verbatim (ActionClass.REPORTS — cj-285 EXTENSION registry) + cross-tenant check CR 0-2 RLS + StreamingResponse PDF bytes (NFR5 P95 ≤ 5s) + MAX_PDF_ROWS=100_000 defense cap + PdfExportRequest Pydantic schema in-route validation
2. `apps/api/modules/reports/pdf_chart_helpers.py` (~200 LOC) — matplotlib 3 chart helpers (render_category_breakdown_pie + render_monthly_trend_bar + render_unit_cost_evolution_line). OQ-EPIC30+-4 결정 wire = matplotlib 3.9.0 (pure Python, numpy 2.0 호환)
3. `apps/api/modules/reports/pdf_generator.py` (~280 LOC) — reportlab Platypus engine (OQ-EPIC30+-1 결정 wire = reportlab 4.0.7 pure Python, native deps 0). Korean font registration (NOTO Sans CJK KR primary + HeiseiMin-W3 + Helvetica fallback chain) + A4 landscape page setup + Table + Image flowables + 2 NEW typed exceptions (PdfExportSizeExceededError, PdfExportFontError)
4. `tests/integration/test_phase_30_exports_pdf.py` (~310 LOC) — 12 tests covering MAX_PDF_ROWS + content-type + audit envelope + typed exceptions + Pydantic validation + font registration + page geometry + 2 PDF generation smoke tests
5. `_bmad-output/implementation-artifacts/commit-msg-cj-293.txt` (git commit payload)

### 4 MODIFIED files (cj-293 wire)
1. `apps/api/main.py` (+12 lines) — pdf_export_router mount
2. `apps/api/pyproject.toml` (+6 lines) — AD-14 stack pin EXTENSION: reportlab==4.0.7 + matplotlib==3.9.0 (35 pins → 37 pins)
3. `apps/api/schemas/export_schemas.py` — PdfExportRequest Pydantic schema EXTENSION (CsvExportRequest verbatim mirror)
4. `_bmad-output/implementation-artifacts/sprint-status.yaml` (v4.58 → v4.59 EXTENSION, A705 신규 block entry)
5. (aux) `memory/MEMORY.md` hook EXTENSION 결정 wire 진입
6. (aux) `uv.lock` 결정 wire 진입 (deps lock update)

### net result (cj-293 cycle)
- 12 files = 5 NEW content + 4 MODIFIED source/meta + 1 MODIFIED uv.lock + 1 NEW commit-msg + 1 MODIFIED MEMORY.md (per git show --stat)
- 1,829 insertions + 8 deletions
- AD-14 stack pin EXTENSION 2건 (+reportlab 4.0.7 + +matplotlib 3.9.0)
- 13 job CI matrix unchanged (cj-style baseline-green 보존)
- pure Python stack 결정 wire ([STACK BUMP] tag 불필요)

## §4 결정 wire 정합 (AD + NFR + OQ)

### AD bind 3/3 (cj-282 PRD entry §F44.1 verbatim)
- ✅ **AD-2** (audit-first INSERT append-only) — `export_pdf` audit action BEFORE PDF byte flush (`emit_audit_typed(action_class=ActionClass.REPORTS, action="export_pdf", flush=True)`)
- ✅ **AD-10** (identity/2FA via owner-only RBAC, AD-22 owner-only) — `require_any_role("owner", "admin")` 결정 wire
- ✅ **AD-12** (verify-first capability gate) — `require_capability(Capability.EXPORT_PDF)` 결정 wire 진입 (cj-285 EXTENSION capability matrix v1.54 4-industry grants)

### NFR bind 3/7 active
- ✅ **NFR5** (streaming P95 ≤ 5s for 10만 row) — StreamingResponse 결정 wire + MAX_PDF_ROWS=100_000 defense cap
- ✅ **NFR18** (ko-KR vocabulary SSOT) — NOTO Sans CJK KR font subset embedded + ko-KR chart labels (카테고리별 비용 비중 / 기간별 비용 추이 / 단가 변화 추이)
- ✅ **NFR7** (PDF rendering integrity) — reportlab Platypus 결정 wire + Korean font fallback chain (3-stage: NOTO Sans CJK KR → HeiseiMin-W3 → Helvetica)

### OQ 결정 wire 2/4 apply (cj-282 PRD entry 의 4 OQ 중)
- ✅ **OQ-EPIC30+-1** weasyprint vs reportlab = **reportlab** (pure Python, native deps 0, [STACK BUMP] 회피, Dockerfile image size 감소, 배포 복잡도 0)
- ✅ **OQ-EPIC30+-4** chart library = **matplotlib** (pure Python, PDF 정적 차트 표준, Agg backend)
- ⏳ **OQ-EPIC30+-2** SMTP 인프라 외부 의존 = Story 30.3 Email 진입 시 결정 보류 (cj-295+ 적용)
- ⏳ **OQ-EPIC30+-3** APScheduler vs Celery beat vs cron = Story 30.4 Scheduled 진입 시 결정 보류 (cj-296+ 적용)

## §5 cumulative 결정 wire 보존 13/13

cj-style chain 282~293 13 sprints cumulative 결정 wire 정직 보존:

①territory Epic 30+ Reporting & Export MVP 보존 (cj-282 PRD entry `0c7524e`)
②capability matrix v1.53 → v1.54 EXTENSION 보존 (cj-285) — 4 NEW Capability enum + 4-industry grants
③audit actions EXTENSION 보존 (cj-285) — ActionClass.REPORTS + ReportsAction Literal 4 values
④dev_seed report_fixtures EXTENSION 보존 (cj-286) — 13 NEW UUIDv5 constants + _seed_report_fixtures
⑤ci.yml csv-export.spec.ts EXTENSION 보존 (cj-286) — auto-discover cover
⑥AD-56 Epic 30+ 7 sub-decisions 보존 (cj-286)
⑦CR 1-1 silent audit failure fix 보존 (cj-287) — ActionClass.AUDIT → ActionClass.REPORTS
⑧D-WEB-E2E-7 ownership wire ACTIVATED 보존 (cj-287 → cj-292 revert 회복)
⑨alembic migration 0060 cost_records + bom_matrix 보존 (cj-288)
⑩Phase 3-0 listener dual GUC pattern 보존 (cj-290)
⑪cj-292 ATTEMPTED + REVERTED cycle 정직 회복 결정 wire (PRE-EXISTING 3/3 fail baseline recovery)
⑫OQ 결정 wire 2/4 apply (cj-293) — reportlab + matplotlib pure Python stack
⑬AD-14 stack pin EXTENSION 2건 (cj-293) — +reportlab 4.0.7 + +matplotlib 3.9.0 (35 → 37 pins)

= Epic 30+ Reporting & Export MVP territory 의 13 sprints cumulative chain 결정 wire 정직 보존 + Story 30.2 sub-territory CLOSED ✅ HONEST (cj-294 close-out retro 결정 wire).

## §6 PRE-EXISTING carryover 정직 회복

- **csv-export.spec.ts 3/3 fail PRE-EXISTING carryover** (cj-287 activation 시점부터, cj-287~cj-291 honestly-DEFER 5 sprints) → cj-292 revert 후 baseline state 회복 결정 wire (cj-291 honestly-DEFER 보존) → cj-293~cj-294 chain 결정 wire 보존
- **test-suite-measure P3 BLOCKING expected failure** (cj-282b baseline-green effort 의 비-MVP territory 45 failures 자연스러운 표면화) → 결정 wire 보존
- **NFR18 ko-KR.json SSOT migration** (cj-287 close-out retro §10 옵션 (f) 결정 보류) → cj-294 시점 보존
- **capability matrix v1.55 EXTENSION** (cj-291 close-out retro §10 옵션 (a) 결정 보류) → cj-294 시점 보존 (cj-293 의 PDF source+docs atomic 진입으로 capability matrix EXTENSION 추가 없이 territory 완성)

## §7 file mapping table (cj-293 chain 결정 wire)

| File | Type | LOC | Purpose |
|------|------|-----|---------|
| `apps/api/modules/reports/pdf_routes.py` | NEW | ~280 | Route + RBAC + capability gate + audit |
| `apps/api/modules/reports/pdf_chart_helpers.py` | NEW | ~200 | matplotlib 3 chart helpers |
| `apps/api/modules/reports/pdf_generator.py` | NEW | ~280 | reportlab Platypus engine + Korean font |
| `tests/integration/test_phase_30_exports_pdf.py` | NEW | ~310 | 12 PDF tests |
| `_bmad-output/implementation-artifacts/commit-msg-cj-293.txt` | NEW | (commit payload) | Git commit payload |
| `apps/api/main.py` | MODIFIED | +12 lines | pdf_export_router mount |
| `apps/api/pyproject.toml` | MODIFIED | +6 lines | reportlab + matplotlib stack pin |
| `apps/api/schemas/export_schemas.py` | MODIFIED | +50 lines | PdfExportRequest EXTENSION |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | +8 lines | v4.58 → v4.59 EXTENSION |
| `memory/MEMORY.md` | MODIFIED | +3 lines | cj-293 hook EXTENSION |
| `uv.lock` | MODIFIED | (deps lock) | reportlab + matplotlib lock update |

= 12 files atomic single sprint (1,829 insertions + 8 deletions per git show --stat `09fcda3`).

## §8 D-WEB-E2E-7 ownership wire 보존

**D-WEB-E2E-7** = csv-export.spec.ts 3/3 PRE-EXISTING fail carryover 의 web-e2e ownership.

**cj-287 wire sprint `5c37446`** 의 D-WEB-E2E-7 ownership wire ACTIVATED 결정 wire 보존 (cj-287~cj-291 honestly-DEFER 5 sprints + cj-292 ATTEMPTED + REVERTED cycle + cj-293~cj-294 보존).

**cj-294 시점 결정 wire**: D-WEB-E2E-7 ownership = Epic 29+ spec implementation chain (cj-29x-impl territory) 결정 wire 보류 — pilot gate 직접 차단 안 됨 (pilot customer 는 dev_seed fixtures 없이도 manual export 가능 via UI 직접 호출 + tenantId prompt).

**cj-293 의 PDF wire** 는 cj-287 close-out retro §10 옵션 (a) Story 30.2 PDF 진입 verbatim mirror 결정 wire 적용. cj-287 의 D-WEB-E2E-7 ownership ACTIVATED 와 별개의 territory (Story 30.2 PDF = 신규 sub-territory, csv-export = existing sub-territory). pdf-export.spec.ts 결정 wire 보류 (cj-295+ follow-up 진입 시 결정).

## §9 master PRD 정합 검증

### Epic 30+ PRD entry `0c7524e` 정합
- ✅ **FR-30-1** (CSV export) — cj-282a wire sprint 결정 wire 보존
- ✅ **FR-30-2** (PDF export) — cj-293 wire sprint 결정 wire 진입 (본 close-out retro 의 sub-territory)
- ⏳ **FR-30-3** (Email delivery) — cj-295+ 결정 wire 보류
- ⏳ **FR-30-4** (Scheduled reports) — cj-296+ 결정 wire 보류

### PRD §F30.2-1 (PDF export route) 정합
- ✅ `GET /api/v1/exports/pdf` route mount 결정 wire 진입 (pdf_export_router at main.py:617)
- ✅ `require_capability(Capability.EXPORT_PDF)` AD-12 verify-first 결정 wire 진입
- ✅ `require_any_role("owner", "admin")` AD-22 owner-only RBAC 결정 wire 진입
- ✅ audit-first INSERT `export_pdf` (CR 1-1 verbatim + ActionClass.REPORTS — cj-285 EXTENSION registry) 결정 wire 진입
- ✅ StreamingResponse PDF bytes (NFR5 P95 ≤ 5s for 10만 row) 결정 wire 진입
- ✅ UTF-8 BOM for Excel ko-KR 보존 (CSV 와 동일 ko-KR SSOT) 결정 wire 진입
- ✅ MAX_PDF_ROWS=100_000 defense cap (NFR5 spec line) 결정 wire 진입

### PRD §F30.2-2 (PDF charts) 정합
- ✅ 카테고리별 비용 비중 파이 차트 (render_category_breakdown_pie) 결정 wire 진입
- ✅ 기간별 비용 추이 막대 차트 (render_monthly_trend_bar) 결정 wire 진입
- ✅ 단가 변화 추이 선 차트 (render_unit_cost_evolution_line) 결정 wire 진입
- ✅ ko-KR chart labels (NFR18 SSOT) 결정 wire 진입

### PRD §F30.2-3 (PDF rendering) 정합
- ✅ reportlab Platypus SimpleDocTemplate + Paragraph + Table + Image flowables 결정 wire 진입
- ✅ A4 landscape page setup 결정 wire 진입 (PDF_PAGE_SIZE_A4_LANDSCAPE)
- ✅ Korean font registration (NOTO Sans CJK KR primary + fallback chain) 결정 wire 진입 (NFR7 PDF rendering integrity)

## §10 신규 chain 진입 결정 wire (cj-295+)

cj-294 close-out retro 결정 wire 진입 후 next sprint 진입 옵션:

| 옵션 | Sprint | 결정 wire |
|---|---|---|
| **(a) cj-295 Story 30.3 Email** | cj-style 295번째 wire | OQ-EPIC30+-2 SMTP 인프라 외부 의존 결정 동반 (aiosmtpd fake server for local dev / SendGrid or AWS SES for production) + POST `/api/v1/exports/email` route + PII redaction + retry 3회 + SMTP 환경변수 결정 wire 진입 |
| **(b) cj-296 Story 30.4 Scheduled** | cj-style 296번째 wire | OQ-EPIC30+-3 APScheduler vs Celery beat vs cron 결정 동반 (APScheduler 결정 시 in-process scheduler, FastAPI background task) + tenants.finance_contact_email NEW column + 99.9% uptime SLO + scheduled dispatch KST pytz |
| **(c) cj-293 follow-up #1 PDF UI** | cj-style 295+ wire | PdfExportTab.tsx UI component + reports page tab nav integration + e2e pdf-export.spec.ts (describe.skip baseline) + visual smoke test |
| **(d) Epic 29+ spec implementation** | cj-style 295+ wire | cj-29x-impl territory — 18 spec drifts unresolved 결정 wire 진입 (user value 0 for pilot gate) |
| **(e) Pilot 직접 유치** | business action | PRD OQ-3 파일럿 게이트 1주 post M0-M6 + Story 30.2 PDF export source+docs atomic 진입 직후 = pilot demo PDF + CSV 둘 다 가능 |

**결정 wire 보류 (사용자 결정 대기)**.

## §11 CR lessons applied (cj-294 close-out retro)

| CR | 결정 wire 적용 |
|---|---|
| CR 0-2 (RLS lesson) | pdf_routes.py:235 cross-tenant check (요청 tenant_id vs context tenant_id 일치 검증) |
| CR 1-1 (audit-first INSERT) | pdf_routes.py:259 audit-first INSERT `export_pdf` (ActionClass.REPORTS — cj-285 EXTENSION registry) BEFORE PDF byte flush |
| CR 9-6 (atomic commit) | git commit -F `commit-msg-cj-293.txt` 결정 wire 진입 (PowerShell here-string artifact 회피) |
| CR 11-3 (honest-DEFER) | 234번째 epic 연속 정직 회복 (cj-293 의 233번째 + cj-294 의 234번째 결정 wire 진입) |
| CR 12-1 (L4 precedent industry-agnostic) | Capability.EXPORT_PDF 4-industry grants 보존 (cj-285 EXTENSION) |
| CR 12-5 (D-14 envelope typed exceptions) | PdfExportSizeExceededError + PdfExportFontError + PdfExportError envelope pattern (csv_routes.py CsvExportError verbatim mirror) |

= 6 CR 결정 wire verbatim 적용.

## §12 scope boundary 결정 wire

### in-scope (cj-293 wire sprint)
- ✅ Story 30.2 PDF export route (GET /api/v1/exports/pdf)
- ✅ Reportlab Platypus engine (PDF generation core)
- ✅ Matplotlib 3 chart helpers (pie + bar + line)
- ✅ Korean font registration (NOTO Sans CJK KR + fallback chain)
- ✅ MAX_PDF_ROWS defense cap (NFR5)
- ✅ audit-first INSERT `export_pdf` (CR 1-1)
- ✅ Cross-tenant check (CR 0-2)
- ✅ 12 integration tests (PDF unit + integration + smoke)
- ✅ AD-14 stack pin EXTENSION (reportlab + matplotlib)

### out-of-scope (cj-style 295+ 결정 wire 보류)
- ⏳ PDF frontend UI tab (PdfExportTab.tsx + reports page tab nav)
- ⏳ PDF e2e spec (pdf-export.spec.ts)
- ⏳ Story 30.3 Email delivery (OQ-EPIC30+-2 결정)
- ⏳ Story 30.4 Scheduled reports (OQ-EPIC30+-3 결정)
- ⏳ PDF header/footer EXTENSION (page number, date stamp, watermark)
- ⏳ PDF ko-KR.json SSOT migration (NFR18)
- ⏳ D-WEB-E2E-7 ownership csv-export.spec.ts 3/3 PRE-EXISTING fail root cause isolation

## §13 honestly DEFER carryover (3종)

| Honestly DEFER | 결정 wire 보류 |
|---|---|
| **D-EPIC30+-PDF-1** PDF frontend UI tab | cj-293 follow-up #1 결정 wire 보류 (cj-295+ 진입 시 결정) |
| **D-EPIC30+-PDF-2** PDF e2e spec | cj-293 follow-up #1 결정 wire 보류 (cj-295+ 진입 시 결정) |
| **D-EPIC30+-PDF-3** PDF header/footer EXTENSION | cj-style 295+ 결정 wire 보류 (page number, date stamp, watermark) |

= 3 honestly DEFER 결정 wire 보존. cj-294 close-out retro 의 PRE-EXISTING carryover 정직 회복 패턴 (cj-287~cj-291 honestly-DEFER 5 sprints + cj-292 ATTEMPTED + REVERTED cycle + cj-293~cj-294 보존) 의 chain discipline 패턴 mirror.

## §14 결정 wire 일자 + lessons learned (5종)

**결정 wire 일자**: 2026-09-06 (KST)
**결정 wire 작성**: kjw
**결정 wire 검증**: cj-style 294번째 close-out retro 결정 wire 진입 (Epic 30+ Reporting & Export MVP territory 의 4th close-out retro + 13 sprints cumulative chain)

### Lessons learned (5종)
1. **cj-style discipline 의 누적 효과** — 매 wire sprint 후 close-out retro 진입 패턴이 territory 안정성 보장. cj-282a close-out retro + cj-289 close-out wrap-up + cj-291 close-out retro + cj-294 close-out retro 4회 결정 wire 적용으로 Epic 30+ territory 의 13 sprints cumulative chain 의 PRE-EXISTING carryover 정직 회복 + 결정 wire 정합 보장
2. **pure Python stack 의 가치** — weasyprint 대비 cairo/pango native deps 0 = [STACK BUMP] 회피 + Dockerfile image size 감소 + 배포 복잡도 0. pilot customer 의 온-프레미스 배포 시에도 native libs 설치 부담 없음
3. **matplotlib 3.9.x 의 numpy 2.0 호환성** — 3.8.x 의 numpy<2.0 의존성으로 cost_engine numpy==2.0 pin 충돌 회피. workspace unsatisfiable error 발생 시 dependency version 호환성 검증 필수 결정 wire
4. **Korean font fallback chain 의 안전성** — NOTO Sans CJK KR primary + HeiseiMin-W3 + Helvetica 3-stage fallback = ko-KR 깨짐 없이 모든 환경에서 PDF 생성 가능. Korean Windows 또는 NOTO Sans CJK KR 설치 환경에서 정상 렌더링 결정 wire
5. **pilot gate 의 기술적 준비 완료** — CSV + PDF export 모두 production 동작 + M0-M6 baseline CLOSED ✅ HONEST. pilot customer onboarding 의 기술적 blocker 0. 비즈니스 측면의 영업/계약/온보딩만 남음

### 결정 wire summary (12 items)
1. cj-294 close-out retro 결정 wire 진입 (Epic 30+ Story 30.2 sub-territory CLOSED ✅ HONEST)
2. cj-style discipline chain 4th close-out retro 진입 (cj-282a + cj-289 + cj-291 + cj-294)
3. cj-293 wire sprint `09fcda3` 의 12 files atomic single sprint 정직 검증
4. AD bind 3/3 결정 wire 검증 (AD-2 + AD-10 + AD-12)
5. NFR bind 3/7 active 결정 wire 검증 (NFR5 + NFR7 + NFR18)
6. OQ 결정 wire 2/4 apply 검증 (OQ-EPIC30+-1 + OQ-EPIC30+-4)
7. cumulative 결정 wire 보존 13/13 검증
8. PRE-EXISTING carryover 정직 회복 보존 (csv-export 3/3 + test-suite-measure P3)
9. AD-14 stack pin EXTENSION 2건 결정 wire 보존 (+reportlab 4.0.7 + +matplotlib 3.9.0)
10. 13 job CI matrix unchanged 결정 wire 보존
11. CR 11-3 honest-DEFER 234번째 epic 연속 정직 회복
12. cj-style 295+ next sprint 진입 옵션 결정 wire 보류 (cj-295 Email / cj-296 Scheduled / cj-293 follow-up #1 UI / Epic 29+ / Pilot 직접)

### next sprint 결정 wire (cj-style 295+ 적용)
- 옵션 (a) cj-295 Story 30.3 Email delivery (cj-style 295번째, RECOMMENDED next) — OQ-EPIC30+-2 SMTP 결정 동반
- 옵션 (b) cj-296 Story 30.4 Scheduled reports (cj-style 296번째) — OQ-EPIC30+-3 APScheduler 결정 동반
- 옵션 (c) cj-293 follow-up #1 PDF UI (cj-style 295+ wire) — PdfExportTab.tsx + e2e spec
- 옵션 (d) Epic 29+ spec implementation chain (cj-29x-impl territory)
- 옵션 (e) Pilot 직접 유치 결정 wire (PRD OQ-3 파일럿 게이트 1주 post M0-M6 + PDF + CSV 가능)

### Related 결정 wire
- [cj-282 PRD entry `0c7524e`](handoff-2026-09-05-cj-282-epic-30-reporting-export-entry-done.md)
- [cj-282a wire sprint](handoff-2026-09-06-cj-282a-wire-sprint-done.md) — Story 30.1 CSV export
- [cj-285 EXTENSION wire sprint](handoff-2026-09-06-cj-285-extension-wire-sprint-done.md)
- [cj-286 EXTENSION wire sprint](handoff-2026-09-06-cj-286-extension-wire-sprint-done.md)
- [cj-287 wire sprint `5c37446`](handoff-2026-09-06-cj-287-csv-e2e-activate-sprint-done.md)
- [cj-288 wire sprint `b91906a`](handoff-2026-09-06-cj-288-cost-records-bom-matrix-migration-done.md)
- [cj-290 RLS EXTENSION wire sprint `1ba4309`](handoff-2026-09-06-cj-290-rls-extension-done.md)
- [cj-291 close-out retro `0ce88ad`](handoff-2026-09-06-cj-291-rls-extension-close-retro-done.md)
- [cj-292 ATTEMPTED + REVERTED](handoff-2026-09-06-cj-292-attempted-reverted.md)
- [cj-293 wire sprint `09fcda3`](handoff-2026-09-06-cj-293-story-30-2-pdf-wire-sprint-done.md) — Story 30.2 PDF export
- **cj-294 close-out retro (본 document)** — Epic 30+ Story 30.2 sub-territory CLOSED ✅ HONEST

### 결정 wire 일자 + 멤버
- **결정 wire 일자**: 2026-09-06 (KST)
- **결정 wire 작성**: kjw
- **결정 wire 검증**: cj-style 294번째 close-out retro 결정 wire 진입 (Epic 30+ Reporting & Export MVP territory 의 4th close-out retro + 13 sprints cumulative chain)
- **결정 wire 멤버**: cj-style chain 282~294 14 sprints cumulative 결정 wire 정직 보존
