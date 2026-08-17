---
story_id: 10.1
story_key: 10-1-ai-document-extraction-input-drafts
title: AI Document Extraction to Input Drafts
created: 2026-08-17
baseline_commit: 7eb41bf
epic: 10
status: ready-for-dev
target_sprint: cj-style Epic 10 1번째 진입점 (cj-style 25번째 epic 연속)
estimated_complexity: medium-high
honestly_defer_count: 4
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

*— Story 10.1 spec entry DONE. cj-style Epic 10 1번째 진입점. 다음: `bmad-dev-story` 진입.*