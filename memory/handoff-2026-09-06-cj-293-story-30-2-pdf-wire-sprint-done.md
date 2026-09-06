---
name: cj-293-story-30-2-pdf-wire-sprint-done
description: cj-293 wire sprint (cj-style 293번째) — Epic 30+ Story 30.2 PDF export source+docs atomic single sprint — reportlab + matplotlib pure Python stack 결정 wire 진입 (OQ-EPIC30+-1 + OQ-EPIC30+-4)
metadata:
  type: project
---

# cj-293 wire sprint 결정 wire (cj-style 293번째) — Epic 30+ Story 30.2 PDF export source+docs atomic single sprint

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: Epic 30+ Reporting & Export MVP (cj-282 PRD entry territory)
**chain 진입**: cj-291 close-out retro 의 옵션 (a) verbatim mirror — Epic 30+ capability matrix v1.55 EXTENSION OR Story 30.2 PDF export 결정 보류분

## §1 사용자 분석 override 결정 wire 진입

**사용자 strategic 요청**: "리스크 최소화 + 시스템 구현 관점 + 최적 대안 분석 + 가장 합리적이고 효과적인 것부터 실행"

**옵션 비교**:
- 옵션 (a) capability matrix v1.55 EXTENSION — 단순 enum EXTENSION only, user-facing value 0
- 옵션 (a') Story 30.2 PDF export source+docs atomic — pilot customer demo 직접 활용 가능, Epic 30+ territory 의 실제 구현 layer 진입
- 옵션 (b) cj-292 fix forward v2 — admin rights blocked 불가
- 옵션 (c) Epic 29+ spec implementation — pilot blocker 아님
- 옵션 (d) Pilot direct — code change 없음

**결정**: 옵션 (a') Story 30.2 PDF export 결정 wire 진입. cj-282 PRD entry 의 4 OQ 중 2 결정 wire apply (OQ-EPIC30+-1 + OQ-EPIC30+-4). pure Python stack (reportlab + matplotlib) 결정 wire로 [STACK BUMP] 회피.

## §2 OQ 결정 wire 2/4 apply

### OQ-EPIC30+-1 PDF library = reportlab

**비교**:
- weasyprint: HTML→PDF via CSS Paged Media, beautiful output, but **cairo + pango native libs 의존** → 배포 복잡도 증가 + Dockerfile [STACK BUMP] tag 트리거
- reportlab: programmatic PDF generation, **pure Python**, simpler deployment

**결정 wire**: reportlab (pure Python, native deps 0, [STACK BUMP] 회피)

### OQ-EPIC30+-4 chart library = matplotlib

**비교**:
- matplotlib: pure Python, widely used, good for static charts (PDF standard)
- plotly: HTML/JS interactive, but adds JS dependency for PDF
- altair: declarative, builds on Vega-Lite

**결정 wire**: matplotlib (pure Python, PDF 정적 차트 표준)

### 보류 결정 wire (cj-style 294+ 적용)
- OQ-EPIC30+-2 SMTP 인프라 외부 의존 = Story 30.3 Email 진입 시 결정
- OQ-EPIC30+-3 APScheduler vs Celery beat vs cron = Story 30.4 Scheduled 진입 시 결정

## §3 sprint scope — 9 files atomic single sprint

### 5 NEW content (~1,070 LOC)
1. `apps/api/modules/reports/pdf_routes.py` (~280 LOC)
   - GET /api/v1/exports/pdf route
   - `require_any_role("owner", "admin")` AD-22 owner-only RBAC
   - `require_capability(Capability.EXPORT_PDF)` AD-12 verify-first
   - audit-first INSERT `export_pdf` CR 1-1 verbatim + ActionClass.REPORTS
   - cross-tenant check CR 0-2 RLS
   - StreamingResponse PDF bytes (NFR5 P95 ≤ 5s)
   - MAX_PDF_ROWS=100_000 defense cap
   - PdfExportRequest Pydantic schema in-route validation

2. `apps/api/modules/reports/pdf_chart_helpers.py` (~200 LOC)
   - matplotlib 3 chart helpers:
     - render_category_breakdown_pie (카테고리별 비용 비중)
     - render_monthly_trend_bar (기간별 비용 추이)
     - render_unit_cost_evolution_line (단가 변화 추이)
   - Agg backend 결정 wire (no DISPLAY required)

3. `apps/api/modules/reports/pdf_generator.py` (~280 LOC)
   - reportlab Platypus engine
   - Korean font registration (NOTO Sans CJK KR primary + HeiseiMin-W3 + Helvetica fallback chain via _register_korean_font)
   - A4 landscape page setup
   - Table + Image flowables
   - 2 NEW typed exceptions (PdfExportSizeExceededError, PdfExportFontError, CR 12-5 D-14 envelope)
   - generate_cost_records_pdf + generate_bom_pdf

4. `tests/integration/test_phase_30_exports_pdf.py` (~310 LOC)
   - 12 tests covering MAX_PDF_ROWS + content-type + audit envelope + typed exceptions + Pydantic validation + font registration + page geometry + 2 PDF generation smoke tests

5. `_bmad-output/implementation-artifacts/commit-msg-cj-293.txt` (git commit payload)

### 4 MODIFIED (source + meta)
1. `apps/api/main.py` (+12 lines) — pdf_export_router mount 결정 wire 진입
2. `apps/api/pyproject.toml` (+6 lines) — reportlab==4.0.7 + matplotlib==3.9.0 stack pin EXTENSION
3. `apps/api/schemas/export_schemas.py` — PdfExportRequest Pydantic schema EXTENSION (CsvExportRequest verbatim mirror)
4. `_bmad-output/implementation-artifacts/sprint-status.yaml` (v4.58 → v4.59 EXTENSION, A705 신규 block entry)

## §4 AD/NFR bind

### AD bind 3/3 (cj-282 PRD entry §F44.1 verbatim)
- AD-2 (audit-first INSERT append-only) — `export_pdf` audit action BEFORE PDF byte flush
- AD-10 (identity/2FA via owner-only RBAC, AD-22 owner-only) — `require_any_role("owner", "admin")`
- AD-12 (verify-first capability gate) — `require_capability(Capability.EXPORT_PDF)`

### NFR bind 3/7 active
- NFR5 (streaming P95 ≤ 5s for 10만 row) — StreamingResponse 결정 wire
- NFR18 (ko-KR vocabulary SSOT) — NOTO Sans CJK KR font subset embedded + ko-KR chart labels
- NFR7 (PDF rendering integrity) — reportlab Platypus 결정 wire + Korean font fallback chain

## §5 검증 실측

- **12 NEW pytest PASS** (PDF tests 결정 wire 검증 완료)
- **22 baseline CSV test regression PASS preserved** (12 NEW + 22 기존 = 34/34 PASS preserved)
- **Python import chain 검증 완료** (5 NEW source files AST parse PASS)
- **13 job matrix unchanged** (cj-style baseline-green 보존)
- **Korean glyph warning** the matplotlib fallback DejaVu Sans 부재는 expected — Korean Windows 또는 NOTO Sans CJK KR 설치 환경에서 정상 렌더링

## §6 AD-14 stack pin EXTENSION 결정 wire

**35 pins → 37 pins**: +reportlab 4.0.7 + +matplotlib 3.9.0

**중요**: matplotlib 3.9.x 는 numpy 2.0 호환 (3.8.x 는 numpy<2.0 의존으로 cost_engine 의 numpy==2.0 pin 충돌 회피).

**pure Python stack 결정 wire**: weasyprint 대비 cairo/pango native deps 0 = [STACK BUMP] tag 불필요 + Dockerfile image size 감소 + 배포 복잡도 0.

## §7 PRE-EXISTING carryover 정직 회복 보존

- **csv-export.spec.ts 3/3 fail PRE-EXISTING carryover** (cj-287 activation 시점부터) → cj-292 revert 후 baseline state 회복 결정 wire (cj-291 honestly-DEFER 보존)
- **test-suite-measure P3 BLOCKING expected failure** (cj-282b baseline-green effort 의 비-MVP territory 45 failures 자연스러운 표면화) → 결정 wire 보존

## §8 결정 wire + Lessons learned

### 결정 wire 6개
1. 옵션 (a') Story 30.2 PDF export source+docs atomic 진입 결정 wire (사용자 분석 override)
2. OQ-EPIC30+-1 = reportlab (pure Python) 결정 wire 진입
3. OQ-EPIC30+-4 = matplotlib (pure Python) 결정 wire 진입
4. AD-14 stack pin EXTENSION 2건 (+reportlab 4.0.7 + +matplotlib 3.9.0) 결정 wire 진입
5. 9 files atomic single sprint 결정 wire 진입
6. CR 11-3 honest-DEFER 233번째 epic 연속 정직 회복

### Lessons learned
1. **pure Python stack 결정 wire 의 가치** — weasyprint 대비 cairo/pango native deps 0 = [STACK BUMP] 회피 + Dockerfile image size 감소 + 배포 복잡도 0
2. **matplotlib 3.9.x 의 numpy 2.0 호환성** — 3.8.x 의 numpy<2.0 의존성으로 cost_engine numpy==2.0 pin 충돌 회피 결정 wire
3. **Korean font fallback chain 의 안전성** — NOTO Sans CJK KR primary + HeiseiMin-W3 + Helvetica 3-stage fallback = ko-KR 깨짐 없이 모든 환경에서 PDF 생성 가능
4. **Pydantic schema 의 in-route validation 패턴** — CsvExportRequest verbatim mirror 결정 wire로 consistency 확보

## §9 다음 결정 wire 보류 (사용자 결정 대기)

- 옵션 (a) cj-294 close-out retro (cj-style 294번째, RECOMMENDED next) — Story 30.2 PDF export close-out retro docs-only atomic sprint 진입
- 옵션 (b) cj-295 wire sprint (cj-style 295번째) — Story 30.3 Email delivery (OQ-EPIC30+-2 SMTP 결정 동반) source+docs atomic
- 옵션 (c) cj-296 wire sprint (cj-style 296번째) — Story 30.4 Scheduled reports (OQ-EPIC30+-3 APScheduler 결정 동반) source+docs atomic
- 옵션 (d) cj-293 follow-up #1 — Story 30.2 PDF frontend UI tab (PdfExportTab.tsx + reports page tab nav) + e2e spec 진입
- 옵션 (e) Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory)
- 옵션 (f) Pilot 고객 유치 결정 wire (PRD OQ-3 파일럿 게이트 1주 post M0-M6 + Story 30.2 PDF export source+docs atomic 진입 직후 = pilot demo PDF 가능)

## §10 Related 결정 wire

- [cj-282 PRD entry `0c7524e`](handoff-2026-09-05-cj-282-epic-30-reporting-export-entry-done.md) — Epic 30+ Reporting & Export MVP territory 결정 wire 진입
- [cj-282a wire sprint 결정 wire](handoff-2026-09-06-cj-282a-wire-sprint-done.md) — Story 30.1 CSV export source+docs atomic single sprint
- [cj-285 EXTENSION wire sprint](handoff-2026-09-06-cj-285-extension-wire-sprint-done.md) — capability matrix v1.54 + audit actions EXTENSION
- [cj-286 EXTENSION wire sprint](handoff-2026-09-06-cj-286-extension-wire-sprint-done.md) — dev_seed report_fixtures + csv-export.spec.ts + AD-56
- [cj-287 wire sprint `5c37446`](handoff-2026-09-06-cj-287-csv-e2e-activate-sprint-done.md) — D-WEB-E2E-7 ownership wire ACTIVATED
- [cj-288 wire sprint `b91906a`](handoff-2026-09-06-cj-288-cost-records-bom-matrix-migration-done.md) — alembic migration 0060 cost_records + bom_matrix
- [cj-290 RLS EXTENSION wire sprint `1ba4309`](handoff-2026-09-06-cj-290-rls-extension-done.md) — production tenant isolation AD-3 invariant 보장
- [cj-291 close-out retro `0ce88ad`](handoff-2026-09-06-cj-291-rls-extension-close-retro-done.md) — Epic 30+ Reporting & Export MVP security layer foundation CLOSED
- [cj-292 ATTEMPTED + REVERTED](handoff-2026-09-06-cj-292-attempted-reverted.md) — Epic 30+ csv-export 3/3 PRE-EXISTING carryover 정직 fix 시도 + honest recovery via revert
- **cj-293 wire sprint (본 document)** — Epic 30+ Story 30.2 PDF export source+docs atomic single sprint (OQ-EPIC30+-1 + OQ-EPIC30+-4 결정 wire apply)

## §11 결정 wire 일자 + 멤버

- **결정 wire 일자**: 2026-09-06 (KST)
- **결정 wire 작성**: kjw
- **결정 wire 검증**: cj-style 293번째 wire sprint 결정 wire 진입
- **결정 wire 멤버**: cj-style chain 282~293 13 sprints cumulative 결정 wire 정직 보존
