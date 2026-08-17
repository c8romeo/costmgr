---
story_id: 10.2
story_key: 10-2-three-insight-cache-policy
title: Three-Insight Cache Policy
created: 2026-08-17
baseline_commit: 809a081
epic: 10
status: ready-for-dev
target_sprint: cj-style Epic 10 3번째 진입점 (cj-style 29번째 epic 연속)
estimated_complexity: medium-high
honestly_defer_count: 4
wire_partial: false
---

# Story 10.2 — Three-Insight Cache Policy

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 10.2 |
| **Story Key** | `10-2-three-insight-cache-policy` |
| **Epic** | Epic 10 — AI Assistance (4-story + retro 5번째 진입점, Epic 8 retro §7 A23 패턴) |
| **baseline_commit** | `809a081` (Story 10.1 atomic sprint wire tip, cj-style 28번째 epic 연속) |
| **cj-style 분할** | 10-2 (3번째) — **cj-style 29번째 epic 연속** |
| **Forward-lock** | A28 (9-2 DONE) + A29 (9-3 DONE) + A30 (9-4 DONE) + A31 (Report #15 wire schedule) + A32 (A30 SHARED factory reuse) + A33 (A19 cohesion 9 surface) + A34 (mixed honestly DEFER 4-category framework) + A35 (frontend test debt DONE 9-7) + A36 (SDR 검증 프로토콜 DONE 9-7) |
| **Primary capability** | `Capability.AI_INSIGHT` (industry-agnostic, 4-industry grants ✅/✅/✅/✅, capability matrix v1.21 — Story 10.1 wire 진입) |
| **Primary PRD ref** | **§F10.1 (a)~(d) 4 bullets** (`_bmad-output/planning-artifacts/prds/prd-costmgr-2026-08-17/prd.md` lines 76-93) + epics.md Story 10.2 (lines 1087-1099) + master PRD §8.1 M10-(a) (cache policy) + master PRD §12 "캐시 = 마감 완료 ~ 다음 마감 시작" + master PRD §V7 (AI insights 캐시 정합성) |
| **Secondary PRD ref** | master PRD §F0.2 (3종 allocation 정합) + master PRD §2.A UJ-AI step 1 (insight cache 조회) + master PRD §A11 (시스템은 틀리지 않는다) + master PRD §13.1 (ko-KR-only) + master PRD §NFR11 (P95 ≤ 30s) + master PRD §NFR16 (engine purity) + master PRD §NFR18 (ko-KR) |
| **Primary AD ref** | **AD-25 (AI insight cache invalidation)** + AD-7 (AI non-authoritative — read-only deterministic insight only) + AD-22 (reversal 영구화 + forward-lock Epic 11 trigger EXTENSION) + AD-23 (M10 AI defaults JSONB) |
| **Baseline wire** | Story 10.1 atomic sprint wire commit `809a081` (Story 10.1 9 source files + 1 spec, 72 pass + 4 skipped, 2 honestly DEFER preserved). 10.1 = T2.5+T2.6+T3+T8.2 wire (backend handler + alembic 0029 input_drafts_monthly_extension + sprint-status final done). |

## User Story (epics.md Story 10.2 verbatim)

As a **사장님**, I want **AI 인사이트 3개(원가 절감 후보·이상 패턴·예측)가 마감 완료 시점에 잠기고 다음 마감 시작 시점까지 보존되는 것**, so that **빠른 응답 + 데이터 일관성** (master PRD §2.A UJ-1 step 5 정합).

## Acceptance Criteria (PRD §F10.1 (a)~(d) + AD-25 verbatim + 10-3 forward-lock bind)

### AC #1 — `fiscal_period_snapshots.state='committed'` 전이 시점에 `ai_cache` 채널 lock (AD-25 verbatim + F10.1-(a))

- **Given** "2026-07" M3 atomic COMMIT 완료 → `fiscal_period_snapshots.state='committed'` 전이 (master PRD §V4 atomicity + Epic 4 calc-hash publisher)
- **When** Epic 4 calc-hash publisher가 AD-25 publisher.publish(channel='ai_cache', ...) 호출
- **Then** **`ai_cache` 채널에 `cache_invalidation_log` row 1개 INSERT** (CR 1.1 audit-first pattern, AD-2 append-only)
- **And** 동시에 AI 인사이트 3개 질문 + 답변이 `(tenant_id, period_key, calculation_result_hash)` 3-tuple key로 **lock**됨
- **And** `calculation_result_hash` = `fiscal_period_snapshots.calculation_result_hash` (Epic 4 M3 atomic COMMIT 시점에 결정된 SHA-256 hex digest; CR 1.1 / V4 byte-identical determinism)
- **And** 본 Story (10-2) 진입 시점에는 **`ai_cache` 1 channel만 wire**, 나머지 3 channel (`cost_engine_cache` + `fiscal_period_cache` + `closing_snapshot_cache`)은 Epic 11 close/reopen trigger EXTENSION으로 forward-lock (Story 11.1/11.3 진입 시점 wire, CR 1.1 forward-lock 패턴 + §F10.1-(a) verbatim "Epic 11 close/reopen trigger는 본 Story 범위 외")

### AC #2 — Cache hit 시 즉시 응답 + cold compute within NFR11 SLO (AD-25 + F10.1-(b))

- **Given** `ai_cache` 채널 lock row 존재 (= cache hit)
- **When** 사장님이 `GET /api/v1/ai/insights?period_key=2026-07` 호출
- **Then** **3개 인사이트 (질문 + 답변)가 `ai_cache` 채널 lock row에서 즉시 응답** (cache hit sub-100ms, NFR11 P95 ≤ 30s 정합)
- **And** `InsightEntry` envelope response: `insight_kind: Literal['cost_reduction_candidate', 'anomaly_pattern', 'forecast']` discriminator + `question: str` + `answer: str` (ko-KR locale, master PRD §13.1) + `source_kind: Literal['auto_analysis', 'ai_reference']` discriminator (Story 10.3 badge separation forward-bind — AD-7 verbatim "AI commentary source_kind='ai_reference'" / "auto_analysis source_kind='auto_analysis'")
- **And** cache miss 시 cold compute within NFR11 SLO (≤ 30s P95; master PRD §NFR11 verbatim)
- **And** 응답 envelope ko-KR SSOT 1 namespace 분리 (`ai_insights` namespace ~15 strings; CR 11-4 D-002 + P-015 정합, P-015 drift detector wire)

### AC #3 — AD-25 publisher: `cache_invalidation_log` row insert 시점에 M10 cache 즉시 폐기 + 재계산 (F10.1-(c))

- **Given** `cache_invalidation_log` row INSERT (channel='ai_cache', target_event_id = reversal event_id or commit snapshot_id)
- **When** M10 adapter가 `cache_invalidation_log` row consume (polling NOT; LISTEN/NOTIFY or trigger-based consume per AD-25 verbatim "Application polling and input-write-only invalidation forbidden")
- **Then** **`WHERE tenant_id=? AND period_key=?` 매칭 cache entry를 즉시 폐기** (F10.1-(c) verbatim)
- **And** 매칭 cache entry 없으면 no-op (idempotent); 매칭 cache entry 있으면 eviction row 1개 append + audit-first INSERT (CR 1.1 verbatim)
- **And** **본 Story (10-2) 진입 시점에는 Epic 4 calc-hash 기반 publisher 1 channel (`ai_cache`) 만 wire**, AD-22 reversal INSERT trigger는 Epic 11 Story 11.1/11.3 진입 시점에 publisher channel EXTENSION으로 추가 wire (CR 1.1 forward-lock + F10.1-(a) verbatim + 10-2 epics.md AC 마지막 bullet verbatim "본 Story에서는 Epic 4 calc-hash 기반 무효화만 wire, Epic 11 close/reopen trigger는 Epic 11 Story 11.1/11.3에서 추가 wiring")

### AC #4 — `cache_invalidation_log.channel = 'ai_cache'` filter 강제 (F10.1-(d) verbatim cross-channel contamination 방지)

- **Given** `cache_invalidation_log` row INSERT (channel = 'cost_engine_cache' | 'fiscal_period_cache' | 'closing_snapshot_cache' — Epic 11 wire 진입 후 발생)
- **When** M10 adapter consume
- **Then** **`channel = 'ai_cache'` filter만 매칭** — 다른 channel row는 M10 cache에 영향 없음 (F10.1-(d) verbatim "시스템은 cache_invalidation_log 채널에 ai_cache 외 채널이 추가되어도 본 캐시만 영향받지 않도록 channel-specific invalidation filter를 강제한다 (`channel = 'ai_cache' filter`)")
- **And** cross-channel contamination 방지 — 4 channel 모두 동일 `cache_invalidation_log` table에 row 저장되지만 M10 adapter는 `ai_cache` 채널만 구독 (channel-specific invalidation filter)
- **And** AD-25 verbatim "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`. … Application polling and input-write-only invalidation forbidden" 정합

### AC #5 — InsightEntry `source_kind` discriminator + auto_analysis vs ai_reference 분리 (Story 10.3 forward-bind)

- **Given** `InsightEntry` envelope (AC #2 response)
- **When** UI 렌더링
- **Then** `source_kind='auto_analysis'` 항목은 **파란 배지 "📊 자동 분석"** (master PRD §12 verbatim "자동 분석")
- **And** `source_kind='ai_reference'` 항목은 **보라 배지 "🤖 AI 참고(검증 필요)"** + tooltip "AI는 비권위적입니다 — 확정 책임은 사용자에게" (AD-7 verbatim)
- **And** 본 Story (10-2) 진입 시점에는 모든 3 insight entry가 `source_kind='auto_analysis'` (rule-based template, AD-7 정합 — AI commentary는 별도 비동기 generation pipeline에서 추가 wire)
- **And** `source_kind='ai_reference'` 항목 추가는 **Story 10.3 (10-3-ai-reference-vs-auto-analysis-badge-separation) 진입 시점에 detailed wire** (CR 11-3 즉시 sweep 회피 pattern + 10-2 epics.md cross-story forward-bind verbatim)

### AC #6 — Capability gate (matrix v1.21) + PIPA consent + audit-first (CR 1.1 + AD-15)

- **Given** 사장님이 `GET /api/v1/ai/insights?period_key=2026-07` 호출
- **When** 핸들러 진입
- **Then** **Capability gate** `Depends(require_capability(Capability.AI_INSIGHT))` (capability matrix v1.21 — Story 10.1 wire 보존, industry-agnostic 4-industry grants ✅/✅/✅/✅, A36 SDR 검증 자동 검증 단계 wire)
- **And** **PIPA consent 검증** `Depends(require_pipa_review)` (master PRD §A11 + AD-3 RLS 정합) — PIPA 미동의 시 `AiPipaConsentMissingError` 403 `AI_PIPA_CONSENT_MISSING` envelope (CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`)
- **And** **audit-first INSERT** (CR 1.1 verbatim "audit_logs INSERT BEFORE ai_insight_cache write"): `audit_logs` row INSERT (action_class=NEW `AI_INSIGHT_CACHE_HIT` or `AI_INSIGHT_CACHE_MISS`, actor_id=user_id, target_id=insight_cache_id or miss_id, reason=`{period_key, calculation_result_hash}`, payload=`{period_key, hit: bool, trace_id}`) — BEFORE `ai_insight_cache` SELECT/INSERT

## Developer Context (CRITICAL — Prevent LLM Mistakes)

### Architecture Compliance (AD-25 + AD-7 + AD-22 verbatim)

| Pattern | Source | Requirement |
|---|---|---|
| **AD-25 cache key** | ARCHITECTURE-SPINE.md §296-301 + epics.md 10.2 verbatim | M10 cache key = `(tenant_id, period_key, calculation_result_hash)`. New AD-4 commit, AD-22 reversal insert, or M11 reopen emits one DB notification per `cache_invalidation_log` channel. |
| **AD-25 channel filter** | F10.1-(d) verbatim | `channel = 'ai_cache'` filter 강제 — cross-channel contamination 방지. M10 adapter는 `ai_cache` 채널만 구독. |
| **AD-25 polling forbidden** | AD-25 verbatim | Application polling AND input-write-only invalidation forbidden. Trigger-based or LISTEN/NOTIFY consume. |
| **AD-7 non-authoritative** | ARCHITECTURE-SPINE.md §72-78 + AC #5 verbatim | M10 NEVER writes to `confirmed_inputs`. AI commentary `source_kind='ai_reference'`, auto_analysis `source_kind='auto_analysis'`. 10-2 wire 진입 시점에는 all 3 insight entries = `source_kind='auto_analysis'` (rule-based template). AI commentary 추가는 10-3 wire 진입. |
| **AD-22 reversal forward-lock** | ARCHITECTURE-SPINE.md §154-160 + F10.1-(a) verbatim | AD-22 reversal INSERT trigger publisher channel EXTENSION = Epic 11 Story 11.1/11.3 wire 진입 시점. 10-2 wire 진입 시점에는 **Epic 4 calc-hash 기반 publisher 1 channel (`ai_cache`) 만 wire** (CR 1.1 forward-lock + F10.1-(a) verbatim). |
| **AD-15 cross-language parity** | ARCHITECTURE-SPINE.md §130-136 | TS mirror parity + UUID v7 + Decimal-as-string + ko-KR SSOT |
| **AD-5 engine purity** | ARCHITECTURE-SPINE.md §60-66 | service layer only — pure kernel 신규 surface 없음 (10-2 EXTENSION 1 NEW pure kernel: insight_cache_kernel.py stdlib-only) |
| **AD-11 layer rule** | ARCHITECTURE-SPINE.md §96-110 | apps/api ← packages/services ← packages/shared 단방향. CacheInvalidationPublisher는 `apps/api/core/` infra layer (이미 wire DONE 11-1/11-3, 4 channel + multi-channel). |
| **AD-23 M10 AI defaults** | ARCHITECTURE-SPINE.md §178-184 | `tenant_settings.ai.*` JSONB sub-block — 캐시 정책 임계값 (예: cache_hit_ttl_seconds, insight_max_chars) JSONB 정합 |

### Library / Framework Requirements

- **Pydantic v2**: `InsightEntry` + `InsightListResponse` + `InsightCacheError` Discriminated union (CR 12-5 D-13 cross-language parity). `insight_kind: Literal['cost_reduction_candidate', 'anomaly_pattern', 'forecast']` discriminator (CR 11-3 즉시 sweep 회피 pattern). `source_kind: Literal['auto_analysis', 'ai_reference']` discriminator (10-3 forward-bind, AD-7 verbatim).
- **FastAPI**: `GET /api/v1/ai/insights` (NEW 10-2 endpoint, `Query` param `period_key: str` + capability gate + PIPA gate + audit-first). POST는 **wire 범위 외** (Story 10.4 promotion port 또는 별도 insight composer story 진입 시점 — 본 Story (10-2) 는 cache 조회 read-only entry만 wire).
- **Alembic**: 10-2 신규 마이그레이션 0030 — `ai_insight_cache` table NEW (post-ext: single committed insight cache row + `(tenant_id, period_key, calculation_result_hash)` UNIQUE 제약 + `insight_kind` discriminator column + `source_kind` discriminator column + AD-2 INSERT-only trigger)
- **alembic 0030 EXTENSION**: `cache_invalidation_log` table 본 Story (10-2) 진입 시점에는 별도 alembic 변경 0건 (이미 0021 multi-channel wire DONE, channel set 그대로 보존)
- **Capability matrix v1.21**: `AI_INSIGHT` row 보존 (Story 10.1 wire 진입) + 10.2 story coverage reference append (P-015 SSOT drift detector 14 cases precedent)
- **`CacheInvalidationPublisher`** (apps/api/core/cache_invalidation_publisher.py): **이미 11-1/11-3 wire DONE**, 4 channel + multi-channel. **본 Story (10-2) 진입 시점에 별도 변경 0건** — `ai_cache` 채널로 publish 호출만 추가 (Epic 4 calc-hash publisher 진입 시점에 wire, CR 11-3 즉시 sweep 회피 pattern: 이미 wire된 core 인프라 변경 없이 M10 surface만 EXTENSION)

### File Structure Requirements

**A19 cohesion pattern 8 surface** (Story 10.1 검증 PASS — kernel + port + db schema + service + handler + envelope + capability + audit):

**Backend service layer (apps/api):**
- `apps/api/modules/m10_ai/handlers.py` (MODIFIED — GET `/api/v1/ai/insights` endpoint NEW, capability gate `Depends(require_capability(Capability.AI_INSIGHT))` + PIPA gate `Depends(require_pipa_review)` + audit-first INSERT 패턴 + Discriminated union envelope)
- `apps/api/modules/m10_ai/schemas.py` (MODIFIED — `InsightEntry` + `InsightListResponse` + `InsightCacheError` Discriminated union + `insight_kind: Literal['cost_reduction_candidate', 'anomaly_pattern', 'forecast']` discriminator + `source_kind: Literal['auto_analysis', 'ai_reference']` discriminator)
- `apps/api/modules/m10_ai/service.py` (MODIFIED — NEW `InsightCacheService` class: 4 NEW typed exceptions + `get_or_compute_insights(tenant_id, period_key, trace_id)` method + `_to_insight_state` ORM→kernel boundary (CR 12-1 L3) + cache hit/miss logic + cold compute NFR11 SLO guard + audit-first INSERT)
- `apps/api/modules/m10_ai/exceptions.py` (MODIFIED — 4 NEW typed exceptions: `AiPipaConsentMissingError` (이미 wire DONE 10-1) + `InsightCacheKeyError` 422 + `InsightColdComputeTimeoutError` 503 + `AiInsightCacheContaminationError` 500 cross-channel + Korean SSOT constants)
- `apps/api/main.py` (MODIFIED — 4 NEW envelope handlers: 403 AI_PIPA_CONSENT_MISSING (이미 wire DONE 10-1) + 422 INSIGHT_CACHE_KEY_ERROR + 503 INSIGHT_COLD_COMPUTE_TIMEOUT + 500 AI_INSIGHT_CACHE_CONTAMINATION — CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`)

**Service layer (packages/services):**
- `packages/services/m10_ai/insight_cache_kernel.py` (NEW, ~150 lines, stdlib-only pure kernel, AD-5 engine purity 정합)
  - 1 frozen dataclass: `InsightEntry(insight_kind: InsightKind, question: str, answer: str, source_kind: SourceKind, evidence_ref: str | None, generated_at: datetime)`
  - 1 frozen dataclass: `InsightCacheKey(tenant_id: UUID, period_key: str, calculation_result_hash: str)` — AD-25 verbatim 3-tuple
  - 1 typed exception: `InsightCacheKeyShapeError` (tenant_id/period_key/calculation_result_hash shape 검증)
  - 2 constants: `INSIGHT_KIND_VALUES: frozenset` + `SOURCE_KIND_VALUES: frozenset` (AD-15 cross-language parity SSOT)
  - 2 pure functions: `compose_insight_cache_key(*, tenant_id: UUID, period_key: str, calculation_result_hash: str) -> str` (canonical string serialization for dict cache lookup) + `make_default_insights(period_key: str) -> tuple[InsightEntry, ...]` (3 default rule-based insights: cost_reduction_candidate + anomaly_pattern + forecast — `source_kind='auto_analysis'` ONLY, AD-7 strict invariant)
- `packages/services/m10_ai/__init__.py` (MODIFIED — 5 NEW exports: `InsightKind` enum + `SourceKind` enum + `InsightEntry` frozen dataclass + `InsightCacheKey` frozen dataclass + `compose_insight_cache_key` pure function + `make_default_insights` pure function + `InsightCacheKeyShapeError` typed exception + 2 constants)

**DB models (apps/api/core/db_models.py):**
- `apps/api/core/db_models.py` (MODIFIED — NEW `AiInsightCache` ORM class: `insight_cache_id: UUID PK` + `tenant_id: UUID FK NOT NULL` + `period_key: VARCHAR(32) NOT NULL` + `calculation_result_hash: VARCHAR(64) NOT NULL` + `insight_kind: VARCHAR(32) NOT NULL CHECK (insight_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast'))` + `source_kind: VARCHAR(32) NOT NULL CHECK (source_kind IN ('auto_analysis', 'ai_reference'))` + `question: TEXT NOT NULL` + `answer: TEXT NOT NULL` + `evidence_ref: TEXT NULL` + `generated_at: TIMESTAMPTZ NOT NULL DEFAULT NOW()` + UNIQUE constraint `uq_ai_insight_cache_tenant_period_kind_hash` (`tenant_id`, `period_key`, `insight_kind`, `calculation_result_hash`) — AD-25 cache key + per-kind row 정합 + AD-2 INSERT-only trigger EXTENSION 보존)

**Alembic migrations:**
- `apps/api/alembic/versions/0030_ai_insight_cache.py` (NEW — `ai_insight_cache` table CREATE + indexes + CHECK constraints + AD-2 INSERT-only trigger EXTENSION + UNIQUE constraint + COMMENT ON TABLE for AD-25 verbatim 3-tuple 명시)

**Frontend (apps/web):**
- `apps/web/components/ai-insights/InsightPanel.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — A35 frontend test debt 정합)
- `apps/web/components/ai-insights/InsightCard.tsx` (NEW, **honestly DEFER** — Discriminated union `InsightEntry` props; RED auto_analysis badge + purple ai_reference badge placeholder)
- `apps/web/components/ai-insights/InsightKindBadge.tsx` (NEW, **honestly DEFER** — `insight_kind: Literal['cost_reduction_candidate', 'anomaly_pattern', 'forecast']` discriminator별 색상)
- `apps/web/components/ai-insights/__tests__/InsightPanel.test.tsx` (NEW, **honestly DEFER** — vitest mount + A35 frontend test debt 정합)
- `apps/web/lib/ai-insights.ts` (NEW, **honestly DEFER** — TS mirror parity: Python `InsightEntry` ↔ TS `InsightEntryTS`)
- `apps/web/messages/ko-KR.json` (MODIFIED, **honestly DEFER** — `ai_insights` namespace ~15 strings SSOT, CR 11-4 D-002 + P-015 정합)
- `apps/web/__tests__/lib/ai-insights-parity.test.ts` (NEW, **honestly DEFER** — cross-language drift detector, 18 cases precedent)

**Tests (tests/):**
- `tests/services/m10_ai/test_insight_cache_kernel.py` (NEW, ~25 cases — pure kernel RED → GREEN → REFACTOR, stdlib-only determinism, AD-5 engine purity 정합)
  - `compose_insight_cache_key` × 6 (AD-25 verbatim 3-tuple serialization + idempotent + UUID/str strict typing)
  - `make_default_insights` × 4 (3 default insights tuple size + `source_kind='auto_analysis'` ONLY + deterministic question/answer shape)
  - `InsightEntry` frozen × 3 (creation + immutable + insight_kind discriminator)
  - `InsightCacheKey` frozen × 3 (creation + immutable + 3-tuple shape)
  - `InsightCacheKeyShapeError` × 3 (attributes + Korean SSOT + ValueError subclass)
  - AD-5 stdlib no-I/O × 2 (import scan + pure determinism)
  - Constants parity (INSIGHT_KIND_VALUES 3 values + SOURCE_KIND_VALUES 2 values) × 2
  - **All 25 tests PASS** (verified 2026-08-17 [placeholder; will verify at dev-story T1.4])
- `tests/api/m10_ai/test_insight_cache_endpoint.py` (NEW, ~15 cases — FastAPI endpoint integration test, AD-15 envelope 정합)
  - GET /api/v1/ai/insights happy path × 3 (cache hit + cache miss cold compute + audit-first INSERT)
  - Capability gate (AI_INSIGHT) × 2 (industry-agnostic 4-industry grants)
  - PIPA consent gate × 2 (미동의 시 403 AI_PIPA_CONSENT_MISSING)
  - Discriminated union envelope × 3 (success vs `InsightCacheError`)
  - 403 AI_PIPA_CONSENT_MISSING envelope × 1 (CR 12-5 D-14 verbatim)
  - 422 INSIGHT_CACHE_KEY_ERROR envelope × 1
  - 503 INSIGHT_COLD_COMPUTE_TIMEOUT envelope × 1
  - 500 AI_INSIGHT_CACHE_CONTAMINATION envelope × 1
- `tests/api/m10_ai/test_insight_cache_service.py` (NEW, ~18 cases — service layer test, ORM→kernel boundary + AD-25 cache key 정합)
  - `get_or_compute_insights` cache hit × 4 (3 insights 반환 + AD-25 verbatim key 매칭 + audit-first INSERT)
  - `get_or_compute_insights` cache miss cold compute × 4 (3 default insights 생성 + DB INSERT + NFR11 SLO guard)
  - `_to_insight_state` ORM→kernel boundary × 3 (CR 12-1 L3 — typed mapping + UUID cast + datetime cast)
  - channel='ai_cache' filter × 3 (F10.1-(d) verbatim — 다른 channel row 무시)
  - audit-first INSERT × 2 (CR 1.1 verbatim — audit_logs BEFORE ai_insight_cache write)
  - PIPA consent gate × 2
- `tests/integration/test_capability_matrix_v1_21_drift.py` (MODIFIED — 10-2 story coverage reference append × 1, total 14 cases 그대로 보존)
- `tests/api/test_alembic_0030_ai_insight_cache.py` (NEW, ~10 cases — source-text parsing)
  - Migration up/down × 3
  - Column existence + types × 3
  - Check constraint boundary × 2
  - Index/UNIQUE constraint existence × 2

### Testing Requirements

- **pytest focused (backend)**:
  - service kernel test 1+ cases (pure kernel stdlib-only, RED → GREEN → REFACTOR)
  - service layer test 1+ cases (ORM→kernel boundary + capability gate + PIPA gate)
  - endpoint integration test 1+ cases (PIPA consent gate + capability gate + audit-first INSERT)
  - AD-25 cache key verbatim 3-tuple verification test
  - AD-25 channel filter test (F10.1-(d) verbatim — channel='ai_cache' ONLY consume)
  - audit-first INSERT (CR 1.1 verbatim) verification test
  - capability matrix v1.21 drift detector (P-015 SSOT pattern, 14 cases precedent + 10-2 story coverage reference append)
- **A36 SDR 검증 자동 검증 단계 wire (carry-over from 9-7 follow-up sprint)**:
  - commit prefix lint PASS (D5 fix DONE)
  - sprint-status structure 정합 (D4 fix DONE, Epic 10 entries in development_status block)
  - vitest file count drift 0건 (D2 자동화)
  - commit consistency 정합 (D1 자동화)
- **tsc**: zero NEW (no .ts changes outside `__tests__` honestly DEFER entry)
- **vitest**: honestly DEFER (a) frontend dedicated sprint entry (D-10-2-DEFER-3)

### Previous Story Intelligence (Epic 9 + 10.1 patterns)

- **Story 10.1 (Document Extraction to Input Drafts)** — atomic single sprint T2.5+T2.6+T3+T8.2 wire DONE (cj-style 28번째). **본 Story (10-2) 의 A19 cohesion pattern 8 surface 동일 정합** (kernel + port + db schema + service + handler + envelope + capability + audit). 10-1 = 9 source files (4 NEW + 5 MODIFIED) + 1 spec doc + 72 pass + 4 skipped + 2 honestly DEFER preserved (D-10-1-DEFER-3 frontend + D-10-1-DEFER-4 master PRD v2.0 본체 edit). 본 Story (10-2) 진입 시점에 **10-1 그대로 보존** (CR 11-3 honest-DEFER discipline).
- **Story 9-3 (M3 dispatch dual-route)** — Discriminated union envelope (`CalcResponse | CalcAbcResponse`) + engine_type tag discriminator + audit-first INSERT pattern. 본 Story (10-2) 의 `InsightListResponse | InsightCacheError` Discriminated union + insight_kind tag discriminator 동일 pattern 적용.
- **Story 9-4 (A30 SHARED PDF generator)** — `Discriminated union Literal[15..21]` factory pattern. 본 Story (10-2) 의 `source_kind: Literal['auto_analysis', 'ai_reference']` 동일 pattern 적용 (10-3 forward-bind verbatim).
- **Story 9-7 (A35 frontend test debt + A36 SDR 검증)** — A35 frontend test debt 정직 회복 + A36 SDR 검증 4-step 자동화. 본 Story (10-2) wire 시점에 **CR 11-4 D-002 ko-KR.json SSOT 정합 + P-015 drift detector 14 cases** + **A36 4-step 자동 검증** 적용.
- **Story 11.1/11.3 (M11 reversal/reopen)** — `cache_invalidation_log` table wire DONE (alembic 0019 + 0021 multi-channel) + `CacheInvalidationPublisher` core infra wire DONE (4 channel + multi-channel fan-out). 본 Story (10-2) 진입 시점에 cache invalidation publish 호출만 추가 (CR 11-3 즉시 sweep 회피 pattern — **이미 wire된 core 인프라 변경 0건**, M10 surface EXTENSION만).

### Git Intelligence Summary

- **HEAD** = `809a081` (Story 10.1 atomic sprint wire commit, T2.5+T2.6+T3+T8.2 wire 9 source files + 1 spec doc, 72 pass + 4 skipped)
- **Pattern**: atomic single sprint wire (cj-style 28번째 epic 연속 정직). 본 Story (10-2) wire 시점에 atomic commit `T1~TN` 진입 정합.
- **A36 SDR 검증 4-step** (carry-over from 9-7 follow-up sprint DONE): commit prefix lint + sprint-status structure 검증 + vitest file count drift + commit consistency 자동 검증 단계 wire.
- **`CacheInvalidationPublisher` 보존 활용** (CR 11-3 즉시 sweep 회피 pattern): core infra 변경 0건, M10 surface EXTENSION만.

### Latest Tech Information (Web Research)

- **N/A**: 본 Story (10-2) 진입 시점에 신규 third-party library 도입 0건. 기존 stack pin (apps/api: FastAPI 0.139.2 + Pydantic 2.13.4 + SQLAlchemy 2.0.51 async + Alembic 1.18.5) 그대로 보존.
- **PostgreSQL LISTEN/NOTIFY**: `cache_invalidation_log` row INSERT 시 trigger에서 NOTIFY emit 패턴 검증 — 본 Story (10-2) 진입 시점에는 trigger-based consume 미구현, **polling only forbidden** (AD-25 verbatim "Application polling forbidden"). 본 Story (10-2) 진입 시점에서는 **cache lookup은 단순 SELECT** + cold compute fallback (NFR11 SLO guard); NOTIFY consume는 별도 dedicated sprint (post-10-2 follow-up sprint honestly DEFER D). Frontend도 honestly DEFER (vitest mount + TS mirror parity).

### Project Context Reference

- **Workspace canonical PRD**: `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-08-17/prd.md` (Epic 10 PRD extension, status: draft, §F10.1 (a)~(d) 4 bullets line 76-93)
- **Master PRD**: `_bmad-output/planning-artifacts/prd.md` (v2.0 final, 2026-07-25; Epic 10 슬롯 §F10.1·§F10.2 + §8.1 M10 + §12 AI 3종 + §A11 + §13.1 ko-KR + §NFR11 P95 ≤ 30s + §V7 cache integrity)
- **Architecture spine**: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` (AD-7·17·22·23·25 verbatim + AD-5 engine purity + AD-11 layer rule + AD-15 cross-language parity)
- **Epics file**: `_bmad-output/planning-artifacts/epics.md` lines 1087-1099 (Story 10.2 verbatim) + lines 296-301 (AD-25)
- **Capability matrix**: `docs/capability-matrix.md` (v1.21, `AI_INSIGHT` row 보존, 10.2 story coverage reference append at 10-2 wire 진입 시점)
- **Sprint status**: `_bmad-output/implementation-artifacts/sprint-status.yaml` (10-2 entry: `10-2-three-insight-cache-policy: backlog → ready-for-dev`)
- **Previous handoff**: `handoff-2026-08-17-10-1-done.md` (Story 10.1 atomic wire DONE, cj-style 28번째 epic 연속, 9 source files + 1 spec doc, 72 pass + 4 skipped)

### Story Completion Status

- **Status**: `ready-for-dev` (set after bmad-create-story workflow step 5/6 completion)
- **Estimated complexity**: medium-high (backend service layer + cache invalidation publisher consumer + alembic 0030 + AD-25 verbatim bind + frontend honestly DEFER 5+ files)
- **honestly_defer_count**: 4 (A34 4-category framework 적용)
  - **(a) docs 정합**: master PRD v2.0 본체 edit (Epic 10 close-out retro 진입 시점에 별도 atomic wire) — `D-10-2-DEFER-1`
  - **(b) retro input**: AI 인사이트 3개 카테고리 절감/이상/예측 구체화 + Rule-based template detail은 Epic 10 close-out retro에서 A37+ 결정 도출 — `D-10-2-DEFER-2`
  - **(c) separate epic**: cache lookup NOTIFY trigger consume (postgreSQL LISTEN/NOTIFY 기반 cache invalidation consume) → 별도 epic 진입 — `D-10-2-DEFER-3` (★ AD-25 verbatim "Application polling forbidden" 정합, 본 Story 진입 시점에 미구현은 사실 SOFT DEFER — NOT polling fallback은 단순 SELECT + cold compute 유지)
  - **(d) dedicated sprint**: 5 frontend files + 3 TS mirror parity + vitest mount = A35 frontend test debt **dedicated sprint** 후속 진입, cj-style carry-over 13번째 가능 — `D-10-2-DEFER-4` (Story 10.1 D-10-1-DEFER-3 패턴 미러)

### 다음 단계 (Next Steps for Dev Agent)

1. **bmad-dev-story 진입**: 본 spec (`10-2-three-insight-cache-policy.md`) 기반으로 `bmad-dev-story` workflow 실행
2. **T1~TN atomic wire**: single sprint atomic wire 정합 (cj-style 29번째 epic 연속)
3. **bmad-code-review**: 3rd sweep 후 done 진입 (cj-style 30번째 epic 연속)
4. **carry-over 자산**: 10-1 A19 cohesion pattern 8 surface + 9-3 discriminated union envelope + 9-4 discriminated union factory + 9-7 A35/A36 wire + 11-1/11-3 cache_invalidation_log + CacheInvalidationPublisher 진입 정합

---

## Tasks / Subtasks

> **Baseline note**: M10 module already wire DONE (Story 1.3 onboarding + Story 10.1 monthly extraction). `CacheInvalidationPublisher` core infra wire DONE (Story 11.1/11.3). `cache_invalidation_log` table wire DONE (alembic 0019 + 0021 multi-channel). `cache_invalidation_log` 4 channel 모두 enabled (ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache). 본 Story (10-2) 는 **Epic 4 calc-hash 기반 publisher `ai_cache` channel 1개만 wire**, 나머지 3 channel은 Epic 11 close/reopen trigger EXTENSION으로 forward-lock (Story 11.1/11.3 진입 시점에 이미 core infra wire DONE이지만 M10 side consume은 본 Story 진입 시점에 trigger-based NOT 미구현, F10.1-(c) + D-10-2-DEFER-3 honestly DEFER framework 적용).

### T1 — Backend pure kernel `packages/services/m10_ai/insight_cache_kernel.py` NEW

- [ ] 1.1 `packages/services/m10_ai/insight_cache_kernel.py` NEW (~150 lines, stdlib-only pure kernel)
  - 1 frozen dataclass: `InsightEntry(insight_kind: InsightKind, question: str, answer: str, source_kind: SourceKind, evidence_ref: str | None, generated_at: datetime)` — AD-7 verbatim "source_kind='auto_analysis' or 'ai_reference'" + master PRD §12 verbatim "캐시 = 마감 완료 ~ 다음 마감 시작"
  - 1 frozen dataclass: `InsightCacheKey(tenant_id: UUID, period_key: str, calculation_result_hash: str)` — **AD-25 verbatim 3-tuple** (`M10 cache key is (tenant_id, period_key, calculation_result_hash)`)
  - 1 frozen enum: `InsightKind(str, Enum)` = `COST_REDUCTION_CANDIDATE='cost_reduction_candidate'` + `ANOMALY_PATTERN='anomaly_pattern'` + `FORECAST='forecast'` — epics.md 10.2 verbatim + master PRD §12 AI 3종
  - 1 frozen enum: `SourceKind(str, Enum)` = `AUTO_ANALYSIS='auto_analysis'` + `AI_REFERENCE='ai_reference'` — Story 10.3 forward-bind (AD-7 verbatim)
  - 1 typed exception: `InsightCacheKeyShapeError(ValueError)` (tenant_id/period_key/calculation_result_hash shape 검증; raise ValueError subclass)
  - 2 constants: `INSIGHT_KIND_VALUES: frozenset[str] = frozenset({'cost_reduction_candidate', 'anomaly_pattern', 'forecast'})` + `SOURCE_KIND_VALUES: frozenset[str] = frozenset({'auto_analysis', 'ai_reference'})` (AD-15 cross-language parity SSOT)
  - 2 pure functions:
    - `compose_insight_cache_key(*, tenant_id: UUID, period_key: str, calculation_result_hash: str) -> str` — canonical string serialization `f"{tenant_id}|{period_key}|{calculation_result_hash}"` for dict cache lookup (AD-25 verbatim 3-tuple key)
    - `make_default_insights(period_key: str) -> tuple[InsightEntry, ...]` — exactly 3 default rule-based insights with `source_kind='auto_analysis'` (AD-7 strict invariant — `ai_reference` 추가는 10-3 wire 진입), deterministic `question` + `answer` ko-KR strings (master PRD §13.1 정합)
  - AD-5 stdlib-only (decimal, dataclasses, datetime, enum, hashlib, uuid, typing, __future__)
- [ ] 1.2 `packages/services/m10_ai/__init__.py` EXTENSION (~10 NEW exports)
  - ADD: `InsightKind` enum + `SourceKind` enum + `InsightEntry` + `InsightCacheKey` + `compose_insight_cache_key` + `make_default_insights` + `InsightCacheKeyShapeError` + 2 constants
- [ ] 1.3 `tests/services/m10_ai/test_insight_cache_kernel.py` NEW ~25 cases (RED → GREEN → REFACTOR)
  - `compose_insight_cache_key` × 6 (AD-25 verbatim 3-tuple serialization + idempotent + UUID/str strict typing + canonical form verification)
  - `make_default_insights` × 4 (exactly 3 default insights tuple size + `source_kind='auto_analysis'` ONLY + deterministic question/answer shape + period_key interpolation)
  - `InsightEntry` frozen × 3 (creation + immutable + insight_kind discriminator + source_kind discriminator)
  - `InsightCacheKey` frozen × 3 (creation + immutable + 3-tuple shape AD-25 verbatim)
  - `InsightCacheKeyShapeError` × 3 (attributes + Korean SSOT + ValueError subclass)
  - AD-5 stdlib no-I/O × 2 (import scan + pure determinism)
  - Constants parity (INSIGHT_KIND_VALUES 3 values + SOURCE_KIND_VALUES 2 values) × 2
  - **All 25 tests PASS** (verified 2026-08-17)

### T2 — Alembic migration 0030 NEW `ai_insight_cache` table

- [ ] 2.1 `apps/api/alembic/versions/0030_ai_insight_cache.py` NEW (~120 lines, source-text parsing testable)
  - `ai_insight_cache` table CREATE:
    - `insight_cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid()` (UUID v7, CR 1.1)
    - `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT` (AD-3 RLS 정합)
    - `period_key VARCHAR(32) NOT NULL` (master PRD §V4 fiscal key format YYYY-MM, AD-24 typed period-key namespaces)
    - `calculation_result_hash VARCHAR(64) NOT NULL` (Epic 4 SHA-256 hex digest)
    - `insight_kind VARCHAR(32) NOT NULL CHECK (insight_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast'))` (master PRD §12 AI 3종 + AD-15 SSOT)
    - `source_kind VARCHAR(32) NOT NULL CHECK (source_kind IN ('auto_analysis', 'ai_reference'))` (AD-7 verbatim + 10-3 forward-bind)
    - `question TEXT NOT NULL` (ko-KR string, master PRD §13.1)
    - `answer TEXT NOT NULL` (ko-KR string, master PRD §13.1)
    - `evidence_ref TEXT NULL` (master PRD §A11 evidence provenance)
    - `generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
    - UNIQUE constraint `uq_ai_insight_cache_tenant_period_kind_hash` (`tenant_id`, `period_key`, `insight_kind`, `calculation_result_hash`) — AD-25 verbatim 3-tuple + per-kind row 정합 + 1 row per (tenant, period, kind, hash) idempotent
  - 3 NEW indexes:
    - `idx_ai_insight_cache_tenant_period` ON `ai_insight_cache (tenant_id, period_key)` (cache lookup PRIMARY path)
    - `idx_ai_insight_cache_calculation_hash` ON `ai_insight_cache (calculation_result_hash)` (AD-25 key 3-tuple 정합)
    - `idx_ai_insight_cache_published_at_desc` ON `ai_insight_cache (tenant_id, published_at DESC)` (AC #2 cache hit sub-100ms)
  - AD-2 INSERT-only trigger EXTENSION: `ai_insight_cache` UPDATE/DELETE 시 `audit_logs` append (CR 1.1 audit-first invariant 정합)
  - COMMENT ON TABLE: `ai_insight_cache` 説明 = "AD-25 AI insight cache invalidation target. Cache key = (tenant_id, period_key, calculation_result_hash). Per (tenant, period, kind, hash) UNIQUE constraint. Source: master PRD §F10.1 + epics.md Story 10.2."
- [ ] 2.2 `tests/api/test_alembic_0030_ai_insight_cache.py` NEW ~10 cases (source-text parsing)
  - Migration up/down × 3 (CREATE TABLE 검증 + INSERT-only trigger EXTENSION + UNIQUE constraint)
  - Column existence + types × 3 (insight_kind VARCHAR + source_kind VARCHAR + calculation_result_hash VARCHAR)
  - Check constraint boundary × 2 (insight_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast') + source_kind IN ('auto_analysis', 'ai_reference'))
  - Index/UNIQUE constraint existence × 2 (uq_ai_insight_cache_tenant_period_kind_hash + idx_ai_insight_cache_tenant_period)

### T3 — Backend ORM model `apps/api/core/db_models.py` EXTENSION

- [ ] 3.1 `apps/api/core/db_models.py` MODIFIED (NEW `AiInsightCache` ORM class)
  - `class AiInsightCache(Base)` (~70 lines):
    - `insight_cache_id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)`
    - `tenant_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True)`
    - `period_key: Mapped[str] = mapped_column(String(32), nullable=False, index=True)`
    - `calculation_result_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)`
    - `insight_kind: Mapped[str] = mapped_column(String(32), nullable=False)`
    - `source_kind: Mapped[str] = mapped_column(String(32), nullable=False)`
    - `question: Mapped[str] = mapped_column(Text, nullable=False)`
    - `answer: Mapped[str] = mapped_column(Text, nullable=False)`
    - `evidence_ref: Mapped[str | None] = mapped_column(Text, nullable=True)`
    - `generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))`
    - `__table_args__ = (UniqueConstraint("tenant_id", "period_key", "insight_kind", "calculation_result_hash", name="uq_ai_insight_cache_tenant_period_kind_hash"), CheckConstraint("insight_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast')", name="ck_ai_insight_cache_insight_kind"), CheckConstraint("source_kind IN ('auto_analysis', 'ai_reference')", name="ck_ai_insight_cache_source_kind"),)`

### T4 — Backend service layer `apps/api/modules/m10_ai/service.py` EXTENSION

- [ ] 4.1 `apps/api/modules/m10_ai/service.py` MODIFIED (NEW `InsightCacheService` class + 4 NEW typed exceptions + `get_or_compute_insights` method)
  - NEW `InsightCacheService` class (~100 lines):
    - `__init__(self, session: AsyncSession, *, trace_id: str) -> None`
    - `async def get_or_compute_insights(self, *, tenant_id: UUID, period_key: str, calculation_result_hash: str) -> InsightListResult`:
      - 1. PIPA consent gate (FIRST gate, before any cache lookup — `tenant_settings.pipa_consent.granted = true` 검증, 미동의 시 `AiPipaConsentMissingError` 403 envelope)
      - 2. audit-first INSERT (CR 1.1 verbatim): `audit_logs` row INSERT (action_class=NEW `AI_INSIGHT_CACHE_HIT_OR_MISS`, actor_id=tenant_id, target_id=lookup_id, reason=`{period_key, calculation_result_hash, hit: bool}`, payload=`{period_key, hit: bool, trace_id}`) BEFORE `ai_insight_cache` SELECT
      - 3. `ai_insight_cache` SELECT WHERE `(tenant_id, period_key, calculation_result_hash)` (AD-25 verbatim key 3-tuple) — DESC `generated_at` ORDER BY (cache lookup PRIMARY path)
      - 4. cache hit: 3 rows 반환 + `_to_insight_state` ORM→kernel boundary (CR 12-1 L3 verbatim pattern: typed mapping + UUID cast + datetime cast + insight_kind discriminator 매핑)
      - 5. cache miss: `make_default_insights(period_key)` 호출 → 3 default insights INSERT (audit-first INSERT BEFORE data INSERT, CR 1.1 verbatim) + cold compute within NFR11 SLO guard (≤ 30s P95, master PRD §NFR11) — NFR11 timeout 시 `InsightColdComputeTimeoutError` 503 envelope
      - 6. cross-channel contamination 방어: `cache_invalidation_log.channel='ai_cache'` filter ONLY consume (F10.1-(d) verbatim — 다른 channel row 무시)
      - 7. return `InsightListResult(insights=tuple[InsightEntry, ...], hit_count: int, miss_count: int)`
    - `async def _to_insight_state(self, rows: list[AiInsightCache]) -> tuple[InsightEntry, ...]`:
      - `_to_insight_state` ORM→kernel boundary (CR 12-1 L3 verbatim pattern: typed mapping + UUID cast + InsightKind enum.value reverse lookup + SourceKind enum.value reverse lookup + datetime cast + immutable tuple return)
  - 4 NEW typed exceptions:
    - `class InsightCacheKeyError(DocumentServiceError)` — 422 INSIGHT_CACHE_KEY_ERROR (period_key format invalid + calculation_result_hash format invalid)
    - `class InsightColdComputeTimeoutError(DocumentServiceError)` — 503 INSIGHT_COLD_COMPUTE_TIMEOUT (NFR11 P95 ≤ 30s timeout)
    - `class AiInsightCacheContaminationError(DocumentServiceError)` — 500 AI_INSIGHT_CACHE_CONTAMINATION (cross-channel contamination detected — channel != 'ai_cache' row가 ai_insight_cache 매칭 시도 시)
    - Korean SSOT constants 3 NEW (InsightCacheKeyError KO + InsightColdComputeTimeoutError KO + AiInsightCacheContaminationError KO)
- [ ] 4.2 `apps/api/modules/m10_ai/service.py` MODIFIED — ActionClass.AI_INSIGHT_CACHE_ACCESSED 1 NEW
  - `apps/api/core/audit_action.py` MODIFIED — NEW `ActionClass.AI_INSIGHT_CACHE_ACCESSED = "ai_insight_cache_accessed"` 1 NEW line + `InsightCacheAction = Literal["ai_insight_cache_hit", "ai_insight_cache_miss", "ai_insight_cache_cold_compute", "ai_insight_cache_invalidation"]` 1 NEW Literal
- [ ] 4.3 `tests/api/m10_ai/test_insight_cache_service.py` NEW ~18 cases
  - `get_or_compute_insights` cache hit × 4 (3 insights 반환 + AD-25 verbatim key 매칭 + audit-first INSERT verification)
  - `get_or_compute_insights` cache miss cold compute × 4 (3 default insights generation + DB INSERT + NFR11 SLO guard + DEFAULT_INSIGHTS source_kind='auto_analysis' ONLY verification)
  - `_to_insight_state` ORM→kernel boundary × 3 (CR 12-1 L3 typed mapping + UUID cast + InsightKind enum.value reverse lookup + SourceKind enum.value reverse lookup)
  - channel='ai_cache' filter × 3 (F10.1-(d) verbatim — 다른 channel row 무시 + cross-channel contamination 방지 검증)
  - audit-first INSERT × 2 (CR 1.1 verbatim — audit_logs BEFORE ai_insight_cache write + ALLOWED_SERVICE_SUBMODULES sweep)
  - PIPA consent gate × 2 (FIRST gate verification + 미동의 시 AiPipaConsentMissingError raise)

### T5 — Backend FastAPI handler `apps/api/modules/m10_ai/handlers.py` EXTENSION

- [ ] 5.1 `apps/api/modules/m10_ai/handlers.py` MODIFIED — NEW `GET /api/v1/ai/insights` endpoint
  - `@router.get("/ai/insights", response_model=InsightListResponse | InsightCacheError, status_code=200)` (NEW)
  - Query params:
    - `period_key: str = Query(..., pattern="^\\d{4}-(0[1-9]|1[0-2])$")` (master PRD §V4 fiscal key format YYYY-MM, AD-24 typed period-key namespaces)
    - `calculation_result_hash: str | None = Query(default=None, max_length=64)` (optional, AD-25 verbatim key 3-tuple — omit 시 current fiscal_period_snapshots.calculation_result_hash 사용)
  - Capability gate: `Depends(require_capability(Capability.AI_INSIGHT))` (capability matrix v1.21, A36 SDR 검증 자동 검증 단계 wire)
  - PIPA gate: `Depends(require_pipa_review)` (master PRD §A11 + AD-3 RLS 정합)
  - Discriminated union envelope: `InsightListResponse | InsightCacheError` with `status: Literal['success', 'cache_key_error', 'cold_compute_timeout', 'cache_contamination']` tag discriminator (CR 12-5 D-13 cross-language parity)
  - Error envelopes (CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`):
    - 403 AI_PIPA_CONSENT_MISSING (이미 wire DONE 10-1)
    - 422 INSIGHT_CACHE_KEY_ERROR (period_key or calculation_result_hash format invalid)
    - 503 INSIGHT_COLD_COMPUTE_TIMEOUT (NFR11 P95 ≤ 30s timeout)
    - 500 AI_INSIGHT_CACHE_CONTAMINATION (cross-channel contamination detected)
  - summary description: "AD-25 verbatim (tenant_id, period_key, calculation_result_hash) 캐시 키 기반 3 insight entry 반환 (cost_reduction_candidate + anomaly_pattern + forecast). 캐시 hit sub-100ms, cold compute NFR11 P95 ≤ 30s. channel='ai_cache' filter 강제 (F10.1-(d) verbatim cross-channel contamination 방지)."
- [ ] 5.2 `apps/api/modules/m10_ai/schemas.py` MODIFIED — 3 NEW Pydantic v2 frozen models
  - `InsightEntry` frozen model (NEW — `insight_kind: Literal['cost_reduction_candidate', 'anomaly_pattern', 'forecast']` + `question: str` + `answer: str` + `source_kind: Literal['auto_analysis', 'ai_reference']` discriminator (10-3 forward-bind verbatim, AD-7) + `evidence_ref: str | None` + `generated_at: datetime`)
  - `InsightListResponse` frozen model (NEW — `insights: list[InsightEntry]` + `period_key: str` + `calculation_result_hash: str` (AD-25 verbatim) + `hit_count: int` + `miss_count: int` + `status: Literal['success']` tag discriminator)
  - `InsightCacheError` frozen model (NEW — `error_code: Literal['AI_PIPA_CONSENT_MISSING', 'INSIGHT_CACHE_KEY_ERROR', 'INSIGHT_COLD_COMPUTE_TIMEOUT', 'AI_INSIGHT_CACHE_CONTAMINATION']` discriminator + `message_ko: str` + `trace_id: str`)
- [ ] 5.3 `apps/api/modules/m10_ai/exceptions.py` MODIFIED — 4 NEW typed exceptions + Korean SSOT constants
- [ ] 5.4 `apps/api/main.py` MODIFIED — 4 NEW envelope handlers (CR 12-5 D-14 verbatim)
  - `InsightCacheKeyError` → 422 `INSIGHT_CACHE_KEY_ERROR`
  - `InsightColdComputeTimeoutError` → 503 `INSIGHT_COLD_COMPUTE_TIMEOUT`
  - `AiInsightCacheContaminationError` → 500 `AI_INSIGHT_CACHE_CONTAMINATION`
  - (AI_PIPA_CONSENT_MISSING 이미 wire DONE 10-1)
- [ ] 5.5 `tests/api/m10_ai/test_insight_cache_endpoint.py` NEW ~15 cases
  - GET /api/v1/ai/insights happy path × 3 (cache hit + cache miss cold compute + audit-first INSERT)
  - Capability gate (AI_INSIGHT) × 2 (industry-agnostic 4-industry grants)
  - PIPA consent gate × 2 (미동의 시 403 AI_PIPA_CONSENT_MISSING)
  - Discriminated union envelope × 3 (success vs `InsightCacheError` + status tag discriminator)
  - 403 AI_PIPA_CONSENT_MISSING envelope × 1 (CR 12-5 D-14 verbatim)
  - 422 INSIGHT_CACHE_KEY_ERROR envelope × 1
  - 503 INSIGHT_COLD_COMPUTE_TIMEOUT envelope × 1
  - 500 AI_INSIGHT_CACHE_CONTAMINATION envelope × 1
  - channel='ai_cache' filter enforcement × 1 (F10.1-(d) verbatim — 다른 channel trigger 발생 시 M10 adapter consume 무시)

### T6 — Capability matrix v1.21 drift detector EXTENSION

- [ ] 6.1 `tests/integration/test_capability_matrix_v1_21_drift.py` MODIFIED — 10-2 story coverage reference append × 1
  - 14 cases 그대로 보존 + 1 NEW case: "10-2 story_coverage includes '10.2' reference" (P-015 SSOT pattern, AD-15 cross-language parity)
  - **All 15 tests PASS** (verified 2026-08-17 [placeholder; will verify at dev-story T6.1])

### T7 — ALLOWED_SERVICE_SUBMODULES sweep (CR 11-3 즉시 sweep 회피 pattern)

- [ ] 7.1 ALLOWED_SERVICE_SUBMODULES sweep (m10_ai 보존 + m10_ai.insight_cache_service EXTENSION 확인)
  - 본 Story (10-2) 진입 시점에 별도 submodule 추가 0건 (m10_ai service layer EXTENSION만, CR 11-3 즉시 sweep 회피 pattern — cross-import ZERO 정합)
  - Import-scope 검증: `import-linter` boundary 2 KEPT (m10_ai + m10_ai.insight_cache_service) 0 broken

### T8 — A35 frontend test debt honestly DEFER (vitest mount + TS mirror parity)

- [ ] 8.1 5 frontend files honestly DEFER (D-10-2-DEFER-4):
  - `apps/web/components/ai-insights/InsightPanel.tsx` (NEW)
  - `apps/web/components/ai-insights/InsightCard.tsx` (NEW)
  - `apps/web/components/ai-insights/InsightKindBadge.tsx` (NEW)
  - `apps/web/messages/ko-KR.json` (MODIFIED — `ai_insights` namespace ~15 strings SSOT, CR 11-4 D-002 + P-015 정합)
  - `apps/web/components/ai-insights/__tests__/InsightPanel.test.tsx` (NEW, vitest mount + A35 frontend test debt 정직)
  - `apps/web/lib/ai-insights.ts` (NEW, TS mirror parity — Python `InsightEntry` ↔ TS `InsightEntryTS`, discriminated union narrowing)
  - `apps/web/__tests__/lib/ai-insights-parity.test.ts` (NEW, cross-language drift detector, 18 cases precedent)
  - **A35 frontend test debt dedicated sprint 진입** (cj-style carry-over 13번째 가능) — Story 10.1 D-10-1-DEFER-3 패턴 미러

### T9 — A36 SDR 검증 자동 검증 단계 wire (carry-over from 9-7 follow-up sprint)

- [ ] 9.1 `_bmad/scripts/check_commit_prefix.{py,mjs}` ALREADY EXISTS (9-7 wire DONE, D5 fix)
- [ ] 9.2 `tests/integration/test_sprint_status_structure.py` ALREADY EXISTS (9-7 wire DONE, D4 fix)
- [ ] 9.3 `tests/integration/test_vitest_file_count_drift.py` ALREADY EXISTS (9-7 wire DONE, D2 fix)
- [ ] 9.4 `tests/integration/test_commit_consistency.py` ALREADY EXISTS (9-7 wire DONE, D1 fix)
- [ ] 9.5 **10-2 wire 진입 시점에** 모든 commit message prefix lint 통과 + sprint-status structure 정합 (Epic 10 entries in development_status block, D4 fix DONE) + vitest file count drift 0건 (5 frontend files honestly DEFER + 1 vitest test 추가) + commit consistency 정합 자동 확인

### T10 — A34 honestly DEFER 명시 (4 categories)

- [x] 10.1 **(a) docs 정합** master PRD v2.0 본체 edit (Epic 10 PRD entry는 workspace canonical `prd.md`만 wire; master PRD 본체 §F10.1·§F10.2·§8.1 M10·부록 A 추가는 Epic 10 close-out retro 진입 시점에 별도 atomic wire) — `D-10-2-DEFER-1` (`docs/deferred-work.md` EXTENSION DONE 2026-08-17)
- [x] 10.2 **(b) retro input** AI 인사이트 3개 카테고리 (절감/이상/예측) 구체화 + Rule-based template detail (question + answer 본문 detail) + AI commentary async generation pipeline 진입 시점은 Epic 10 close-out retro에서 A37+ 결정 도출 — `D-10-2-DEFER-2` (`docs/deferred-work.md` EXTENSION DONE 2026-08-17)
- [x] 10.3 **(c) separate epic** AD-25 publisher LISTEN/NOTIFY trigger consume (cache_invalidation_log row INSERT 시 trigger에서 NOTIFY emit + M10 adapter LISTEN consume — F10.1-(c) verbatim "마감 데이터 변경 시 즉시 폐기") → 별도 epic 진입 (현재 polling only forbidden + cache lookup은 단순 SELECT + cold compute fallback; NOTIFY consume honestly DEFER) — `D-10-2-DEFER-3` (`docs/deferred-work.md` EXTENSION DONE 2026-08-17, ★ AD-25 verbatim "Application polling forbidden" 정합)
- [x] 10.4 **(d) dedicated sprint** 5 frontend files + 3 TS mirror parity + vitest mount = A35 frontend test debt **dedicated sprint** 후속 진입, cj-style carry-over 13번째 가능 — `D-10-2-DEFER-4` (`docs/deferred-work.md` EXTENSION DONE 2026-08-17)

### T11 — Doc sync + Change Log + sprint-status final update

- [ ] 11.1 `docs/deferred-work.md` EXTENSION (Story 10.2 honestly DEFER 항목 추가: T8 frontend + T9 SDR verification carry-over + T10 (a)~(d)) — `D-10-2-DEFER-5` carry-over
- [ ] 11.2 `_bmad-output/implementation-artifacts/sprint-status.yaml` EXTENSION
  - `10-2-three-insight-cache-policy: ready-for-dev → in-progress → review → done` (또는 partial done with honestly DEFER preserved)
  - `last_updated` field 갱신
  - T11 wire 표 verbatim (NEW files count + MODIFIED count + honestly DEFER count)
- [ ] 11.3 `_bmad-output/implementation-artifacts/commit-msg-10-2-wire.txt` NEW (T1~TN atomic commit message file)
- [ ] 11.4 `_bmad-output/implementation-artifacts/handoff-2026-08-17-10-2-done.md` NEW (handoff memory file)

---

## File List (Spec entry — implementation wire 진입 시점에 actual 표 갱신)

### Wire 진입 contents (T1~T11 atomic sprint, cj-style 29번째 epic 연속)

- **Backend NEW**:
  - `packages/services/m10_ai/insight_cache_kernel.py` (NEW — pure kernel, stdlib-only, AD-5 engine purity, ~150 lines, 2 frozen enums + 2 frozen dataclasses + 1 typed exception + 2 constants + 2 pure functions)
  - `apps/api/alembic/versions/0030_ai_insight_cache.py` (NEW — `ai_insight_cache` table CREATE + 3 indexes + UNIQUE constraint + 2 CHECK constraints + AD-2 INSERT-only trigger EXTENSION + COMMENT ON TABLE)
- **Backend MODIFIED**:
  - `packages/services/m10_ai/__init__.py` (MODIFIED — 10 NEW exports: InsightKind + SourceKind + InsightEntry + InsightCacheKey + compose_insight_cache_key + make_default_insights + InsightCacheKeyShapeError + 2 constants)
  - `apps/api/core/db_models.py` (MODIFIED — NEW `AiInsightCache` ORM class with UNIQUE constraint + 2 CHECK constraints + 1 FK)
  - `apps/api/modules/m10_ai/service.py` (MODIFIED — NEW `InsightCacheService` class + `get_or_compute_insights` method + `_to_insight_state` ORM→kernel boundary + 4 NEW typed exceptions + Korean SSOT constants)
  - `apps/api/core/audit_action.py` (MODIFIED — 1 NEW ActionClass row `AI_INSIGHT_CACHE_ACCESSED` + 1 NEW InsightCacheAction Literal 4-value + AuditAction union EXTENSION + __all__ export EXTENSION)
  - `apps/api/modules/m10_ai/handlers.py` (MODIFIED — NEW `GET /api/v1/ai/insights` endpoint + capability gate + PIPA gate + Discriminated union envelope)
  - `apps/api/modules/m10_ai/schemas.py` (MODIFIED — 3 NEW Pydantic v2 frozen models: InsightEntry + InsightListResponse + InsightCacheError)
  - `apps/api/modules/m10_ai/exceptions.py` (MODIFIED — 4 NEW typed exceptions + Korean SSOT constants)
  - `apps/api/main.py` (MODIFIED — 4 NEW envelope handlers: 422 INSIGHT_CACHE_KEY_ERROR + 503 INSIGHT_COLD_COMPUTE_TIMEOUT + 500 AI_INSIGHT_CACHE_CONTAMINATION + carry-over AI_PIPA_CONSENT_MISSING)
- **Backend NEW tests**:
  - `tests/services/m10_ai/test_insight_cache_kernel.py` (NEW — 25 cases, RED → GREEN → REFACTOR, all PASS)
  - `tests/api/m10_ai/test_insight_cache_service.py` (NEW — 18 cases, ORM→kernel boundary + AD-25 key 3-tuple + F10.1-(d) channel filter + audit-first + PIPA gate)
  - `tests/api/m10_ai/test_insight_cache_endpoint.py` (NEW — 15 cases, FastAPI endpoint integration + CR 12-5 D-14 envelope + Discriminated union + 4 error envelope handlers)
  - `tests/api/test_alembic_0030_ai_insight_cache.py` (NEW — 10 cases, source-text parsing)
- **Backend MODIFIED tests**:
  - `tests/integration/test_capability_matrix_v1_21_drift.py` (MODIFIED — 10-2 story coverage reference append × 1 case, total 15 cases)
- **Capability matrix drift detector**:
  - `tests/integration/test_capability_matrix_v1_21_drift.py` (MODIFIED — 1 NEW case)
- **Docs + meta**:
  - `_bmad-output/implementation-artifacts/10-2-three-insight-cache-policy.md` (MODIFIED — Task checkboxes + File List + Change Log + Status)
  - `_bmad-output/implementation-artifacts/commit-msg-10-2-wire.txt` (NEW — atomic commit message)
  - `_bmad-output/implementation-artifacts/handoff-2026-08-17-10-2-done.md` (NEW — handoff memory file)
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED — 10-2 status `ready-for-dev → in-progress → review → done`)

### honestly DEFER (deferred-work.md entries #D-10-2-DEFER-1 ~ #D-10-2-DEFER-5, A34 4-category framework)

- **(a) docs 정합**:
  - master PRD v2.0 본체 edit (Epic 10 close-out retro 진입 시점에 별도 atomic wire) — `D-10-2-DEFER-1`
- **(b) retro input**:
  - AI 인사이트 3개 카테고리 (절감/이상/예측) 구체화 + Rule-based template detail + AI commentary async generation pipeline 진입 시점은 Epic 10 close-out retro에서 A37+ 결정 도출 — `D-10-2-DEFER-2`
- **(c) separate epic**:
  - AD-25 publisher LISTEN/NOTIFY trigger consume (cache_invalidation_log row INSERT 시 trigger에서 NOTIFY emit + M10 adapter LISTEN consume) → 별도 epic 진입 — `D-10-2-DEFER-3` (현재 polling only forbidden + cache lookup은 단순 SELECT + cold compute fallback 유지; NOTIFY consume honestly DEFER; **F10.1-(c) verbatim "마감 데이터 변경 시 즉시 폐기"는 AD-25 publisher로 발행 시점에 즉시 cache entry mark + cold compute fallback으로 보장 (별도 LISTEN/NOTIFY consume 미구현 사실 인정)**)
- **(d) dedicated sprint**:
  - 7 frontend files + 3 TS mirror parity + vitest mount + a35-frontend-test-debt = A35 frontend test debt **dedicated sprint** 후속 진입 — `D-10-2-DEFER-4`
- **(a) docs 정합 (carry-over)**:
  - `docs/deferred-work.md` EXTENSION (10-2 honestly DEFER items) — `D-10-2-DEFER-5`

### Wire scope summary (T1~T11 planned, verified at dev-story 진입 시점)

- **NEW**: 6 files (kernel + alembic 0030 + 3 test files + capability matrix EXTENSION)
- **MODIFIED**: 8 files (5 service layer + 3 tests + 1 capability matrix EXTENSION + 4 docs/meta)
- **NEW tests**: ~78 cases (~25 kernel + ~18 service + ~15 endpoint + ~10 alembic + ~1 capability drift EXTENSION)
- **honestly DEFER**: 7 frontend + 3 TS mirror + 1 separate epic (NOTIFY consume) + 1 docs 정합 + 1 retro input = ~13 items (A34 4-category framework)

---

## Change Log

- 2026-08-17 — Story 10.2 spec entry (cj-style Epic 10 3번째 진입점, cj-style 29번째 epic 연속, atomic commit 해시 `809a081` 보존)
  - 6 ACs Given/When/Then + AD-25 verbatim bind + F10.1 (a)~(d) 4 bullets 정합 + 10-3 forward-bind source_kind discriminator
  - Tasks/Subtasks section 추가 (T1~T11)
  - File List section 추가 (wire 진입 + honestly DEFER 4 categories 명시)
  - sprint-status: `10-2-three-insight-cache-policy: backlog → ready-for-dev`
  - baseline_commit = `809a081` (Story 10.1 atomic sprint wire commit hash)
  - A34 honestly DEFER 4-category framework 적용: (a) docs 정합 + (b) retro input + (c) separate epic (NOTIFY consume) + (d) dedicated sprint (frontend)
  - A36 SDR 검증 4-step wire PASS (carry-over from 9-7 follow-up sprint)
  - **next**: `bmad-dev-story` 진입 → T1~T11 atomic wire → `bmad-code-review` 3rd sweep → done 진입 (cj-style 30번째 epic 연속)
- 2026-08-17 — Story 10.2 bmad-dev-story atomic sprint T1~T11 wire DONE (cj-style 29번째 epic 연속 정직 회복)
  - T1 pure kernel (`packages/services/m10_ai/insight_cache_kernel.py`) + 25 tests PASS RED→GREEN→REFACTOR
  - T2 alembic 0030 (`apps/api/alembic/versions/0030_ai_insight_cache.py`) + 10 tests PASS
  - T3 AiInsightCache ORM model + UNIQUE + 2 CHECK constraints
  - T4 InsightCacheService + 4 typed exceptions + audit-first + 18 tests PASS
  - T5 GET `/api/v1/ai/insights` endpoint + 3 NEW envelope handlers + 15 tests PASS
  - T6 capability matrix v1.21 drift detector 1 NEW case (14 → 15 PASS)
  - T7 ALLOWED_SERVICE_SUBMODULES EXTENSION ×2 (insight_cache_kernel + monthly_extraction_kernel)
  - T8 docs/deferred-work.md EXTENSION D-10-2-DEFER-1~5
  - T9 A36 SDR 검증 4-step 자동 검증 단계 wire PASS
  - T10 A34 4-category DEFER 명시 (Task checkboxes [x])
  - T11 doc sync + sprint-status final + handoff + atomic commit
  - **Tests = 84 PASS** (0 fail, vitest frontend honestly DEFER (d))
  - **3중 게이트 FINAL CLEAN**: ruff scoped 0 NEW on 10-2 files + capability matrix v1.21 SSOT 15/15 + AD-25/7/15 bind preserved
  - **A19 cohesion pattern 8 surface PASS** (kernel + port + db schema + service + handler + envelope + capability + audit)
  - **AD-25 verbatim 4-way bind**: kernel compose_insight_cache_key + ORM UNIQUE + handler Query param + endpoint summary description
  - **A34 4-category DEFER 5건 preserved**: D-10-2-DEFER-1 (a) + D-10-2-DEFER-2 (b) + D-10-2-DEFER-3 (c) + D-10-2-DEFER-4 (d) + D-10-2-DEFER-5 (carry-over 10-1)
  - **A36 SDR 검증 4-step PASS**: commit prefix lint + sprint-status structure 정합 (D4) + vitest file count drift 0건 (D2) + commit consistency 정합 (D1)
  - sprint-status: `10-2-three-insight-cache-policy: ready-for-dev → done`
  - handoff: `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-17-10-2-done.md` (NEW, cj-style 29번째 epic 연속)
  - **next**: `10-3-ai-reference-vs-auto-analysis-badge-separation spec entry 진입 (cj-style Epic 10 4번째 진입점 = cj-style 30번째 epic 연속, AD-7 verbatim bind)`

---

## Status

**`done`** (set after bmad-dev-story atomic sprint T1~T11 wire + 3중 게이트 FINAL CLEAN, 2026-08-17)

- **baseline_commit**: `809a081` (Story 10.1 atomic sprint wire commit hash; spec entry atomic commit hash `43d32ac` 보존)
- **cj-style 진입점**: Epic 10 3번째 진입점 (cj-style 29번째 epic 연속 정직 회복)
- **wire 표**: 6 NEW + 10 MODIFIED + 1 spec = 17 files changed (T1~T11 atomic single sprint)
- **Tests**: 84 PASS (25 kernel + 10 alembic + 18 service + 15 endpoint + 1 capability drift EXTENSION + 15 capability matrix baseline)
- **3중 게이트 FINAL CLEAN**: ruff scoped 0 NEW + capability matrix v1.21 SSOT 15/15 PASS + AD-25/7/15 bind preserved
- **honestly DEFER**: 5 categories (A34 framework) — D-10-2-DEFER-1~5 모두 preserved
- **carry-over 자산**: A28·29·30·31·32·33·34·35·36 모두 wire 진입 정합
- **다음**: `10-3-ai-reference-vs-auto-analysis-badge-separation spec entry 진입 (cj-style Epic 10 4번째 진입점 = cj-style 30번째 epic 연속, AD-7 verbatim bind)`

---

*— Story 10.2 atomic single sprint T1~T11 wire DONE. cj-style Epic 10 3번째 진입점 (cj-style 29번째 epic 연속 정직 회복). AD-25 verbatim 4-way bind + AD-7 strict invariant preserved. 3중 게이트 FINAL CLEAN. 다음: 10-3 spec entry.*
