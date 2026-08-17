---
name: handoff-2026-08-17-10-1-followup-done
description: Story 10.1 follow-up sprint (T2 + T7 + T8.1 partial 해소) DONE — cj-style Epic 10 3번째 진입점 = cj-style 27번째 epic 연속. Service layer + master PRD + deferred-work.md EXTENSION. 3 honestly DEFER preserved.
metadata:
  type: project
  epic: 10
  story: 10.1
  followup_sprint: true
  status: review
  wire_commit: d56959c
  baseline_commit: b8f8217
  wire_partial: true
  honestly_defer_count: 3
  tests_pass: 40
  target_sprint: cj-style Epic 10 3번째 진입점
  carry_over: [10-1 partial wire, A34 4-category framework]
---

# Story 10.1 Follow-up Sprint DONE (cj-style 27번째 epic 연속)

## Summary

**Story 10.1 follow-up sprint** partial 해소 DONE.

- **cj-style Epic 10 3번째 진입점** = 본 handoff (cj-style 27번째 epic 연속 = 9-7 follow-up sprint 패턴 미러)
- **T2 service layer + T7 master PRD edit + T8.1 docs/deferred-work.md EXTENSION** wire DONE
- **D-10-1-DEFER-2 (T3 alembic) + D-10-1-DEFER-3 (T5 frontend) + D-10-1-DEFER-6 (T8.2 final done)** honestly DEFER preserved
- **40 tests pass** (이전 partial wire preserved)

## Wire Contents

### T2 service layer partial EXTENSION (D-10-1-DEFER-1 partial 해소)

- **T2.1** `apps/api/modules/m10_ai/schemas.py` MODIFIED
  - `MonthlyExtractRequest` Pydantic v2 frozen model (period_key + document_b64 + document_type Literal['pdf', 'xlsx'])
  - `MonthlyDraftResponse` Pydantic v2 frozen model (field_name + value Decimal + confidence Decimal + target_table Literal['monthly_inputs'] discriminator + evidence_page + requires_user_confirmation)
  - `MonthlyExtractResponse` Pydantic v2 frozen model (extraction_id + period_key + drafts + low_confidence_count + status Literal['success', 'low_confidence_warning'] Discriminated union tag discriminator — CR 11-3 즉시 sweep 회피 pattern)
  - `MonthlyExtractError` Pydantic v2 frozen model (3 envelope codes: AI_PIPA_CONSENT_MISSING + INVALID_MONTHLY_FIELD_VALUE + MONTHLY_EXTRACTION_ERROR)

- **T2.2** `apps/api/core/audit_action.py` MODIFIED
  - `ActionClass.AI_EXTRACTION_EXECUTED = "ai_extraction_executed"` NEW (Story 10.1 audit-first INSERT target)

- **T2.3** `apps/api/modules/m10_ai/service.py` MODIFIED (~225 lines EXTENSION)
  - `AiPipaConsentMissingError` typed exception (403 AI_PIPA_CONSENT_MISSING envelope, DocumentServiceError subclass)
  - `MonthlyExtractionError` typed exception (500 MONTHLY_EXTRACTION_ERROR envelope)
  - `MonthlyExtractionResult` dataclass (extraction_id + period_key + drafts tuple + low_confidence_count + trace_id)
  - `MonthlyInputDraftPersistenceRow` dataclass (field_name + value + confidence + target_table='monthly_inputs' discriminator + requires_user_confirmation + source_draft_id)
  - `extract_monthly_input(...)` service method (~120 lines):
    1. PIPA consent gate FIRST (fail-closed)
    2. audit_logs INSERT FIRST (CR 1.1 audit-first invariant)
    3. DocumentExtractionPort adapter call (FakeDocumentExtractionAdapter for tests/dev, Claude Vision for prod)
    4. Map ExtractionField -> MonthlyInputDraftRow via pure kernel (normalize_monthly_field_value + compute_extraction_confidence)
    5. AD-7 strict invariant: target_table='monthly_inputs' ONLY, NEVER 'confirmed_inputs'

- **T2.4** `apps/api/modules/m10_ai/handlers.py` MODIFIED (documented placeholder)
  - POST /api/v1/ai/extract-monthly endpoint documented as follow-up sprint second pass
  - Detailed wire (handler body + envelope mapping + main.py registration) → 10-1 follow-up sprint second pass

### T7 master PRD v2.0 본체 edit (D-10-1-DEFER-4 partial 해소)

- **T7.1** `_bmad-output/planning-artifacts/prd.md` MODIFIED
  - §8.1 M10 (c)·(d)·(e)·(f) 4-story AC extension:
    - (c) 10-1 (AI 문서추출 → 입력 초안) — 6 monthly input fields + 0.70 RED badge 강제 + input_drafts.target_table='monthly_inputs' only
    - (d) 10-2 (인사이트 캐시 정책) — cache key `(tenant_id, period_key, calculation_result_hash)` + 4-channel publisher EXTENSION (Epic 11 close/reopen trigger 진입 시점)
    - (e) 10-3 (자동 분석 vs AI 참고 배지 분리) — source_kind Discriminated union + tooltip "AI는 비권위적입니다"
    - (f) 10-4 (승격 포트 멱등성) — InputPromoter.promote idempotent + audit_logs 2행 append + AD-7 SM-3a
  - 부록 A 결정 이력 확장 (Epic 7~9 retro):
    - A19~A22 (cj-style 22번째 epic 연속, Epic 7 retro)
    - A23~A27 (cj-style 23번째 epic 연속, Epic 8 retro)
    - A28~A36 (cj-style 24~27번째 epic 연속, Epic 9 retro)

### T8.1 docs/deferred-work.md EXTENSION (D-10-1-DEFER-5 partial 해소)

- **T8.1** `docs/deferred-work.md` MODIFIED (~60 lines)
  - D-10-1-DEFER-1 (T2 service layer) — partial 해소: 5 MODIFIED + 2 NEW (handler follow-up)
  - D-10-1-DEFER-2 (T3 alembic) — preserved (1 NEW migration + 1 NEW test)
  - D-10-1-DEFER-3 (T5 frontend) — preserved (8 NEW files, A35 dedicated sprint)
  - D-10-1-DEFER-4 (T7 master PRD 본체) — partial 해소: §8.1 M10 + 부록 A done; §F10.1·§F10.2 detailed bullets는 close-out retro 진입 시점
  - D-10-1-DEFER-5 (T8.1) — DONE (본 항목 EXTENSION 완료)
  - D-10-1-DEFER-6 (T8.2 final done) — preserved (follow-up sprint second pass 후)

## honestly DEFER preserved (3 categories)

### D-10-1-DEFER-2 (T3 alembic migration + tests) — preserved

- 1 NEW migration + 1 NEW test = 2 files. Migration up/down × 3 cases + column existence × 3 + check constraint boundary × 2 + index existence × 2.
- Pickup plan: 10-1 follow-up sprint second pass (T2 service layer wire 진입 후 alembic 먼저 wire 권장).

### D-10-1-DEFER-3 (T5 frontend 5 components + TS mirror + 3 vitest files) — preserved

- 8 NEW files = ~600 LOC frontend + ~120 NEW vitest cases. A35 frontend test debt dedicated sprint (9-7 wire 패턴 미러).
- Pickup plan: T2/T3 wire done 진입 후 dedicated sprint (frontend work는 backend wire done 진입 후 권장).

### D-10-1-DEFER-6 (T8.2 sprint-status.yaml final done) — preserved

- 1 MODIFIED file. `10-1-ai-document-extraction-input-drafts: review → done` 정합.
- Pickup plan: 10-1 follow-up sprint second pass DONE 후 진입.

## 3중 게이트 FINAL CLEAN

- **backend import OK**: `apps.api.modules.m10_ai.{schemas,service,handlers}` + `apps.api.core.audit_action` 모두 importable (verified 2026-08-17)
- **master PRD v2.0 SSOT**: §8.1 M10 4-story AC + 부록 A A19~A36 결정 이력 정합
- **AD-7·17·25 bind preserved**:
  - **AD-7** (AI non-authoritative): `MonthlyInputDraftPersistenceRow.target_table='monthly_inputs'` discriminator, M10 NEVER writes `confirmed_inputs` (T2.3 service method fail-closed)
  - **AD-17** (promotion port idempotency): `InputPromoter.promote(...)` M2-only, M10 has no promote method on purpose
  - **AD-25** (cache invalidation): `ai_cache` channel 1개 wire 진입, Epic 11 close/reopen trigger EXTENSION forward-lock

## A36 SDR 검증 프로토콜 (carry-over 9-7 follow-up sprint + 10-1 partial wire)

- **commit prefix lint PASS**: `@ @` prefix (Story 10.1 follow-up sprint)
- **sprint-status structure 정합**: D4 fix DONE preserved (Epic 10 entries in development_status block)
- **vitest file count drift 0건**: frontend 5 components NOT added in this sprint (D-10-1-DEFER-3 preserved)
- **commit consistency 정합**: handoff memory file sync (honestly DEFER 3 categories 명시)

## Wire scope summary

- **NEW**: 1 file (`_bmad-output/implementation-artifacts/commit-msg-10-1-followup.txt`)
- **MODIFIED**: 6 files (`_bmad-output/planning-artifacts/prd.md` + `apps/api/core/audit_action.py` + `apps/api/modules/m10_ai/{schemas,service,handlers}.py` + `docs/deferred-work.md`)
- **7 files changed, 475 insertions(+)**
- **Tests**: 40 pass + service module importable (verified 2026-08-17)
- **honestly DEFER**: 3 categories preserved (D-10-1-DEFER-2 + D-10-1-DEFER-3 + D-10-1-DEFER-6)

## Next steps

1. **10-1 follow-up sprint second pass** — T2 handler detailed wire + T3 alembic + T5 frontend + T8.2 final done (cj-style 28번째 epic 연속)
2. **10-1 done 진입** — sprint-status: `review → done`
3. **10-2 spec entry 진입** — cj-style 29번째 epic 연속 (Three-Insight Cache Policy)
4. **10-3 spec entry 진입** — cj-style 30번째 epic 연속 (Reference vs Auto Analysis Badge)
5. **10-4 spec entry 진입** — cj-style 31번째 epic 연속 (AI Promotion Port Idempotency)
6. **Epic 10 close-out retro 진입** — cj-style 32번째 epic 연속 (4-story + retro 5번째 진입점 패턴 완료)

## Related mems

- [[handoff-2026-08-17-10-1-done]] — Story 10.1 partial wire (cj-style 26번째 epic 연속)
- [[handoff-2026-08-17-epic-10-prd-entry-done]] — Epic 10 PRD entry (cj-style 25번째 epic 연속)
- [[handoff-2026-08-17-9-7-done]] — Epic 9 9-7 follow-up sprint (A35 + A36 wire, cj-style 24번째 epic 연속)
- [[handoff-2026-08-17-epic-9-retro-done]] — Epic 9 retro + A31~A36 wire (cj-style 23번째 epic 연속)
