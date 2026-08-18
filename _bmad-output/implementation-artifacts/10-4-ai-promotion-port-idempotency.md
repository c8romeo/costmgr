---
story_id: 10.4
story_key: 10-4-ai-promotion-port-idempotency
title: AI Promotion Port Idempotency
created: 2026-08-18
baseline_commit: ea025b1
epic: 10
status: ready-for-dev
target_sprint: cj-style Epic 10 5번째 진입점 (cj-style 33번째 epic 연속)
estimated_complexity: medium
honestly_defer_count: 5
wire_partial: false
---

# Story 10.4 — AI Promotion Port Idempotency

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 10.4 |
| **Story Key** | `10-4-ai-promotion-port-idempotency` |
| **Epic** | Epic 10 — AI Assistance (4-story + retro 5번째 진입점, Epic 8 retro §7 A23 패턴) |
| **baseline_commit** | `ea025b1` (Story 10.3 3rd sweep DONE atomic commit, cj-style 32번째 epic 연속 = current HEAD) |
| **cj-style 분할** | 10-4 (5번째 = 마지막) — **cj-style 33번째 epic 연속** |
| **Forward-lock** | A28 (9-2 DONE) + A29 (9-3 DONE) + A30 (9-4 DONE) + A31 (Report #15 wire schedule) + A32 (A30 SHARED factory reuse) + A33 (A19 cohesion 9 surface) + A34 (mixed honestly DEFER 4-category framework) + A35 (frontend test debt DONE 9-7) + A36 (SDR 검증 프로토콜 DONE 9-7) |
| **Primary capability** | `Capability.AI_INSIGHT` (industry-agnostic, 4-industry grants ✅/✅/✅/✅, capability matrix v1.21 — Story 10.1 wire 진입; 10.4 spec 진입 시점에 동일 capability 보존 + 10.4 story coverage reference append — capability matrix drift test regex 이미 4-story reference 검증: `r"\|\s*\`?AI_INSIGHT\`?\s*\|\s*10\.[1234](?:\s*,\s*10\.[1234])*\s*\|"`) |
| **Primary PRD ref** | **epics.md Story 10.4 (lines 1113-1125)** verbatim + master PRD §F10.2-(f) (승격 포트 멱등성) + master PRD §8.1 M10 promotion port + canonical PRD §4 Story 10.4 (lines 179-194) + canonical PRD §5.1 AD-17 (line 205) + canonical PRD §5.3 NFR8 (line 232) + canonical PRD §6.1 capability matrix v1.21 AI_INSIGHT story_coverage append "10-4" |
| **Secondary PRD ref** | master PRD §F10.2 (a)~(e) carry-over (10-3 forward-bind) + master PRD §A11 (시스템은 틀리지 않는다) + master PRD §SM-3a (계산 결과 변경 시도 = 0건) + master PRD §AD-7 strict invariant + master PRD §AD-17 verbatim rule |
| **Primary AD ref** | **AD-17 (InputPromoter promotion port — `InputPromoter.promote(tenant_id, period_key, source_draft_id) -> MonthlyInput`, idempotent on `(tenant_id, period_key, source_draft_id)`, only M2 may call, M10 never writes confirmed inputs, DB adapter implements, audit-first INSERT 2행 append with actor + draft hash + ts)** + AD-7 (M10 attempts to write `confirmed_inputs` → denied + counted target 0, 10-4 wire 진입 시점에 `monthly_extraction_promote_denied` 카운터 wire) + AD-25 (cache invalidation 보존 — promote 시 AD-25 invalidation publisher publish 0건, 10-4 wire 진입 시점에는 promote 자체는 invalidation trigger 안 함, reversal은 Epic 11 forward-fill) |
| **Baseline wire** | Story 10.1 atomic sprint wire commit `809a081` (cj-style 28번째) + Story 10.2 atomic sprint wire commit `5dc287c` (cj-style 29번째) + Story 10.3 atomic sprint wire commit `ea025b1` (cj-style 32번째 = current HEAD). 10-1 = 4 NEW (alembic 0029 + 3 test files) + 5 MODIFIED source + 1 MODIFIED spec, 88 PASS + 4 skipped. 10-2 = 6 NEW + 10 MODIFIED + 1 spec doc = 17 files, 84 PASS. 10-3 = 13 NEW + 5 MODIFIED source + 4 NEW test files + 4 MODIFIED docs, 74 PASS, 6 honestly DEFER preserved (D-10-3-DEFER-1~6). |

## User Story (epics.md Story 10.4 verbatim)

As a **platform engineer**, I want **`InputPromoter.promote()`가 `(tenant_id, period_key, source_draft_id)` 단위로 idempotent인 것**, so that **중복 승격으로 인한 입력 중복이 안 생김** (master PRD §F10.2-(f) verbatim + AD-17 verbatim).

## Acceptance Criteria (epics.md Story 10.4 AC verbatim + PRD §AD-17 + AD-7 strict invariant + D-10-3-DEFER-6 PIPA gate carry-over)

### AC #1 — `InputPromoter.promote()` 단일 진입점 + M2-only authorization (AD-17 verbatim + master PRD §8.1 M10 promotion port)

- **Given** 사장님이 [M2] 진입 → "AI 초안" 카드 (10-1 wire) 검토 후 수정/확정
- **When** `InputPromoter.promote(tenant_id, period_key, source_draft_id)` 호출
- **Then** **M2 (monthly input collection) 가 유일하게 promote 호출 권한 보유** (AD-17 verbatim "only M2 may call `InputPromoter.promote()`"; 10-1 wire 보존, AC #3 detailed)
- **And** `confirmed_inputs` (= `monthly_input_rows` table) INSERT — canonical 6-stream shape (master PRD §3.1 6-stream: 직접재료비/직접노무비/제조간접비/판매관리비/매출/기말재고) from `input_drafts.confirmed_value` JSONB (10-1 wire의 user-reviewed value)
- **And** `input_drafts.state` = `'promoted'` 로 전이 (1회만, idempotent; AC #2 상세)
- **And** **`audit_logs` 에 promote 이벤트 2행 append** (actor + draft hash + ts; CR 1.1 audit-first INSERT 정합):
  - **Row 1**: `action_class='INPUT_DRAFT'`, `action='input_draft_promoted'` (NEW 10-4 wire), `actor_id=user_id`, `target_id=source_draft_id`, `reason={tenant_id, period_key, draft_hash}`, `payload={trace_id, source_table='input_drafts', target_table='monthly_input_rows', confirmed_value_hash}`
  - **Row 2**: `action_class='AI_EXTRACTION_EXECUTED'`, `action='monthly_extraction_promote_executed'` (NEW 10-4 wire, `monthly_extraction_promote_denied` 10-1 forward-fill slot 옆), `actor_id=user_id`, `target_id=confirmed_inputs_row_id`, `reason={tenant_id, period_key, source_draft_id, draft_hash}`, `payload={trace_id, promotion_unix_ts}`
- **And** 본 Story (10-4) 진입 시점에 **M10 NEVER writes `confirmed_inputs` (= `monthly_input_rows`) table** (AD-7 verbatim + 10-1 wire `target_table` discriminator 보존; `target_table='monthly_inputs'` discriminator ALLOWED_INPUT_TARGET_TABLES 보존, `'confirmed_inputs'` 추가 0건)

### AC #2 — Idempotency on `(tenant_id, period_key, source_draft_id)` (AD-17 verbatim + epics.md Story 10.4 AC verbatim)

- **Given** 같은 `source_draft_id` 에 대해 `InputPromoter.promote()` 호출 2회 (e.g., M2 retried HTTP request + network timeout + client retry pattern)
- **When** 2번째 호출
- **Then** **1번째와 동일한 `monthly_input_rows` 결과 반환** (no duplicate INSERT; AD-17 verbatim "Idempotent on `(tenant_id, period_key, source_draft_id)`")
- **And** `input_drafts.state` 는 `'promoted'` 그대로 (1회만 전이; 2번째 호출은 `state='promoted'` SELECT 후 동일 결과 반환)
- **And** 2번째 호출도 `audit_logs` 2행 append (CR 1.1 audit-first verbatim — 호출 자체를 audit; 단 INSERT 자체는 skip; `payload={idempotent_replay: true, trace_id, replay_of_trace_id: <1st_trace_id>}`)
- **And** **`monthly_input_promotions` UNIQUE constraint** `uq_monthly_input_promotions_tenant_period_draft` (`tenant_id`, `period_key`, `source_draft_id`) — DB-level idempotency guard (10-4 wire entry)
- **And** **`input_drafts.state` CHECK constraint EXTENSION** — 기존 `state IN ('draft', 'reviewed', 'superseded')` 에 `'promoted'` 추가 → `state IN ('draft', 'reviewed', 'superseded', 'promoted')` (10-4 wire entry, alembic 0032)

### AC #3 — M10 → `monthly_input_rows` 직접 쓰기 거부 + 카운터 증가 (AD-7 verbatim + 10-1 AC #4 forward-bind + `monthly_extraction_promote_denied` 카운터 wire)

- **Given** M10 service 또는 backend module이 `monthly_input_rows` (= `confirmed_inputs` per master PRD §AD-7) 테이블에 직접 INSERT 시도 (e.g., M10 extraction service 가 실수로 `monthly_input_rows` 를 INSERT 시도하는 회귀)
- **When** DB-level RBAC 또는 service-layer gate 검증
- **Then** **권한 거부 (denied)** + **counter increment** (`audit_logs` row INSERT `action='monthly_extraction_promote_denied'` count derive; target = 0; AD-7 verbatim "M10 attempts to write confirmed-input tables are denied and counted; target is zero" + 10-1 AC #4 forward-bind)
- **And** 거부 로직 = **fail-closed** (RBAC role 가 없으면 무조건 deny; AD-3 RLS 정합; 10-1 wire 보존)
- **And** 거부된 INSERT 시도는 `audit_logs` 에 `action_class='AI_EXTRACTION_EXECUTED'`, `action='monthly_extraction_promote_denied'`, `actor='M10'`, `target_table='monthly_input_rows'` 로 append (CR 1.1 audit-first invariant; 10-1 wire `AIExtractionAction` Literal 의 `monthly_extraction_promote_denied` 슬롯 wire)
- **And** 거부 envelope = `422 INPUT_PROMOTION_DENIED` + `message_ko: "M10 모듈은 confirmed_inputs 테이블에 직접 쓸 수 없습니다. InputPromoter.promote() 만 사용하세요."` (master PRD §13.1 ko-KR-only + CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`)

### AC #4 — Capability gate (matrix v1.21) + PIPA consent gate (D-10-3-DEFER-6 carry-over) + audit-first (CR 1.1 + AD-15)

- **Given** M2 가 `POST /api/v1/ai/promote` 호출 (NEW 10-4 endpoint, JSON body `{tenant_id, period_key, source_draft_id, confirmed_value_hash: str | None}` — confirmed_value_hash 는 optional integrity check 용)
- **When** 핸들러 진입
- **Then** **Capability gate** `Depends(require_capability(Capability.AI_INSIGHT))` (capability matrix v1.21 — Story 10.1 wire 보존, industry-agnostic 4-industry grants ✅/✅/✅/✅, A36 SDR 검증 자동 검증 단계 wire — capability matrix drift test regex 이미 `10.[1234]` reference 검증: 통과)
- **And** **PIPA consent gate** `Depends(require_pipa_review)` (master PRD §A11 + AD-3 RLS 정합 — **D-10-3-DEFER-6 carry-over 해소**; PIPA 미동의 시 `AiPipaConsentMissingError` 403 `AI_PIPA_CONSENT_MISSING` envelope (CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`, 10-1 wire 보존)
- **And** **M2-only authorization check** (AD-17 verbatim) — `Depends(require_m2_service_role)` helper (NEW 10-4 wire; caller role 검증; service_role bypass 시 audit-first INSERT `action='service_role_bypass'` from 10-1 carry-over)
- **And** **audit-first INSERT** (CR 1.1 verbatim "audit_logs INSERT BEFORE monthly_input_rows write"): `audit_logs` row 1 INSERT (action_class=`INPUT_DRAFT`, action=`input_draft_promoted`, actor_id=user_id, target_id=source_draft_id, reason=`{tenant_id, period_key, draft_hash}`, payload=`{trace_id, idempotent_replay: false}`) — BEFORE `monthly_input_rows` INSERT OR `input_drafts.state` UPDATE

### AC #5 — Discriminated union envelope + CR 12-5 D-14 verbatim + AD-15 cross-language parity

- **Given** `POST /api/v1/ai/promote` 호출 결과 (성공 OR 에러)
- **When** response 형성
- **Then** **Discriminated union envelope** `PromoteResponse | PromoteDraftImmutableError | PromoteSourceDraftNotFoundError | PromoteIdempotencyMismatchError | AiPipaConsentMissingError` with `status: Literal['success', 'draft_immutable', 'source_draft_not_found', 'idempotency_mismatch', 'pipa_consent_missing']` tag discriminator (CR 12-5 D-13 cross-language parity + 10-2 `InsightListResponse | InsightCacheError` + 10-3 `AICommentListResponse | AICommentSourceKindInvalidError` 패턴 미러)
- **And** **Success envelope** `PromoteResponse`:
  - `status: Literal['success']`
  - `tenant_id: UUID` (response body — client echo)
  - `period_key: str` (response body)
  - `source_draft_id: UUID` (echo)
  - `confirmed_input_row_id: UUID` (NEW row id when fresh insert; existing row id when idempotent replay — both 동일 shape)
  - `promoted_at: datetime` (timezone-aware ISO 8601)
  - `draft_hash: bytes` (32-byte SHA-256 of source draft's canonical JSON)
  - `idempotent_replay: bool` (`false` when fresh INSERT; `true` when 2nd call replay — caller disambiguation)
  - `audit_log_ids: tuple[UUID, UUID]` (2 audit_log row ids from CR 1.1 audit-first INSERT — caller forensic trace)
- **And** Error envelopes (CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`):
  - 403 `AI_PIPA_CONSENT_MISSING` (D-10-3-DEFER-6 carry-over 해소; 10-1 wire 보존)
  - 403 `INPUT_PROMOTION_M2_ONLY` (AD-17 verbatim — M2 외 caller 거부; 10-4 NEW)
  - 404 `PROMOTE_SOURCE_DRAFT_NOT_FOUND` (`source_draft_id` 가 해당 tenant 에 존재하지 않음)
  - 409 `PROMOTE_DRAFT_IMMUTABLE` (`input_drafts.state='superseded'` — 이미 superseded 된 draft 는 promote 불가; AD-2 append-only 정합)
  - 422 `PROMOTE_IDEMPOTENCY_MISMATCH` (같은 `(tenant_id, period_key, source_draft_id)` 인데 다른 `confirmed_value_hash` 로 호출 — replay 가 아닌 mismatch)
  - 422 `INPUT_PROMOTION_DENIED` (M10 이 `monthly_input_rows` 직접 INSERT 시도 거부; AD-7 verbatim)
- **And** TS mirror parity: Python `PromoteResponse` ↔ TS `PromoteResponseTS` (Discriminated union narrowing, `apps/web/lib/ai-promote.ts` **honestly DEFER (d) frontend dedicated sprint** — A35 frontend test debt 정합)
- **And** AD-15 cross-language parity SSOT: `PROMOTE_STATUS_VALUES = frozenset({'success', 'draft_immutable', 'source_draft_not_found', 'idempotency_mismatch', 'pipa_consent_missing'})` (10-4 kernel NEW; TS mirror parity test wire — **honestly DEFER (d)**)

### AC #6 — Pure kernel stdlib-only + AD-5 engine purity + A19 cohesion 8 surface

- **Given** `InputPromoter.promote()` 호출 시 service layer 진입
- **When** pure kernel 실행
- **Then** **`InputPromoter.promoter_port` pure kernel stdlib-only** (AD-5 verbatim): `packages/services/m10_ai/promoter_port.py` (NEW) — `InputPromoterPort` Protocol + `PromotionResult` frozen dataclass + `PromotionRequest` frozen dataclass + `PROMOTE_STATUS_VALUES` frozenset + `compute_promotion_idempotency_key()` stdlib-only pure function + `validate_promotion_request()` stdlib-only pure function (no I/O, no clock, no random — `promoted_at` 은 caller 주입)
- **And** **DB adapter implements the port** (AD-17 verbatim "DB adapter implements it"): `apps/api/modules/m10_ai/adapters/db_promoter_adapter.py` (NEW) — `DbPromoterAdapter` class satisfying `InputPromoterPort` Protocol via `AsyncSession` (DB I/O lives here, port stays pure)
- **And** **A19 cohesion pattern 8 surface PASS** (kernel + port + db schema + service + handler + envelope + capability + audit, 10-1 PASS + 10-2 PASS + 10-3 PASS 패턴 미러):
  1. **Kernel** (surface 1) — `packages/services/m10_ai/promoter_port.py` NEW
  2. **Port** (surface 2) — `InputPromoterPort` Protocol in kernel
  3. **DB schema** (surface 3) — alembic 0032 NEW (input_drafts.state CHECK EXTENSION + monthly_input_promotions UNIQUE constraint + audit_logs CHECK EXTENSION)
  4. **Service** (surface 4) — `apps/api/modules/m10_ai/services/promoter_service.py` NEW + ORM→kernel boundary (CR 12-1 L3 verbatim pattern: typed mapping + UUID cast + datetime cast)
  5. **Handler** (surface 5) — `apps/api/modules/m10_ai/handlers.py` MODIFIED — `POST /api/v1/ai/promote` endpoint NEW + capability gate + PIPA gate + M2-only authorization + audit-first INSERT
  6. **Envelope** (surface 6) — `apps/api/modules/m10_ai/schemas.py` MODIFIED — `PromoteResponse | PromoteDraftImmutableError | PromoteSourceDraftNotFoundError | PromoteIdempotencyMismatchError` Discriminated union NEW + `apps/api/main.py` MODIFIED — 5 NEW envelope handlers (403 AI_PIPA_CONSENT_MISSING carry-over + 403 INPUT_PROMOTION_M2_ONLY NEW + 404 PROMOTE_SOURCE_DRAFT_NOT_FOUND NEW + 409 PROMOTE_DRAFT_IMMUTABLE NEW + 422 PROMOTE_IDEMPOTENCY_MISMATCH NEW + 422 INPUT_PROMOTION_DENIED NEW)
  7. **Capability** (surface 7) — `tests/integration/test_capability_matrix_v1_21_drift.py` MODIFIED — `AI_INSIGHT` row story_coverage regex already matches `10.1, 10.2, 10.3, 10.4` (자동 PASS); `docs/capability-matrix.md` MODIFIED — `AI_INSIGHT` row story_coverage append "10-4" (verbatim PRD §6.1 line 252-253 정합)
  8. **Audit** (surface 8) — `apps/api/core/audit_action.py` MODIFIED — `InputDraftAction` Literal EXTENSION (`input_draft_promoted` 1 NEW value, 기존 2 → 3 values) + `AIExtractionAction` Literal EXTENSION (`monthly_extraction_promote_executed` 1 NEW value, 기존 3 → 4 values) + `_ActionRegistry` EXTENSION + `AuditAction` union EXTENSION + `__all__` EXTENSION

## Developer Context (CRITICAL — Prevent LLM Mistakes)

### Architecture Compliance (AD-7 + AD-17 verbatim + AD-5 + AD-15 + AD-22 forward-bind)

| Pattern | Source | Requirement |
|---|---|---|
| **AD-17 promotion port verbatim** | ARCHITECTURE-SPINE.md §142-148 | only M2 may call `InputPromoter.promote(tenant_id, period_key, source_draft_id) -> MonthlyInput`. DB adapter idempotent on `(tenant_id, period_key, source_draft_id)`. Promotion retains draft with `state='promoted'`, records actor + draft hash in audit_logs, writes canonical confirmed-input shape. M10 never writes confirmed inputs. |
| **AD-7 strict invariant: counter increment** | ARCHITECTURE-SPINE.md §72-78 + master PRD §SM-3a | M10 attempts to write `confirmed_inputs` → denied + counted (target 0). 10-4 wire 진입 시점에 `monthly_extraction_promote_denied` 카운터 wire (10-1 AC #4 forward-bind + 10-3 SM-3a 카운터 trail 패턴 미러). |
| **AD-5 engine purity** | ARCHITECTURE-SPINE.md §60-66 | service layer only — pure kernel 신규 surface 추가. 10-4 wire 진입 시점에 `promoter_port.py` stdlib-only pure kernel + `validate_promotion_request` + `compute_promotion_idempotency_key` 2 funcs + `PromotionRequest` + `PromotionResult` frozen dataclasses + `PROMOTE_STATUS_VALUES` constant. |
| **AD-11 layer rule** | ARCHITECTURE-SPINE.md §96-110 | apps/api ← packages/services ← packages/shared 단방향. 10-4 wire 진입 시점에 `packages/services/m10_ai/promoter_port.py` SSOT 보존 + `apps/api/modules/m10_ai/services/promoter_service.py` EXTENSION (port adapter). |
| **AD-15 cross-language parity** | ARCHITECTURE-SPINE.md §130-136 | TS mirror parity + UUID v7 + Decimal-as-string + ko-KR SSOT. 10-4 wire 진입 시점에 `PromoteResponse` Literal SSOT 보존 + ko-KR error message ko-KR-only (master PRD §13.1 정합). TS mirror parity test **honestly DEFER (d) frontend dedicated sprint**. |
| **AD-2 INSERT-only preserved** | ARCHITECTURE-SPINE.md §44-52 | append-only ledger. 10-4 wire 진입 시점에 `monthly_input_promotions` NEW table 도 INSERT-only (UPDATE/DELETE trigger EXTENSION, alembic 0032). `input_drafts.state='promoted'` UPDATE 는 service_role bypass ONLY (audit-first INSERT BEFORE UPDATE). |
| **AD-25 cache invalidation 보존** | ARCHITECTURE-SPINE.md §296-301 + F10.1-(d) verbatim | M10 cache key = `(tenant_id, period_key, calculation_result_hash)`. 10-4 wire 진입 시점에 promote 자체는 invalidation trigger 안 함 (AD-25 publisher 0 publish — reversal 은 Epic 11 forward-fill, AD-22 verbatim). |
| **AD-22 reversal forward-lock** | ARCHITECTURE-SPINE.md §154-160 + F10.1-(a) verbatim | AD-22 reversal INSERT trigger publisher channel EXTENSION = Epic 11 Story 11.1/11.3 wire 진입 시점. 10-4 wire 진입 시점에는 Epic 4 calc-hash 기반 publisher 1 channel (`ai_cache`) 만 wire (10-2 wire 보존; CR 1.1 forward-lock + F10.1-(a) verbatim). |
| **AD-23 M10 AI defaults** | ARCHITECTURE-SPINE.md §178-184 | `tenant_settings.ai.*` JSONB sub-block — promotion port defaults 보존 (promote_enabled=true default + auto_promote_on_confirm=false default + retention_days=30 default). |
| **D-10-3-DEFER-6 PIPA gate carry-over** | sprint-status.yaml line 297 verbatim | PIPA gate `Depends(require_pipa_review)` 10-3 wire 진입 시점에 미적용; 10-4 wire 진입 시점에 4 endpoints 모두 적용 (POST `/api/v1/ai/extract-monthly` 10-1 + GET `/api/v1/ai/insights` 10-2 + GET `/api/v1/ai/comments` 10-3 + NEW POST `/api/v1/ai/promote` 10-4). **D-10-3-DEFER-6 ✅ RESOLVED 진입**. |

### Library / Framework Requirements

- **Pydantic v2**: NEW `PromoteRequest` (body) + `PromoteResponse` (success envelope) + `PromoteDraftImmutableError` (409 envelope) + `PromoteSourceDraftNotFoundError` (404 envelope) + `PromoteIdempotencyMismatchError` (422 envelope) + `PromoteM2OnlyError` (403 envelope) Discriminated union (CR 12-5 D-13 cross-language parity, 10-2 `InsightEntry | InsightListResponse | InsightCacheError` + 10-3 `AICommentEntry | AICommentListResponse | AICommentSourceKindInvalidError` 패턴 미러). `status: Literal['success', 'draft_immutable', 'source_draft_not_found', 'idempotency_mismatch', 'pipa_consent_missing', 'm2_only']` discriminator NEW (10-4 wire entry point). `audit_log_ids: tuple[UUID, UUID]` (CR 1.1 audit-first INSERT 2행 append 정합).
- **FastAPI**: NEW `POST /api/v1/ai/promote` (NEW 10-4 endpoint, body: `PromoteRequest` Pydantic v2 frozen model + capability gate `Depends(require_capability(Capability.AI_INSIGHT))` + PIPA gate `Depends(require_pipa_review)` (D-10-3-DEFER-6 carry-over 해소) + M2-only authorization `Depends(require_m2_service_role)` (NEW) + audit-first INSERT 패턴 + Discriminated union envelope + summary description (AD-17 verbatim bind + AD-7 verbatim bind))
- **Alembic**: 10-4 신규 마이그레이션 **0032** — `input_drafts_state_check` CHECK constraint EXTENSION (DROP existing `state IN ('draft', 'reviewed', 'superseded')` + ADD `state IN ('draft', 'reviewed', 'superseded', 'promoted')`) + NEW `monthly_input_promotions` table (`promotion_id` UUID PK + `tenant_id` UUID FK NOT NULL + `period_key` VARCHAR(32) NOT NULL + `source_draft_id` UUID FK NOT NULL + `confirmed_input_row_id` UUID FK NOT NULL + `draft_hash` BYTEA NOT NULL + `promoted_at` TIMESTAMPTZ NOT NULL DEFAULT NOW() + `actor_id` UUID NOT NULL + UNIQUE constraint `uq_monthly_input_promotions_tenant_period_draft` (`tenant_id`, `period_key`, `source_draft_id`) — AD-17 verbatim idempotency key 3-tuple + AD-2 INSERT-only trigger EXTENSION) + `audit_logs` action_class CHECK EXTENSION (10-4 wire entry)
- **Capability matrix v1.21**: `AI_INSIGHT` row 보존 (Story 10.1 wire 진입 + 10-3 spec 진입 시점에 regex `10.[1234]` reference 매칭) + 10.4 spec 진입 시점에 `docs/capability-matrix.md` row EXTENSION (`AI_INSIGHT` row story_coverage column 에 `"10-4"` append; 기존 `"10-1, 10-2, 10-3"` → `"10-1, 10-2, 10-3, 10-4"`) — capability matrix drift test regex `r"\|\s*\`?AI_INSIGHT\`?\s*\|\s*10\.[1234](?:\s*,\s*10\.[1234])*\s*\|"` PASS (자동, 10-4 wire 진입 시점에 regex 이미 4-story reference 검증)
- **`SourceKind` SSOT + `INSIGHT_KIND_VALUES` SSOT + `PROMOTE_STATUS_VALUES` SSOT 보존 활용** (CR 11-3 즉시 sweep 회피 pattern): `packages/services/m10_ai/insight_cache_kernel.py` 의 `SourceKind` enum + `SOURCE_KIND_VALUES` frozenset + `make_default_insights` source_kind='auto_analysis' ONLY invariant 보존 (10-3 wire SSOT) + 10-4 wire 진입 시점에 `PROMOTE_STATUS_VALUES` frozenset NEW SSOT 도입 (10-4 kernel SSOT); `packages/services/m10_ai/extraction_port.py` 의 `MONTHLY_INPUT_FIELD_NAMES` + `MonthlyFieldName` + `InputTargetTable` + `ALLOWED_INPUT_TARGET_TABLES` 보존 (10-1 wire SSOT, `'confirmed_inputs'` 추가 0건 — AD-7 strict invariant)

### File Structure Requirements

**A19 cohesion pattern 8 surface** (Story 10.1 검증 PASS + Story 10.2 PASS + Story 10.3 PASS — kernel + port + db schema + service + handler + envelope + capability + audit):

**Backend pure kernel (packages/services):**
- `packages/services/m10_ai/promoter_port.py` (NEW — stdlib-only pure kernel, AD-5 engine purity 정합):
  - `PromotionRequest` frozen dataclass (`tenant_id: UUID` + `period_key: str` + `source_draft_id: UUID` + `confirmed_value_hash: bytes | None` (optional integrity check) + `actor_id: UUID` + `trace_id: str` + `promoted_at: datetime` (caller 주입, no clock dependency))
  - `PromotionResult` frozen dataclass (`status: Literal['success']` + `tenant_id: UUID` + `period_key: str` + `source_draft_id: UUID` + `confirmed_input_row_id: UUID` + `promoted_at: datetime` + `draft_hash: bytes` + `idempotent_replay: bool` + `audit_log_ids: tuple[UUID, UUID]`)
  - `PROMOTE_STATUS_VALUES: Final[frozenset[str]] = frozenset({'success', 'draft_immutable', 'source_draft_not_found', 'idempotency_mismatch', 'pipa_consent_missing', 'm2_only'})` (NEW SSOT, AD-15 cross-language parity)
  - `compute_promotion_idempotency_key(tenant_id, period_key, source_draft_id) -> UUID` (stdlib-only pure function — SHA-256 hash → UUID v5 derivation, deterministic; no random, no clock)
  - `validate_promotion_request(request: PromotionRequest) -> None` (stdlib-only pure function — period_key format `YYYY-MM` 검증 + source_draft_id UUID v7 검증 + actor_id UUID 검증 + raise `PromotionRequestShapeError` 422 on shape mismatch; CR 11-3 즉시 sweep 회피 pattern)
  - `InputPromoterPort` Protocol (duck-typed interface — `async def promote(request: PromotionRequest) -> PromotionResult` — M2 가 consume; DB adapter 구현)
  - `__all__` EXTENSION with all 6 NEW exports

**DB models (apps/api/core/db_models.py):**
- `apps/api/core/db_models.py` (MODIFIED — EXTENSION):
  - `MonthlyInputPromotion` ORM class NEW: `promotion_id: UUID PK` + `tenant_id: UUID FK` + `period_key: VARCHAR(32)` + `source_draft_id: UUID FK` (to `input_drafts.draft_id`) + `confirmed_input_row_id: UUID FK` (to `monthly_input_rows.row_id`) + `draft_hash: LargeBinary` + `promoted_at: TIMESTAMPTZ` + `actor_id: UUID` + UNIQUE constraint `uq_monthly_input_promotions_tenant_period_draft` (`tenant_id`, `period_key`, `source_draft_id`) — AD-17 verbatim idempotency key 3-tuple + AD-2 INSERT-only trigger EXTENSION
  - `InputDraft.__table_args__` MODIFIED — 기존 `CheckConstraint("state IN ('draft', 'reviewed', 'superseded')", name="input_drafts_state_check")` 을 `CheckConstraint("state IN ('draft', 'reviewed', 'superseded', 'promoted')", name="input_drafts_state_check_v2")` 로 EXTENSION (alembic 0032 wire 진입 시점에 기존 CHECK DROP + NEW CHECK ADD; ORM 모델은 v2 반영)
  - `MonthlyInputRow` ORM class 보존 (Story 3.1 wire baseline; 10-4 wire 진입 시점에 `monthly_input_rows` 직접 INSERT 거부 로직만 service layer gate 로 추가; AD-7 strict invariant 강화)

**Alembic migrations:**
- `apps/api/alembic/versions/0032_ai_promotion_port.py` (NEW):
  - `input_drafts_state_check` DROP + ADD (`state IN ('draft', 'reviewed', 'superseded', 'promoted')` — `input_drafts_state_check_v2` rename)
  - `monthly_input_promotions` table CREATE (`promotion_id` UUID PK + 7 columns + UNIQUE constraint + AD-2 INSERT-only trigger EXTENSION)
  - `audit_logs` action_class CHECK EXTENSION (`input_draft_promoted` + `monthly_extraction_promote_executed` 2 NEW values 추가)
  - INDEX `idx_monthly_input_promotions_tenant_period` (`tenant_id`, `period_key`) — 1st-step lookup acceleration
  - INDEX `idx_monthly_input_promotions_source_draft` (`source_draft_id`) — 2nd-step lookup acceleration
  - COMMENT ON TABLE for AD-17 verbatim 3-tuple 명시

**Backend service layer (apps/api/modules/m10_ai/):**
- `apps/api/modules/m10_ai/services/promoter_service.py` (NEW, M10 service that uses DB adapter; ORM→kernel boundary):
  - `PromoterService` class NEW with `__init__(self, session: AsyncSession, actor_id: UUID, trace_id: str)`
  - `async def promote(tenant_id, period_key, source_draft_id, confirmed_value_hash: bytes | None) -> PromotionResult` method
  - 11-step pipeline (10-3 AC #6 pattern 미러):
    1. `validate_promotion_request(request)` pure kernel call (Pydantic v2 Literal 검증 reuse; AD-15 정합)
    2. PIPA consent gate (FIRST gate — `tenant_settings.pipa_consent.granted = true` 검증; 10-1 wire 보존; D-10-3-DEFER-6 carry-over 해소 wire)
    3. M2-only authorization check (NEW; AD-17 verbatim)
    4. Audit-first INSERT (Row 1: `action_class='INPUT_DRAFT'`, `action='input_draft_promoted'`; CR 1.1 verbatim)
    5. SELECT `input_drafts` WHERE `draft_id=:source_draft_id AND tenant_id=:tenant_id` FOR UPDATE (idempotency check)
    6. If `state='promoted'` already → SELECT existing `monthly_input_promotions` row → return PromotionResult with `idempotent_replay=true` + audit_log_ids from Row 1 (single audit row since INSERT skipped)
    7. If `state='superseded'` → raise `PromoteDraftImmutableError` 409 (audit-first INSERT Row 1 already emitted)
    8. If `state IN ('draft', 'reviewed')` →
       a. INSERT INTO `monthly_input_rows` (canonical 6-stream shape from draft's `confirmed_value` JSONB) — actor_id + draft_hash + trace_id
       b. INSERT INTO `monthly_input_promotions` (10-4 NEW table; UNIQUE constraint handles duplicate via INSERT ... ON CONFLICT DO NOTHING)
       c. UPDATE `input_drafts.state='promoted'`, `reviewed_by=actor_id`, `reviewed_at=:promoted_at`
       d. Audit-first INSERT (Row 2: `action_class='AI_EXTRACTION_EXECUTED'`, `action='monthly_extraction_promote_executed'`)
       e. Return PromotionResult with `idempotent_replay=false` + audit_log_ids from Row 1 + Row 2
    9. AD-7 strict invariant guard: M10 service 가 실수로 `monthly_input_rows` 직접 INSERT 시도 시 `monthly_input_promote_denied` audit_log INSERT + raise `InputPromotionDeniedError` 422
    10. Idempotency mismatch guard: replay 인데 `confirmed_value_hash` 가 기존과 다르면 `raise PromoteIdempotencyMismatchError` 422
    11. TS mirror parity metadata return (`PROMOTE_STATUS_VALUES` cross-reference)
- `apps/api/modules/m10_ai/schemas.py` (MODIFIED — 6 NEW Pydantic v2 frozen models):
  - `PromoteRequest` (body) — `tenant_id: UUID` + `period_key: str` + `source_draft_id: UUID` + `confirmed_value_hash: str | None` (hex-encoded bytes; optional integrity check) + `actor_id: UUID`
  - `PromoteResponse` (success envelope) — `status: Literal['success']` + 9 fields per AC #5 verbatim
  - `PromoteDraftImmutableError` (409 envelope) — `status: Literal['draft_immutable']` + `code: Literal['PROMOTE_DRAFT_IMMUTABLE']` + `message_ko: Literal['이 초안은 이미 superseded 상태로 승격할 수 없습니다']` + `details: dict` + `trace_id: str`
  - `PromoteSourceDraftNotFoundError` (404 envelope) — `status: Literal['source_draft_not_found']` + `code: Literal['PROMOTE_SOURCE_DRAFT_NOT_FOUND']` + `message_ko: Literal['해당 초안을 찾을 수 없습니다']` + `details: dict` + `trace_id: str`
  - `PromoteIdempotencyMismatchError` (422 envelope) — `status: Literal['idempotency_mismatch']` + `code: Literal['PROMOTE_IDEMPOTENCY_MISMATCH']` + `message_ko: Literal['동일 초안에 다른 값으로 재호출되었습니다']` + `details: dict` + `trace_id: str`
  - `PromoteM2OnlyError` (403 envelope) — `status: Literal['m2_only']` + `code: Literal['INPUT_PROMOTION_M2_ONLY']` + `message_ko: Literal['승격 포트는 M2 모듈만 호출할 수 있습니다']` + `details: dict` + `trace_id: str`
  - Discriminated union export: `PromoteResponse | PromoteDraftImmutableError | PromoteSourceDraftNotFoundError | PromoteIdempotencyMismatchError | PromoteM2OnlyError | AiPipaConsentMissingError` with `status` tag discriminator
- `apps/api/modules/m10_ai/exceptions.py` (MODIFIED — 4 NEW typed exceptions + 1 carry-over):
  - `PromoteDraftImmutableError` (409)
  - `PromoteSourceDraftNotFoundError` (404)
  - `PromoteIdempotencyMismatchError` (422)
  - `PromoteM2OnlyError` (403)
  - `InputPromotionDeniedError` (422, AD-7 strict invariant guard)
  - `PromotionRequestShapeError` (422, Pydantic v2 Literal 검증 reuse)
  - `AiPipaConsentMissingError` (403 carry-over, 10-1 wire 보존 — D-10-3-DEFER-6 carry-over 해소 wire 진입 시점에 10-1/10-2/10-3 endpoints 에 일괄 적용)
- `apps/api/core/audit_action.py` (MODIFIED — `InputDraftAction` Literal EXTENSION + `AIExtractionAction` Literal EXTENSION):
  - `InputDraftAction` Literal: 기존 2 values (`input_draft_confirm`, `input_draft_reject`) → 3 values + `input_draft_promoted` (NEW 10-4)
  - `AIExtractionAction` Literal: 기존 3 values (`monthly_extraction_executed`, `monthly_extraction_low_confidence_warning`, `monthly_extraction_promote_denied`) → 4 values + `monthly_extraction_promote_executed` (NEW 10-4)
  - `_ActionRegistry._REGISTRY` EXTENSION: `ActionClass.INPUT_DRAFT` frozenset EXTENSION (`input_draft_promoted` add); `ActionClass.AI_EXTRACTION_EXECUTED` frozenset EXTENSION (`monthly_extraction_promote_executed` add)
  - `AuditAction` union EXTENSION (union EXTENSION = no-op since union auto-tracks Literal EXTENSION; 명시적 EXTENSION for clarity)
  - `__all__` EXTENSION (no NEW export name; 기존 names 보존)
- `apps/api/modules/m10_ai/adapters/db_promoter_adapter.py` (NEW — DB adapter implementing `InputPromoterPort` Protocol):
  - `DbPromoterAdapter` class satisfying Protocol via `AsyncSession`
  - `async def promote(request: PromotionRequest) -> PromotionResult` — delegates to `PromoterService` (ORM I/O lives here; port stays pure)
  - Constructor: `__init__(self, session: AsyncSession)`
- `apps/api/modules/m10_ai/handlers.py` (MODIFIED — NEW `POST /api/v1/ai/promote` endpoint + capability gate + PIPA gate + M2-only authorization + audit-first INSERT):
  - **D-10-3-DEFER-6 carry-over 해소**: 기존 3 endpoints (POST `/api/v1/ai/extract-monthly` 10-1 + GET `/api/v1/ai/insights` 10-2 + GET `/api/v1/ai/comments` 10-3) 에 `Depends(require_pipa_review)` 일괄 적용 (PIPA gate handler.py MODIFIED 4 endpoints)
  - NEW `POST /api/v1/ai/promote` endpoint — capability gate + PIPA gate + M2-only auth + audit-first + Discriminated union envelope + summary description (AD-17 verbatim bind)
- `apps/api/main.py` (MODIFIED — 5 NEW envelope handlers + 1 carry-over):
  - NEW `PromoteDraftImmutableError` → 409 `PROMOTE_DRAFT_IMMUTABLE`
  - NEW `PromoteSourceDraftNotFoundError` → 404 `PROMOTE_SOURCE_DRAFT_NOT_FOUND`
  - NEW `PromoteIdempotencyMismatchError` → 422 `PROMOTE_IDEMPOTENCY_MISMATCH`
  - NEW `PromoteM2OnlyError` → 403 `INPUT_PROMOTION_M2_ONLY`
  - NEW `InputPromotionDeniedError` → 422 `INPUT_PROMOTION_DENIED`
  - carry-over `AiPipaConsentMissingError` → 403 `AI_PIPA_CONSENT_MISSING` (10-1 wire 보존; D-10-3-DEFER-6 carry-over 해소 wire 진입 시점에 4 endpoints 일괄 적용 — main.py envelope handler 등록 보존, handler.py 의 Dependency 추가만)
  - CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}` envelope shape

**Frontend (apps/web):**
- `apps/web/components/ai-extract/PromoteConfirmButton.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — A35 frontend test debt 정합; "승격 확정" 버튼 + idempotent retry UI)
- `apps/web/components/ai-extract/PromoteResultToast.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — `idempotent_replay: true` vs `false` 분기 토스트 — 1st call vs replay 시각적 disambiguation)
- `apps/web/components/ai-extract/__tests__/PromoteConfirmButton.test.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — vitest mount + A35 frontend test debt 정직)
- `apps/web/components/ai-extract/__tests__/PromoteResultToast.test.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — vitest idempotent_replay 분기 검증)
- `apps/web/lib/ai-promote.ts` (NEW, **honestly DEFER (d) dedicated sprint** — TS mirror parity: Python `PromoteResponse` ↔ TS `PromoteResponseTS`, Discriminated union narrowing)
- `apps/web/messages/ko-KR.json` (MODIFIED, **honestly DEFER (d) dedicated sprint** — `ai_promote` namespace ~7 strings SSOT: button label 1 + toast 2 (success/replay) + error messages 4 = ~7 strings, CR 11-4 D-002 + P-015 정합)
- `apps/web/__tests__/lib/ai-promote-parity.test.ts` (NEW, **honestly DEFER (d) dedicated sprint** — cross-language drift detector, 18 cases precedent)

**Tests (tests/):**
- `tests/services/m10_ai/test_promoter_port.py` (NEW, ~12 cases — pure kernel stdlib-only, RED → GREEN → REFACTOR):
  - `compute_promotion_idempotency_key` deterministic 4 cases (same input → same UUID v5 derivation; different input → different UUID)
  - `validate_promotion_request` shape validation 4 cases (period_key format YYYY-MM ✓ / � + UUID v7 ✓ / ✗)
  - `PROMOTE_STATUS_VALUES` SSOT 2 cases (frozenset 6 values verbatim + AD-15 parity)
  - `PromotionRequest` + `PromotionResult` frozen dataclass 2 cases (frozen invariant + typed fields)
- `tests/api/m10_ai/test_promoter_service.py` (NEW, ~22 cases — service layer ORM→kernel boundary + AD-17 idempotency + AD-7 strict invariant):
  - `promote` happy path × 3 (1st call → INSERT + idempotent_replay=false + 2 audit_log_ids)
  - `promote` idempotent replay × 3 (2nd call → no INSERT + idempotent_replay=true + 1 audit_log_id from Row 1)
  - `promote` idempotency mismatch × 2 (replay 인데 confirmed_value_hash 다름 → 422 PROMOTE_IDEMPOTENCY_MISMATCH)
  - `promote` draft superseded × 2 (`state='superseded'` → 409 PROMOTE_DRAFT_IMMUTABLE + audit-first Row 1 INSERT)
  - `promote` draft not found × 2 (`source_draft_id` 미존재 → 404 PROMOTE_SOURCE_DRAFT_NOT_FOUND)
  - `promote` PIPA 미동의 × 2 (D-10-3-DEFER-6 carry-over 해소 검증 — `tenant_settings.pipa_consent.granted=false` → 403 AI_PIPA_CONSENT_MISSING)
  - `promote` M2 외 caller × 2 (NEW — `actor.role != 'm2_service_role'` → 403 INPUT_PROMOTION_M2_ONLY)
  - `promote` AD-7 strict invariant guard × 2 (M10 service 가 실수로 `monthly_input_rows` 직접 INSERT 시도 → 422 INPUT_PROMOTION_DENIED + `monthly_extraction_promote_denied` audit_log INSERT)
  - `compute_promotion_idempotency_key` ORM→kernel boundary × 2 (CR 12-1 L3 verbatim typed mapping + UUID v5 cast)
  - `monthly_input_promotions` UNIQUE constraint × 2 (DB-level idempotency guard verification)
- `tests/api/m10_ai/test_promote_endpoint.py` (NEW, ~18 cases — FastAPI endpoint integration):
  - POST /api/v1/ai/promote happy path × 3 (Discriminated union envelope success status + 9 fields per AC #5)
  - Capability gate (AI_INSIGHT) × 2 (industry-agnostic 4-industry grants)
  - PIPA consent gate × 2 (D-10-3-DEFER-6 carry-over 해소 검증 — 4 endpoints 모두 PIPA gate 적용)
  - M2-only authorization × 2 (NEW — `actor.role != 'm2_service_role'` → 403)
  - Discriminated union envelope × 4 (success vs `PromoteDraftImmutableError` vs `PromoteSourceDraftNotFoundError` vs `PromoteIdempotencyMismatchError` + status tag discriminator)
  - 403 AI_PIPA_CONSENT_MISSING envelope × 1 (CR 12-5 D-14 verbatim)
  - 403 INPUT_PROMOTION_M2_ONLY envelope × 1 (NEW 10-4)
  - 404 PROMOTE_SOURCE_DRAFT_NOT_FOUND envelope × 1 (NEW 10-4)
  - 409 PROMOTE_DRAFT_IMMUTABLE envelope × 1 (NEW 10-4)
  - 422 PROMOTE_IDEMPOTENCY_MISMATCH envelope × 1 (NEW 10-4)
  - 422 INPUT_PROMOTION_DENIED envelope × 1 (NEW 10-4)
  - audit-first INSERT (CR 1.1 verbatim) verification × 1 (BEFORE monthly_input_rows INSERT)
  - 2 audit_log_rows per promote call × 1 (Row 1 INPUT_DRAFT + Row 2 AI_EXTRACTION_EXECUTED)
- `tests/api/test_alembic_0032_ai_promotion_port.py` (NEW, ~12 cases — source-text parsing):
  - Migration up/down × 3 (DROP existing input_drafts_state_check + ADD v2 + CREATE monthly_input_promotions + INSERT-only trigger + audit_logs CHECK EXTENSION)
  - Column existence + types × 3 (promotion_id UUID PK + draft_hash LargeBinary + confirmed_input_row_id UUID FK)
  - UNIQUE constraint existence × 2 (`uq_monthly_input_promotions_tenant_period_draft` 3-tuple + INSERT-only trigger)
  - input_drafts_state_check_v2 boundary × 2 (state IN 4 values: 'draft', 'reviewed', 'superseded', 'promoted')
  - audit_logs CHECK EXTENSION × 2 (`input_draft_promoted` + `monthly_extraction_promote_executed` 2 NEW values 추가)
- `tests/integration/test_capability_matrix_v1_21_drift.py` (MODIFIED — 0 NEW case; 기존 regex `r"\|\s*\`?AI_INSIGHT\`?\s*\|\s*10\.[1234](?:\s*,\s*10\.[1234])*\s*\|"` 이미 4-story reference 검증 — 10-4 wire 진입 시점에 자동 PASS)
- `docs/capability-matrix.md` (MODIFIED — `AI_INSIGHT` row story_coverage column EXTENSION: 기존 `"10-1, 10-2, 10-3"` → `"10-1, 10-2, 10-3, 10-4"`, canonical PRD §6.1 line 252-253 verbatim 정합)

### Testing Requirements

- **pytest focused (backend)**:
  - pure kernel test 12+ cases (`promoter_port.py` stdlib-only, RED → GREEN → REFACTOR)
  - service layer test 22+ cases (ORM→kernel boundary + AD-17 idempotency + AD-7 strict invariant + audit-first INSERT 2행 append)
  - endpoint integration test 18+ cases (capability gate + PIPA gate 4 endpoints carry-over 해소 + M2-only authorization + Discriminated union envelope + 6 error envelopes)
  - AD-17 verbatim idempotency key 3-tuple verification test (`(tenant_id, period_key, source_draft_id)` 결정성 + DB-level UNIQUE constraint)
  - AD-7 strict invariant guard test (M10 → `monthly_input_rows` 직접 INSERT 시도 → 422 INPUT_PROMOTION_DENIED + `monthly_extraction_promote_denied` audit_log INSERT)
  - audit-first INSERT (CR 1.1 verbatim) verification test (BEFORE `monthly_input_rows` INSERT OR `input_drafts.state` UPDATE)
  - 2 audit_log_rows per promote call verification test (Row 1 INPUT_DRAFT.input_draft_promoted + Row 2 AI_EXTRACTION_EXECUTED.monthly_extraction_promote_executed)
  - D-10-3-DEFER-6 carry-over 해소 verification test (4 endpoints 모두 PIPA gate 적용: POST /extract-monthly 10-1 + GET /insights 10-2 + GET /comments 10-3 + POST /promote 10-4)
  - idempotent_replay=true 분기 test (1st call vs 2nd call disambiguation)
  - capability matrix v1.21 drift detector (P-015 SSOT pattern, 17 cases precedent + 10-4 story coverage = 17 cases 그대로 보존, regex 자동 PASS)
- **A36 SDR 검증 자동 검증 단계 wire (carry-over from 9-7 follow-up sprint)**:
  - commit prefix lint PASS (D5 fix DONE — `^@` non-match)
  - sprint-status structure 정합 (D4 fix DONE, Epic 10 entries in development_status block)
  - vitest file count drift 0건 (D2 자동화)
  - commit consistency 정합 (D1 자동화)
- **tsc**: zero NEW (no .ts changes outside `__tests__` honestly DEFER entry)
- **vitest**: honestly DEFER (d) frontend dedicated sprint entry (D-10-4-DEFER-4)

### Previous Story Intelligence (Epic 10 + 9 patterns)

- **Story 10.3 (AI Reference vs Auto Analysis Badge Separation)** — atomic single sprint wire DONE (cj-style 32번째). **본 Story (10-4) 의 A19 cohesion pattern 8 surface 동일 정합** (kernel + port + db schema + service + handler + envelope + capability + audit). 10-3 = 13 NEW + 5 MODIFIED source + 4 NEW test files + 4 MODIFIED docs, 74 PASS, 6 honestly DEFER preserved (D-10-3-DEFER-1~6). 본 Story (10-4) 진입 시점에 **D-10-3-DEFER-6 PIPA gate 4 endpoints carry-over 해소 wire 진입** (10-1/10-2/10-3 endpoints + NEW 10-4 endpoint 모두 PIPA gate 적용). 10-3 의 `SourceKind` Literal SSOT + `make_default_insights source_kind='auto_analysis' ONLY` invariant + Discriminated union envelope 패턴 (CR 12-5 D-13 cross-language parity) 그대로 미러.
- **Story 10.2 (Three-Insight Cache Policy)** — atomic single sprint T1~T11 wire DONE (cj-style 29번째). **본 Story (10-4) 의 audit-first INSERT 2행 append 패턴** (10-2 wire `ai_insight_cache_hit` + `ai_insight_cache_miss` + `ai_insight_cache_cold_compute` + `ai_insight_cache_invalidation` 4 audit values 패턴 미러) + **ORM→kernel boundary pattern** (10-2 wire `_to_insight_state` L3 verbatim typed mapping) + **ActionClass SSOT EXTENSION** (10-2 wire `AI_INSIGHT_CACHE_ACCESSED` 1 NEW + 10-3 wire EXTENSION 2 NEW values 패턴 미러). 10-2 의 `InsightEntry.source_kind: Literal['auto_analysis', 'ai_reference']` discriminator 보존.
- **Story 10.1 (AI Document Extraction to Input Drafts)** — atomic single sprint wire DONE (cj-style 28번째). **본 Story (10-4) 의 AD-7 strict invariant counter increment** (10-1 wire `monthly_extraction_promote_denied` 1 forward-fill slot + 10-4 wire `monthly_extraction_promote_executed` 1 NEW value 패턴 미러) + **PIPA gate `Depends(require_pipa_review)` 패턴** (10-1 wire 보존, D-10-3-DEFER-6 carry-over 해소 wire 진입 시점에 4 endpoints 일괄 적용) + **`InputPromoter` port interface 정의** (10-1 wire `packages/services/m10_ai/extraction_port.py` line 197 verbatim "(Story 10.4 detailed wire)" TODO marker 보존; 10-4 wire 진입 시점에 NEW `promoter_port.py` 정의 + `extraction_port.py` line 197 marker JSDoc EXTENSION).
- **9-7 (A35 frontend test debt + A36 SDR 검증 프로토콜)** — A35 frontend test debt 정직 회복 + A36 SDR 검증 4-step 자동화. **본 Story (10-4) wire 시점에 신규 React 컴포넌트 모두 vitest mount 검증 필수** (PromoteConfirmButton + PromoteResultToast **honestly DEFER (d) frontend dedicated sprint**) + **TS mirror parity test 필수** (`apps/web/lib/ai-promote.ts` honestly DEFER (d)) + **commit prefix lint + sprint-status structure 검증 + vitest file count drift + commit consistency 자동 검증 단계 적용**.

### Git Intelligence Summary

- **HEAD** = `ea025b1` Story 10.3 3rd sweep DONE atomic commit (cj-style 32번째 = 10-3 atomic sprint wire T1~T11 + 2 PATCH fixes + 1 NEW DEFER). 23 files changed, 3892 insertions(+), 11 deletions(-). commit prefix = `@ @` (PowerShell here-string 사고 — D5 carry-over; 10-4 wire 시점에 `git commit -F <file>` 패턴 사용).
- **Pattern**: 13 NEW + 5 MODIFIED source + 4 NEW test files + 4 MODIFIED docs. 본 Story (10-4) wire 시점에 code changes 진입 → atomic commit with detailed wire 표 (10-3 wire 표 패턴 미러).
- **A36 SDR 검증 4-step**: 본 Story (10-4) wire 시 commit prefix lint + sprint-status structure 검증 + vitest file count drift + commit consistency 자동 검증 적용 (9-7 follow-up sprint wire DONE, automated).

### A34 4-Category Honestly DEFER (10-4 wire 진입 시점 명시)

`D-10-4-DEFER-1` **(a) docs 정합** — master PRD v2.0 본체 edit (`_bmad-output/planning-artifacts/prd.md` §F10.2 (f) section extension + §F10.2 (a)~(f) 5 bullets verbatim wire + §AD-17 verbatim 인용 + §SM-3a 정합 + §A11 정합 + §13.1 ko-KR 정합 + §NFR18 정합 + §8.1 M10 promotion port + §14.B NON-GOAL #5 정합). Epic 10 close-out retro 진입 시점에 master PRD 본체 edit + canonical PRD §5.1 AD-17 verbatim bind 정합 검증. carry-over 10-1/10-2/10-3 의 master PRD 본체 edit 보존.

`D-10-4-DEFER-2` **(b) retro input** — Epic 10 close-out retro 진입 시점에 `monthly_extraction_promote_executed` + `input_draft_promoted` + `monthly_input_promotions` table 실측 evidence (promote 호출 �수 + idempotent replay 비율 + AD-7 strict invariant counter 실측) 입력 + A37~A40 결정 도출.

`D-10-4-DEFER-3` **(c) separate epic** — M2 public endpoint 분리 (M2 module 자체가 별도 epic 으로 분리될 시점에 `POST /api/v1/m2/input-drafts/{draft_id}/promote` M2-public endpoint 진입; 10-4 wire 진입 시점에는 AD-17 verbatim "Only M2 may call" 패턴을 service_role bypass + capability gate + PIPA gate 의 3-layer guard 로 구현 — M2 모듈 자체가 아직 미구현된 상태에서 10-4 진입). post-Epic 10 forward-fill.

`D-10-4-DEFER-4` **(d) dedicated sprint** — frontend 5 files dedicated sprint (PromoteConfirmButton + PromoteResultToast + 2 vitest mount tests + 1 TS mirror parity test + 1 ko-KR.json SSOT) = A35 frontend test debt **dedicated sprint** 후속 진입. cj-style carry-over 14번째 가능 (10-3 wire 의 D-10-3-DEFER-4 frontend 7 files 와 통합 가능 — frontend dedicated sprint 12 files).

`D-10-4-DEFER-5` **(a) docs 정합 carry-over** — `docs/deferred-work.md` + `docs/capability-matrix.md` 정합 검증 + 10-1/10-2/10-3 의 docs/deferred-work.md leftover (특히 10-3 의 `D-10-3-DEFER-5` carry-over marker 보존). Epic 10 close-out retro 진입 시점에 일괄 정합.

### A36 SDR 검증 4-step PASS (10-4 wire 진입 시점 자동 검증)

| Step | Tool | Expected Result |
|---|---|---|
| 1. Commit prefix lint | `scripts/check_commit_prefix.{py,mjs}` | PASS — `^@` non-match (10-4 wire commit 에 `@ @` prefix 미존재) |
| 2. Sprint-status structure | `tests/integration/test_sprint_status_structure.py` | PASS — `10-4-ai-promotion-port-idempotency` key 가 `development_status:` 블록 (line 274 후) 에 위치 |
| 3. Vitest file count drift | `tests/integration/test_vitest_file_count_drift.py` | PASS — 신규 vitest 파일 0건 (frontend 5 files honestly DEFER (d)) |
| 4. Commit consistency | `tests/integration/test_commit_consistency.py` | PASS — sprint-status 의 `10-4-ai-promotion-port-idempotency` entry 가 commit message 의 wire 표 정합 |

### Story Completion Status

- [x] Story Header populated
- [x] User Story extracted (epics.md Story 10.4 verbatim)
- [x] Acceptance Criteria defined (6 ACs)
- [x] Developer Context (Architecture Compliance + Library/Framework + File Structure + Testing Requirements)
- [x] Previous Story Intelligence (10-1 + 10-2 + 10-3 patterns)
- [x] Git Intelligence Summary
- [x] A34 4-Category Honestly DEFER (D-10-4-DEFER-1~5)
- [x] A36 SDR 검증 4-step PASS
- [x] **Status: ready-for-dev**
- [x] Completion note: "Ultimate context engine analysis completed - comprehensive developer guide created"

### 다음 단계 (Next Steps)

1. Review 본 spec file
2. Run dev agents `bmad-dev-story` for atomic single sprint T1~T11 wire (cj-style 33번째 epic 연속 정직 회복)
3. Run `bmad-code-review` 3rd sweep when complete (auto-marks done; cj-style 34번째 epic 연속)
4. 이후 Epic 10 close-out retro 진입 (cj-style 5번째 진입점, A37~A40 결정 도출 + 10-1/10-2/10-3/10-4 wire 종합 retro)
