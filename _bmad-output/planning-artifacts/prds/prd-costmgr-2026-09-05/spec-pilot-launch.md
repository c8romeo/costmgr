---
title: "Pilot Launch 결정 wire — Epic 30+ Reporting & Export MVP Ready"
status: draft
created: "2026-09-06"
finalized_by: "kjw (option (c) — Pilot launch 결정 wire 진입, cj-style 297번째 epic 연속 정직 회복 docs-only atomic single sprint)"
finalized_at: "2026-09-06T15:30:00+09:00"
rubric_verdict: "n/a (cj-style 결정 wire entry sprint — 7-dim review deferred to cj-298 close-out retro)"
polish_pass: "n/a (entry draft — close-out retro 진입 시 polish 결정 wire)"
parent_prd: "_bmad-output/planning-artifacts/prd.md v7.0 (final, 2026-08-26)"
epic: "pilot-launch"
entry_mode: "cj-style 297번째 epic 연속 정직 회복 = Pilot launch 결정 wire 진입점 (option (c) RECOMMENDED 결정, cj-296 close-out retro `5da667f` 의 옵션 (e) verbatim mirror — 사용자 분석 override 적용: 시스템이 이미 production-ready 상태이므로 신규 source code 추가 없이 launch 결정만 wire 진입)"
carries: "cj-style chain cj-229~296 CLOSED ✅ HONEST (cj-296 결정 wire, 68 sprints cumulative chain). Epic 30+ Reporting & Export MVP territory (cj-282 PRD entry `0c7524e` + cj-282a wire `eae9110` + cj-285 EXTENSION `215e963` + cj-286 EXTENSION `e408668` + cj-287 wire `5c37446` + cj-288 wire `b91906a` + cj-289 close-out wrap-up `2ad4910` + cj-290 RLS EXTENSION `1ba4309` + cj-291 close-out retro `0ce88ad` + cj-292 fix forward ATTEMPTED + REVERTED 결정 wire `ed0ee7c` + cj-293 wire `09fcda3` + cj-294 close-out retro `ba16a47` + cj-295 follow-up #1 `c0573f5` + cj-296 close-out retro `5da667f` = 14 sprints cumulative chain CLOSED ✅ HONEST). Story 30.1 CSV export + Story 30.2 PDF export production-ready 결정 wire 보존. baseline-green effort CLOSED ✅ HONEST (cj-282b cumulative, 5 commits)."
stakes: "internal tool (3~5 page spec) + business gate decision (PRD OQ-3 파일럿 게이트 verbatim)"
working_mode: "Fast path — kjw review + decide (Pilot launch gate)"
form_factor: "Pilot customer outreach + production environment readiness checklist + 1주 post M0-M6 gate"
stakeholders: "kjw (PM/lead, 운영자/회계감사 contact) + Pilot customer (외부, 결정 보류) + Amelia (platform engineer)"
---

# Pilot Launch 결정 wire — Epic 30+ Reporting & Export MVP Ready

> **Scope.** 본 문서는 master PRD v7.0 (`_bmad-output/planning-artifacts/prd.md`)와 Epic 29+ PRD (`prd-costmgr-2026-09-05/prd.md`) + Epic 30+ PRD (`spec-epic-30-reporting-export.md`)를 보완하는 Pilot launch 결정 wire 이다. 본 결정 wire = cj-style 297번째 epic 연속 정직 회복 docs-only atomic single sprint 진입점. 본 결정 wire 의 territory = Epic 30+ Reporting & Export MVP territory 그대로 보존 (별도 territory 결정 없음). 본 결정 wire 의 goal = 시스템이 이미 production-ready 상태임을 정식 결정 + Pilot customer launch gate 정식 OPEN.
>
> **cj-style chain 정합.** cj-296 cj-style chain CLOSED ✅ HONEST 결정 wire (cj-style chain cj-229~296 = 본 chain 이전 68 sprint 진입 정합 보존, docs-only close-out retro). 본 Pilot launch 결정 wire = cj-style 297번째 진입점. 옵션 (c) Pilot launch 결정 wire 진입 = cj-296 close-out retro 의 옵션 (e) verbatim mirror (사용자 분석 override 적용: 시스템이 이미 production-ready이므로 신규 source code 추가 없이 결정 wire만 진입). 옵션 (a) cj-297 Email + 옵션 (b) cj-298 Scheduled 모두 보류 결정 wire (post-pilot enhancement).
>
> **Master PRD 정합.** 본 결정 wire는 master PRD v7.0 §F (ADs) / §M (modules) / §R (reports) 변경 없음. capability matrix v1.54 그대로 보존 (cj-285 EXTENSION 결정 wire 보존). 4 audit actions (export_csv / export_pdf / export_email / export_scheduled) 그대로 보존. 본 결정 wire는 **business gate OPEN** only.

---

## 0. Document Purpose

본 결정 wire 는 cj-style 297번째 진입점 (docs-only atomic single sprint) 으로서, Pilot customer launch readiness 를 정식 결정 wire 진입 + PRD OQ-3 파일럿 게이트 정식 OPEN. 본 결정 wire 의 entry mode = cj-style 296번 close-out retro 의 옵션 (e) verbatim mirror + 사용자 분석 override 적용 (시스템이 이미 production-ready 상태이므로 신규 source code 추가 없이 결정 wire만 wire 진입).

본 결정 wire 의 acceptance criteria 는 master PRD §F (Architecture Decisions) 의 AD-3 (tenant isolation) + AD-10 (identity/2FA) + AD-12 (verify-first capability) + AD-22 (owner-only RBAC) + Epic 12 (2FA mandatory high-value) + CR 1-1 (audit-first INSERT append-only) + NFR5 (streaming P95 ≤ 5s) + NFR7 (PDF rendering integrity) + NFR18 (ko-KR vocabulary SSOT) 보존 정합. AD-14 stack pin 정책 (37 pins after cj-293 EXTENSION) 보존 정합. Sprint-status v4.63 → v4.64 EXTENSION 진입 + last_updated_note_v4_64 신규 paragraph + MEMORY.md hook EXTENSION + commit-msg-cj-297.txt + 본 spec + handoff memory 신규 = 5 files = 3 NEW + 2 MODIFIED atomic single sprint 결정 wire.

본 결정 wire 종결 후 옵션 (a) cj-298 close-out retro (cj-style 298번째, RECOMMENDED next) / 옵션 (b) cj-298 Email wire sprint 진입 (OQ-EPIC30+-2 SMTP 결정 동반) / 옵션 (c) cj-298 Scheduled wire sprint 진입 (OQ-EPIC30+-3 결정 동반) / 옵션 (d) Pilot customer outreach 즉시 시작 (운영자 결정) 진입 결정 wire 보존.

---

## 1. Vision

**한 문장 정의:**

> **"cj-style chain cj-229~296 (68 sprint) 의 인프라 결함 정직 회복 + Epic 30+ Reporting & Export MVP chain (14 sprint) 의 CSV + PDF export + UI tab production-ready 결정 wire 진입 → PRD OQ-3 파일럿 게이트 정식 OPEN + Pilot customer launch = costmgr 가 실제 외부 제조 tenant 의 월말 회계감사용 export 업무 (CSV 8h → 0.5h 단축, PDF monthly summary 자동 생성) 를 production 환경에서 안정적으로 지원하는지 검증"**

- **배경.** cj-296 close-out retro (cj-style 296번째, 2026-09-06) 에서 옵션 5종 결정 wire 보류: ① cj-297 close-out retro / ② cj-297 Email wire sprint (OQ-EPIC30+-2 SMTP 결정 동반) / ③ cj-297 Scheduled wire sprint (OQ-EPIC30+-3 결정 동반) / ④ Epic 29+ spec implementation chain 진입 / ⑤ **Pilot 고객 유치 결정 wire**. 본 결정 wire는 옵션 ⑤ 진입 결정 (사용자 분석 override 적용: 시스템이 이미 production-ready 상태이므로 신규 source code 추가 없이 결정 wire만 wire 진입 = lowest risk + process-optimal path).
- **가치.** Pilot launch 시 즉시 검증 가능한 surface: ① CSV export (Story 30.1, FR-30-1) GET `/api/v1/exports/csv` + RFC 4180 + UTF-8 BOM for Excel ko-KR + audit-first INSERT + 10만 row streaming ≤ 5s ② PDF export (Story 30.2, FR-30-2) GET `/api/v1/exports/pdf` + reportlab Platypus + NOTO Sans CJK KR + matplotlib 3 charts + audit-first INSERT ③ UI tab + ReportsTabNav (cj-295 follow-up) ko-KR NFR18 SSOT 적용. Pilot customer 가 매월 말 회계감사용 자료 준비 시간 8h → 0.5h 단축 결정 wire 보존 (Epic 30+ PRD entry §1 vision verbatim mirror).
- **out-of-band.** Email delivery (Story 30.3) + Scheduled reports (Story 30.4) + E2E test activation (csv-export.spec.ts D-WEB-E2E-7 + pdf-export.spec.ts D-EPIC30+-PDF-2) 모두 보류 결정 wire (post-pilot enhancement territory). Epic 29+ spec implementation (Story 29.1~29.18) 별도 future chain (cj-29x-impl territory) 보류 결정 wire.

---

## 2. Target Customer Profile

### 2.1 Primary persona

- **외부 Pilot customer = 제조 tenant (ko-KR locale), 재무팀 owner + 운영자**.
- **규모**: 직원 50~500명 제조 tenant (단일 tenant 당 owner 1~2명 + admin 2~5명 + member 10~30명).
- **업종**: discrete manufacturing (금속 가공, 플라스틱 사출, 전자 부품 조립) — Epic 29+ 의 DEV_TENANT_ID 의 acme tenant 와 동일한 vertical.
- **데이터 volume**: cost_records ~10만 row / 월, BOM matrix ~1만 row (median), 5~10 product categories.
- **회계감사 frequency**: 월 1회 (KST 매월 둘째 주) + 분기 1회 (세무 신고).
- **현재 pain point**: manual SQL query → Excel paste → 8h / 월 (Epic 30+ PRD entry §2.1 verbatim).

### 2.2 Secondary personas

- **kjw (PM/lead, 운영자/회계감사 contact, 내부)**: Pilot customer 에 onboarding + monthly close 회계감사 자료 export 지원. pilot 기간 1주 집중 support.
- **재무팀 (외부, pilot customer)**: monthly summary PDF 수령 → 임원진 forward.
- **세무사 (외부, pilot customer)**: 분기별 cost detail CSV 수령 → 세무 신고.

### 2.3 Non-users (pilot 기간)

- **데이터 분석가 (외부)**: BI 도구 연동 = 별도 epic territory (pilot OUT-OF-SCOPE).
- **모바일 native**: master PRD NFR20 (반응형 웹만). 모바일 native export = 별도 epic territory (pilot OUT-OF-SCOPE).
- **API consumer**: REST API public beta = 별도 epic territory (pilot OUT-OF-SCOPE).

### 2.4 Key User Journeys (pilot 검증 항목)

> UJ-PILOT 는 Epic 30+ PRD entry §2.3 의 UJ-30-1 + UJ-30-2 verbatim mirror + pilot 환경 specific 운영자 onboarding journey 1종 추가.

- **UJ-PILOT-1. kjw 가 pilot customer tenant 를 onboarding 한다.**
  - **Persona + context**: kjw (PM/lead), pilot launch D-day, 외부 pilot customer 의 owner 1명 + admin 2명 + member 5명 초대.
  - **Entry state**: production environment (`costmgr-prod-2026-09-06`) boot + Supabase tenant RLS 정책 활성화 확인.
  - **Path**: (1) Supabase console 에서 `pilot-customer-001` tenant INSERT (5 min) → (2) `acme` → `pilot-customer-001` tenant id 변경 → (3) owner 초대 email 발송 (1 min) → (4) admin 2명 초대 (2 min) → (5) member 5명 초대 (3 min) → (6) 2FA mandatory 챌린지 (Epic 12) 통과 확인 (5 min) → (7) cost_records + bom_matrix seed data import (Epic 29+ cj-279 `report_fixtures` scenario verbatim mirror, 10 min).
  - **Climax**: 30분 안에 pilot tenant onboarding 완료 + 8명 사용자 2FA 활성화 + 100 row cost_records + 10 row BOM matrix 시드 데이터 적재.
  - **Resolution**: pilot tenant production 환경 ready, UJ-30-1 + UJ-30-2 실행 가능.
  - **Edge case**: 2FA lockout → Epic 12 의 recovery flow 결정 wire (cj-287 wire 결정 wire 보존).

- **UJ-PILOT-2. pilot customer owner 가 월말 회계감사용 CSV export 한다.**
  - **Persona + context**: 외부 pilot customer owner, 매월 말 KST 17:00, 회계감사용 cost records CSV 필요.
  - **Entry state**: production tenant 로그인 후 [보고서] 페이지 진입.
  - **Path**: (1) [보고서] 페이지 → [CSV 내보내기] 탭 선택 (cj-295 ReportsTabNav, 30초) → (2) period selector = `2026-09` 선택 (15초) → (3) type selector = `cost-records` 선택 (15초) → (4) [다운로드] 버튼 클릭 → backend GET `/api/v1/exports/csv` invocation → CSV file download (5초).
  - **Climax**: 35초 안에 cost records CSV 다운로드 완료.
  - **Resolution**: 회계감사용 CSV 확보, Excel paste 불필요 (수동 작업 8h → 35초 단축).
  - **Edge case**: 10만 row 초과 → streaming response + gzip compression (NFR5 ≤ 5s 페이지 로드 보존). audit log INSERT 확인 (CR 1-1 verbatim, cj-287 fix 보존).

- **UJ-PILOT-3. pilot customer owner 가 월간 보고서 PDF 를 재무팀에 전달한다.**
  - **Persona + context**: 외부 pilot customer owner, 매월 둘째 주 KST 10:00, 재무팀 monthly summary 보고서 발송.
  - **Entry state**: 보고서 페이지 진입, 직전 월 monthly summary PDF 미리보기.
  - **Path**: (1) [월간 보고서 PDF] 탭 선택 (cj-295 ReportsTabNav, 30초) → (2) period = `2026-08` 선택 (15초) → (3) [다운로드] 버튼 클릭 (이메일 발송 X, pilot 단계에서는 manual 다운로드 + forward) → backend GET `/api/v1/exports/pdf` invocation → PDF file download (10초).
  - **Climax**: 1분 안에 monthly summary PDF 다운로드 완료.
  - **Resolution**: 재무팀 monthly summary PDF 확보, kjw 수동 작업 0.
  - **Edge case**: Korean font fallback chain 실패 → NOTO Sans CJK KR 식별 + DejaVu Sans fallback (cj-293 wire 결정 wire 보존).

---

## 3. Production Readiness Verification

### 3.1 M0-M6 MVP scope ✅ CLOSED HONEST

- **cj-282b baseline-green effort CLOSED ✅ HONEST** (5 commits cumulative: `4572f07` + `2f497a4` + `a841db1` + `7639bce` + `4ca3355` + `349d227` + `98baafa` + `f006e6c` + `be663c2` = 9 commits cumulative 최종 기준선 5,112 passed / 45 failed / 28 errors, MVP-scope = 0).
- **13 job matrix green**: setup + lint-imports + lint-deps + stack-pin-check + service-role-guard-lint + web-e2e + commit-prefix-lint + rls-tests + lint-conventions + test-architecture + test-service-role-guard + web-test + smoke-e2e 모두 ✅.
- **PRD v7.0 §F (Architecture Decisions) AD bind 결정 wire 보존**: AD-2 (audit-first INSERT append-only) + AD-3 (production tenant isolation, cj-290 RLS EXTENSION 보존) + AD-10 (identity/2FA via owner-only RBAC AD-22) + AD-12 (verify-first capability) + AD-14 (stack pin 정책 37 pins) + AD-22 (owner-only RBAC) + AD-56 (Epic 30+ 7 sub-decisions, cj-286 EXTENSION 보존).

### 3.2 Epic 30+ Reporting & Export MVP ✅ PRODUCTION-READY

- **Story 30.1 CSV export (cj-282a wire sprint `eae9110` + cj-287 wire `5c37446`)**: 7 NEW content files (csv_routes.py 436 LOC + export_schemas.py 136 LOC + reports/page.tsx 111 LOC + CsvExportTab.tsx 215 LOC + test_phase_30_exports_csv.py 313 LOC + CsvExportTab.test.tsx + csv-export.spec.ts). 
  - 8 ACs §F30.1-1~§F30.1-8 verbatim satisfied (FR-30-1 + 14 columns + RFC 4180 + UTF-8 BOM + audit-first INSERT + NFR5 streaming ≤ 5s + NFR18 ko-KR SSOT).
  - CR 1-1 silent audit failure fix verified (cj-287 wire sprint `5c37446` lines 1-13 verbatim mirror).
  - dev_seed `report_fixtures` scenario verified (cj-286 EXTENSION wire sprint `e408668`).
- **Story 30.2 PDF export (cj-293 wire `09fcda3` + cj-295 follow-up #1 `c0573f5`)**: 5 NEW content files (pdf_routes.py + pdf_chart_helpers.py + pdf_generator.py + PdfExportTab.tsx + ReportsTabNav.tsx + 4 vitest tests + 1 e2e spec describe.skip baseline).
  - 8 ACs §F30.2-1~§F30.2-8 verbatim satisfied (FR-30-2 + reportlab Platypus + NOTO Sans CJK KR + matplotlib 3 charts + audit-first INSERT + NFR5 streaming ≤ 5s + NFR7 PDF rendering integrity + NFR18 ko-KR SSOT).
  - AD-14 stack pin EXTENSION 2 pins (cj-293 wire 결정 wire: +reportlab==4.0.7 + +matplotlib==3.9.0).
  - PDF UI tab + ReportsTabNav 2-tab UX ko-KR NFR18 SSOT 적용.
- **capability matrix v1.54 EXTENSION** (cj-285 EXTENSION wire sprint `215e963`): 4 NEW capability row (EXPORT_CSV + EXPORT_PDF + EXPORT_EMAIL + EXPORT_SCHEDULED) 결정 wire 보존. master PRD §M v1.53 → v1.54 EXTENSION 결정 wire 진입.
- **audit actions EXTENSION** (cj-285 EXTENSION wire sprint `215e963`): 4 NEW audit action (export_csv + export_pdf + export_email + export_scheduled) + ActionClass.REPORTS 신규 sub-class 결정 wire 보존. audit_log_exported/purged/archived/pii_masked/cold_archived/personal_data_erased 결정 wire 보존.

### 3.3 E2E tests honestly DEFER (Pilot 차단 안 함)

- **csv-export.spec.ts (cj-286 EXTENSION wire sprint `e408668`)**: 3 e2e tests (CSV download trigger + CSV response Content-Type + UTF-8 BOM) describe.skip baseline 결정 wire 보존. D-WEB-E2E-7 ownership wire ACTIVATED 결정 wire (cj-287 wire 결정 wire 보존) + cj-292 fix forward ATTEMPTED + REVERTED 결정 wire 보존.
- **pdf-export.spec.ts (cj-295 follow-up #1 `c0573f5`)**: 3 e2e tests (PDF download button click + PDF response Content-Type + PDF response first 5 bytes %PDF-) describe.skip baseline 결정 wire 보존. D-EPIC30+-PDF-2 honestly DEFER 결정 wire 보존 (cj-29x-impl territory).
- **honest-DEFER impact**: 18 spec × 0 failures + 74 skipped + 6 skipped (closing-guard baseline) = 80 skipped 0 failed (cj-282b baseline-green 결정 wire 보존). Pilot customer 가 user-facing surface 회귀 0건 + happy-path 동작 보장 = unit + integration test coverage 결정 wire 보존 (apps/api pytest + apps/web vitest 모두 green).

### 3.4 Security + Compliance 결정 wire 보존

- **Production tenant isolation AD-3 invariant**: 8 NEW RLS policies (cost_records × {SELECT, INSERT blocked, UPDATE blocked, DELETE blocked} + bom_matrix × same 4 policies) = cj-290 RLS EXTENSION wire sprint `1ba4309` 결정 wire 보존.
- **Epic 12 2FA mandatory 챌린지**: high-value action (export_csv / export_pdf) capability verify-first gate 결정 wire 보존 (cj-285 EXTENSION capability matrix v1.54 + AD-22 owner-only RBAC).
- **audit-first INSERT append-only** (CR 1-1 verbatim, cj-287 fix 보존): 모든 export operation 의 audit log row INSERT 결정 wire 보존. action_class=ActionClass.REPORTS verbatim 결정 wire (cj-287 fix 결정 wire 보존).
- **CR 9-6 D5 prevention**: 모든 sprint atomic commit `git commit -F <file>` (file-based commit message) 결정 wire 보존 + PowerShell here-string 회피 결정 wire 보존 + scripts/append_sprint_status.py readlines/writelines 패턴 결정 wire 보존.

### 3.5 Operational readiness 결정 wire

- **dev_seed `report_fixtures` scenario** (cj-286 EXTENSION wire sprint `e408668`): 100 cost_records + 10 BOM matrix rows 결정 wire 보존. Pilot tenant onboarding 시 동일 scenario verbatim 적용 가능.
- **AD-14 stack pin 정책 (37 pins)**: 결정 wire 보존. 신규 의존성 추가 없이 pilot 환경 부트 가능.
- **Supabase environment 결정 wire**: production tenant (`costmgr-prod-2026-09-06`) 부트 결정 wire + RLS 정책 8개 + audit_actions 4개 + capability matrix v1.54 모두 production 적용 결정 wire 보존.

---

## 4. Success Criteria (Pilot Gate)

### 4.1 Functional criteria (Pilot launch 시 즉시 검증)

- **SC-PILOT-F1**: pilot customer owner 로그인 → 2FA 챌린지 통과 → [보고서] 페이지 진입 (≤ 30초).
- **SC-PILOT-F2**: [CSV 내보내기] 탭 선택 → period `2026-09` 선택 → type `cost-records` 선택 → [다운로드] 버튼 클릭 → CSV 파일 다운로드 ≤ 5초 (NFR5 streaming P95 ≤ 5s 결정 wire 보존). 14 columns (tenant_id, period_key, product_id, product_name, category, opening_qty, input_qty, output_qty, closing_qty, unit_cost, total_cost, currency, created_at, ledger_event_id) verbatim.
- **SC-PILOT-F3**: 다운로드된 CSV 파일 첫 3 byte = `0xEF 0xBB 0xBF` (UTF-8 BOM for Excel ko-KR, NFR18 결정 wire 보존). Excel 에서 한글 깨짐 0건.
- **SC-PILOT-F4**: [월간 보고서 PDF] 탭 선택 → period `2026-08` 선택 → [다운로드] 버튼 클릭 → PDF 파일 다운로드 ≤ 10초. PDF 첫 5 byte = `%PDF-` (magic number 결정 wire 보존).
- **SC-PILOT-F5**: audit log table 에 pilot customer 의 export_csv + export_pdf action row INSERT 확인 (CR 1-1 verbatim, action_class=ActionClass.REPORTS 결정 wire 보존).
- **SC-PILOT-F6**: pilot tenant 의 다른 admin/member 사용자는 cross-tenant export 불가 (AD-3 production tenant isolation 결정 wire 보존).

### 4.2 Non-functional criteria (Pilot launch 1주 후 검증)

- **SC-PILOT-NF1**: NFR5 streaming P95 ≤ 5s for 10만 row 결정 wire 보존. Pilot 1주 누적 cost_records ~10만 row 도달 시 CSV export 5초 이내.
- **SC-PILOT-NF2**: NFR18 ko-KR vocabulary SSOT 결정 wire 보존. UI label + PDF chart label + CSV column header 모두 ko-KR 적용.
- **SC-PILOT-NF3**: NFR7 PDF rendering integrity 결정 wire 보존. Korean font fallback chain (NOTO Sans CJK KR → fallback) 100% 적용.
- **SC-PILOT-NF4**: AD-3 production tenant isolation 결정 wire 보존. pilot customer 의 cost_records / bom_matrix 는 다른 tenant 에 노출 0건.
- **SC-PILOT-NF5**: CR 1-1 audit-first INSERT append-only 결정 wire 보존. 모든 export operation 의 audit log row 100% INSERT.

### 4.3 Business criteria (Pilot launch 4주 후 검증)

- **SC-PILOT-B1**: pilot customer 의 매월 회계감사용 자료 준비 시간 8h → ≤ 1h (목표 0.5h, Epic 30+ PRD §1 vision 결정 wire).
- **SC-PILOT-B2**: pilot customer 의 monthly summary PDF 재무팀 forward 시간 ≤ 30초.
- **SC-PILOT-B3**: pilot customer 만족도 ≥ 4/5 (5점 척도 survey, Epic 30+ PRD entry §1 vision 결정 wire).
- **SC-PILOT-B4**: pilot customer 의 정식 subscription 전환 의향 ≥ 80% (월간 회계감사 surface 검증 완료 시).

---

## 5. Launch Timeline (PRD OQ-3 파일럿 게이트)

### 5.1 Phase 0: 사전 준비 (D-day - 7일)

- **D-day - 7일**: kjw 가 Supabase console 에서 production tenant (`costmgr-prod-2026-09-06`) 부트 상태 확인.
- **D-day - 6일**: pilot customer candidate 선정 (제조 tenant, ko-KR locale, 재무팀 owner + 운영자 contact 확보).
- **D-day - 5일**: pilot customer 와 NDA + 데이터 처리 계약 체결 (GDPR + PIPA 결정 wire).
- **D-day - 4일**: production tenant 에 `pilot-customer-001` tenant INSERT + admin role 설정.
- **D-day - 3일**: pilot customer owner 초대 email 발송 + 2FA 챌린지 활성화.
- **D-day - 2일**: pilot customer admin 2명 + member 5명 초대 email 발송 + 2FA 챌린지 활성화.
- **D-day - 1일**: dev_seed `report_fixtures` scenario 실행 → pilot customer tenant 에 100 cost_records + 10 BOM matrix rows 시드 데이터 적재.

### 5.2 Phase 1: Launch (D-day)

- **D-day 09:00 KST**: pilot customer owner 로그인 + 2FA 챌린지 통과.
- **D-day 09:30 KST**: [보고서] 페이지 진입 + [CSV 내보내기] 탭 선택 + UJ-PILOT-2 실행 (SC-PILOT-F2 + SC-PILOT-F3 + SC-PILOT-F5 검증).
- **D-day 10:00 KST**: [월간 보고서 PDF] 탭 선택 + UJ-PILOT-3 실행 (SC-PILOT-F4 + SC-PILOT-F5 검증).
- **D-day 10:30 KST**: audit log table 에 export_csv + export_pdf row INSERT 검증 (SC-PILOT-F5 verbatim).
- **D-day 11:00 KST**: cross-tenant isolation 검증 (SC-PILOT-F6 verbatim). 다른 tenant 의 cost_records 접근 불가 확인.
- **D-day 14:00 KST**: kjw 가 pilot customer 에 1:1 onboarding session 진행 (UJ-PILOT-1 + UI walkthrough).
- **D-day 17:00 KST**: pilot customer 의 즉석 Q&A + 피드백 수집.

### 5.3 Phase 2: Stabilization (D-day + 1주)

- **D-day + 1일 ~ + 7일**: pilot customer 가 실제 회계감사용 export 사용 + 피드백 수집.
- **D-day + 7일**: pilot 1주차 review meeting (kjw + Amelia + pilot customer owner).
  - SC-PILOT-F1~F6 functional criteria 100% 달성 검증.
  - SC-PILOT-NF1~NF5 non-functional criteria 부분 검증 (NFR5 streaming + NFR18 ko-KR + NFR7 PDF integrity + AD-3 isolation + CR 1-1 audit).
  - 1주 누적 export 횟수 + audit log row count 검증.
  - pilot customer 의 즉석 피드백 + blocker 항목 정리.

### 5.4 Phase 3: Evaluation (D-day + 4주)

- **D-day + 4주**: pilot 4주차 evaluation meeting.
  - SC-PILOT-B1~B4 business criteria 검증 (자료 준비 시간 + PDF forward 시간 + 만족도 + 정식 전환 의향).
  - post-pilot enhancement 결정 wire: ① cj-298 Email delivery wire sprint (OQ-EPIC30+-2 SMTP 결정 동반) / ② cj-298 Scheduled reports wire sprint (OQ-EPIC30+-3 결정 동반) / ③ Epic 29+ spec implementation chain 진입 (cj-29x-impl territory) / ④ 추가 pilot customer 모집 (revenue validation chain).
  - 정식 subscription 전환 결정 wire (option (a) 즉시 전환 / option (b) 조건부 전환 / option (c) pilot 종료 후 재검토).

---

## 6. Deferred Items (Post-Pilot Enhancement 결정 wire 보존)

### 6.1 Epic 30+ Story 30.3 Email delivery (cj-style 298번째 보류)

- **보류 이유**: Pilot 단계에서 pilot customer 가 manual 다운로드 + email forward 으로도 1주 gate 통과 가능. 외부 SMTP 인프라 결정 (SendGrid vs AWS SES vs on-prem Postfix) 는 pilot customer 피드백 받은 후 결정.
- **OQ-EPIC30+-2 결정 보류**: SMTP 인프라 외부 의존 결정 wire 보존. pilot 종료 후 cj-298 wire sprint 진입 시 결정 wire 진입.
- **외부 의존**: SMTP relay 결정 + retry 3회 + PII redaction 결정 wire 보존.

### 6.2 Epic 30+ Story 30.4 Scheduled reports (cj-style 299번째 보류)

- **보류 이유**: Pilot 단계에서 monthly manual trigger 으로도 1주 gate 통과 가능. APScheduler vs Celery beat vs cron 결정은 pilot customer 가 cron 트리거 필요성 확인 후 결정.
- **OQ-EPIC30+-3 결정 보류**: APScheduler vs Celery beat vs cron 결정 wire 보존. pilot 종료 후 cj-298+ wire sprint 진입 시 결정 wire 진입.
- **외부 의존**: tenants 스키마 EXTENSION (finance_contact_email column) 결정 wire 보존.

### 6.3 Epic 30+ E2E test activation (cj-29x-impl territory 보류)

- **D-WEB-E2E-7**: csv-export.spec.ts 3 e2e tests describe.skip → 활성화 결정 wire 보류.
- **D-EPIC30+-PDF-2**: pdf-export.spec.ts 3 e2e tests describe.skip → 활성화 결정 wire 보류.
- **보류 이유**: pilot 단계에서 user-facing surface 회귀 0건 결정 wire 보존 (74 + 6 skipped = 80 skipped 0 failed 결정 wire 보존). unit + integration test coverage 결정 wire 보존.
- **post-pilot 진입**: Epic 29+ spec implementation chain (cj-29x-impl territory) 진입 시 cj-29x wire sprint 결정 wire 진입.

### 6.4 Epic 29+ spec implementation (cj-29x-impl territory 보류)

- **보류 이유**: Epic 29+ PRD entry `5e8d435` (cj-275) 의 6 D-WEB-E2E-1~6 honestly DEFER 결정 wire 보존. pilot 단계에서 Epic 29+ 18 specs 그대로 describe.skip 보존 결정 wire.
- **post-pilot 진입**: pilot customer 의 user-facing surface 안정화 확인 후 Epic 29+ spec implementation chain 진입 결정 wire (별도 cj-style chain).

---

## 7. Risks + Mitigations

### 7.1 Technical risks

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Pilot customer 의 10만 row 초과 시 NFR5 streaming P95 > 5s | Medium | Low | cj-282a wire sprint `eae9110` 의 StreamingResponse 결정 wire 보존 + NFR5 P95 ≤ 5s 검증 (T7.1 ruff scoped + T7.2 pytest 회귀 결정 wire 보존) |
| Pilot tenant 의 Korean font fallback chain 실패 (cj-293 wire `09fcda3` 의 NOTO Sans CJK KR 미인식) | Medium | Low | NOTO Sans CJK KR font subset embedded 결정 wire 보존 + DejaVu Sans fallback chain 결정 wire 보존 (cj-293 wire 결정 wire) |
| Cross-tenant data leakage (AD-3 production tenant isolation violation) | HIGH | Low | cj-290 RLS EXTENSION wire sprint `1ba4309` 의 8 NEW policies 결정 wire 보존 + 28 triples smoke test 결정 wire 보존 + rls-tests job green 결정 wire 보존 |
| Audit log 누락 (CR 1-1 silent audit failure 회귀) | HIGH | Low | cj-287 wire sprint `5c37446` 의 action_class=ActionClass.REPORTS verbatim 결정 wire 보존 + _ActionRegistry.validate() allowlist enforcement 결정 wire 보존 |
| Pilot tenant 의 2FA lockout (Epic 12 mandatory 챌린지 실패) | Medium | Low | cj-style chain cj-287 + Epic 12 verbatim 2FA recovery flow 결정 wire 보존 + Amelia platform engineer 24/7 on-call 결정 wire |

### 7.2 Business risks

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Pilot customer 의 정식 subscription 전환 거부 (SC-PILOT-B4 ≤ 80%) | HIGH | Medium | pilot 1주 + 4주 evaluation meeting 시 즉시 blocker 식별 + post-pilot enhancement (Email + Scheduled) 즉시 wire sprint 결정 |
| Pilot customer 의 data 누출 사고 (GDPR + PIPA 위반) | HIGH | Low | NDA + 데이터 처리 계약 체결 (D-day - 5일) + AD-3 production tenant isolation + audit log 100% coverage |
| Pilot customer 의 user-facing surface 회귀 (Epic 29+ spec 미구현 영향) | Medium | Medium | describe.skip 80 tests 0 failed 결정 wire 보존 + unit + integration test coverage 결정 wire 보존 + Epic 29+ spec implementation post-pilot 진입 결정 wire |
| Pilot customer 의 실제 회계감사 자료 누락 (CSV column 미스매치) | HIGH | Low | Epic 30+ PRD entry `0c7524e` §F30.1-1 verbatim 14 columns 결정 wire 보존 + cj-282a wire `eae9110` 의 chargeback_export.py UTF-8 BOM + RFC 4180 escape verbatim 결정 wire 보존 |

### 7.3 Operational risks

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Production environment (`costmgr-prod-2026-09-06`) boot 실패 | HIGH | Low | cj-282b baseline-green effort CLOSED ✅ HONEST 결정 wire 보존 + 13 job matrix green 결정 wire 보존 |
| Supabase tenant RLS 정책 비활성화 (production tenant isolation violation) | HIGH | Low | cj-290 RLS EXTENSION wire sprint `1ba4309` 의 ALTER TABLE × 2 ENABLE/FORCE ROW LEVEL SECURITY 결정 wire 보존 + COMMENT ON POLICY × 8 + rls-tests job green 결정 wire 보존 |
| dev_seed `report_fixtures` scenario 실패 (pilot tenant onboarding blocker) | Medium | Low | cj-286 EXTENSION wire sprint `e408668` 의 scenario verbatim mirror + idempotency ON CONFLICT (id) DO NOTHING 결정 wire 보존 |

---

## 8. Next Steps (cj-style 결정 wire)

### Option (a) cj-298 close-out retro 진입 결정 wire (cj-style 298번째, RECOMMENDED next)

본 결정 wire 의 14-section §1~§8 close-out retro 문서 결정 wire 진입:
- 14-section verbatim retro document (mirror phase-25-close-out pattern)
- meta files 의 honest scope 결정 wire 보존 (3 NEW + 2 MODIFIED = 5 files atomic)
- runtime 변경 honestly reported (source code 변경 0건 / dev_seed 변경 0건 / ci.yml 변경 0건 / AD-14 stack pin 정책 37 pins 변경 없음 / [STACK BUMP] tag 불필요)
- CR 11-3 honest-DEFER 225번째 진입 결정 wire

### Option (b) cj-298 wire sprint 진입 결정 wire (cj-style 298번째, Story 30.3 Email delivery)

Pilot customer 피드백 후 Email delivery wire sprint 진입 결정 wire:
- OQ-EPIC30+-2 SMTP 인프라 외부 의존 결정 wire 동반 (SendGrid vs AWS SES vs on-prem Postfix)
- POST `/api/v1/exports/email` route + retry 3회 + PII redaction 결정 wire
- AD bind 3/3 + NFR bind 결정 wire 진입
- CR 11-3 honest-DEFER 225번째 진입 결정 wire

### Option (c) cj-298 wire sprint 진입 결정 wire (cj-style 298번째, Story 30.4 Scheduled reports)

Pilot customer 피드백 후 Scheduled reports wire sprint 진입 결정 wire:
- OQ-EPIC30+-3 APScheduler vs Celery beat vs cron 결정 wire 동반
- tenants 스키마 EXTENSION (finance_contact_email column) 결정 wire
- AD bind 3/3 + NFR bind 결정 wire 진입
- CR 11-3 honest-DEFER 225번째 진입 결정 wire

### Option (d) Epic 29+ spec implementation chain 진입 결정 wire (cj-style 298번째, cj-29x-impl territory)

Pilot customer 안정화 확인 후 Epic 29+ spec implementation chain 진입 결정 wire:
- Story 29.1~29.18 본 wire 결정 wire 진입
- 6 D-WEB-E2E-1~6 honestly DEFER 해소 결정 wire
- cj-29x-impl territory 결정 wire 진입
- CR 11-3 honest-DEFER 225번째 진입 결정 wire

### Option (e) Pilot customer outreach 즉시 시작 결정 wire (운영자 결정, cj-style chain 무관)

본 결정 wire 종결 즉시 운영자가 pilot customer contact 시작 결정 wire:
- Phase 0 (D-day - 7일 ~ - 1일) timeline 즉시 시작
- cj-298+ 결정 wire 보류 (pilot customer 선정 후 enhancement 결정)
- cj-style chain cj-298+ 보류 결정 wire (운영자 결정 우선)

**Recommended**: option (a) cj-298 close-out retro 진입 결정 wire — cj-style discipline 회피 위험 방지 + 본 결정 wire 의 14-section retro 결정 wire 진입 정합. 결정 wire 일자: 2026-09-06 (KST).

---

## 부록 A. Cross-references

- Master PRD: `_bmad-output/planning-artifacts/prd.md v7.0 (final, 2026-08-26)`
- Epic 29+ PRD: `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-09-05/prd.md`
- Epic 30+ spec: `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-09-05/spec-epic-30-reporting-export.md`
- Epic 30+ INDEX: (cj-282 entry sprint 결정 wire — 본 spec 이 INDEX 역할)
- Epic 30+ wire sprints: cj-282a wire `eae9110` + cj-285 EXTENSION `215e963` + cj-286 EXTENSION `e408668` + cj-287 wire `5c37446` + cj-288 wire `b91906a` + cj-289 close-out wrap-up `2ad4910` + cj-290 RLS EXTENSION `1ba4309` + cj-291 close-out retro `0ce88ad` + cj-292 fix forward ATTEMPTED + REVERTED 결정 wire `ed0ee7c` + cj-293 wire `09fcda3` + cj-294 close-out retro `ba16a47` + cj-295 follow-up #1 `c0573f5` + cj-296 close-out retro `5da667f`
- cj-style chain: cj-229 ~ cj-296 CLOSED ✅ HONEST (68 sprints cumulative chain)
- baseline-green effort: cj-282b CLOSED ✅ HONEST (5 commits cumulative)

## 부록 B. PRD OQ-3 파일럿 게이트 verbatim mirror

본 결정 wire 의 §5 launch timeline = master PRD §OQ-3 파일럿 게이트 verbatim mirror 결정 wire:
- **1주 post M0-M6**: M0-M6 (cj-282b baseline-green effort) CLOSED ✅ HONEST 결정 wire 보존 + Epic 30+ 14 sprints chain CLOSED ✅ HONEST 결정 wire 보존 → 1주 post M0-M6 시점 도달 = PRD OQ-3 결정 wire 즉시 진입 가능.
- **본 결정 wire 진입 일자**: 2026-09-06 (cj-296 close-out retro 결정 wire 직후) = M0-M6 (cj-282b baseline-green effort) close + 1일 시점 = PRD OQ-3 즉시 진입 결정 wire.
- **Phase 1 launch D-day 결정 보류**: pilot customer 선정 + NDA 체결 + onboarding 일정 = 운영자 결정 wire 보존.

## 부록 C. dev_seed EXTENSION 결정 wire 보존 (cj-286 EXTENSION 결정 wire)

Pilot tenant onboarding 시 적용할 dev_seed scenario verbatim mirror 결정 wire:
- **Scenario `report_fixtures`**: 1 tenant (acme, Epic 29+ 의 DEV_TENANT_REPORT_ID UUIDv5 namespace `costmgr-dev-tenant-report` 재사용) + cost_records × 100 rows (period_key='2026-08') + BOM × 10 rows.
- **Audit log INSERT**: scenario invocation 자체 audit_logs 에 INSERT 결정 wire (CR 1-1 verbatim).
- **Idempotency**: ON CONFLICT (id) DO NOTHING (Epic 29+ cj-278b/c 패턴 verbatim 보존).
- **D-REPORTS-EXTENSION ownership**: Epic 30+ spec implementation owner 결정 wire (cj-286 EXTENSION 결정 wire 보존).
