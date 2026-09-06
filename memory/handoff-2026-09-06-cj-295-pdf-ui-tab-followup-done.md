---
name: cj-295-pdf-ui-tab-followup-done
description: cj-293 follow-up #1 wire sprint (cj-style 295번째) — Epic 30+ Story 30.2 PDF export UI tab + ReportsTabNav source+docs atomic — pilot customer UX 완성도 우선 결정 wire 진입
metadata:
  type: project
---

# cj-293 follow-up #1 wire sprint 결정 wire (cj-style 295번째) — Epic 30+ Story 30.2 PDF export UI tab + tab nav source+docs atomic

**결정 wire 일자**: 2026-09-06 (KST)
**territory**: Epic 30+ Reporting & Export MVP (cj-282 PRD entry territory)
**chain 진입**: cj-294 close-out retro `ba16a47` 의 next 옵션 (c) verbatim mirror — pilot customer UX 완성도 우선 결정 wire

## §1 사용자 분석 override 결정 wire 진입

**사용자 strategic 요청**: "리스크 최소화 + 시스템 구현 관점 + 최적 대안 분석 + 가장 합리적이고 효과적인 것부터 실행"

**옵션 비교 (5종)**:
- 옵션 (a) cj-295 wire sprint — Story 30.3 Email delivery (OQ-EPIC30+-2 SMTP 인프라 외부 의존 결정 동반). Risk HIGH (SMTP 외부 인프라 + retry + PII redaction). Pilot value LOW (first week 불필요)
- 옵션 (b) cj-296 wire sprint — Story 30.4 Scheduled reports (OQ-EPIC30+-3 APScheduler vs Celery beat vs cron 결정 동반). Risk HIGHEST (alembic + scheduler + 99.9% uptime SLO). Pilot value VERY LOW (first week 불필요)
- **옵션 (c) cj-293 follow-up #1 PDF UI tab** — Story 30.2 PDF frontend UI tab (PdfExportTab.tsx + reports page tab nav) + e2e spec. Risk LOW-MEDIUM (UI component verbatim mirror). Pilot value HIGH (dashboard UX 완성)
- 옵션 (d) Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory) — 18 spec drifts unresolved 결정 wire. Risk HIGHEST. Pilot value 0 (pilot blocker 아님, cj-291 honestly-DEFER 보존)
- 옵션 (e) Pilot 고객 유치 결정 wire (PRD OQ-3 파일럿 게이트 1주 post M0-M6) — Risk HIGHEST (business). Pilot value HIGHEST. 그러나 코드 변경 0 = cj-style discipline chain 일시 정지

**결정**: 옵션 (c) cj-293 follow-up #1 PDF UI tab 결정 wire 진입. cj-282a CsvExportTab.tsx verbatim mirror pattern 적용 가능 (이미 검증된 UI layer 패턴) + cj-293의 backend PDF route production-ready 의존.

## §2 sprint scope — 8 files atomic single sprint

### 5 NEW content (~560 LOC)
1. `apps/web/components/reports/PdfExportTab.tsx` (~150 LOC)
   - Story 30.2 PDF export tab UI (FR-30-2, cj-282 PRD entry §F30.2-1)
   - Period selector dropdown + type selector (cost-records/bom) + PDF download button
   - GET `/api/v1/exports/pdf?type=...&period=...&tenant_id=...` 결정 wire 진입
   - ko-KR NFR18 SSOT verbatim 적용
   - data-testid: pdf-export-tab-panel, pdf-export-tab, pdf-period-selector-{YYYY-MM}, pdf-download-button
   - AD bind 3/3 (backend 결정 wire 보존) + NFR bind 3/7 active (NFR5 + NFR7 + NFR18)

2. `apps/web/components/reports/ReportsTabNav.tsx` (~80 LOC)
   - Client component wrapping CsvExportTab + PdfExportTab with simple tab nav (CSV / PDF 2-tab UX, NFR18 ko-KR SSOT)
   - data-testid: reports-tab-nav, reports-tab-csv, reports-tab-pdf

3. `apps/web/__tests__/components/PdfExportTab.test.tsx` (~120 LOC)
   - 4 vitest tests (ko-KR NFR18 SSOT labels verbatim + 4 data-testids + period dropdown 12 monthly options + type selector default cost-records + bom option)

4. `apps/web/__tests__/components/ReportsTabNav.test.tsx` (~70 LOC)
   - 3 vitest tests (default CSV tab on mount + 3 data-testids + ko-KR labels for both tabs)

5. `apps/web/e2e/pdf-export.spec.ts` (~140 LOC, describe.skip baseline)
   - 3 e2e tests (PDF download button click triggers download + PDF response Content-Type is application/pdf + PDF response first 5 bytes are %PDF- magic number)
   - D-EPIC30+-PDF-2 honestly DEFER 결정 wire 보류 (cj-29x-impl territory)

### 3 MODIFIED (source + meta)
1. `apps/web/app/[locale]/(dashboard)/reports/page.tsx` (MODIFIED ~+15 lines) — Mounts `<ReportsTabNav>` (cj-295 NEW component) instead of direct `<CsvExportTab>` mount 결정 wire 진입
2. `_bmad-output/implementation-artifacts/sprint-status.yaml` (v4.62 → v4.63 EXTENSION, A707 신규 block entry + last_updated_note_v4_63 신규 paragraph)
3. `memory/MEMORY.md` (cj-295 hook EXTENSION 결정 wire 진입)

## §3 AD/NFR bind

### AD bind 3/3 (cj-282 PRD entry §F44.1 verbatim + cj-285 EXTENSION 결정 wire 보존)
- AD-2 (audit-first INSERT append-only) — backend 결정 wire 검증 (export_pdf cj-293 + export_csv cj-282a)
- AD-10 (identity/2FA via owner-only RBAC, AD-22 owner-only) — backend 결정 wire 검증 (require_any_role owner/admin 보존)
- AD-12 (verify-first capability gate) — Capability.EXPORT_PDF (cj-285 EXTENSION capability matrix v1.54 4-industry grants) + Capability.EXPORT_CSV 결정 wire 검증

### NFR bind 3/7 active (cj-293 PDF + cj-295 UI tab 합산)
- NFR5 (streaming P95 ≤ 5s for 10만 row) — StreamingResponse 결정 wire 보존 (PDF + CSV)
- NFR7 (PDF rendering integrity) — reportlab Platypus + Korean font fallback chain (cj-293 wire 결정 wire)
- NFR18 (ko-KR vocabulary SSOT) — NOTO Sans CJK KR font subset embedded + ko-KR chart labels + ko-KR UI tab labels (PDF 내보내기 / CSV 내보내기)

## §4 검증 실측

- **7 NEW vitest tests PASS** (PdfExportTab 4 tests + ReportsTabNav 3 tests) — pattern verbatim from CsvExportTab.test.tsx
- **e2e pdf-export.spec.ts describe.skip baseline** (3 tests skipped = 0 failed) — D-EPIC30+-PDF-2 honestly DEFER 보존
- **13 job matrix unchanged** (cj-style baseline-green 보존)
- **Korean glyph warning** the matplotlib fallback DejaVu Sans 부재는 expected — Korean Windows 또는 NOTO Sans CJK KR 설치 환경에서 정상 렌더링 (cj-293 결정 wire 보존)

## §5 cumulative 결정 wire 보존 14/14

cj-style chain 282~295 14 sprints cumulative 결정 wire 정직 보존:

①territory Epic 30+ Reporting & Export MVP 보존 (cj-282 PRD entry `0c7524e`)
②capability matrix v1.53 → v1.54 EXTENSION 보존 (cj-285)
③audit actions EXTENSION 보존 (cj-285 ActionClass.REPORTS + export_csv/export_pdf)
④dev_seed report_fixtures EXTENSION 보존 (cj-286)
⑤ci.yml csv-export.spec.ts EXTENSION 보존 (cj-286 auto-discover)
⑥AD-56 Epic 30+ 7 sub-decisions 보존 (cj-286)
⑦CR 1-1 silent audit failure fix 보존 (cj-287)
⑧D-WEB-E2E-7 ownership wire ACTIVATED 보존 (cj-287 → cj-292 revert 회복)
⑨alembic migration 0060 cost_records + bom_matrix 보존 (cj-288)
⑩Phase 3-0 listener dual GUC pattern 보존 (cj-290)
⑪OQ 결정 wire 2/4 apply (cj-293 OQ-EPIC30+-1 + OQ-EPIC30+-4)
⑫AD-14 stack pin EXTENSION 2건 +reportlab==4.0.7 + +matplotlib==3.9.0 (cj-293)
⑬cj-293~cj-294 chain 결정 wire 보존 (cj-294 close-out retro)
⑭NEW cj-295 follow-up #1 PDF UI tab + ReportsTabNav + tab nav 결정 wire 진입

= Epic 30+ Reporting & Export MVP territory 의 14 sprints cumulative chain 결정 wire 정직 보존 + Story 30.2 PDF export sub-territory 진짜 CLOSED ✅ HONEST (UI layer 포함).

## §6 honestly DEFER carryover 결정 wire

### 해소 (cj-295 follow-up #1 의 본 sprint)
- ✅ D-EPIC30+-PDF-1 PDF frontend UI tab — 해소됨 (PdfExportTab.tsx 결정 wire 진입)
- ✅ NEW D-EPIC30+-PDF-4 PDF frontend tab nav — 해소됨 (ReportsTabNav.tsx 결정 wire 진입)

### 보존 (cj-style 296+ 결정 wire 진입 시)
- ⏳ D-EPIC30+-PDF-2 PDF e2e spec activation — describe.skip baseline (cj-29x-impl territory 결정 wire 보류)
- ⏳ D-EPIC30+-PDF-3 PDF header/footer EXTENSION (page number, date stamp, watermark)

## §7 결정 wire + Lessons learned

### 결정 wire 6개
1. 옵션 (c) cj-293 follow-up #1 PDF UI tab 진입 결정 wire (사용자 분석 override)
2. PdfExportTab.tsx + ReportsTabNav.tsx 결정 wire 진입 (verbatim mirror pattern)
3. AD bind 3/3 결정 wire 검증 (backend 결정 wire 보존)
4. NFR bind 3/7 active 결정 wire 검증 (NFR5 + NFR7 + NFR18)
5. 8 files atomic single sprint 결정 wire 진입
6. CR 11-3 honest-DEFER 235번째 epic 연속 정직 회복

### Lessons learned
1. **cj-style discipline 의 누적 효과** — cj-294 close-out retro 직후 follow-up wire sprint 진입 = cj-style discipline chain 5th close-out retro 진입 (cj-282a + cj-289 + cj-291 + cj-294 + **cj-296 예정**) 의 자연스러운 다음 단계
2. **verbatim mirror pattern 의 가치** — cj-282a CsvExportTab.tsx 의 검증된 UI layer pattern 그대로 PDF tab 에 적용 = risk minimization
3. **tab nav UX 의 일관성** — CSV tab (파란색) + PDF tab (빨간색) 의 색상 코딩으로 UX 직관성 향상 (download 버튼 색상과 일치)
4. **describe.skip baseline pattern** — csv-export.spec.ts (cj-286 EXTENSION) 의 describe.skip pattern 그대로 적용 = cj-style discipline 보존 + PRE-EXISTING carryover 회피

## §8 다음 결정 wire 보류 (사용자 결정 대기)

- 옵션 (a) cj-296 close-out retro (cj-style 296번째, RECOMMENDED next) — Story 30.2 PDF UI tab follow-up close-out retro docs-only atomic sprint 진입 (cj-style discipline chain 5th close-out retro)
- 옵션 (b) cj-296 wire sprint (cj-style 296번째) — Story 30.3 Email delivery (OQ-EPIC30+-2 SMTP 인프라 외부 의존 결정 동반) source+docs atomic
- 옵션 (c) cj-297 wire sprint (cj-style 297번째) — Story 30.4 Scheduled reports (OQ-EPIC30+-3 APScheduler vs Celery beat vs cron 결정 동반) source+docs atomic
- 옵션 (d) Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory) — 18 spec drifts unresolved 결정 wire
- 옵션 (e) Pilot 고객 유치 결정 wire (PRD OQ-3 파일럿 게이트 1주 post M0-M6 + Story 30.2 PDF export UI layer 포함 CSV + PDF 둘 다 production-ready)

## §9 Related 결정 wire

- [cj-282 PRD entry `0c7524e`](handoff-2026-09-05-cj-282-epic-30-reporting-export-entry-done.md) — Epic 30+ Reporting & Export MVP territory 결정 wire 진입
- [cj-282a wire sprint](handoff-2026-09-06-cj-282a-wire-sprint-done.md) — Story 30.1 CSV export
- [cj-285 EXTENSION wire sprint](handoff-2026-09-06-cj-285-extension-wire-sprint-done.md)
- [cj-286 EXTENSION wire sprint](handoff-2026-09-06-cj-286-extension-wire-sprint-done.md)
- [cj-287 wire sprint `5c37446`](handoff-2026-09-06-cj-287-csv-e2e-activate-sprint-done.md)
- [cj-288 wire sprint `b91906a`](handoff-2026-09-06-cj-288-cost-records-bom-matrix-migration-done.md)
- [cj-290 RLS EXTENSION wire sprint `1ba4309`](handoff-2026-09-06-cj-290-rls-extension-done.md)
- [cj-291 close-out retro `0ce88ad`](handoff-2026-09-06-cj-291-rls-extension-close-retro-done.md)
- [cj-292 ATTEMPTED + REVERTED](handoff-2026-09-06-cj-292-attempted-reverted.md)
- [cj-293 wire sprint `09fcda3`](handoff-2026-09-06-cj-293-story-30-2-pdf-wire-sprint-done.md) — Story 30.2 PDF backend
- [cj-294 close-out retro `ba16a47`](handoff-2026-09-06-cj-294-story-30-2-pdf-close-retro-done.md) — Epic 30+ Story 30.2 sub-territory CLOSED ✅ HONEST
- **cj-295 follow-up #1 wire sprint (본 document)** — Epic 30+ Story 30.2 PDF UI tab + ReportsTabNav source+docs atomic (pilot customer UX 완성도 우선)

## §10 결정 wire 일자 + 멤버

- **결정 wire 일자**: 2026-09-06 (KST)
- **결정 wire 작성**: kjw
- **결정 wire 검증**: cj-style 295번째 wire sprint 결정 wire 진입
- **결정 wire 멤버**: cj-style chain 282~295 14 sprints cumulative 결정 wire 정직 보존
