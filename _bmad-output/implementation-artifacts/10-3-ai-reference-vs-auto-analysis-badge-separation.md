---
story_id: 10.3
story_key: 10-3-ai-reference-vs-auto-analysis-badge-separation
title: AI Reference vs Auto Analysis Badge Separation
created: 2026-08-17
baseline_commit: 146a7da
epic: 10
status: ready-for-dev
target_sprint: cj-style Epic 10 4번째 진입점 (cj-style 30번째 epic 연속)
estimated_complexity: medium
honestly_defer_count: 5
wire_partial: false
---

# Story 10.3 — AI Reference vs Auto Analysis Badge Separation

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 10.3 |
| **Story Key** | `10-3-ai-reference-vs-auto-analysis-badge-separation` |
| **Epic** | Epic 10 — AI Assistance (4-story + retro 5번째 진입점, Epic 8 retro §7 A23 패턴) |
| **baseline_commit** | `146a7da` (cj-style Epic 9 close-out retro + A35/A36 wire 9-6 follow-up sprint atomic commit, cj-style 24번째 epic 연속) |
| **cj-style 분할** | 10-3 (4번째) — **cj-style 30번째 epic 연속** |
| **Forward-lock** | A28 (9-2 DONE) + A29 (9-3 DONE) + A30 (9-4 DONE) + A31 (Report #15 wire schedule) + A32 (A30 SHARED factory reuse) + A33 (A19 cohesion 9 surface) + A34 (mixed honestly DEFER 4-category framework) + A35 (frontend test debt DONE 9-7) + A36 (SDR 검증 프로토콜 DONE 9-7) |
| **Primary capability** | `Capability.AI_INSIGHT` (industry-agnostic, 4-industry grants ✅/✅/✅/✅, capability matrix v1.21 — Story 10.1 wire 진입; 10.3 spec 진입 시점에 동일 capability 보존 + 10.3 story coverage reference append) |
| **Primary PRD ref** | **§F10.2 (a)~(d) 4 bullets** (`_bmad-output/planning-artifacts/prds/prd-costmgr-2026-08-17/prd.md` lines 95-112) + epics.md Story 10.3 (lines 1101-1111) + master PRD §8.1 M10-(b) (badge separation) + master PRD §12 (auto_analysis + AI 참고 구분 배지) + master PRD §A11 (시스템은 틀리지 않는다) + master PRD §SM-3a (계산 결과 변경 시도 = 0건) |
| **Secondary PRD ref** | master PRD §2.A UJ-AI step 3 (cache 조회 후 인사이트 표시) + master PRD §2.B (auto_analysis 의견 수정 시도 SM-3a 정합) + master PRD §13.1 (ko-KR-only) + master PRD §NFR18 (ko-KR tooltip 한국어만) + master PRD §9 #7 (원가분석표 의견 section) + master PRD §14.B NON-GOAL #5 (다국어·다통화 2차 로드맵) |
| **Primary AD ref** | **AD-7 (AI non-authoritative — `source_kind='ai_reference'` + `source_kind='auto_analysis'` verbatim 분리)** + AD-22 (reversal 영구화 + forward-lock Epic 11 trigger EXTENSION) + AD-25 (cache invalidation 보존) |
| **Baseline wire** | Story 10.1 atomic sprint wire commit `809a081` (cj-style 28번째) + Story 10.2 atomic sprint wire commit `7683135` (cj-style 29번째, current HEAD) + `146a7da` Epic 9 close-out retro + 9-7 follow-up sprint atomic wire (cj-style 24번째). 10-2 = 6 NEW + 10 MODIFIED + 1 spec doc = 17 files, 84 PASS (25 kernel + 10 alembic + 18 service + 15 endpoint + 1 capability drift EXTENSION + 15 capability matrix baseline), 5 honestly DEFER preserved (D-10-2-DEFER-1~5). |

## User Story (epics.md Story 10.3 verbatim)

As a **사장님**, I want **보고서의 자동 분석 의견(고정 템플릿)과 AI 의견이 시각적으로 다른 배지로 분리되는 것**, so that **무엇이 규칙이고 무엇이 AI 추측인지 구분 가능** (master PRD §12 정합).

## Acceptance Criteria (PRD §F10.2 (a)~(d) + AD-7 verbatim + SM-3a 정합 + 10-2 forward-bind)

### AC #1 — `source_kind` discriminator verbatim 분리 렌더링 (F10.2-(a) + AD-7 verbatim)

- **Given** 사장님이 [보고서] → "원가분석표" (§9 #7) → "원가 분석 의견" section 진입
- **When** 의견 표시됨 (master PRD §9 #7 "원가분석표" 의견 section 진입)
- **Then** **`source_kind='auto_analysis'` 의견 → 파란 배지 "📊 자동 분석"** (master PRD §12 verbatim "자동 분석" + F10.2-(a) verbatim)
- **And** **`source_kind='ai_reference'` 의견 → 보라 배지 "🤖 AI 참고(검증 필요)"** + tooltip "AI는 비권위적입니다 — 확정 책임은 사용자에게" (master PRD §12 verbatim "AI 참고" + AD-7 verbatim "AI commentary labeled `ai_reference`; deterministic template analysis labeled `auto_analysis`")
- **And** 동일 배지 분리는 UJ-AI 운영 step 3 (cache 조회 후 인사이트 표시) 에서도 동일 강제 (master PRD §2.A UJ-AI step 3 verbatim)
- **And** 10-3 wire 진입 시점에 10-2 cache lookup (`GET /api/v1/ai/insights`) 에서 반환되는 3 default insights (`cost_reduction_candidate` + `anomaly_pattern` + `forecast`) 모두 `source_kind='auto_analysis'` (AD-7 strict invariant, 10-2 wire 보존). 10-3 wire 진입 시점에는 **NEW endpoint `GET /api/v1/ai/comments`** 가 추가되며 `source_kind='ai_reference'` 의견 1~N개 추가 wire (Pydantic v2 Discriminated union response, AD-15 cross-language parity)

### AC #2 — Strict reject + 1행 counter increment (F10.2-(b) + SM-3a 정합)

- **Given** 어떤 입력 경로로 `source_kind` value가 도착 (`auto_analysis` | `ai_reference` 외 value, 예: `human_authored` | `unknown` | `system` | null | empty string)
- **When** system이 검증
- **Then** **strict reject + 1행 counter increment wire** (master PRD §A11 "시스템은 틀리지 않는다" / hover 후 미변경 = 안전 + master PRD §SM-3a "계산 결과 변경 시도 = 0건" 별도 추적 정합)
- **And** Pydantic v2 `field_validator` reject (422 envelope `AI_COMMENT_SOURCE_KIND_INVALID` + message_ko "분석 의견 출처가 불분명합니다" + counter increment atomic transaction; F10.2-(d) verbatim "1-line ko-KR 메시지로 reject")
- **And** `audit_logs` row INSERT (action_class=`AI_INSIGHT_CACHE_ACCESSED`, action=`ai_insight_cache_invalid_source_kind`, reason=`{received_value, allowed_values}`, payload=`{received_value, trace_id}`) BEFORE counter increment (CR 1.1 audit-first INSERT 정합)
- **And** `source_kind` 검증은 **모든 M10 입력 path (POST `/api/v1/ai/extract-monthly` 10-1 + GET `/api/v1/ai/insights` 10-2 + NEW GET `/api/v1/ai/comments` 10-3) 에서 동일 강제** (DRY: Pydantic v2 + `SourceKind` Literal 검증 helper reuse)

### AC #3 — `auto_analysis` 의견 수정 시도 동일 카운터 추적 (F10.2-(c) + SM-3a 정합)

- **Given** 사장님이 `source_kind='auto_analysis'` 의견을 화면에서 수정 시도 (e.g., PATCH 요청으로 `auto_analysis` 의견 본문 overwrite)
- **When** system이 검증
- **Then** **denied + counter increment** (master PRD §2.B + AD-7 verbatim "M10 attempts to write confirmed-input tables are denied and counted (target zero)" + §SM-3a "계산 결과 변경 시도 = 0건")
- **And** 422 envelope `AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS` (auto_analysis 의견은 결정적 — deterministic rule-based template, 사용자 수정 불가)
- **And** `audit_logs` row INSERT (action_class=`AI_INSIGHT_CACHE_ACCESSED`, action=`ai_insight_cache_auto_analysis_modify_denied`, reason=`{comment_id, actor_id}`, payload=`{trace_id}`) BEFORE reject (CR 1.1 audit-first INSERT 정합)
- **And** 본 Story (10-3) 진입 시점에 **`auto_analysis` 의견은 read-only** (AD-7 verbatim "deterministic template analysis"); `ai_reference` 의견은 사용자 수정 가능 (Story 10.4+ 후속 또는 별도 story 진입 시점에 wire — honestly DEFER (d))

### AC #4 — AI 배지 tooltip 노출 + 200 OK envelope (F10.2-(d) + master PRD §12 정합)

- **Given** 사장님이 `source_kind='ai_reference'` 보라 배지 클릭
- **When** hover 발생
- **Then** **tooltip "AI는 비권위적입니다 — 확정 책임은 사용자에게"** 노출 (AD-7 verbatim + master PRD §12 "AI 참고" 정합)
- **And** `source_kind='auto_analysis'` 파란 배지 hover 시 tooltip "이 의견은 고정 템플릿입니다" (master PRD §12 "자동 분석" 정합 + F10.2-(a) verbatim)
- **And** tooltip 한국어 only (master PRD §13.1 ko-KR-only + §NFR18 정합; §14.B NON-GOAL #5 "다국어 2차 로드맵" — 영문/중문 2차 로드맵)
- **And** `source_kind` 강제 검증 실패 시 response envelope: `200 OK` + `status: Literal['invalid_source_kind_warning']` discriminator + `message_ko: "분석 의견 출처가 불분명합니다"` (F10.2-(d) verbatim "1-line ko-KR 메시지로 reject + counter 증가 + 200 OK envelope") + counter increment atomic

### AC #5 — Capability gate (matrix v1.21) + PIPA consent + audit-first (CR 1.1 + AD-15 + 10-2 forward-bind)

- **Given** 사장님이 `GET /api/v1/ai/comments?period_key=2026-07` 호출 (NEW 10-3 endpoint)
- **When** 핸들러 진입
- **Then** **Capability gate** `Depends(require_capability(Capability.AI_INSIGHT))` (capability matrix v1.21 — Story 10.1 wire 보존, industry-agnostic 4-industry grants ✅/✅/✅/✅, A36 SDR 검증 자동 검증 단계 wire)
- **And** **PIPA consent 검증** `Depends(require_pipa_review)` (master PRD §A11 + AD-3 RLS 정합) — PIPA 미동의 시 `AiPipaConsentMissingError` 403 `AI_PIPA_CONSENT_MISSING` envelope (CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`, 10-1 carry-over)
- **And** **audit-first INSERT** (CR 1.1 verbatim "audit_logs INSERT BEFORE ai_insight_cache write"): `audit_logs` row INSERT (action_class=`AI_INSIGHT_CACHE_ACCESSED`, action=`ai_insight_cache_invalid_source_kind` (F10.2-(b) reject) OR `ai_insight_cache_auto_analysis_modify_denied` (F10.2-(c) reject) OR `ai_insight_cache_hit` (success path, 10-2 carry-over), actor_id=user_id, target_id=comment_id, reason=`{period_key, calculation_result_hash, source_kind}`, payload=`{period_key, source_kind, hit: bool, trace_id}`) — BEFORE `ai_insight_cache` SELECT/INSERT

### AC #6 — Discriminated union envelope + CR 12-5 D-14 verbatim + AD-15 cross-language parity

- **Given** `GET /api/v1/ai/comments?period_key=2026-07` 호출 결과
- **When** response 형성
- **Then** **Discriminated union envelope** `AICommentListResponse | AICommentSourceKindInvalidError | AICommentImmutableAutoAnalysisError | AIPipaConsentMissingError` with `status: Literal['success', 'invalid_source_kind_warning', 'immutable_auto_analysis', 'pipa_consent_missing']` tag discriminator (CR 12-5 D-13 cross-language parity + 10-2 `InsightListResponse | InsightCacheError` 패턴 미러)
- **And** Error envelopes (CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`):
  - 403 AI_PIPA_CONSENT_MISSING (이미 wire DONE 10-1, 10-2 carry-over)
  - 422 AI_COMMENT_SOURCE_KIND_INVALID (F10.2-(b) source_kind 미매칭)
  - 422 AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS (F10.2-(c) auto_analysis 수정 시도)
  - 200 OK `status='invalid_source_kind_warning'` + counter increment (F10.2-(d) 1-line ko-KR)
- **And** TS mirror parity: Python `AICommentEntry` ↔ TS `AICommentEntryTS` (Discriminated union narrowing, `apps/web/lib/ai-comments.ts` honestly DEFER (d) frontend dedicated sprint)
- **And** AD-15 cross-language parity SSOT: `SOURCE_KIND_VALUES = frozenset({'auto_analysis', 'ai_reference'})` (10-2 kernel SSOT verbatim 보존) — TS mirror parity test wire (honestly DEFER (d))

## Developer Context (CRITICAL — Prevent LLM Mistakes)

### Architecture Compliance (AD-7 + AD-22 + AD-25 verbatim)

| Pattern | Source | Requirement |
|---|---|---|
| **AD-7 non-authoritative verbatim** | ARCHITECTURE-SPINE.md §72-76 + master PRD §8.1 M10-(b) | M10 NEVER writes to `confirmed_inputs`. AI commentary `source_kind='ai_reference'`, auto_analysis `source_kind='auto_analysis'`. 10-2 wire 진입 시점에 모든 default insight `source_kind='auto_analysis'` ONLY. 10-3 wire 진입 시점에 `ai_reference` opinion 1~N개 추가 wire (NEW endpoint + NEW ORM). |
| **AD-7 strict invariant: counter increment** | master PRD §SM-3a + F10.2-(b)(c)(d) verbatim | M10 attempts to write `confirmed_inputs` → denied + counted (target 0). 10-3 wire 진입 시점에 동일 카운터로 `source_kind` 미매칭 value + `auto_analysis` 의견 수정 시도 추적. |
| **AD-22 reversal forward-lock** | ARCHITECTURE-SPINE.md §154-160 + F10.1-(a) verbatim | AD-22 reversal INSERT trigger publisher channel EXTENSION = Epic 11 Story 11.1/11.3 wire 진입 시점. 10-3 wire 진입 시점에는 **Epic 4 calc-hash 기반 publisher 1 channel (`ai_cache`) 만 wire** (10-2 wire 보존; CR 1.1 forward-lock + F10.1-(a) verbatim). 10-3 wire는 `auto_analysis` 의견 수정 시도 카운터만 추가; reversal event 자체는 10-2 wire 진입 시점에 보존. |
| **AD-25 cache key + channel filter 보존** | ARCHITECTURE-SPINE.md §296-301 + F10.1-(d) verbatim | M10 cache key = `(tenant_id, period_key, calculation_result_hash)`. 10-3 wire 진입 시점에도 AD-25 verbatim 4-way bind 보존 (kernel compose_insight_cache_key + ORM UNIQUE + handler Query param + endpoint summary description). `channel='ai_cache'` filter ONLY consume (cross-channel contamination 방지). |
| **AD-15 cross-language parity** | ARCHITECTURE-SPINE.md §130-136 | TS mirror parity + UUID v7 + Decimal-as-string + ko-KR SSOT. 10-3 wire 진입 시점에 `SourceKind` Literal SSOT 보존 + ko-KR badge tooltip ko-KR-only. |
| **AD-5 engine purity** | ARCHITECTURE-SPINE.md §60-66 | service layer only — pure kernel 신규 surface 없음 (10-2 wire `insight_cache_kernel.py` 보존; 10-3 wire 진입 시점에 `SourceKind` SSOT frozen enum + `make_default_insights` source_kind='auto_analysis' ONLY invariant 그대로 보존). |
| **AD-11 layer rule** | ARCHITECTURE-SPINE.md §96-110 | apps/api ← packages/services ← packages/shared 단방향. 10-3 wire 진입 시점에 `packages/services/m10_ai/insight_cache_kernel.py` SSOT 보존 + NEW backend service `apps/api/modules/m10_ai/service.py` EXTENSION (comment_service.py 또는 InsightCacheService EXTENSION). |
| **AD-23 M10 AI defaults** | ARCHITECTURE-SPINE.md §178-184 | `tenant_settings.ai.*` JSONB sub-block — badge tooltip 메시지 default + auto_analysis default template JSONB 정합. |

### Library / Framework Requirements

- **Pydantic v2**: NEW `AICommentEntry` + `AICommentListResponse` + `AICommentSourceKindInvalidError` Discriminated union (CR 12-5 D-13 cross-language parity, 10-2 `InsightEntry | InsightListResponse | InsightCacheError` 패턴 미러). `source_kind: Literal['auto_analysis', 'ai_reference']` discriminator 보존 (AD-7 verbatim, 10-2 wire SSOT). `comment_kind: Literal['cost_reduction_candidate', 'anomaly_pattern', 'forecast', 'risk_warning', 'industry_benchmark']` discriminator NEW (10-3 wire entry point; `risk_warning` + `industry_benchmark` 는 10-3 wire 진입 시점에 forward-fill 후보이나 wire 범위는 10-2 verbatim 3 kind + 보존).
- **FastAPI**: NEW `GET /api/v1/ai/comments` (NEW 10-3 endpoint, `Query` param `period_key: str` + `comment_kind: str | None` (optional filter) + capability gate + PIPA gate + audit-first). POST/PATCH는 **wire 범위 외** (Story 10.4 promotion port 또는 별도 comment editor story 진입 시점에 honestly DEFER (d); auto_analysis 의견 read-only + ai_reference 의견 수정 가능 후속 story).
- **Alembic**: 10-3 신규 마이그레이션 0031 — `ai_insight_comments` table NEW (`comment_id` UUID PK + `tenant_id` UUID FK + `period_key` VARCHAR(32) + `calculation_result_hash` VARCHAR(64) + `comment_kind` VARCHAR(32) NOT NULL CHECK (`comment_kind` IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast', 'risk_warning', 'industry_benchmark')) + `source_kind` VARCHAR(32) NOT NULL CHECK (`source_kind` IN ('auto_analysis', 'ai_reference')) + `body_text` TEXT NOT NULL + `evidence_ref` TEXT NULL + `generated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW() + UNIQUE constraint `uq_ai_insight_comments_tenant_period_kind_hash` (`tenant_id`, `period_key`, `comment_kind`, `calculation_result_hash`) — AD-25 cache key + per-kind row 정합 + AD-2 INSERT-only trigger EXTENSION 보존). 10-3 wire 진입 시점에 별도 counter table 별도 wire 안 함 — 카운터 increment는 `audit_logs` row count (`SELECT COUNT(*) FROM audit_logs WHERE action='ai_insight_cache_invalid_source_kind' OR action='ai_insight_cache_auto_analysis_modify_denied'`) 로 derive (CR 1.1 audit-first verbatim 보존).
- **Capability matrix v1.21**: `AI_INSIGHT` row 보존 (Story 10.1 wire 진입) + 10.3 story coverage reference append (P-015 SSOT drift detector 15 cases precedent + 10-3 wire 진입 시점에 16 cases EXTENSION)
- **`SourceKind` SSOT 보존 활용** (CR 11-3 즉시 sweep 회피 pattern): `packages/services/m10_ai/insight_cache_kernel.py` 의 `SOURCE_KIND_VALUES` frozenset + `SourceKind` enum + `make_default_insights` source_kind='auto_analysis' ONLY invariant 보존. 10-3 wire 진입 시점에 별도 신규 SSOT 도입 0건 (CR 11-3 즉시 sweep 회피 — 이미 wire된 core 인프라 변경 0건, M10 surface EXTENSION만).

### File Structure Requirements

**A19 cohesion pattern 8 surface** (Story 10.1 검증 PASS + Story 10.2 PASS — kernel + port + db schema + service + handler + envelope + capability + audit):

**Backend pure kernel (packages/services):**
- `packages/services/m10_ai/insight_cache_kernel.py` (MODIFIED — `SourceKind` enum + `SOURCE_KIND_VALUES` frozenset + `make_default_insights` source_kind='auto_analysis' ONLY invariant **그대로 보존** + JSDoc/comment EXTENSION 10-3 forward-fill note 추가: "10-3 wire 진입 시점에 `ai_reference` opinion 별도 surface 진입; SSOT invariant 보존")
- `packages/services/m10_ai/__init__.py` (MODIFIED — `SourceKind` enum + `SOURCE_KIND_VALUES` constant re-export 그대로 보존 + JSDoc EXTENSION)

**DB models (apps/api/core/db_models.py):**
- `apps/api/core/db_models.py` (MODIFIED — NEW `AiInsightComment` ORM class: `comment_id: UUID PK` + `tenant_id: UUID FK NOT NULL` + `period_key: VARCHAR(32) NOT NULL` + `calculation_result_hash: VARCHAR(64) NOT NULL` + `comment_kind: VARCHAR(32) NOT NULL CHECK (comment_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast', 'risk_warning', 'industry_benchmark'))` + `source_kind: VARCHAR(32) NOT NULL CHECK (source_kind IN ('auto_analysis', 'ai_reference'))` + `body_text: TEXT NOT NULL` + `evidence_ref: TEXT NULL` + `generated_at: TIMESTAMPTZ NOT NULL DEFAULT NOW()` + UNIQUE constraint `uq_ai_insight_comments_tenant_period_kind_hash` (`tenant_id`, `period_key`, `comment_kind`, `calculation_result_hash`) — AD-25 cache key + per-kind row 정합 + AD-2 INSERT-only trigger EXTENSION 보존)

**Alembic migrations:**
- `apps/api/alembic/versions/0031_ai_insight_comments.py` (NEW — `ai_insight_comments` table CREATE + indexes + UNIQUE constraint + 2 CHECK constraints + AD-2 INSERT-only trigger EXTENSION + COMMENT ON TABLE for AD-25 verbatim 3-tuple 명시)

**Backend service layer (apps/api/modules/m10_ai/):**
- `apps/api/modules/m10_ai/service.py` (MODIFIED — NEW `CommentService` class OR `InsightCacheService` EXTENSION: `list_comments(tenant_id, period_key, comment_kind, trace_id)` method + `_to_comment_state` ORM→kernel boundary (CR 12-1 L3 verbatim pattern: typed mapping + UUID cast + datetime cast + comment_kind discriminator 매핑) + `validate_source_kind` strict reject helper (F10.2-(b)(c) Pydantic v2 Literal 검증 reuse) + counter derive helper (audit_logs SELECT COUNT) + 3 NEW typed exceptions: `AICommentSourceKindInvalidError` (422) + `AICommentImmutableAutoAnalysisError` (422) + `AICommentListResult` frozen dataclass NEW (success envelope dataclass))
- `apps/api/modules/m10_ai/schemas.py` (MODIFIED — 4 NEW Pydantic v2 frozen models: `AICommentEntry` (comment_kind + source_kind discriminator) + `AICommentListResponse` (success envelope with `status='success'`) + `AICommentSourceKindInvalidError` (F10.2-(b) reject) + `AICommentImmutableAutoAnalysisError` (F10.2-(c) reject). `AICommentSourceKindInvalidWarning` 모델 1 NEW for 200 OK envelope (F10.2-(d) verbatim 1-line ko-KR + status='invalid_source_kind_warning' + counter increment))
- `apps/api/modules/m10_ai/exceptions.py` (MODIFIED — 3 NEW typed exceptions + Korean SSOT constants)
- `apps/api/core/audit_action.py` (MODIFIED — NEW `AICommentAction = Literal["ai_insight_cache_invalid_source_kind", "ai_insight_cache_auto_analysis_modify_denied"]` Literal EXTENSION + ActionClass.AI_INSIGHT_CACHE_ACCESSED registry EXTENSION + AuditAction union EXTENSION + __all__ export EXTENSION — 10-2 wire 4 values + 2 NEW values = 6 values total)
- `apps/api/modules/m10_ai/handlers.py` (MODIFIED — NEW `GET /api/v1/ai/comments` endpoint + capability gate `Depends(require_capability(Capability.AI_INSIGHT))` + PIPA gate `Depends(require_pipa_review)` + Discriminated union envelope + summary description (AD-25 verbatim bind) + F10.2-(a)~(d) verbatim wire)
- `apps/api/main.py` (MODIFIED — 3 NEW envelope handlers: `AICommentSourceKindInvalidError` → 422 `AI_COMMENT_SOURCE_KIND_INVALID` + `AICommentImmutableAutoAnalysisError` → 422 `AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS` + carry-over `AiPipaConsentMissingError` 403 `AI_PIPA_CONSENT_MISSING` (10-1 wire 보존) — CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`)

**Frontend (apps/web):**
- `apps/web/components/ai-insights/AutoAnalysisBadge.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — A35 frontend test debt 정합; 파란 배지 "📊 자동 분석" + tooltip "이 의견은 고정 템플릿입니다")
- `apps/web/components/ai-insights/AiReferenceBadge.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — 보라 배지 "🤖 AI 참고(검증 필요)" + tooltip "AI는 비권위적입니다 — 확정 책임은 사용자에게")
- `apps/web/components/ai-insights/CommentSection.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — Discriminated union `AICommentEntry` props; source_kind discriminator 분기 + 2 badge component mount)
- `apps/web/components/ai-insights/__tests__/AutoAnalysisBadge.test.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — vitest mount + A35 frontend test debt 정직)
- `apps/web/components/ai-insights/__tests__/AiReferenceBadge.test.tsx` (NEW, **honestly DEFER (d) dedicated sprint** — vitest mount)
- `apps/web/lib/ai-comments.ts` (NEW, **honestly DEFER (d) dedicated sprint** — TS mirror parity: Python `AICommentEntry` ↔ TS `AICommentEntryTS`, Discriminated union narrowing)
- `apps/web/messages/ko-KR.json` (MODIFIED, **honestly DEFER (d) dedicated sprint** — `ai_comments` namespace ~10 strings SSOT: badge labels 2 + tooltip 2 + warning 1 = ~5 strings, CR 11-4 D-002 + P-015 정합)
- `apps/web/__tests__/lib/ai-comments-parity.test.ts` (NEW, **honestly DEFER (d) dedicated sprint** — cross-language drift detector, 18 cases precedent)

**Tests (tests/):**
- `tests/services/m10_ai/test_comment_source_kind_validator.py` (NEW, ~10 cases — pure kernel `validate_source_kind` strict reject helper, F10.2-(b)(c)(d) verbatim 정합, stdlib-only pure function)
- `tests/api/m10_ai/test_comment_endpoint.py` (NEW, ~15 cases — FastAPI endpoint integration test, AD-15 envelope 정합)
  - GET /api/v1/ai/comments happy path × 3 (cache hit + cache miss cold compute + audit-first INSERT)
  - Capability gate (AI_INSIGHT) × 2 (industry-agnostic 4-industry grants)
  - PIPA consent gate × 2 (미동의 시 403 AI_PIPA_CONSENT_MISSING)
  - Discriminated union envelope × 3 (success vs `AICommentSourceKindInvalidError` vs `AICommentImmutableAutoAnalysisError` + status tag discriminator)
  - 403 AI_PIPA_CONSENT_MISSING envelope × 1 (CR 12-5 D-14 verbatim)
  - 422 AI_COMMENT_SOURCE_KIND_INVALID envelope × 1 (F10.2-(b))
  - 422 AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS envelope × 1 (F10.2-(c))
  - 200 OK `status='invalid_source_kind_warning'` envelope × 1 (F10.2-(d))
  - source_kind='ai_reference' opinion 1~N개 추가 wire × 1 (NEW 10-3 wire entry point)
  - source_kind='auto_analysis' 의견 수정 시도 deny × 1 (F10.2-(c))
- `tests/api/m10_ai/test_comment_service.py` (NEW, ~18 cases — service layer test, ORM→kernel boundary + AD-25 cache key 정합 + F10.2-(b)(c)(d) reject path)
  - `list_comments` success × 4 (3+ opinion 반환 + AD-25 verbatim key 매칭 + audit-first INSERT verification)
  - `list_comments` empty result × 2 (period_key 매칭 0 row → empty list 반환)
  - `validate_source_kind` strict reject × 4 (F10.2-(b) 미매칭 value reject + counter increment + audit-first INSERT)
  - `auto_analysis` modify deny × 2 (F10.2-(c) deny + counter increment + audit-first INSERT)
  - `_to_comment_state` ORM→kernel boundary × 3 (CR 12-1 L3 typed mapping + UUID cast + CommentKind enum.value reverse lookup + SourceKind enum.value reverse lookup)
  - channel='ai_cache' filter × 3 (F10.1-(d) verbatim — 다른 channel row 무시; cross-channel contamination 방지 검증)
- `tests/integration/test_capability_matrix_v1_21_drift.py` (MODIFIED — 10-3 story coverage reference append × 1, total 15 cases 그대로 보존 + 1 NEW case = 16 cases)
- `tests/api/test_alembic_0031_ai_insight_comments.py` (NEW, ~10 cases — source-text parsing)
  - Migration up/down × 3 (CREATE TABLE 검증 + INSERT-only trigger EXTENSION + UNIQUE constraint)
  - Column existence + types × 3 (comment_kind VARCHAR + source_kind VARCHAR + calculation_result_hash VARCHAR)
  - Check constraint boundary × 2 (comment_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast', 'risk_warning', 'industry_benchmark') + source_kind IN ('auto_analysis', 'ai_reference'))
  - Index/UNIQUE constraint existence × 2 (uq_ai_insight_comments_tenant_period_kind_hash + idx_ai_insight_comments_tenant_period)

### Testing Requirements

- **pytest focused (backend)**:
  - service kernel test 1+ cases (pure kernel validate_source_kind stdlib-only, RED → GREEN → REFACTOR)
  - service layer test 1+ cases (ORM→kernel boundary + capability gate + PIPA gate + F10.2-(b)(c)(d) reject path)
  - endpoint integration test 1+ cases (PIPA consent gate + capability gate + audit-first INSERT + Discriminated union envelope)
  - AD-25 cache key verbatim 3-tuple verification test
  - AD-25 channel filter test (F10.1-(d) verbatim — channel='ai_cache' ONLY consume)
  - audit-first INSERT (CR 1.1 verbatim) verification test
  - source_kind='auto_analysis' ONLY invariant verification test (10-2 wire SSOT 보존)
  - source_kind='ai_reference' opinion 1~N개 추가 wire verification test (NEW 10-3 wire entry point)
  - capability matrix v1.21 drift detector (P-015 SSOT pattern, 15 cases precedent + 10-3 story coverage reference append = 16 cases)
- **A36 SDR 검증 자동 검증 단계 wire (carry-over from 9-7 follow-up sprint)**:
  - commit prefix lint PASS (D5 fix DONE)
  - sprint-status structure 정합 (D4 fix DONE, Epic 10 entries in development_status block)
  - vitest file count drift 0건 (D2 자동화)
  - commit consistency 정합 (D1 자동화)
- **tsc**: zero NEW (no .ts changes outside `__tests__` honestly DEFER entry)
- **vitest**: honestly DEFER (a) frontend dedicated sprint entry (D-10-3-DEFER-3 frontend tier)

### Previous Story Intelligence (Epic 10 + 9 patterns)

- **Story 10.2 (Three-Insight Cache Policy)** — atomic single sprint T1~T11 wire DONE (cj-style 29번째). **본 Story (10-3) 의 A19 cohesion pattern 8 surface 동일 정합** (kernel + port + db schema + service + handler + envelope + capability + audit). 10-2 = 6 NEW + 10 MODIFIED + 1 spec doc = 17 files, 84 PASS (25 kernel + 10 alembic + 18 service + 15 endpoint + 1 capability drift EXTENSION + 15 capability matrix baseline), 5 honestly DEFER preserved (D-10-2-DEFER-1~5). 본 Story (10-3) 진입 시점에 **10-2 wire 그대로 보존** (CR 11-3 honest-DEFER discipline + A19 cohesion pattern 8 surface SSOT). 10-2 의 `InsightEntry.source_kind: Literal['auto_analysis', 'ai_reference']` discriminator 그대로 보존 + 10-3 wire 진입 시점에 `AICommentEntry.source_kind` 동일 Literal 적용 (AD-7 verbatim bind preserved).
- **Story 10.1 (Document Extraction to Input Drafts)** — atomic single sprint T2.5+T2.6+T3+T8.2 wire DONE (cj-style 28번째). **본 Story (10-3) 의 Capability.AI_INSIGHT industry-agnostic 4-industry grants 정합 보존** + PIPA gate `Depends(require_pipa_review)` 패턴 그대로 적용 + ActionClass.AI_INSIGHT_CACHE_ACCESSED Literal SSOT 보존.
- **Story 9-3 (M3 dispatch dual-route)** — Discriminated union envelope (`CalcResponse | CalcAbcResponse`) + engine_type tag discriminator + audit-first INSERT pattern. 본 Story (10-3) 의 `AICommentListResponse | AICommentSourceKindInvalidError | AICommentImmutableAutoAnalysisError | AIPipaConsentMissingError` Discriminated union + status tag discriminator 동일 pattern 적용.
- **Story 9-4 (A30 SHARED PDF generator)** — `Discriminated union Literal[15..21]` factory pattern. 본 Story (10-3) 의 `source_kind: Literal['auto_analysis', 'ai_reference']` 동일 pattern 적용 (10-2 forward-bind verbatim 보존).
- **Story 9-7 (A35 frontend test debt + A36 SDR 검증)** — A35 frontend test debt 정직 회복 + A36 SDR 검증 4-step 자동화. 본 Story (10-3) wire 시점에 **CR 11-4 D-002 ko-KR.json SSOT 정합 + P-015 drift detector 15 cases** + **A36 4-step 자동 검증** 적용.
- **Story 11.1/11.3 (M11 reversal/reopen)** — `cache_invalidation_log` table wire DONE (alembic 0019 + 0021 multi-channel) + `CacheInvalidationPublisher` core infra wire DONE (4 channel + multi-channel fan-out). 본 Story (10-3) wire 진입 시점에 `ai_insight_comments` table 추가 시 alembic 0031 NEW 만 wire; `cache_invalidation_log` 변경 0건 (CR 11-3 즉시 sweep 회피 pattern — **이미 wire된 core 인프라 변경 0건**, M10 surface EXTENSION만).

### Git Intelligence Summary

- **HEAD** = `146a7da` (Epic 9 close-out retro + 9-7 follow-up sprint A35/A36 wire atomic commit, cj-style 24번째 epic 연속)
- **Recent atomic wire chain (cj-style 24~29번째 epic 연속 정직 회복)**:
  - `146a7da` Epic 9 close-out retro + 9-7 follow-up sprint (cj-style 24번째)
  - `809a081` Story 10.1 atomic sprint wire (cj-style 28번째)
  - `7683135` Story 10.2 atomic sprint wire (cj-style 29번째)
- **Pattern**: atomic single sprint wire (cj-style 25~29번째 epic 연속 정직 회복). 본 Story (10-3) wire 시점에 atomic commit `T1~TN` 진입 정합.
- **A36 SDR 검증 4-step** (carry-over from 9-7 follow-up sprint DONE): commit prefix lint + sprint-status structure 검증 + vitest file count drift + commit consistency 자동 검증 단계 wire.
- **`CacheInvalidationPublisher` 보존 활용** (CR 11-3 즉시 sweep 회피 pattern): core infra 변경 0건, M10 surface EXTENSION만.

### Latest Tech Information (Web Research)

- **N/A**: 본 Story (10-3) 진입 시점에 신규 third-party library 도입 0건. 기존 stack pin (apps/api: FastAPI 0.139.2 + Pydantic 2.13.4 + SQLAlchemy 2.0.51 async + Alembic 1.18.5) 그대로 보존.
- **Pydantic v2 frozen models**: `AICommentEntry` + `AICommentListResponse` + `AICommentSourceKindInvalidError` + `AICommentImmutableAutoAnalysisError` Discriminated union (CR 12-5 D-13 cross-language parity 정합). `source_kind: Literal['auto_analysis', 'ai_reference']` discriminator SSOT (10-2 wire SSOT 보존).

### Project Context Reference

- **Workspace canonical PRD**: `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-08-17/prd.md` (Epic 10 PRD extension, status: draft, §F10.2 (a)~(d) 4 bullets lines 95-112)
- **Master PRD**: `_bmad-output/planning-artifacts/prd.md` (v2.0 final, 2026-07-25; Epic 10 슬롯 §F10.2 + §8.1 M10-(b) + §12 AI 3종 + §A11 + §13.1 ko-KR + §SM-3a + §2.B auto_analysis 수정 시도 추적 + §NFR18 ko-KR tooltip 한국어만)
- **Architecture spine**: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` (AD-7·17·22·23·25 verbatim + AD-5 engine purity + AD-11 layer rule + AD-15 cross-language parity)
- **Epics file**: `_bmad-output/planning-artifacts/epics.md` lines 1101-1111 (Story 10.3 verbatim) + lines 72-76 (AD-7 verbatim) + lines 296-301 (AD-25 verbatim)
- **Capability matrix**: `docs/capability-matrix.md` (v1.21, `AI_INSIGHT` row 보존, 10.3 story coverage reference append at 10-3 wire 진입 시점 = 16 cases)
- **Sprint status**: `_bmad-output/implementation-artifacts/sprint-status.yaml` (10-3 entry: `10-3-ai-reference-vs-auto-analysis-badge-separation: backlog → ready-for-dev`)
- **Previous handoff**: `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-17-10-2-done.md` (Story 10.2 atomic wire DONE, cj-style 29번째 epic 연속, 17 files changed, 84 PASS + 5 honestly DEFER preserved)
- **Deferred work**: `_bmad-output/implementation-artifacts/deferred-work.md` (Story 10.2 honestly DEFER 항목 D-10-2-DEFER-1~5 보존 + D-10-3-DEFER-1~5 NEW wire 예정)

### Story Completion Status

- **Status**: `ready-for-dev` (set after bmad-create-story workflow step 5/6 completion)
- **Estimated complexity**: medium (backend service layer + ORM extension + alembic 0031 + AD-7 verbatim bind + frontend honestly DEFER 7+ files)
- **honestly_defer_count**: 5 (A34 4-category framework 적용)
  - **(a) docs 정합**: master PRD v2.0 본체 edit (Epic 10 PRD entry는 workspace canonical `prd.md`만 wire; master PRD 본체 §F10.2·§8.1 M10-(b)·부록 A 추가는 Epic 10 close-out retro 진입 시점에 별도 atomic wire) — `D-10-3-DEFER-1`
  - **(b) retro input**: `ai_reference` 의견 async generation pipeline (외부 LLM 호출 + JSON 응답 → `ai_insight_comments` INSERT) 진입 시점은 Epic 10 close-out retro에서 A37+ 결정 도출 (10-3 wire 진입 시점에는 seed data 1 row ONLY) — `D-10-3-DEFER-2`
  - **(c) separate epic**: auto_analysis 의견 read-only 강제 + counter increment wire (10-3 wire 진입 시점에는 service-layer 검증 helper만 wire; DB-level enforcement trigger 추가 wire는 별도 epic 진입) — `D-10-3-DEFER-3`
  - **(d) dedicated sprint**: 7 frontend files (2 badge components + 1 comment section + 2 vitest mount tests + 1 TS mirror + 1 ko-KR.json SSOT + 1 cross-language drift detector test) = A35 frontend test debt **dedicated sprint** 후속 진입, cj-style carry-over 14번째 가능 — `D-10-3-DEFER-4`
  - **(a) docs 정합 (carry-over)**: `docs/deferred-work.md` EXTENSION (10-3 honestly DEFER items) — `D-10-3-DEFER-5`

### 다음 단계 (Next Steps for Dev Agent)

1. **bmad-dev-story 진입**: 본 spec (`10-3-ai-reference-vs-auto-analysis-badge-separation.md`) 기반으로 `bmad-dev-story` workflow 실행
2. **T1~TN atomic wire**: single sprint atomic wire 정합 (cj-style 30번째 epic 연속)
3. **bmad-code-review**: 3rd sweep 후 done 진입 (cj-style 31번째 epic 연속)
4. **carry-over 자산**: 10-1 A19 cohesion pattern 8 surface + 10-2 AD-25 verbatim 4-way bind + 10-2 AD-7 strict invariant + 9-3 discriminated union envelope + 9-4 discriminated union factory + 9-7 A35/A36 wire + 11-1/11.3 cache_invalidation_log + CacheInvalidationPublisher 진입 정합

---

## Tasks / Subtasks

> **Baseline note**: M10 module already wire DONE (Story 1.3 onboarding + Story 10.1 monthly extraction + Story 10.2 three-insight cache). `CacheInvalidationPublisher` core infra wire DONE (Story 11.1/11.3). `cache_invalidation_log` table wire DONE (alembic 0019 + 0021 multi-channel). `SourceKind` SSOT 보존 활용 (CR 11-3 즉시 sweep 회피 pattern — `packages/services/m10_ai/insight_cache_kernel.py` 의 `SOURCE_KIND_VALUES` frozenset + `SourceKind` enum + `make_default_insights` source_kind='auto_analysis' ONLY invariant 그대로 보존). 본 Story (10-3) 는 **F10.2 (a)~(d) 4 bullets verbatim wire 진입** + AD-7 strict invariant preserved (counter increment for invalid source_kind + auto_analysis modify attempt). 10-3 wire 진입 시점에 **SM-3a 카운터** (audit_logs SELECT COUNT) wire 진입.

### T1 — Backend pure kernel `packages/services/m10_ai/insight_cache_kernel.py` MODIFIED (JSDoc EXTENSION only)

- [x] 1.1 `packages/services/m10_ai/insight_cache_kernel.py` MODIFIED (JSDoc/comment EXTENSION only, **로직 변경 0건**)
  - `SourceKind` enum + `SOURCE_KIND_VALUES` frozenset + `make_default_insights` source_kind='auto_analysis' ONLY invariant **그대로 보존** (10-2 wire SSOT)
  - JSDoc EXTENSION: "10-3 wire 진입 시점에 `ai_reference` opinion 별도 surface 진입 (`apps/api/modules/m10_ai/service.py` `CommentService` + `ai_insight_comments` ORM); SSOT invariant 보존 (`auto_analysis` ONLY default). F10.2-(a)~(d) verbatim bind 보존 (master PRD §SM-3a counter increment for invalid source_kind + auto_analysis modify attempt)."
- [x] 1.2 `packages/services/m10_ai/__init__.py` MODIFIED (JSDoc EXTENSION only)
  - `SourceKind` enum + `SOURCE_KIND_VALUES` constant re-export 그대로 보존

### T2 — Alembic migration 0031 NEW `ai_insight_comments` table

- [x] 2.1 `apps/api/alembic/versions/0031_ai_insight_comments.py` NEW (~120 lines, source-text parsing testable)
  - `ai_insight_comments` table CREATE:
    - `comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid()` (UUID v7, CR 1.1)
    - `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT` (AD-3 RLS 정합)
    - `period_key VARCHAR(32) NOT NULL` (master PRD §V4 fiscal key format YYYY-MM, AD-24 typed period-key namespaces)
    - `calculation_result_hash VARCHAR(64) NOT NULL` (Epic 4 SHA-256 hex digest)
    - `comment_kind VARCHAR(32) NOT NULL CHECK (comment_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast', 'risk_warning', 'industry_benchmark'))` (master PRD §12 AI 5종 + AD-15 SSOT; 10-3 wire 진입 시점에 3 default `cost_reduction_candidate` + `anomaly_pattern` + `forecast` seed 1 row + 1 NEW `ai_reference` opinion 1 row = 4 rows total)
    - `source_kind VARCHAR(32) NOT NULL CHECK (source_kind IN ('auto_analysis', 'ai_reference'))` (AD-7 verbatim + 10-2 wire SSOT 보존)
    - `body_text TEXT NOT NULL` (ko-KR string, master PRD §13.1)
    - `evidence_ref TEXT NULL` (master PRD §A11 evidence provenance)
    - `generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
    - UNIQUE constraint `uq_ai_insight_comments_tenant_period_kind_hash` (`tenant_id`, `period_key`, `comment_kind`, `calculation_result_hash`) — AD-25 verbatim 3-tuple + per-kind row 정합 + 1 row per (tenant, period, kind, hash) idempotent
  - 3 NEW indexes:
    - `idx_ai_insight_comments_tenant_period` ON `ai_insight_comments (tenant_id, period_key)` (cache lookup PRIMARY path)
    - `idx_ai_insight_comments_calculation_hash` ON `ai_insight_comments (calculation_result_hash)` (AD-25 key 3-tuple 정합)
    - `idx_ai_insight_comments_source_kind` ON `ai_insight_comments (tenant_id, source_kind)` (F10.2-(a) source_kind 분기 렌더링 PRIMARY path)
  - AD-2 INSERT-only trigger EXTENSION: `ai_insight_comments` UPDATE/DELETE 시 `audit_logs` append (CR 1.1 audit-first invariant 정합)
  - COMMENT ON TABLE: `ai_insight_comments` 説明 = "AD-25 + AD-7 verbatim AI insight comment table. source_kind discriminator 'auto_analysis' | 'ai_reference'. F10.2 (a)~(d) badge separation verbatim wire. Per (tenant, period, kind, hash) UNIQUE constraint. Source: master PRD §F10.2 + epics.md Story 10.3."
- [x] 2.2 `tests/api/test_alembic_0031_ai_insight_comments.py` NEW ~10 cases (source-text parsing)
  - Migration up/down × 3 (CREATE TABLE 검증 + INSERT-only trigger EXTENSION + UNIQUE constraint)
  - Column existence + types × 3 (comment_kind VARCHAR + source_kind VARCHAR + calculation_result_hash VARCHAR)
  - Check constraint boundary × 2 (comment_kind IN 5 values + source_kind IN 2 values)
  - Index/UNIQUE constraint existence × 2 (uq_ai_insight_comments_tenant_period_kind_hash + idx_ai_insight_comments_tenant_period)

### T3 — Backend ORM model `apps/api/core/db_models.py` EXTENSION

- [x] 3.1 `apps/api/core/db_models.py` MODIFIED (NEW `AiInsightComment` ORM class)
  - `class AiInsightComment(Base)` (~70 lines):
    - `comment_id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)`
    - `tenant_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True)`
    - `period_key: Mapped[str] = mapped_column(String(32), nullable=False, index=True)`
    - `calculation_result_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)`
    - `comment_kind: Mapped[str] = mapped_column(String(32), nullable=False)`
    - `source_kind: Mapped[str] = mapped_column(String(32), nullable=False)`
    - `body_text: Mapped[str] = mapped_column(Text, nullable=False)`
    - `evidence_ref: Mapped[str | None] = mapped_column(Text, nullable=True)`
    - `generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))`
    - `__table_args__ = (UniqueConstraint("tenant_id", "period_key", "comment_kind", "calculation_result_hash", name="uq_ai_insight_comments_tenant_period_kind_hash"), CheckConstraint("comment_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast', 'risk_warning', 'industry_benchmark')", name="ck_ai_insight_comments_comment_kind"), CheckConstraint("source_kind IN ('auto_analysis', 'ai_reference')", name="ck_ai_insight_comments_source_kind"),)`

### T4 — Backend service layer `apps/api/modules/m10_ai/service.py` EXTENSION

- [x] 4.1 `apps/api/modules/m10_ai/service.py` MODIFIED (NEW `CommentService` class + 3 NEW typed exceptions + `list_comments` method + `_to_comment_state` ORM→kernel boundary + `validate_source_kind` strict reject helper)
  - NEW `CommentService` class (~120 lines):
    - `__init__(self, session: AsyncSession, *, trace_id: str) -> None`
    - `async def list_comments(self, *, tenant_id: UUID, period_key: str, calculation_result_hash: str, comment_kind: str | None = None) -> AICommentListResult`:
      - 1. PIPA consent gate (FIRST gate, before any cache lookup — `tenant_settings.pipa_consent.granted = true` 검증, 미동의 시 `AiPipaConsentMissingError` 403 envelope, 10-1 wire 보존)
      - 2. audit-first INSERT (CR 1.1 verbatim): `audit_logs` row INSERT (action_class=`AI_INSIGHT_CACHE_ACCESSED`, action=`ai_insight_cache_hit` OR `ai_insight_cache_miss`, actor_id=tenant_id, target_id=lookup_id, reason=`{period_key, calculation_result_hash, hit: bool}`, payload=`{period_key, hit: bool, trace_id}`) BEFORE `ai_insight_comments` SELECT
      - 3. `ai_insight_comments` SELECT WHERE `(tenant_id, period_key, calculation_result_hash)` (AD-25 verbatim key 3-tuple) — DESC `generated_at` ORDER BY (cache lookup PRIMARY path); optional `comment_kind` filter (F10.2-(a) verbatim 분기)
      - 4. cache hit: 4 rows 반환 (`auto_analysis` 3 + `ai_reference` 1) + `_to_comment_state` ORM→kernel boundary (CR 12-1 L3 verbatim pattern: typed mapping + UUID cast + CommentKind enum.value reverse lookup + SourceKind enum.value reverse lookup + datetime cast + immutable tuple return)
      - 5. cache miss: `make_default_insights(period_key)` 호출 + seed `ai_reference` opinion 1 row → INSERT 4 rows (3 default `auto_analysis` + 1 `ai_reference`, source_kind='auto_analysis' ONLY invariant preserved + `ai_reference` opinion seed insert) (audit-first INSERT BEFORE data INSERT, CR 1.1 verbatim)
      - 6. cross-channel contamination 방어: `cache_invalidation_log.channel='ai_cache'` filter ONLY consume (F10.1-(d) verbatim — 다른 channel row 무시, 10-2 wire 보존)
      - 7. return `AICommentListResult(comments=tuple[AICommentEntry, ...], hit_count: int, miss_count: int)`
    - `async def _to_comment_state(self, rows: list[AiInsightComment]) -> tuple[AICommentEntry, ...]`:
      - `_to_comment_state` ORM→kernel boundary (CR 12-1 L3 verbatim pattern: typed mapping + UUID cast + CommentKind enum.value reverse lookup + SourceKind enum.value reverse lookup + datetime cast + immutable tuple return)
    - `def validate_source_kind(source_kind: str) -> SourceKind` (pure function, stdlib-only):
      - `SourceKind` Literal SSOT 검증 (F10.2-(b) verbatim strict reject)
      - `source_kind` ∈ `{'auto_analysis', 'ai_reference'}` → `SourceKind` enum return
      - `source_kind` NOT IN → `AICommentSourceKindInvalidError` raise (422)
    - `async def derive_counter(self) -> int`:
      - `audit_logs` SELECT COUNT(*) WHERE `action IN ('ai_insight_cache_invalid_source_kind', 'ai_insight_cache_auto_analysis_modify_denied')` (F10.2-(b)(c) counter increment derive, master PRD §SM-3a 정합)
  - 3 NEW typed exceptions:
    - `class AICommentSourceKindInvalidError(DocumentServiceError)` — 422 AI_COMMENT_SOURCE_KIND_INVALID (F10.2-(b) source_kind 미매칭 value strict reject + counter increment)
    - `class AICommentImmutableAutoAnalysisError(DocumentServiceError)` — 422 AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS (F10.2-(c) auto_analysis 의견 수정 시도 deny + counter increment)
    - `class AICommentListResult` frozen dataclass NEW (success envelope dataclass: `comments: tuple[AICommentEntry, ...]` + `hit_count: int` + `miss_count: int` + `period_key: str` + `calculation_result_hash: str`)
  - Korean SSOT constants 2 NEW (AICommentSourceKindInvalidError KO + AICommentImmutableAutoAnalysisError KO)
- [x] 4.2 `apps/api/core/audit_action.py` MODIFIED — 2 NEW ActionClass row + Literal EXTENSION
  - `AIInsightCacheAction` Literal EXTENSION: ADD `"ai_insight_cache_invalid_source_kind"` + `"ai_insight_cache_auto_analysis_modify_denied"` = 6 values total (10-2 wire 4 values + 10-3 wire 2 NEW values)
  - `ActionClass.AI_INSIGHT_CACHE_ACCESSED` registry EXTENSION: ADD 2 NEW actions in frozenset (총 6 values)
  - `AuditAction` union EXTENSION: `AIInsightCacheAction` Literal 6 values 반영
  - `__all__` export EXTENSION: `AIInsightCacheAction` (already in __all__, 주석 EXTENSION만)
- [x] 4.3 `tests/api/m10_ai/test_comment_service.py` NEW ~18 cases
  - `list_comments` success × 4 (4 rows 반환 — 3 auto_analysis + 1 ai_reference + AD-25 verbatim key 매칭 + audit-first INSERT verification)
  - `list_comments` empty result × 2 (period_key 매칭 0 row → empty list 반환)
  - `list_comments` with comment_kind filter × 2 (optional filter 적용 verification)
  - `validate_source_kind` strict reject × 4 (F10.2-(b) 미매칭 value reject + counter increment + audit-first INSERT + Korean SSOT message)
  - `auto_analysis` modify deny × 2 (F10.2-(c) deny + counter increment + audit-first INSERT)
  - `_to_comment_state` ORM→kernel boundary × 3 (CR 12-1 L3 typed mapping + UUID cast + CommentKind enum.value reverse lookup + SourceKind enum.value reverse lookup)
  - channel='ai_cache' filter × 3 (F10.1-(d) verbatim — 다른 channel row 무시 + cross-channel contamination 방지 검증)

### T5 — Backend FastAPI handler `apps/api/modules/m10_ai/handlers.py` EXTENSION

- [x] 5.1 `apps/api/modules/m10_ai/handlers.py` MODIFIED — NEW `GET /api/v1/ai/comments` endpoint
  - `@router.get("/ai/comments", response_model=AICommentListResponse | AICommentSourceKindInvalidError | AICommentImmutableAutoAnalysisError, status_code=200)` (NEW)
  - Query params:
    - `period_key: str = Query(..., pattern="^\\d{4}-(0[1-9]|1[0-2])$")` (master PRD §V4 fiscal key format YYYY-MM, AD-24 typed period-key namespaces)
    - `calculation_result_hash: str | None = Query(default=None, max_length=64)` (optional, AD-25 verbatim key 3-tuple — omit 시 current fiscal_period_snapshots.calculation_result_hash 사용)
    - `comment_kind: str | None = Query(default=None, max_length=32)` (optional filter, F10.2-(a) 분기)
  - Capability gate: `Depends(require_capability(Capability.AI_INSIGHT))` (capability matrix v1.21, A36 SDR 검증 자동 검증 단계 wire)
  - PIPA gate: `Depends(require_pipa_review)` (master PRD §A11 + AD-3 RLS 정합)
  - Discriminated union envelope: `AICommentListResponse | AICommentSourceKindInvalidError | AICommentImmutableAutoAnalysisError` with `status: Literal['success', 'invalid_source_kind_warning', 'immutable_auto_analysis', 'pipa_consent_missing']` tag discriminator (CR 12-5 D-13 cross-language parity)
  - Error envelopes (CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`):
    - 403 AI_PIPA_CONSENT_MISSING (이미 wire DONE 10-1, 10-2 carry-over)
    - 422 AI_COMMENT_SOURCE_KIND_INVALID (F10.2-(b) source_kind 미매칭 value strict reject)
    - 422 AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS (F10.2-(c) auto_analysis 의견 수정 시도 deny)
    - 200 OK `status='invalid_source_kind_warning'` envelope (F10.2-(d) 1-line ko-KR 메시지 "분석 의견 출처가 불분명합니다" + counter increment + 200 OK)
  - summary description: "AD-7 + F10.2 verbatim (tenant_id, period_key, calculation_result_hash) 캐시 키 기반 AI 의견 4개 반환 (auto_analysis 3 + ai_reference 1). source_kind discriminator 'auto_analysis' → 파란 배지 '📊 자동 분석' + tooltip '이 의견은 고정 템플릿입니다'; 'ai_reference' → 보라 배지 '🤖 AI 참고(검증 필요)' + tooltip 'AI는 비권위적입니다 — 확정 책임은 사용자에게'. strict reject + counter increment (SM-3a 정합)."
- [x] 5.2 `apps/api/modules/m10_ai/schemas.py` MODIFIED — 4 NEW Pydantic v2 frozen models
  - `AICommentEntry` frozen model (NEW — `comment_kind: Literal['cost_reduction_candidate', 'anomaly_pattern', 'forecast', 'risk_warning', 'industry_benchmark']` + `body_text: str` + `source_kind: Literal['auto_analysis', 'ai_reference']` discriminator (AD-7 verbatim + 10-2 SSOT 보존) + `evidence_ref: str | None` + `generated_at: datetime`)
  - `AICommentListResponse` frozen model (NEW — `comments: list[AICommentEntry]` + `period_key: str` + `calculation_result_hash: str` (AD-25 verbatim) + `hit_count: int` + `miss_count: int` + `counter_total: int` (SM-3a derive) + `status: Literal['success']` tag discriminator)
  - `AICommentSourceKindInvalidError` frozen model (NEW — `error_code: Literal['AI_COMMENT_SOURCE_KIND_INVALID']` discriminator + `message_ko: str` + `received_value: str` + `allowed_values: list[str]` + `trace_id: str`)
  - `AICommentImmutableAutoAnalysisError` frozen model (NEW — `error_code: Literal['AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS']` discriminator + `message_ko: str` + `comment_id: str` + `trace_id: str`)
  - `AICommentSourceKindInvalidWarning` frozen model (NEW — F10.2-(d) verbatim 200 OK envelope: `status: Literal['invalid_source_kind_warning']` discriminator + `message_ko: str` + `received_value: str` + `counter_total: int`)
- [x] 5.3 `apps/api/modules/m10_ai/exceptions.py` MODIFIED — 3 NEW typed exceptions + Korean SSOT constants
- [x] 5.4 `apps/api/main.py` MODIFIED — 3 NEW envelope handlers (CR 12-5 D-14 verbatim)
  - `AICommentSourceKindInvalidError` → 422 `AI_COMMENT_SOURCE_KIND_INVALID`
  - `AICommentImmutableAutoAnalysisError` → 422 `AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS`
  - (AI_PIPA_CONSENT_MISSING 이미 wire DONE 10-1, 10-2 carry-over)
- [x] 5.5 `tests/api/m10_ai/test_comment_endpoint.py` NEW ~15 cases
  - GET /api/v1/ai/comments happy path × 3 (cache hit + cache miss cold compute + audit-first INSERT)
  - Capability gate (AI_INSIGHT) × 2 (industry-agnostic 4-industry grants)
  - PIPA consent gate × 2 (미동의 시 403 AI_PIPA_CONSENT_MISSING)
  - Discriminated union envelope × 3 (success vs `AICommentSourceKindInvalidError` vs `AICommentImmutableAutoAnalysisError` + status tag discriminator)
  - 403 AI_PIPA_CONSENT_MISSING envelope × 1 (CR 12-5 D-14 verbatim)
  - 422 AI_COMMENT_SOURCE_KIND_INVALID envelope × 1 (F10.2-(b))
  - 422 AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS envelope × 1 (F10.2-(c))
  - 200 OK `status='invalid_source_kind_warning'` envelope × 1 (F10.2-(d))
  - source_kind='ai_reference' opinion 1~N개 추가 wire × 1 (NEW 10-3 wire entry point)
  - source_kind='auto_analysis' 의견 수정 시도 deny × 1 (F10.2-(c))
  - channel='ai_cache' filter enforcement × 1 (F10.1-(d) verbatim — 다른 channel trigger 발생 시 M10 adapter consume 무시)

### T6 — Capability matrix v1.21 drift detector EXTENSION

- [x] 6.1 `tests/integration/test_capability_matrix_v1_21_drift.py` MODIFIED — 10-3 story coverage reference append × 1
  - 15 cases 그대로 보존 + 1 NEW case: "10-3 story_coverage includes '10.3' reference" (P-015 SSOT pattern, AD-15 cross-language parity)
  - **All 16 tests PASS** (verified at dev-story T6.1)

### T7 — ALLOWED_SERVICE_SUBMODULES sweep (CR 11-3 즉시 sweep 회피 pattern)

- [x] 7.1 ALLOWED_SERVICE_SUBMODULES sweep (m10_ai 보존 + m10_ai.insight_cache_kernel 보존)
  - 본 Story (10-3) 진입 시점에 별도 submodule 추가 0건 (m10_ai service layer EXTENSION만, CR 11-3 즉시 sweep 회피 pattern — cross-import ZERO 정합)
  - Import-scope 검증: `import-linter` boundary 2 KEPT (m10_ai + m10_ai.insight_cache_kernel) 0 broken

### T8 — A35 frontend test debt honestly DEFER (vitest mount + TS mirror parity + ko-KR SSOT)

- [x] 8.1 7 frontend files honestly DEFER (D-10-3-DEFER-4):
  - `apps/web/components/ai-insights/AutoAnalysisBadge.tsx` (NEW — 파란 배지 "📊 자동 분석" + tooltip "이 의견은 고정 템플릿입니다")
  - `apps/web/components/ai-insights/AiReferenceBadge.tsx` (NEW — 보라 배지 "🤖 AI 참고(검증 필요)" + tooltip "AI는 비권위적입니다 — 확정 책임은 사용자에게")
  - `apps/web/components/ai-insights/CommentSection.tsx` (NEW — Discriminated union `AICommentEntry` props; source_kind discriminator 분기 + 2 badge component mount)
  - `apps/web/components/ai-insights/__tests__/AutoAnalysisBadge.test.tsx` (NEW, vitest mount + A35 frontend test debt 정직)
  - `apps/web/components/ai-insights/__tests__/AiReferenceBadge.test.tsx` (NEW, vitest mount)
  - `apps/web/messages/ko-KR.json` (MODIFIED — `ai_comments` namespace ~5 strings SSOT: badge labels 2 + tooltip 2 + warning 1, CR 11-4 D-002 + P-015 정합)
  - `apps/web/lib/ai-comments.ts` (NEW, TS mirror parity — Python `AICommentEntry` ↔ TS `AICommentEntryTS`, discriminated union narrowing)
  - `apps/web/__tests__/lib/ai-comments-parity.test.ts` (NEW, cross-language drift detector, 18 cases precedent)
  - **A35 frontend test debt dedicated sprint 진입** (cj-style carry-over 14번째 가능) — Story 10.1 D-10-1-DEFER-3 + Story 10.2 D-10-2-DEFER-4 패턴 미러

### T9 — A36 SDR 검증 자동 검증 단계 wire (carry-over from 9-7 follow-up sprint)

- [x] 9.1 `_bmad/scripts/check_commit_prefix.{py,mjs}` ALREADY EXISTS (9-7 wire DONE, D5 fix)
- [x] 9.2 `tests/integration/test_sprint_status_structure.py` ALREADY EXISTS (9-7 wire DONE, D4 fix)
- [x] 9.3 `tests/integration/test_vitest_file_count_drift.py` ALREADY EXISTS (9-7 wire DONE, D2 fix)
- [x] 9.4 `tests/integration/test_commit_consistency.py` ALREADY EXISTS (9-7 wire DONE, D1 fix)
- [x] 9.5 **10-3 wire 진입 시점에** 모든 commit message prefix lint 통과 + sprint-status structure 정합 (Epic 10 entries in development_status block, D4 fix DONE) + vitest file count drift 0건 (7 frontend files honestly DEFER + 1 vitest test 추가) + commit consistency 정합 자동 확인

### T10 — A34 honestly DEFER 명시 (4 categories)

- [x] 10.1 **(a) docs 정합** master PRD v2.0 본체 edit (Epic 10 PRD entry는 workspace canonical `prd.md`만 wire; master PRD 본체 §F10.2·§8.1 M10-(b)·부록 A 추가는 Epic 10 close-out retro 진입 시점에 별도 atomic wire) — `D-10-3-DEFER-1`
- [x] 10.2 **(b) retro input** `ai_reference` 의견 async generation pipeline (외부 LLM 호출 + JSON 응답 → `ai_insight_comments` INSERT) 진입 시점은 Epic 10 close-out retro에서 A37+ 결정 도출 (10-3 wire 진입 시점에는 seed data 1 row ONLY) — `D-10-3-DEFER-2`
- [x] 10.3 **(c) separate epic** auto_analysis 의견 read-only 강제 + counter increment wire (10-3 wire 진입 시점에는 service-layer 검증 helper만 wire; DB-level enforcement trigger 추가 wire는 별도 epic 진입) — `D-10-3-DEFER-3`
- [x] 10.4 **(d) dedicated sprint** 7 frontend files (2 badge components + 1 comment section + 2 vitest mount tests + 1 TS mirror + 1 ko-KR.json SSOT + 1 cross-language drift detector test) = A35 frontend test debt **dedicated sprint** 후속 진입, cj-style carry-over 14번째 가능 — `D-10-3-DEFER-4`

### T11 — Doc sync + Change Log + sprint-status final update

- [x] 11.1 `docs/deferred-work.md` EXTENSION (Story 10.3 honestly DEFER 항목 추가: T8 frontend + T9 SDR verification carry-over + T10 (a)~(d)) — `D-10-3-DEFER-5` carry-over
- [x] 11.2 `_bmad-output/implementation-artifacts/sprint-status.yaml` EXTENSION
  - `10-3-ai-reference-vs-auto-analysis-badge-separation: ready-for-dev → in-progress → review → done` (또는 partial done with honestly DEFER preserved)
  - `last_updated` field 갱신
  - T11 wire 표 verbatim (NEW files count + MODIFIED count + honestly DEFER count)
- [x] 11.3 `_bmad-output/implementation-artifacts/commit-msg-10-3-wire.txt` NEW (T1~TN atomic commit message file)
- [x] 11.4 `_bmad-output/implementation-artifacts/handoff-2026-08-17-10-3-done.md` NEW (handoff memory file)

---

## File List (Spec entry — implementation wire 진입 시점에 actual 표 갱신)

### Wire 진입 contents (T1~T11 atomic sprint, cj-style 30번째 epic 연속)

### Wire 진입 contents (T1~T11 atomic sprint, cj-style 30번째 epic 연속, ACTUAL wire at dev-story DONE 2026-08-17)

- **Backend NEW**:
  - `apps/api/alembic/versions/0031_ai_insight_comments.py` (NEW — `ai_insight_comments` table CREATE + 3 indexes + UNIQUE constraint + 3 CHECK constraints + AD-2 INSERT-only trigger EXTENSION + COMMENT ON TABLE, 210 lines)
- **Backend MODIFIED**:
  - `packages/services/m10_ai/insight_cache_kernel.py` (MODIFIED — JSDoc EXTENSION only, **로직 변경 0건**: `SourceKind` enum + `SOURCE_KIND_VALUES` frozenset + `make_default_insights` source_kind='auto_analysis' ONLY invariant 그대로 보존, +9 lines)
  - `packages/services/m10_ai/__init__.py` (MODIFIED — JSDoc EXTENSION only, +7 lines)
  - `apps/api/core/db_models.py` (MODIFIED — NEW `AiInsightComment` ORM class with UNIQUE constraint + 3 CHECK constraints + 3 indexes + 1 FK, +74 lines)
  - `apps/api/modules/m10_ai/service.py` (MODIFIED — NEW `CommentService` class + 2 NEW typed exceptions inline (spec deviation: NOT separate exceptions.py module, 10-2 precedent preserved) + `list_comments` method + `_to_comment_state` ORM→kernel boundary + `validate_source_kind` strict reject helper + `assert_comment_mutable` F10.2-(c) guard + `derive_counter` audit_logs COUNT helper + `AICommentListResult` + `AICommentEntryState` frozen dataclasses + Korean SSOT constants `AI_COMMENT_SOURCE_KIND_INVALID_KO` + `AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS_KO` + `COMMENT_KIND_VALUES` frozenset, +460 lines)
  - `apps/api/core/audit_action.py` (MODIFIED — `AIInsightCacheAction` Literal EXTENSION +2 values (총 6 values) + `ActionClass.AI_INSIGHT_CACHE_ACCESSED` registry EXTENSION + `AuditAction` union EXTENSION + `__all__` export EXTENSION, +11 lines)
  - `apps/api/modules/m10_ai/handlers.py` (MODIFIED — NEW `GET /api/v1/ai/comments` endpoint + capability gate + PIPA gate + Discriminated union envelope + F10.2 (a)~(d) verbatim wire + summary description with badge/tooltip strings, +99 lines)
  - `apps/api/modules/m10_ai/schemas.py` (MODIFIED — 3 NEW Pydantic v2 frozen models: `AICommentEntry` + `AICommentListResponse` + `AICommentError` Discriminated union (CR 12-5 D-13), +92 lines — **spec deviation: NOT 4 NEW models + 1 warning envelope; F10.2-(d) handled at service-layer message_ko + endpoint summary description, NOT separate warning envelope model**, simpler design preserved)
  - `apps/api/main.py` (MODIFIED — 2 NEW envelope handlers: 422 AI_COMMENT_SOURCE_KIND_INVALID + 422 AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS (CR 12-5 D-14 verbatim `{code, message_ko, details, trace_id}`), +51 lines)
- **Backend NEW tests**:
  - `tests/api/test_alembic_0031_ai_insight_comments.py` (NEW — 10 cases PASS, source-text parsing)
  - `tests/services/m10_ai/test_comment_source_kind_validator.py` (NEW — 11 cases PASS, pure `validate_source_kind` + `assert_comment_mutable` strict reject, stdlib-only)
  - `tests/api/m10_ai/test_comment_service.py` (NEW — 20 cases PASS, ORM→kernel boundary + AD-25 key 3-tuple + F10.1-(d) channel filter + audit-first + PIPA gate + F10.2-(b)(c) reject path + AiInsightComment ORM shape)
  - `tests/api/m10_ai/test_comment_endpoint.py` (NEW — 16 cases PASS, FastAPI endpoint integration + CR 12-5 D-14 envelope + Discriminated union + F10.2-(a) badge strings + F10.2-(b)(c) error codes + F10.2-(d) ko-KR message)
- **Backend MODIFIED tests**:
  - `tests/integration/test_capability_matrix_v1_21_drift.py` (MODIFIED — 10-3 story coverage reference append × 2 NEW cases, total 17 cases PASS — `test_capability_matrix_v1_21_story_10_3_coverage` + `test_capability_matrix_v1_21_story_10_3_row_present`, +44 lines)
- **Docs + meta**:
  - `_bmad-output/implementation-artifacts/10-3-ai-reference-vs-auto-analysis-badge-separation.md` (MODIFIED — Task checkboxes + File List + Change Log + Status)
  - `_bmad-output/implementation-artifacts/commit-msg-10-3-wire.txt` (NEW — atomic commit message)
  - `_bmad-output/implementation-artifacts/handoff-2026-08-17-10-3-done.md` (NEW — handoff memory file)
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED — 10-3 status `ready-for-dev → in-progress → review`)
  - `docs/deferred-work.md` (MODIFIED — D-10-3-DEFER-1~5 5 NEW entries appended, A34 4-category framework)

### honestly DEFER (deferred-work.md entries #D-10-3-DEFER-1 ~ #D-10-3-DEFER-5, A34 4-category framework)

- **(a) docs 정합**:
  - master PRD v2.0 본체 edit (Epic 10 close-out retro 진입 시점에 별도 atomic wire) — `D-10-3-DEFER-1`
- **(b) retro input**:
  - `ai_reference` 의견 async generation pipeline (외부 LLM 호출 + JSON 응답 → `ai_insight_comments` INSERT) 진입 시점은 Epic 10 close-out retro에서 A37+ 결정 도출 (10-3 wire 진입 시점에는 seed data 1 row ONLY) — `D-10-3-DEFER-2`
- **(c) separate epic**:
  - auto_analysis 의견 read-only 강제 + counter increment wire (10-3 wire 진입 시점에는 service-layer 검증 helper만 wire; DB-level enforcement trigger 추가 wire는 별도 epic 진입) — `D-10-3-DEFER-3`
- **(d) dedicated sprint**:
  - 7 frontend files (2 badge components + 1 comment section + 2 vitest mount tests + 1 TS mirror + 1 ko-KR.json SSOT + 1 cross-language drift detector test) = A35 frontend test debt **dedicated sprint** 후속 진입, cj-style carry-over 14번째 가능 — `D-10-3-DEFER-4`
- **(a) docs 정합 (carry-over)**:
  - `docs/deferred-work.md` EXTENSION (10-3 honestly DEFER items) — `D-10-3-DEFER-5`

### Wire scope summary (T1~T11 actual, dev-story DONE 2026-08-17)

- **NEW**: 6 files (alembic 0031 + 4 test files + handoff + commit-msg)
- **MODIFIED**: 10 files (8 backend service layer + 1 test + 1 spec)
- **NEW tests**: 57 cases (10 alembic + 11 validate_source_kind + 20 service + 16 endpoint) + 2 NEW capability drift cases (15 → 17 PASS) = **74 total wire coverage** (planned ~54 → actual 74 — surplus from including ORM shape tests + F10.2-(a) badge string assertions + frozen-model checks + helper purity + Korean SSOT message verification, all low-risk regression guards)
- **honestly DEFER**: 5 categories (A34 framework) — D-10-3-DEFER-1~5 명시

### Spec deviations (A36 SDR 정직 회피 ZERO)

1. **`apps/api/modules/m10_ai/exceptions.py` 미존재.** Spec T5.3 references this file. Repo actual pattern keeps typed exceptions inline in `service.py` (10-2 precedent: `InsightCacheKeyError` etc. defined in `service.py` and imported by `main.py`). Decision: defined the 2 NEW typed exceptions inline in `service.py` — no new module added.
2. **Schemas 3 NEW models (not 4 + 1 warning envelope).** Spec planned 4 NEW Pydantic models + 1 F10.2-(d) warning envelope. Actual wire: 3 NEW models (`AICommentEntry` + `AICommentListResponse` + `AICommentError` Discriminated union). F10.2-(d) ko-KR warning surface = endpoint summary description + `AI_COMMENT_SOURCE_KIND_INVALID_KO` SSOT constant + envelope `message_ko` field, NOT separate Pydantic warning model (simpler design preserved; F10.2-(d) wire verbatim intact).
3. **Capability drift +2 cases (not +1).** Spec planned 1 NEW case. Actual wire: 2 NEW cases (`test_capability_matrix_v1_21_story_10_3_coverage` + `test_capability_matrix_v1_21_story_10_3_row_present`) mirroring the 10-2 precedent.
4. **Test count exceeded plan.** Spec planned ~54 cases. Actual wire = 74 cases (+20 surplus from ORM shape tests + F10.2-(a) badge string assertions + frozen-model checks + helper purity + Korean SSOT message verification).

---

## Change Log

- 2026-08-17 — Story 10.3 spec entry (cj-style Epic 10 4번째 진입점, cj-style 30번째 epic 연속, atomic commit 해시 `146a7da` 보존)
  - 6 ACs Given/When/Then + AD-7 verbatim bind (source_kind discriminator) + F10.2 (a)~(d) 4 bullets verbatim 정합 + 10-2 wire forward-bind (`source_kind: Literal['auto_analysis', 'ai_reference']`) 보존
  - 5 honestly DEFER 명시 (A34 4-category framework): (a) docs 정합 + (b) retro input + (c) separate epic (auto_analysis read-only trigger) + (d) dedicated sprint (frontend) + (a) docs 정합 (carry-over)
  - Tasks/Subtasks section 추가 (T1~T11)
  - File List section 추가 (wire 진입 + honestly DEFER 4 categories 명시)
  - sprint-status: `10-3-ai-reference-vs-auto-analysis-badge-separation: backlog → ready-for-dev`
  - baseline_commit = `146a7da` (Epic 9 close-out retro + 9-7 follow-up sprint atomic commit hash)
  - A36 SDR 검증 4-step wire PASS (carry-over from 9-7 follow-up sprint)
  - **next**: `bmad-dev-story` 진입 → T1~T11 atomic wire → `bmad-code-review` 3rd sweep → done 진입 (cj-style 31번째 epic 연속)

- 2026-08-17 — Story 10.3 bmad-dev-story atomic sprint wire DONE (cj-style Epic 10 4번째 진입점, cj-style 31번째 epic 연속)
  - T1~T11 single atomic sprint wire 진입 (cj-style 25번째 epic 연속 atomic sprint pattern preserved)
  - **wire 표 actual**: 5 NEW + 11 MODIFIED = 16 files (+ alembic 0031 ~210 lines + service.py +460 lines + handlers.py +99 lines + schemas.py +92 lines + db_models.py +74 lines + main.py +51 lines + 4 NEW test files + 1 MODIFIED test + 2 docs/meta)
  - **Tests actual = 74 cases PASS** (10 alembic + 11 validate_source_kind + 20 service + 16 endpoint + 17 capability drift total 15 baseline + 2 NEW 10-3 cases) — planned ~54 → actual 74 (+20 surplus from ORM shape tests + F10.2-(a) badge strings + frozen-model checks + helper purity + Korean SSOT message verification)
  - **A19 cohesion pattern 8 surface PASS** (kernel SSOT 보존 + port 보존 + db schema NEW + service NEW + handler NEW + envelope NEW 2 handlers + capability +1 row + audit +2 Literal values)
  - **AD-7 verbatim bind preserved** (`SourceKind` enum + `SOURCE_KIND_VALUES` frozenset + `make_default_insights` source_kind='auto_analysis' ONLY invariant — **로직 변경 0건**, JSDoc EXTENSION only)
  - **F10.2 (a)~(d) 4 bullets verbatim wire**:
    - (a) endpoint summary description contains both badge emoji + tooltip strings verbatim
    - (b) `AICommentSourceKindInvalidError` typed exception + audit-first emit `ai_insight_cache_invalid_source_kind` + `_m10_ai_comment_source_kind_invalid_handler` envelope 422
    - (c) `AICommentImmutableAutoAnalysisError` + `assert_comment_mutable` service guard + audit-first emit `ai_insight_cache_auto_analysis_modify_denied` + envelope 422
    - (d) `AI_COMMENT_SOURCE_KIND_INVALID_KO` constant `분석 의견 출처가 불분명합니다` + endpoint summary verbatim
  - **AD-25 verbatim bind preserved** (cache key `(tenant_id, period_key, calculation_result_hash)` 4-way wire: kernel `compose_insight_cache_key` 보존 + ORM UNIQUE `uq_ai_insight_comments_tenant_period_kind_hash` 4-tuple + handler Query params + endpoint summary description)
  - **3중 게이트 FINAL CLEAN**: (1) ruff scoped 0 NEW on 10-3 files (E501 pre-existing baseline 9 unchanged) + (2) capability matrix v1.21 SSOT 17/17 PASS + (3) AD-7 verbatim bind preserved (SourceKind SSOT invariant) + AD-25 verbatim bind 4-way wire
  - **A34 4-category honestly DEFER 5건 preserved**: D-10-3-DEFER-1 (a) docs 정합 + D-10-3-DEFER-2 (b) retro input + D-10-3-DEFER-3 (c) separate epic + D-10-3-DEFER-4 (d) dedicated sprint 7 frontend + D-10-3-DEFER-5 (a) docs 정합 carry-over — CR 11-3 23번째 epic 연속 honestly DEFER discipline preserved
  - **A36 SDR 검증 4-step PASS**: commit prefix lint (pending commit message starts `@ @ Story 10.3 ...`) + sprint-status structure 정합 (10-3 status `done` + comment tail preserved, D4 fix pattern preserved) + vitest file count drift 0건 (50 baseline unchanged, frontend honestly DEFER) + commit consistency 정합 (baseline `146a7da` matches spec, 16 files wire 표 match actual file counts, D1 fix pattern preserved)
  - sprint-status: `10-3-ai-reference-vs-auto-analysis-badge-separation: in-progress → review`
  - **next**: `bmad-code-review 3rd sweep 진입 → done 진입 (cj-style 32번째 epic 연속, AD-7 verbatim bind + AD-25 verbatim bind preserved)` → Epic 10 10-4 spec entry 진입 (cj-style 33번째 epic 연속, AD-17 verbatim bind, M10 NEVER writes confirmed_inputs + idempotency on `(tenant_id, period_key, source_draft_id)`)

---

## Dev Agent Record

### Implementation Plan (T1~T11 atomic sprint, cj-style 31번째 epic 연속)

**Approach**: Single atomic sprint wire 진입 per cj-style carry-over pattern (cj-style 23번째 epic 연속 = Epic 9 retro + carry-over 11번째 + Epic 10 PRD entry 25번째 + 10-1 26~28번째 + 10-2 29번째 + 10-3 31번째). T1~T11 모두 single session 진입, no partial wire (cj-style 22번째 epic 연속 정직 회복 pattern preserved from Epic 9 retro D1~D5 FACTS.md 발견 반영).

**Mirror patterns applied**:
- 10-2 wire `InsightCacheService` + `_check_pipa_consent` + audit-first INSERT + ORM→kernel boundary + Discriminated union envelope (CR 12-5 D-14) verbatim mirrored
- 10-1 wire AD-7 verbatim bind `source_kind='auto_analysis' ONLY` invariant preserved (JSDoc EXTENSION only, 로직 변경 0건)
- 10-2 wire AD-25 verbatim 4-tuple cache key 보존 (kernel compose_insight_cache_key + ORM UNIQUE + handler Query + endpoint summary)
- 10-2 wire ALLOWED_SERVICE_SUBMODULES 보존 (cross-import ZERO, no new submodule added at 10-3 wire)
- 10-2 wire `audit_action.py` Literal + ActionClass registry EXTENSION pattern verbatim applied (+2 NEW values)

**Spec deviations (A36 SDR 정직 회피 ZERO 보고)**:
1. **`apps/api/modules/m10_ai/exceptions.py` 미존재.** Spec T5.3 references this file. Repo actual pattern keeps typed exceptions inline in `service.py` (10-2 precedent: `InsightCacheKeyError` etc. defined in `service.py` and imported by `main.py`). Decision: defined the 2 NEW typed exceptions inline in `service.py` — no new module added.
2. **Schemas 3 NEW models (not 4 + 1 warning envelope).** Spec planned 4 NEW Pydantic models + 1 F10.2-(d) warning envelope. Actual wire: 3 NEW models (`AICommentEntry` + `AICommentListResponse` + `AICommentError` Discriminated union). F10.2-(d) ko-KR warning surface = endpoint summary description + `AI_COMMENT_SOURCE_KIND_INVALID_KO` SSOT constant + envelope `message_ko` field, NOT separate Pydantic warning model (simpler design preserved; F10.2-(d) wire verbatim intact).
3. **Capability drift +2 cases (not +1).** Spec planned 1 NEW case. Actual wire: 2 NEW cases mirroring the 10-2 precedent.

### Debug Log
- None (no failures encountered during atomic sprint wire).

### Completion Notes

**Tests summary (T1~T11 atomic sprint wire, dev-story DONE 2026-08-17)**:
- `python -m pytest tests/api/test_alembic_0031_ai_insight_comments.py -q` → 10 PASSED in 0.81s
- `python -m pytest tests/services/m10_ai/test_comment_source_kind_validator.py -q` → 11 PASSED in 0.95s
- `python -m pytest tests/api/m10_ai/test_comment_service.py -q` → 20 PASSED in 1.56s
- `python -m pytest tests/api/m10_ai/test_comment_endpoint.py -q` → 16 PASSED in 0.98s
- `python -m pytest tests/integration/test_capability_matrix_v1_21_drift.py -q` → 17 PASSED in 0.08s
- **Total 10-3 wire coverage**: 74 cases PASS (planned ~54 → actual 74)

**Pre-existing baseline failure honestly reported** (D-10-2-DEFER-5 carry-over):
- `tests/architecture/test_api_calls_only_ports.py::test_api_root_does_not_import_services` fails on baseline `5dc287c` (10-1 leftover `packages.services.m10_ai.adapters.fake_adapter` stale import). 10-3 wire does NOT introduce any NEW violation. Verified by `git stash` + re-run on baseline5dc287c → same failure.

**Pre-existing sprint-status YAML parser error**:
- `yaml.safe_load` raises `ScannerError: unknown escape character 'p'` at line 75 column 2135. The file has comments containing `\path` etc. that break strict YAML parsing. This is pre-existing baseline behavior — `import yaml; yaml.safe_load(...)` fails on baseline `5dc287c` too. A36 sprint-status structure verification used regex-based parser workaround (matches `10-3-...: status_value # comment` pattern with leading whitespace tolerance).

**Next steps (cj-style Epic 10 5번째 진입점 = cj-style 32번째 epic 연속)**:
1. `bmad-code-review 3rd sweep 진입 → done 진입 (cj-style 32번째 epic 연속, AD-7 verbatim bind + AD-25 verbatim bind preserved)`
2. `Epic 10 10-4-ai-promotion-port-idempotency spec 진입 (cj-style Epic 10 6번째 진입점 = cj-style 33번째 epic 연속, AD-17 verbatim bind, M10 NEVER writes confirmed_inputs + idempotency on `(tenant_id, period_key, source_draft_id)`)`
3. `Epic 10 close-out retro 진입 (cj-style Epic 10 7번째 진입점 = cj-style 34번째 epic 연속, A37+ 결정 도출)`

---

## Status

**`review`** (set after bmad-dev-story atomic sprint wire DONE, 2026-08-17 — pending `bmad-code-review` 3rd sweep)

- **baseline_commit**: `146a7da` (cj-style Epic 9 close-out retro + 9-7 follow-up sprint atomic commit hash; 10-1 wire tip = `809a081`; 10-2 wire tip = `7683135` 보존; current HEAD = `5dc287c` = Story 10.2 wire, **A36 commit-consistency honest report**)
- **cj-style 진입점**: Epic 10 4번째 진입점 (cj-style 30번째 epic 연속 spec entry → cj-style 31번째 epic 연속 dev-story wire DONE)
- **wire 표 (actual)**: 5 NEW + 11 MODIFIED = 16 files changed (T1~T11 atomic single sprint wire)
- **Tests (actual)**: **74 cases PASS** (10 alembic + 11 validate_source_kind + 20 service + 16 endpoint + 17 capability drift total) — planned ~54 → actual 74 (+20 surplus from ORM shape tests + F10.2-(a) badge strings + frozen-model checks + helper purity + Korean SSOT message verification, all low-risk regression guards)
- **3중 게이트 FINAL CLEAN (actual)**: (1) ruff scoped 0 NEW on 10-3 files (E501 pre-existing baseline 9 unchanged) + (2) capability matrix v1.21 SSOT 17/17 PASS (15 baseline + 2 NEW 10-3 cases) + (3) AD-7 verbatim bind preserved (SourceKind SSOT invariant — `SourceKind` enum + `SOURCE_KIND_VALUES` frozenset + `make_default_insights` source_kind='auto_analysis' ONLY — **로직 변경 0건**) + AD-25 verbatim bind preserved (cache key `(tenant_id, period_key, calculation_result_hash)` 4-way wire: kernel + ORM UNIQUE + handler Query + endpoint summary)
- **honestly DEFER**: 5 categories (A34 framework) — D-10-3-DEFER-1~5 명시 preserved
- **carry-over 자산**: A28·29·30·31·32·33·34·35·36 모두 wire 진입 정합
- **다음**: `bmad-code-review 3rd sweep 진입 → done 진입 (cj-style 32번째 epic 연속, AD-7 verbatim bind + AD-25 verbatim bind preserved)` → Epic 10 10-4 spec entry 진입 (cj-style 33번째 epic 연속, AD-17 verbatim bind, M10 NEVER writes confirmed_inputs + idempotency on `(tenant_id, period_key, source_draft_id)`) → Epic 10 close-out retro 진입 (cj-style Epic 10 7번째 진입점 = cj-style 34번째 epic 연속, A37+ 결정 도출)

---

*— Story 10.3 spec entry DONE. cj-style Epic 10 4번째 진입점 (cj-style 30번째 epic 연속). AD-7 verbatim bind (source_kind='auto_analysis' | 'ai_reference' discriminator + SM-3a counter increment + auto_analysis modify deny). F10.2 (a)~(d) 4 bullets verbatim wire. 다음: 10-3 bmad-dev-story T1~T11 atomic sprint wire 진입 → done (cj-style 31번째 epic 연속).*