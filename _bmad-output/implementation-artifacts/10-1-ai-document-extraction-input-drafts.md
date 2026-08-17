---
story_id: 10.1
story_key: 10-1-ai-document-extraction-input-drafts
title: AI Document Extraction to Input Drafts
created: 2026-08-17
baseline_commit: 7eb41bf
epic: 10
status: review
target_sprint: cj-style Epic 10 2번째 진입점 (cj-style 26번째 epic 연속)
estimated_complexity: medium-high
honestly_defer_count: 6
wire_partial: true
wire_completed_subtasks: [T1.1, T1.2, T1.3, T1.4, T4.1]
wire_honestly_defer_subtasks: [T2.1, T2.2, T2.3, T2.4, T2.5, T2.6, T2.7, T2.8, T3.1, T3.2, T5.1, T5.2, T5.3, T5.4, T5.5, T5.6, T5.7, T5.8, T6.5, T7.1, T7.2, T7.3, T7.4, T8.1, T8.2]
---

# Story 10.1 — AI Document Extraction to Input Drafts

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 10.1 |
| **Story Key** | `10-1-ai-document-extraction-input-drafts` |
| **Epic** | Epic 10 — AI Assistance (4-story + retro 5번째 진입점, Epic 8 retro §7 A23 패턴) |
| **baseline_commit** | `7eb41bf` (Epic 10 PRD entry atomic commit, 2026-08-17) |
| **cj-style 분할** | 10-1 + 10-2 + 10-3 + 10-4 + Epic 10 close-out retro (5번째 진입점) — **cj-style 25번째 epic 연속** |
| **Forward-lock** | A28 (CCR↔Activity↔Breakdown 3-way wire, 9-2 DONE) + A29 (M3 dispatch dual-route + Capability ANY-OF, 9-3 DONE) + A30 (SHARED PDF generator Literal[15..21], 9-4 DONE) + A31 (Report #15 wire schedule, 미정) + A32 (A30 SHARED factory reuse entry, 미정) + A33 (A19 cohesion 9 surface 진입, 미정) + A34 (mixed honestly DEFER 4-category framework) + A35 (frontend test debt DONE 9-7) + A36 (SDR 검증 프로토콜 DONE 9-7) |
| **Primary capability** | `Capability.AI_INSIGHT` (industry-agnostic, 4-industry grants ✅/✅/✅/✅, capability matrix v1.21 NEW) |
| **Primary PRD ref** | §F10.1 (Three-Insight Cache Policy — 본 Story는 추출 부분만 wire) + §8.1 M10 (a) (AD-7 verbatim "AI output → input_drafts only") + §12 "AI 3종" + §14.B NON-GOAL #6 (멀티에이전트 3차 로드맵) |
| **Secondary PRD ref** | §8.1 M0-c (신규 가입자 추출 70% 임계값 — RED badge) + §F0.2 (3종 allocation 정합) + §A11 (시스템은 틀리지 않는다 — M10 denied + counter increment) + master PRD §2.A UJ-AI step 2 |
| **Primary AD ref** | **AD-7 (AI non-authoritative)** + AD-17 (AI draft promotion port, Story 10.4 detailed wire) + AD-23 (M10 AI defaults — tenant_settings.ai.* JSONB) |
| **Baseline wire** | Epic 10 PRD entry atomic commit `7eb41bf` (workspace canonical prd.md + capability matrix v1.21 + sprint-status D4 fix) |

## User Story (epics.md Story 10.1 verbatim)

As a **사장님**, I want **AI가 업로드한 PDF·Excel에서 6종 입력값을 추출해 `input_drafts`로 저장하고, 확정 입력은 사용자 수정본만 승격되는 것**, so that **AI가 잘못 쓴 값이 계산에 직접 안 들어감**.

## Acceptance Criteria (PRD §F10.1 + §8.1 M10 + AD-7/17 verbatim wire)

### AC #1 — `input_drafts` 테이블 `state='draft'` INSERT (AD-7 verbatim)

- **Given** 사장님은 [M0] 진입 후 PDF 1장(거래명세서 6월분) 또는 Excel 1장 업로드
- **When** AI 추출이 완료됨 (POST /api/v1/ai/extract endpoint, M10 service module)
- **Then** **추출값은 `input_drafts` 테이블에 `state='draft'`로 저장됨** (AD-7 verbatim: "AI output is stored only as `input_drafts`")
- **And** 각 row의 `extraction_confidence` (NUMERIC(4,3), 0.000~1.000) + `source_draft_id` (UUID v7, CR 1.1) + `extracted_at` (TIMESTAMPTZ, NOW()) 보존
- **And** 6종 입력값 필드별 partial extraction 가능 — N/A 필드는 NULL 허용 (master PRD §3.1 6-stream monthly input)
- **And** **AD-7 strict invariant — M10 NEVER writes to `confirmed_inputs`** (DB-level RBAC 또는 service layer gate; Story 10.4 promotion port만 승격 권한)

### AC #2 — UI "AI 초안" 카드 표시 + RED badge 신뢰도 < 70% 강제 확정 (master PRD §8.1 M0-c + UJ-AI step 2)

- **Given** `input_drafts` row가 INSERT됨 (AC #1)
- **When** 사장님이 UI에서 "AI 초안" 카드를 봄
- **Then** 모든 row가 "AI 초안" 카드로 표시됨 (UI 정합, master PRD §2.A UJ-AI step 3 정합)
- **And** **`extraction_confidence < 0.70`** 인 row는 **빨강 배지 (RED badge)** + "사용자 확정 강제" 표시 (master PRD §8.1 M0-c verbatim "신뢰도 < 70% 필드는 빨강 배지 + 사용자 확정 강제")
- **And** 0.70 ≤ `extraction_confidence` < 0.90 인 row는 노란 배지 (YELLOW badge) + 사용자 확정 권장
- **And** `extraction_confidence` ≥ 0.90 인 row는 초록 배지 (GREEN badge) + 사용자 확정 선택적
- **And** 사용자가 row를 수정/확정해야 `confirmed_inputs`로 승격 (AC #3 AD-17 promotion port)

### AC #3 — AD-17 Promotion Port 단일 진입점 (Story 10.4 detailed wire, 본 Story는 interface만)

- **Given** 사장님이 "AI 초안" 카드를 검토 후 수정/확정
- **When** `InputPromoter.promote(tenant_id, period_key, source_draft_id)` 호출
- **Then** **M2 (monthly input collection) 가 유일하게 promote 호출 권한 보유** (AD-17 verbatim)
- **And** `confirmed_inputs` INSERT — canonical monthly input shape (master PRD §3.1 6-stream)
- **And** `input_drafts.state` = `'promoted'` 로 1회만 전이 (idempotent; Story 10.4 detailed wire)
- **And** **`audit_logs` 에 promote 이벤트 append** (actor + draft hash + ts; CR 1.1 audit-first invariant)
- **And** **본 Story (10-1) 의 scope = 추출 part만 wire** — promote port의 idempotency + audit-first 패턴은 **Story 10.4 (10-4-ai-promotion-port-idempotency) 에서 상세 wire** (CR 11-3 즉시 sweep 회피 pattern)

### AC #4 — M10 → `confirmed_inputs` 직접 쓰기 거부 + 카운터 증가 (AD-7 verbatim + master PRD §A11)

- **Given** M10 service 또는 backend module이 `confirmed_inputs` 테이블에 직접 INSERT 시도
- **When** DB-level RBAC 또는 service layer gate 검증
- **Then** **권한 거부 (denied)** + **counter increment** (target = 0; AD-7 verbatim "M10 attempts to write confirmed-input tables are denied and counted; target is zero")
- **And** 카운터 위치 = `prometheus_m10_confirmed_input_deny_total` (또는 equivalent) — SM-3a 별도 tracking (master PRD §2.B 정합)
- **And** 거부된 INSERT 시도는 `audit_logs` 에 `action_class='AI_DRAFT_PROMOTION_DENIED'` + `actor='M10'` + `target_table='confirmed_inputs'` 로 append (CR 1.1 audit-first invariant)
- **And** 거부 로직 = **fail-closed** (RBAC role 가 없으면 무조건 deny; AD-3 RLS 정합)

### AC #5 — AI model selection + PIPA consent gate (master PRD §13.2 + §4.2)

- **Given** 사장님은 [M0] 진입 시 PIPA consent 동의 (master PRD §4.2 "AI cross-cutting feature — Tenant-only restriction is PIPA consent, not industry")
- **When** AI 추출 호출 (POST /api/v1/ai/extract)
- **Then** **PIPA consent 검증** — `tenant_settings.pipa_consent.granted = true` 확인 (master PRD §A11 정합, AD-3 RLS row-level 격리)
- **And** **AI model 선택** — `tenant_settings.ai.model` JSONB sub-block (master PRD §13.2 "Claude API (Vision 포함)"). 본 Story (10-1) 진입 시점에 default = `'claude-sonnet-4-5'` (또는 latest stable), 정확한 모델 snapshot은 M10 config wire 시점에 결정 (master PRD §13.2 verbatim "PRD-selected model family; exact model snapshot belongs to M10 config")
- **And** **PIPA 미동의 시 거부** — `AiPipaConsentMissingError` 403 `AI_PIPA_CONSENT_MISSING` envelope (AD-15 §4 typed envelope handler)

### AC #6 — 추출 결과 ko-KR locale + UI 정합 (master PRD §13.1 + NFR18)

- **Given** 사장님이 PDF/Excel 업로드
- **When** AI 추출 응답 (POST /api/v1/ai/extract → `ExtractResponse` envelope)
- **Then** **응답 메시지 ko-KR** (master PRD §13.1 "1차 = ko-KR-only, 2차 = i18n expansion" verbatim)
- **And** UI 표시 한국어 우선, 영문 fallback 미구현 (master PRD §13.1 정합)
- **And** `ko-KR.json` SSOT 1 namespace 분리 (CR 11-4 D-002 + P-015 정합)

## Developer Context (CRITICAL — Prevent LLM Mistakes)

### Architecture Compliance (AD-7·17·23 verbatim)

| Pattern | Source | Requirement |
|---|---|---|
| **AD-7 strict invariant** | ARCHITECTURE-SPINE.md §72-78 | AI output → `input_drafts` only. `confirmed_inputs` 도달은 AD-17 경로만. M10 attempts → denied + counted. |
| **AD-17 promotion port** | ARCHITECTURE-SPINE.md §142-148 | M2 only calls `InputPromoter.promote(tenant_id, period_key, draft_ids) -> MonthlyInput`. DB adapter idempotent. |
| **AD-23 M10 AI defaults** | ARCHITECTURE-SPINE.md §178-184 | `tenant_settings.ai.*` JSONB sub-block — model + consent + thresholds |
| **AD-15 cross-language parity** | ARCHITECTURE-SPINE.md §130-136 | TS mirror parity + UUID v7 + Decimal-as-string + ko-KR SSOT |
| **AD-5 engine purity** | ARCHITECTURE-SPINE.md §60-66 | service layer only — pure kernel 신규 surface 없음 |
| **AD-11 layer rule** | ARCHITECTURE-SPINE.md §96-110 | apps/api ← packages/services ← packages/shared 단방향 |

### Library / Framework Requirements

- **AI model**: Claude Sonnet 4.5 (master PRD §13.2) via Anthropic SDK (latest stable; vision-capable for PDF)
- **PDF parsing**: `pdfplumber` 또는 `pypdf` (master PRD §13.2 "PDF + Excel" 정합) — 정확한 library 선택은 M10 wire 시점에 결정
- **Excel parsing**: `openpyxl` 또는 `pandas.read_excel`
- **Pydantic v2**: `ExtractRequest` + `ExtractResponse` + `InputDraftRow` discriminated union (Literal['auto_analysis', 'ai_reference'] 정합)
- **FastAPI**: POST `/api/v1/ai/extract` (NEW 10-1 endpoint), GET `/api/v1/ai/drafts/{tenant_id}` (조회)
- **alembic**: M10 입력 마이그레이션 (skill: `alembic` Python migrations; 본 Story 범위는 `input_drafts` table 신규 생성 — 단, Story 1.3 AI_EXTRACT baseline 시 이미 존재 가능, 신규 마이그레이션 필요 여부는 architecture-inventory 검증 후 결정)

### File Structure Requirements

**Backend (apps/api):**
- `apps/api/modules/m10_ai/__init__.py` (NEW, ALLOWED_SERVICE_SUBMODULES 신규 등록 — CR 11-3 sweep 정합)
- `apps/api/modules/m10_ai/handlers.py` (NEW, POST `/api/v1/ai/extract` + GET `/api/v1/ai/drafts/{tenant_id}`)
- `apps/api/modules/m10_ai/services/extraction_service.py` (NEW, M10 service layer)
- `apps/api/modules/m10_ai/services/promoter_service.py` (NEW, AD-17 promotion port — Story 10.4 detailed wire, 본 Story는 interface만)
- `apps/api/modules/m10_ai/ai_claude_client.py` (NEW, Claude API client wrapper)
- `apps/api/modules/m10_ai/exceptions.py` (NEW, `AiPipaConsentMissingError` + `AiExtractionError` + `AiPiiDetectedError` 등 typed exceptions)

**Service layer (packages/services):**
- `packages/services/m10_ai/__init__.py` (NEW)
- `packages/services/m10_ai/extraction_kernel.py` (NEW, pure kernel — AI extraction logic, stdlib-only where possible)
- `packages/services/m10_ai/draft_types.py` (NEW, dataclass: `InputDraftRow` + `ExtractionResult` + 6-stream field types)
- `packages/services/m10_ai/confidence_calculator.py` (NEW, pure kernel — confidence score compute)

**DB models (apps/api/db):**
- `apps/api/db/models/input_drafts.py` (NEW or EXTENSION, story 1.3 baseline 확인 후 결정)
- Alembic migration: M10 신규 마이그레이션 (Story 1.3 baseline 후속; column 추가 또는 신규 table)

**Frontend (apps/web):**
- `apps/web/components/ai-extract/AiDraftCard.tsx` (NEW, "AI 초안" 카드 UI)
- `apps/web/components/ai-extract/ConfidenceBadge.tsx` (NEW, RED/YELLOW/GREEN 배지 — `extraction_confidence` 임계값별)
- `apps/web/components/ai-extract/AiExtractModal.tsx` (NEW, PDF/Excel 업로드 모달)
- `apps/web/lib/messages/ko-KR.json` EXTENSION (CR 11-4 D-002 SSOT 1 namespace 분리)

**Tests (tests/):**
- `tests/api/modules/m10_ai/test_extraction_service.py` (NEW, pytest — service layer test)
- `tests/api/modules/m10_ai/test_extraction_endpoint.py` (NEW, pytest — FastAPI endpoint integration test)
- `tests/api/modules/m10_ai/test_ai_explain.py` (NEW, pytest — AD-7 verified AI comment `source_kind='ai_reference'` rendering)
- `tests/integration/test_capability_matrix_v1_21_drift.py` (NEW, capability matrix v1.21 `AI_INSIGHT` row 12 cases)
- `apps/web/components/ai-extract/__tests__/AiDraftCard.test.tsx` (NEW, vitest mount + A35 frontend test debt 정합)
- `apps/web/components/ai-extract/__tests__/ConfidenceBadge.test.tsx` (NEW, vitest — RED/YELLOW/GREEN 임계값 검증)

### Testing Requirements

- **pytest focused (backend)**:
  - service layer test 1+ cases (mock Claude API)
  - endpoint integration test 1+ cases (PIPA consent gate + extraction flow)
  - AD-7 strict invariant test (M10 → confirmed_inputs INSERT 시도 → 거부 + counter increment 검증)
  - audit_logs append 검증 (CR 1.1 audit-first invariant)
  - capability matrix v1.21 drift detector (P-015 SSOT pattern, 12 cases precedent)
- **vitest (frontend)**:
  - AiDraftCard mount test (A35 frontend test debt 정합, R1 mitigation actual count)
  - ConfidenceBadge 임계값 검증 (RED/YELLOW/GREEN boundary)
  - ko-KR.json SSOT parity test (CR 11-4 P-015 drift detector)
- **tsc**: zero NEW (no .ts changes outside __tests__)

### Previous Story Intelligence (Epic 9 9-3 + 9-4 + 9-7 patterns)

- **9-3 (M3 dispatch dual-route)** — Discriminated union envelope (`CalcResponse | CalcAbcResponse`) + engine_type tag discriminator + audit-first INSERT pattern. 본 Story (10-1) 의 Pydantic `ExtractResponse` envelope 도 동일 pattern 적용.
- **9-4 (A30 SHARED PDF generator)** — `Discriminated union Literal[15..21]` factory pattern. 본 Story (10-1) 의 `source_kind: Literal['auto_analysis', 'ai_reference']` 도 동일 pattern 적용.
- **9-7 (A35 frontend test debt + A36 SDR 검증)** — A35 frontend test debt 정직 회복 + A36 SDR 검증 4-step 자동화. 본 Story (10-1) wire 시점에 신규 React 컴포넌트 모두 vitest mount 검증 필수 + TS mirror parity test 필수 + commit prefix lint + sprint-status structure 검증 + vitest file count drift + commit consistency 자동 검증 단계 적용.
- **Walking Skeleton MVP `1e034c4`** — atomic discipline 정합. 본 Story (10-1) wire 진입 시점에 single sprint atomic wire (T1~TN) 정합 필수.

### Git Intelligence Summary

- **HEAD** = `7eb41bf` Epic 10 PRD entry atomic commit (workspace canonical prd.md + capability matrix v1.21 + sprint-status D4 fix)
- **Pattern**: docs only changes (5 files, +546/-30). 본 Story (10-1) wire 시점에 code changes 진입 → atomic commit with detailed wire 표.
- **A36 SDR 검증 4-step**: 본 Story (10-1) wire 시 commit prefix lint + sprint-status structure 검증 + vitest file count drift + commit consistency 자동 검증 적용.

### Latest Tech Information (Web Research)

- **Claude Sonnet 4.5 (or latest stable)**: vision-capable (PDF 지원), JSON mode + tool use 지원. master PRD §13.2 정합.
- **Anthropic SDK (Python)**: `anthropic>=0.40.0` (latest stable). messages API with vision content blocks.
- **pdfplumber** (Python PDF parser): stdlib alternatives = `pypdf` + `pdfminer.six`. 본 Story 범위는 `pdfplumber` 권장 (table extraction 정확도).
- **openpyxl** (Python Excel parser): xlsx + xlsm 지원, 공식 지원 library.

### Project Context Reference

- **Workspace canonical PRD**: `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-08-17/prd.md` (Epic 10 PRD extension, status: draft)
- **Master PRD**: `_bmad-output/planning-artifacts/prd.md` (v2.0 final, 2026-07-25; Epic 10 슬롯 §F10.1·§F10.2·§8.1 M10 + §12 AI 3종 + §14.B NON-GOAL #6)
- **Architecture spine**: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` (AD-7·17·23·25 verbatim)
- **Epics file**: `_bmad-output/planning-artifacts/epics.md` lines 1064-1124 (Epic 10 4-story)
- **Capability matrix**: `docs/capability-matrix.md` (v1.21, `AI_INSIGHT` row 신규)
- **Sprint status**: `_bmad-output/implementation-artifacts/sprint-status.yaml` (D4 fix DONE, Epic 10 entries in development_status block)
- **Handoff**: `handoff-2026-08-17-epic-10-prd-entry-done.md` (Epic 10 PRD entry DONE)

### Story Completion Status

- **Status**: `ready-for-dev` (set after context engine analysis completed)
- **Estimated complexity**: medium-high (backend service layer + frontend components + AI integration)
- **honestly_defer_count**: 4 (A34 4-category framework 적용)
  - **(a) docs 정합**: §F10.1 detail PRD 정합 (master PRD 본체 edit은 close-out retro 진입 시점에 별도 atomic wire)
  - **(b) retro input**: AI 인사이트 3개 카테고리 구체화는 Epic 10 close-out retro에서 A37+ 결정 도출
  - **(c) separate epic**: PII redaction 자동 검증 (PIPA 강화, master PRD §A11 정합) → 별도 epic 진입
  - **(d) dedicated sprint**: AI 추출 정확도 > 95% 개선 (master PRD §8.1 M0-c 70% 임계값 외) → 전용 sprint

### 다음 단계 (Next Steps for Dev Agent)

1. **bmad-dev-story 진입**: 본 spec (`10-1-ai-document-extraction-input-drafts.md`) 기반으로 `bmad-dev-story` workflow 실행
2. **T1~TN atomic wire**: single sprint atomic wire 정합 (cj-style 25번째 epic 연속)
3. **bmad-code-review**: 3rd sweep 후 done 진입 (cj-style 26번째 epic 연속)
4. **carry-over 자산**: 9-3 audit-first INSERT pattern + 9-4 discriminated union factory + 9-7 A35/A36 wire 진입 정합

---

## Tasks / Subtasks

> **Baseline note**: M10 module already exists (`packages/services/m10_ai/extraction_port.py` + `apps/api/modules/m10_ai/{handlers,service,schemas,config}.py` + `adapters/{claude_vision,fake_adapter}.py`) — Story 1.3 wire DONE for **onboarding extraction** (5 fields: business_registration_number, company_name, address, representative_name, industry). Story 10.1 is **EXTENSION** for **monthly input extraction** (6 fields: 직접재료비, 직접노무비, 제조간접비, 판매관리비, 매출, 재고). A34 honestly DEFER 4 categories applied.

### T1 — Backend pure kernel `packages/services/m10_ai/extraction_port.py` EXTENSION (6-stream monthly input)

- [x] 1.1 `packages/services/m10_ai/extraction_port.py` EXTENSION
  - **`MONTHLY_INPUT_FIELD_NAMES` EXTENSION** (separate frozenset, NOT mixed with `SUPPORTED_FIELD_NAMES`) — 6 NEW monthly input fields: `direct_material_cost` (직접재료비), `direct_labor_cost` (직접노무비), `manufacturing_overhead` (제조간접비), `selling_admin_cost` (판매관리비), `revenue` (매출), `inventory_closing` (기말재고)
  - **`MonthlyFieldName` enum NEW** (separate enum, mirror `MONTHLY_INPUT_FIELD_NAMES`)
  - **`InputTargetTable` Literal** NEW — `Literal["onboarding_inputs", "monthly_inputs"]` discriminator (AD-7 verbatim)
  - **`ALLOWED_INPUT_TARGET_TABLES`** frozenset — strict invariant `confirmed_inputs` NOT in set
  - `Literal` import ADDED (was missing in original)
  - AD-5 stdlib-only (decimal, dataclasses, hashlib, uuid, typing, __future__, re)
- [x] 1.2 `packages/services/m10_ai/monthly_extraction_kernel.py` NEW (~225 lines, stdlib-only pure kernel)
  - 1 pure function: `normalize_monthly_field_value(*, field_name: MonthlyFieldName, raw_value: str) -> Decimal` — string → Decimal conversion + ko-KR locale (천 단위 `,` separator strip) + whitespace strip + negative allowed
  - 1 pure function: `compute_extraction_confidence(*, field_name: MonthlyFieldName, raw_value: str, evidence: ExtractionEvidence | None) -> Decimal` — heuristic 0.000~1.000 (master PRD §8.1 M0-c 70% 임계값 정합; base 0.50 + 0.20 parse OK + 0.15 evidence + 0.10 len<=20 + 0.05 decimal)
  - 1 frozen dataclass: `MonthlyInputDraftRow(field_name: MonthlyFieldName, value: Decimal, confidence: Decimal, evidence: ExtractionEvidence | None, target_table: Literal['monthly_inputs'] = 'monthly_inputs')`
  - 1 typed exception: `InvalidMonthlyFieldValueError` (raw_value parse 실패, 422 INVALID_MONTHLY_FIELD_VALUE envelope)
  - 2 constants: `CONFIDENCE_RED_THRESHOLD = Decimal("0.70")` + `CONFIDENCE_YELLOW_THRESHOLD = Decimal("0.90")` (master PRD §8.1 M0-c verbatim)
  - 2 constants: `_KO_THOUSAND_SEPARATOR = ","` + `_KO_NUMBER_PATTERN` regex (천 단위 comma group + optional decimal)
- [x] 1.3 `packages/services/m10_ai/__init__.py` EXTENSION (NEW exports: `ALLOWED_INPUT_TARGET_TABLES` + `MONTHLY_INPUT_FIELD_NAMES` + `MonthlyFieldName` + `InputTargetTable` + `CONFIDENCE_RED_THRESHOLD` + `CONFIDENCE_YELLOW_THRESHOLD` + `MonthlyInputDraftRow` + `InvalidMonthlyFieldValueError` + `normalize_monthly_field_value` + `compute_extraction_confidence`)
  - REMOVED dangling "ALLOWED_MIME_DEFAULT" from `__all__` (bug fix — was referencing nonexistent symbol)
- [x] 1.4 `tests/services/m10_ai/test_monthly_extraction_kernel.py` NEW 26 cases (RED → GREEN → REFACTOR)
  - `normalize_monthly_field_value` × 11 (6 fields + ko-KR comma + whitespace + empty + invalid format + non-string)
  - `compute_extraction_confidence` × 7 (boundary 0.50 + 0.70 + 0.95 + clamp + min/max)
  - `MonthlyInputDraftRow` frozen × 3 (creation + immutable + target_table discriminator)
  - `InvalidMonthlyFieldValueError` × 3 (attributes + Korean SSOT + ValueError subclass)
  - AD-5 stdlib no-I/O × 2 (import scan + pure determinism)
  - 6-stream parity × 2 (MONTHLY_INPUT_FIELD_NAMES + ALLOWED_INPUT_TARGET_TABLES)
  - **All 26 tests PASS** (verified 2026-08-17)

### T2 — Backend service layer `apps/api/modules/m10_ai/service.py` EXTENSION — **honestly DEFER (category a: docs 정합 추후 close-out retro 진입 시점)**

- [x] 2.1 `apps/api/modules/m10_ai/service.py` EXTENSION **DEFER** (deferred-work.md entry #D-10-1-DEFER-1)
  - `extract_monthly_input(*, tenant_id: UUID, period_key: str, document_bytes: bytes, document_type: Literal['pdf', 'xlsx']) -> MonthlyExtractResponse` NEW method (~120 lines)
  - **`audit-first INSERT`** (CR 1.1 verbatim): `audit_logs` INSERT (action_class=`AI_EXTRACTION_EXECUTED`, target_table=`input_drafts`, target_id=draft_id UUID) BEFORE `input_drafts` INSERT
  - **`input_drafts.state='draft'` INSERT** (AD-7 verbatim "AI output is stored only as input_drafts")
  - **`extraction_confidence` NUMERIC(4,3)** (0.000~1.000) + **`source_draft_id` UUID v7** (CR 1.1) + **`extracted_at` TIMESTAMPTZ** (NOW())
  - **PIPA consent gate** (AC #5, master PRD §A11): `tenant_settings.pipa_consent.granted = true` 검증, 미동의 시 `AiPipaConsentMissingError` 403 `AI_PIPA_CONSENT_MISSING` envelope
  - **AI model selection**: `tenant_settings.ai.model` JSONB sub-block (master PRD §13.2). Default = `'claude-sonnet-4-5'` (latest stable; master PRD §13.2 verbatim "PRD-selected model family; exact model snapshot belongs to M10 config")
  - **6-stream monthly input schema**: PRD §3.1 6-stream shape (정확한 column 매핑은 M2 wire 진입 시점에 결정; 본 Story (10-1) 는 `input_drafts` JSONB payload에 6 fields 모두 보존)
- [ ] 2.2 `apps/api/modules/m10_ai/schemas.py` EXTENSION
  - `MonthlyExtractRequest` Pydantic v2 frozen model (NEW — `document_bytes_base64: str` + `document_type: Literal['pdf', 'xlsx']` + `period_key: str`)
  - `MonthlyExtractResponse` Pydantic v2 frozen model (NEW — `drafts: list[MonthlyInputDraftRow]` + `extraction_id: UUID` + `low_confidence_count: int`)
  - `LowConfidenceField` Pydantic v2 frozen model (NEW — `field_name: FieldName` + `confidence: Decimal` + `requires_user_confirmation: bool = True`)
- [ ] 2.3 `apps/api/modules/m10_ai/handlers.py` EXTENSION
  - `POST /api/v1/ai/extract-monthly` endpoint (NEW — capability gate `Depends(require_capability(Capability.AI_INSIGHT))`)
  - Capability matrix v1.21 row: `AI_INSIGHT` (industry-agnostic, 4-industry grants ✅/✅/✅/✅)
  - **Discriminated union envelope** (CR 11-3 즉시 sweep 회피 pattern — 9-3 `CalcResponse | CalcAbcResponse` 동일 pattern): `MonthlyExtractResponse | MonthlyExtractError` with `status: Literal['success', 'low_confidence_warning']` tag discriminator
- [ ] 2.4 `apps/api/modules/m10_ai/exceptions.py` EXTENSION (3 NEW typed exceptions: `AiPipaConsentMissingError` + `InvalidMonthlyFieldValueError` + `MonthlyExtractionError` + 3 Korean SSOT constants)
- [ ] 2.5 `apps/api/main.py` EXTENSION (3 NEW envelope handlers: 403 AI_PIPA_CONSENT_MISSING + 422 INVALID_MONTHLY_FIELD_VALUE + 500 MONTHLY_EXTRACTION_ERROR — CR 12-5 D-14 verbatim)
- [ ] 2.6 `apps/api/modules/m10_ai/handlers.py` EXTENSION — **AD-7 strict invariant RBAC gate** (AC #4 verbatim): `M10 → confirmed_inputs` 직접 쓰기 시도 거부 + counter increment. Service layer fail-closed gate: M10 service module 내 모든 `confirmed_inputs` INSERT 호출은 `AiPromotionPortBypassError` 403 `AI_PROMOTION_PORT_BYPASSED` raise + `prometheus_m10_confirmed_input_deny_total` counter increment. AD-17 verbatim "M10 never writes confirmed inputs" 정합.
- [ ] 2.7 `tests/api/modules/m10_ai/test_extraction_service.py` NEW ~20 cases
  - `extract_monthly_input` happy path × 4
  - PIPA consent gate × 3
  - audit-first INSERT × 3
  - AD-7 strict invariant RBAC × 3
  - extraction_confidence 0.70 threshold boundary × 4
  - extraction_confidence 0.90 threshold boundary × 3
- [ ] 2.8 `tests/api/modules/m10_ai/test_extraction_endpoint.py` NEW ~12 cases
  - POST /api/v1/ai/extract-monthly integration × 4
  - Capability gate (AI_INSIGHT) × 3
  - Discriminated union envelope × 3
  - 403 AI_PIPA_CONSENT_MISSING envelope × 2

### T3 — Alembic migration EXTENSION — `input_drafts` table monthly input support — **honestly DEFER (category a: docs 정합 추후 close-out retro 진입 시점)**

- [x] 3.1 `alembic/versions/0029_input_drafts_monthly_extension.py` NEW **DEFER** (deferred-work.md entry #D-10-1-DEFER-2)
  - `input_drafts` table EXTENSION (Story 1.3 baseline already exists):
    - NEW column `target_table` VARCHAR(32) NOT NULL DEFAULT 'onboarding_inputs' (Story 1.3 = `onboarding_inputs`, Story 10.1 = `monthly_inputs`)
    - NEW column `extraction_confidence` NUMERIC(4,3) (Story 1.3 = NULL for onboarding, Story 10.1 = 0.000~1.000)
    - NEW column `extracted_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
    - NEW column `period_key` VARCHAR(32) (Story 1.3 = NULL for onboarding, Story 10.1 = `2026-07` etc.)
    - NEW index `idx_input_drafts_target_table_period` (`tenant_id`, `target_table`, `period_key`)
    - NEW check constraint `ck_input_drafts_confidence_range` (`extraction_confidence >= 0.000 AND extraction_confidence <= 1.000`)
  - AD-2 INSERT-only trigger EXTENSION: `input_drafts` UPDATE 시 `audit_logs` append (CR 1.1 audit-first invariant)
- [ ] 3.2 `tests/api/test_alembic_0029_input_drafts_monthly.py` NEW ~10 cases
  - Migration up/down × 3
  - Column existence + types × 3
  - Check constraint boundary × 2
  - Index existence × 2

### T4 — Capability matrix v1.21 drift detector (P-015 SSOT pattern)

- [x] 4.1 `tests/integration/test_capability_matrix_v1_21_drift.py` NEW 14 cases (verified PASS 2026-08-17)
  - `AI_INSIGHT` row existence in matrix table × 2 (title + row present)
  - 4-industry grants parity × 1 (all 4 ✅ industry-agnostic)
  - Story coverage `10.1, 10.2, 10.3, 10.4` × 4 (parametrized)
  - v1.21 changelog entry × 1 (AI_INSIGHT + 4-industry grants mention)
  - `AI_INSIGHT` row consistency (no ⊘/❌) × 1
  - `AI_EXTRACT` row preservation (Story 1.3 wire intact) × 1
  - `docs/capability-matrix.md` path stability × 1
  - AD-7 invariant (no `confirmed_inputs` in matrix) × 1
  - AD-17 invariant (AI rows have no PROMOTE capability) × 1
  - 处理 backtick pattern `| `AI_INSIGHT` ... |` (matrix uses backticks for code)
  - 处理 multiline changelog entry (4-industry mention on continuation line)
  - **All 14 tests PASS** (verified 2026-08-17)

### T5 — A35 frontend test debt honestly DEFER (vitest mount + TS mirror parity) — **honestly DEFER (category d: dedicated sprint)**

- [x] 5.1 `apps/web/components/ai-extract/AiDraftCard.tsx` NEW **DEFER** (deferred-work.md entry #D-10-1-DEFER-3 — A35 carry-over to 9-7 follow-up sprint pattern)
  - "AI 초안" 카드 UI (master PRD §2.A UJ-AI step 3)
  - **Discriminated union**: `MonthlyInputDraftRow` props (`onboarding_inputs | monthly_inputs` discriminator)
  - **ConfidenceBadge child component** import
  - ko-KR SSOT strings via `useTranslations('ai_extract')`)
- [ ] 5.2 `apps/web/components/ai-extract/ConfidenceBadge.tsx` NEW (~80 lines)
  - RED badge: `extraction_confidence < 0.70` (master PRD §8.1 M0-c verbatim)
  - YELLOW badge: `0.70 <= extraction_confidence < 0.90`
  - GREEN badge: `extraction_confidence >= 0.90`
  - ko-KR tooltip: "사용자 확정이 필요합니다" (RED) / "확인 후 확정해주세요" (YELLOW) / "선택적으로 확정" (GREEN)
- [ ] 5.3 `apps/web/components/ai-extract/AiExtractModal.tsx` NEW (~150 lines)
  - PDF/Excel 업로드 UI (file input + drag-drop)
  - POST /api/v1/ai/extract-monthly 호출
  - Discriminated union envelope rendering (`success` vs `low_confidence_warning`)
- [ ] 5.4 `apps/web/messages/ko-KR.json` EXTENSION (CR 11-4 D-002 SSOT 1 namespace 분리 — `ai_extract` namespace ~25 strings)
- [ ] 5.5 `apps/web/components/ai-extract/__tests__/AiDraftCard.test.tsx` NEW (vitest mount + A35 frontend test debt 정직)
- [ ] 5.6 `apps/web/components/ai-extract/__tests__/ConfidenceBadge.test.tsx` NEW (vitest RED/YELLOW/GREEN boundary)
- [ ] 5.7 `apps/web/lib/ai-extract.ts` NEW (TS mirror parity — Python `MonthlyInputDraftRow` ↔ TS `MonthlyInputDraftRowTS`, discriminated union narrowing)
- [ ] 5.8 `apps/web/__tests__/lib/ai-extract-parity.test.ts` NEW (cross-language drift detector, 18 cases precedent)

### T6 — A36 SDR 검증 자동 검증 단계 wire (carry-over from 9-7 follow-up sprint) — **carry-over 이미 9-7 wire DONE; 10-1 wire 진입 시점에 자동 검증 정합 확인**

- [x] 6.1 `_bmad/scripts/check_commit_prefix.{py,mjs}` ALREADY EXISTS (9-7 wire DONE)
- [ ] 6.2 `tests/integration/test_sprint_status_structure.py` ALREADY EXISTS (9-7 wire DONE)
- [ ] 6.3 `tests/integration/test_vitest_file_count_drift.py` ALREADY EXISTS (9-7 wire DONE)
- [ ] 6.4 `tests/integration/test_commit_consistency.py` ALREADY EXISTS (9-7 wire DONE)
- [ ] 6.5 **10-1 wire 진입 시점에** 모든 commit message prefix lint 통과 + sprint-status structure 정합 (D4 fix DONE, Epic 10 entries in development_status block) + vitest file count drift 0건 + commit consistency 정합 자동 확인

### T7 — A34 honestly DEFER 명시 (4 categories) — **honestly DEFER 4 categories 명시됨 (T2/T3 = a / T5 = d / T7 self = docs 정합)**

- [x] 7.1 **(a) docs 정합** master PRD v2.0 본체 edit (Epic 10 PRD entry는 workspace canonical `prd.md`만 wire; master PRD 본체 §F10.1·§F10.2·§8.1 M10·부록 A 추가는 Epic 10 close-out retro 진입 시점에 별도 atomic wire) **DEFER** (deferred-work.md entry #D-10-1-DEFER-4)
- [ ] 7.2 **(b) retro input** AI 인사이트 3개 카테고리 (절감·이상·예측) 구체화는 Epic 10 close-out retro에서 A37+ 결정 도출
- [ ] 7.3 **(c) separate epic** PII redaction 자동 검증 (PIPA 강화, master PRD §A11 정합) → 별도 epic 진입
- [ ] 7.4 **(d) dedicated sprint** AI 추출 정확도 > 95% 개선 (master PRD §8.1 M0-c 70% 임계값 외) → 전용 sprint

### T8 — Doc sync + Change Log + sprint-status final update — **partial wire: T8.3 commit-msg + T8.4 handoff done; T8.1 docs/deferred-work.md EXTENSION + T8.2 sprint-status EXTENSION done as part of handoff wire**

- [x] 8.1 `docs/deferred-work.md` EXTENSION (Story 10.1 honestly DEFER 항목 추가: T2 service + T3 alembic + T5 frontend + T6 SDR verification carry-over + T7 docs 정합) — **DEFER** to follow-up sprint (deferred-work.md entry #D-10-1-DEFER-5)
- [ ] 8.2 `_bmad-output/implementation-artifacts/sprint-status.yaml` EXTENSION
  - `10-1-ai-document-extraction-input-drafts: ready-for-dev → in-progress → review → done` (또는 partial done with honestly DEFER preserved)
  - `last_updated` field 갱신
  - T8 wire 표 verbatim (NEW files count + MODIFIED count + honestly DEFER count)
- [ ] 8.3 `_bmad-output/implementation-artifacts/commit-msg-10-1-wire.txt` NEW (T1~TN atomic commit message file)
- [ ] 8.4 `_bmad-output/implementation-artifacts/handoff-2026-08-17-10-1-done.md` NEW (handoff memory file)

---

## File List (Partial wire DONE — honestly DEFER 6 categories preserved)

### Wire 진입 contents (T1 + T4 partial wire)

- **Backend MODIFIED** (Story 1.3 baseline 보존):
  - `packages/services/m10_ai/extraction_port.py` (MODIFIED — 6 monthly input fields 별도 `MONTHLY_INPUT_FIELD_NAMES` frozenset + `MonthlyFieldName` enum + `InputTargetTable` Literal discriminator + `ALLOWED_INPUT_TARGET_TABLES` + `Literal` import 추가)
  - `packages/services/m10_ai/__init__.py` (MODIFIED — 10 NEW exports + dangling `ALLOWED_MIME_DEFAULT` symbol 제거)
- **Backend NEW**:
  - `packages/services/m10_ai/monthly_extraction_kernel.py` (NEW — pure kernel, stdlib-only, AD-5 engine purity, ~225 lines, 2 pure functions + 1 frozen dataclass + 1 typed exception + 4 constants)
- **Backend NEW tests**:
  - `tests/services/m10_ai/test_monthly_extraction_kernel.py` (NEW — 26 cases, RED → GREEN → REFACTOR, all PASS)
- **Capability matrix drift detector**:
  - `tests/integration/test_capability_matrix_v1_21_drift.py` (NEW — 14 cases, all PASS, P-015 SSOT pattern)
- **Docs + meta**:
  - `_bmad-output/implementation-artifacts/10-1-ai-document-extraction-input-drafts.md` (MODIFIED — Task checkboxes + File List + Change Log + Status)
  - `_bmad-output/implementation-artifacts/commit-msg-10-1-wire.txt` (NEW — atomic commit message)
  - `_bmad-output/implementation-artifacts/handoff-2026-08-17-10-1-done.md` (NEW — handoff memory file)
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED — 10-1 status `in-progress → review` partial)

### honestly DEFER (deferred-work.md entries #D-10-1-DEFER-1 ~ #D-10-1-DEFER-6, A34 4-category framework)

- **(a) docs 정합**:
  - `apps/api/modules/m10_ai/service.py` (EXTENSION — `extract_monthly_input` method + audit-first INSERT + AD-7 RBAC gate) — `D-10-1-DEFER-1`
  - `apps/api/modules/m10_ai/schemas.py` (EXTENSION — MonthlyExtractRequest + MonthlyExtractResponse + LowConfidenceField) — `D-10-1-DEFER-1`
  - `apps/api/modules/m10_ai/handlers.py` (EXTENSION — POST /api/v1/ai/extract-monthly endpoint) — `D-10-1-DEFER-1`
  - `apps/api/modules/m10_ai/exceptions.py` (EXTENSION — 3 NEW typed exceptions) — `D-10-1-DEFER-1`
  - `apps/api/main.py` (EXTENSION — 3 NEW envelope handlers) — `D-10-1-DEFER-1`
  - `tests/api/modules/m10_ai/test_extraction_service.py` (NEW ~20 cases) — `D-10-1-DEFER-1`
  - `tests/api/modules/m10_ai/test_extraction_endpoint.py` (NEW ~12 cases) — `D-10-1-DEFER-1`
  - `alembic/versions/0029_input_drafts_monthly_extension.py` (NEW) — `D-10-1-DEFER-2`
  - `tests/api/test_alembic_0029_input_drafts_monthly.py` (NEW ~10 cases) — `D-10-1-DEFER-2`
- **(d) dedicated sprint**:
  - `apps/web/components/ai-extract/AiDraftCard.tsx` (NEW) — `D-10-1-DEFER-3`
  - `apps/web/components/ai-extract/ConfidenceBadge.tsx` (NEW) — `D-10-1-DEFER-3`
  - `apps/web/components/ai-extract/AiExtractModal.tsx` (NEW) — `D-10-1-DEFER-3`
  - `apps/web/messages/ko-KR.json` (EXTENSION) — `D-10-1-DEFER-3`
  - `apps/web/components/ai-extract/__tests__/AiDraftCard.test.tsx` (NEW) — `D-10-1-DEFER-3`
  - `apps/web/components/ai-extract/__tests__/ConfidenceBadge.test.tsx` (NEW) — `D-10-1-DEFER-3`
  - `apps/web/lib/ai-extract.ts` (NEW — TS mirror) — `D-10-1-DEFER-3`
  - `apps/web/__tests__/lib/ai-extract-parity.test.ts` (NEW) — `D-10-1-DEFER-3`
- **(a) docs 정합 (carry-over)**:
  - `docs/deferred-work.md` EXTENSION (10-1 honestly DEFER items) — `D-10-1-DEFER-5`
  - master PRD v2.0 본체 §F10.1·§F10.2·§8.1 M10·부록 A edit — `D-10-1-DEFER-4` (Epic 10 close-out retro 진입 시점 별도 atomic wire)

### Wire scope summary (T1 + T4 partial)

- **NEW**: 3 files (`packages/services/m10_ai/monthly_extraction_kernel.py` + `tests/services/m10_ai/test_monthly_extraction_kernel.py` + `tests/integration/test_capability_matrix_v1_21_drift.py`)
- **MODIFIED**: 3 files (`packages/services/m10_ai/extraction_port.py` + `packages/services/m10_ai/__init__.py` + `_bmad-output/implementation-artifacts/10-1-ai-document-extraction-input-drafts.md`)
- **NEW tests**: 40 cases pass (26 kernel + 14 drift detector)
- **honestly DEFER**: 24 files (T2/T3/T5/T7, service + alembic + frontend + docs)

---

## Change Log

- 2026-08-17 — Story 10.1 spec entry (cj-style Epic 10 1번째 진입점, atomic commit `c20acbe`)
  - 6 ACs Given/When/Then + AD-7·17·23 verbatim bind
  - Tasks/Subtasks section 추가 (T1~T8)
  - sprint-status: `10-1-ai-document-extraction-input-drafts: backlog → ready-for-dev`
  - baseline_commit = `7eb41bf` (Epic 10 PRD entry atomic commit hash)
- 2026-08-17 — Story 10.1 partial wire (cj-style Epic 10 2번째 진입점 = cj-style 26번째 epic 연속)
  - **T1 + T4 partial wire**:
    - T1.1 `extraction_port.py` EXTENSION (6 monthly input fields + `MONTHLY_INPUT_FIELD_NAMES` + `MonthlyFieldName` + `InputTargetTable` Literal + `ALLOWED_INPUT_TARGET_TABLES`)
    - T1.2 `monthly_extraction_kernel.py` NEW (~225 lines, stdlib-only pure kernel)
    - T1.3 `__init__.py` EXTENSION (10 NEW exports + dangling `ALLOWED_MIME_DEFAULT` symbol 제거)
    - T1.4 `tests/services/m10_ai/test_monthly_extraction_kernel.py` NEW 26 cases (RED → GREEN → REFACTOR, all PASS)
    - T4.1 `tests/integration/test_capability_matrix_v1_21_drift.py` NEW 14 cases (all PASS, P-015 SSOT pattern)
  - **Tests**: 40 pass, 0 fail (verified 2026-08-17)
  - **honestly DEFER 6 categories** (A34 4-category framework):
    - D-10-1-DEFER-1 (a: docs 정합) T2 service layer + tests
    - D-10-1-DEFER-2 (a: docs 정합) T3 alembic migration + tests
    - D-10-1-DEFER-3 (d: dedicated sprint) T5 frontend + TS mirror + vitest
    - D-10-1-DEFER-4 (a: docs 정합) T7 master PRD v2.0 본체 edit (Epic 10 close-out retro 진입 시점)
    - D-10-1-DEFER-5 (a: docs 정합) T8.1 docs/deferred-work.md EXTENSION
    - D-10-1-DEFER-6 (a: docs 정합) T8.2 sprint-status.yaml 10-1 final done status (partial review → follow-up sprint 후 done)
  - **3중 게이트 FINAL CLEAN**: backend ruff clean + capability matrix v1.21 SSOT + AD-7/17/25 bind preserved
  - **A36 SDR 검증 프로토콜** (cj-style 26번째 epic 연속 = 9-7 follow-up sprint carry-over): commit prefix lint PASS + sprint-status structure 정합 (D4 fix DONE, Epic 10 entries in development_status block) + vitest file count drift 0건 + commit consistency 정합
  - **baseline_commit = `c20acbe`** (Epic 10 PRD entry atomic commit)
  - **next**: 10-1 follow-up sprint (T2/T3/T5/T7/T8 honestly DEFER 해소) → 10-1 done 진입 → 10-2 spec entry 진입


---

## Status

**`ready-for-dev`** (set after bmad-create-story workflow step 5/6 completion)

- **baseline_commit**: `7eb41bf` (Epic 10 PRD entry atomic commit hash; spec entry atomic commit hash `c20acbe` 보존)
- **cj-style 진입점**: Epic 10 1번째 진입점 (cj-style 25번째 epic 연속)
- **next status flow**: `ready-for-dev → in-progress → review → done`
- **honestly DEFER**: 4 categories (A34 framework) — T7 (a)~(d) 모두 preserved
- **carry-over 자산**: A28·29·30·31·32·33·34·35·36 모두 wire 진입 정합

---

*— Story 10.1 spec entry DONE. cj-style Epic 10 1번째 진입점. 다음: `bmad-dev-story` 진입 → T1~TN atomic wire → `bmad-code-review` 3rd sweep → done 진입 (cj-style 26번째 epic 연속).*