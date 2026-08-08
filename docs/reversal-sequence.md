# Reversal Sequence — Story 11.1 operator/dev guide

> **M11 module authority** + AD-22 reversal ledger wire + H6 production bug
> fix + AD-25 1-channel cache invalidation publisher. Story 11.1 (cj-style
> 3-story 분할 1번째 — Epic 5 retro §6 W1 패턴 적용).
>
> **대상 독자**: 회계사 (PRD §F11.3 메인 사용처) + 운영자 (H6 fix 결과 확인)
> + 개발자 (Epic 11 11-2 + 11-3 진입점 wire).
>
> **상태**: Story 11.1 wire done (in-progress → review 진입 대기).

## 1. 왜 역분개인가?

PRD §F11.3 ("Reversal sequence") + AD-2 (append-only ledger) + AD-22
(reversal construction) SSOT:

> "마감 후 입력 수정은 역분개로만 가능합니다."

5-2 inventory_ledger wire + PostgreSQL `BEFORE UPDATE OR DELETE`
trigger로 인하여 원본 row는 **절대 변경 불가**. 사용자가 마감 후 오류를
발견하면 (1) M4 entrypoint (`POST /api/v1/inventory/ledger/reversal-requests`
501 forward-fill) → (2) M11 actual write (`POST /api/v1/close/reversal-requests`)
wire가 발동되며, AD-22 sequence가 sign-negating row + corrected row
2개를 append-only INSERT 합니다.

| 사용자 흐름 | wire | 결과 |
|---|---|---|
| 마감 후 오류 발견 | `POST /api/v1/close/reversal-requests` (201) | correction_group_id 발급 + sonner toast.success |
| 잠긴 기간 (`status='locked'`) | `POST .../reversal-requests` (422) | LOCKED_PERIOD_REVERSAL_REJECTED + sonner toast.error |
| 동일 target 2회 호출 | `POST .../reversal-requests` (422) | REVERSAL_DUPLICATE + sonner toast.error |
| service-only tenant | `POST .../reversal-requests` (403) | INDUSTRY_NOT_SUPPORTED + ReversalRequestButton 비노출 |

## 2. AD-22 reversal sequence 9-step orchestrator

`apps/api/modules/m11_close/services/reversal_service.py::ReversalService.execute_reversal`:

1. **SELECT target_event** FROM `inventory_ledger` WHERE `event_id = target_event_id` AND `tenant_id = tenant_id` FOR UPDATE (SELECT FOR UPDATE — 6-1 wire closing_period_service 동일 패턴).
2. **SELECT period_status** FROM `monthly_input_periods` WHERE `tenant_id = tenant_id` AND `period_key = target_event.period_key`. period_status='open' / 'closed' 허용, 'locked' → `LockedPeriodReversalRejectedError` 422.
3. **`authorize_reversal`** (T1.3 pure kernel) decision — `capability_granted` 검증 (M11 owns authorization — PRD §F11.3 + AD-22).
4. **`correction_group_id = uuid7()`** (5-2 P8 pattern, uuid4 fallback).
5. **sign-negating row INSERT** (event_type='reversal_negating' + `reverses_event_id=target_event.event_id` + `reversal_of_period_key=target_event.period_key` + `correction_group_id=correction_group_id` + `qty=-target_event.qty` + banker's rounding). 11-value event_type CHECK + reversal_coherence CHECK + qty_signed_coherence CHECK 통과 검증 (DB trigger).
6. **corrected row INSERT** (corrected_qty / corrected_period_key NOT None 시) — event_type='reversal_corrected' + `reverses_event_id=target_event.event_id` + `correction_group_id=correction_group_id` + `qty=corrected_qty` + `period_key=corrected_period_key`. DB CHECK 통과 검증.
7. **AD-25 publisher publish** (channel='ai_cache') — `cache_invalidation_publisher.publish(...)` 호출.
8. **audit-first INSERT** to `reversal_log` + `audit_logs` (`m11_reversal_handler_invoked` + `reversal_negating_inserted` + `reversal_corrected_inserted` + `monthly_input_period_opening_unlocked` if 5-1 opening carry 관련 시 + `inventory_ledger_reversal_logged` for INVENTORY_LEDGER).
9. **COMMIT** — atomic transaction 종료 (REPEATABLE READ isolation level).

## 3. (tenant_id, reverses_event_id) UNIQUE 제약 보장

Alembic 0015 `uq_inventory_ledger_reverses_event_id` UNIQUE
`(tenant_id, reverses_event_id) WHERE reverses_event_id IS NOT NULL`
PARTIAL UNIQUE INDEX 보존. 동일 `target_event_id` 로 reversal sequence
2회 호출 시 2번째 호출에서 `uq_inventory_ledger_reverses_event_id`
violation → 422 REVERSAL_DUPLICATE typed envelope.

defense-in-depth:
- pure kernel #1 `validate_reversal_negating_constraints`
- service layer SELECT FOR UPDATE 직전 pre-check (CR 4-2 TOCTOU 방지)
- `pg_advisory_xact_lock(uuid5)` 보강 (Epic 2 2-3 D2 결정 패턴)

## 4. capability matrix v1.10 wire

`docs/capability-matrix.md` v1.10 — `Capability.REVERSAL_REQUEST` 신규
정의 + manufacturing-kind 3종 (manufacturing / manufacturing_service /
manufacturing_service_other) wire. service-only ❌ 403
INDUSTRY_NOT_SUPPORTED typed envelope. PRISM gate (A9 결정 + PRD §F11.3
명시).

drift protection: `tests/api/test_audit_action_m11_extension.py::test_capability_reversal_request_*`.

## 5. A9 결정 5개 범위 fill

Epic 5 close-out retro (2026-08-07) §7 A9 결정 wire:

1. **`reversal_negating` + `reversal_corrected` event type fill** —
   Alembic 0015 11-value CHECK (lines 92-110) 이미 wire. 11-1 wire =
   actual INSERT (T1.1 + T1.2 pure kernel) + ReversalService.execute_reversal.
2. **`opening_inventory_unlocked` action** — `apps/api/core/audit_action.py`
   `MonthlyInputPeriodAction` Literal extension — `opening_inventory_unlocked`
   1 value 신규 fill. `_ActionRegistry._REGISTRY[ActionClass.MONTHLY_INPUT_PERIOD]`
   accepted frozenset 3 → 4 values fill.
3. **`reversal_request_enabled` field wire** — `Capability.REVERSAL_REQUEST`
   신규 정의 (manufacturing 3종 ✅ / service-only ❌).
   `MonthlyInputStateResponse.reversal_request_enabled` field =
   Capability.REVERSAL_REQUEST capability_granted mirror.
4. **service layer reversal handler** — `apps/api/modules/m11_close/services/reversal_service.py`
   (NEW) — ReversalService class 4 operations.
5. **UI reversal request form** — `apps/web/components/m4-inventory/ReversalRequestDialog.tsx`
   (NEW) + ReversalRequestForm + ReversalRequestButton.

## 6. H6 production bug fix

`closing_period_service.py:528/531` calls
`LedgerService.count_period_events` + `query_period_closing_snapshot_all`
정의 부재 → monthly closing report read-only aggregator 진입 시
`AttributeError` 가능 (production 진입 차단).

**11-1 wire = H6 fix close-out**:
- `packages/services/m5_ledger/count_period_events.py` (NEW pure kernel #4)
  — `count_period_events_sql(period_key, *, event_type=None)` text SQL builder.
- `packages/services/m5_ledger/query_period_closing_snapshot_all.py` (NEW pure kernel #5)
  — `query_period_closing_snapshot_all_sql(period_key)` closing_snapshot per-product qty aggregate.
- `apps/api/modules/m4_inventory/services/ledger_service.py` extension
  — 2 NEW method 추가 (pure kernel dispatch).
- `closing_period_service.py:528/531` 호출 정합.

drift protection: `tests/api/test_ledger_service_h6_extension.py` (7 NEW tests).

## 7. AD-25 cache invalidation notification (1-channel)

`apps/api/core/cache_invalidation_publisher.py::CacheInvalidationPublisher`
— M10 AI cache invalidation 1-channel wire. channel FROZENSET = `{'ai_cache'}`.

M11 reversal sequence 완료 시 publish → M10 cache invalidation queue +
AI cache reset.

**11-3 entry 시점에 channel registry 확장** (cost_engine_cache /
fiscal_period_cache / closing_snapshot_cache 등).

**수동 publish endpoint**: `POST /api/v1/close/cache-invalidation`
(200) — M10 AI cache consumer가 on-demand flush 가능.

## 8. A8 inline projection deprecation timeline

PRD §F11.3 spec = "역분개는 같은 기간 내". `correction_group_id` link
+ `reversal_of_period_key` 보존. Epic 3.3 inline projection은 11-1
wire 시점에 보존 (Epic 6 close-out 시점 미도래).

- **11-1 wire 시점**: inline projection 보존 (Epic 6 close-out 시점 미도래).
- **11-2 wire**: inline projection 보존 (close lock 무관).
- **11-3 wire**: inline projection fold-in 결정 + reversal_corrected row
  가 `monthly_input_periods.opening_inventory` JSONB 업데이트 trigger.
- **Epic 11 close-out 시점**: inline projection 완전 제거 (Epic 6 close-out 후).

## 9. Defense in depth — Layer 4 (역분개)

PRD §A11 4-layer → 11-1 wire 시점 5-layer 확장:

1. **Layer 1 (입력 시 경고)** — Story 3.3 inline projection + 5-2 ledger aggregate.
2. **Layer 2 (마감 시 차단)** — Story 5-3 `closing_guard_service.request_close_attempt`.
3. **Layer 3 (마감 확정 시 snapshot)** — Story 6-1 `closing_period_service.confirm_closing_period`.
4. **Layer 4 (마감 보고서 시각화)** — 6-2 `monthly_closing_report_service.get_monthly_closing_report`.
5. **Layer 5 (역분개 — 11-1 PRIMARY)** — `ReversalService.execute_reversal` dispatch.

capability gate 4-tier defense:
- `Capability.REVERSAL_REQUEST` (11-1 v1.10 wire)
- `Capability.INVENTORY_LEDGER` (5-2 wire)
- `Capability.MONTHLY_CLOSING_REPORT` (6-1 v1.8 wire)
- `Capability.MONTHLY_INPUT_PRODUCTION` (3-1 wire)

## 10. 11-2 + 11-3 진입점

| Story | Spec 진입 | Primary AC | AD-22 wire 추가 |
|---|---|---|---|
| 11-2 close-sequence-lock | epics.md 11.1 greenfield | fiscal_periods 테이블 신설 + 4단계 divisions→manufacturing→ABC→common 순서 강제 + 부분 마감 불허 + AD-6 INSERT 거부 | reversal sequence 진입점 monthly_input_periods.status 가드 확장 (fiscal_periods.status 추가) |
| 11-3 snapshot-persistence-with-reverse | epics.md 11.2 + 11.3 통합 | fiscal_period_snapshots.state='committed'→'reversed' 전이 + snapshot hash 영구 보존 + AD-25 publisher full wire + report 재계산 trigger | reversal sequence → snapshot state 전이 trigger + correction_group_id → fiscal_period_snapshots.reversal_log link |

## 11. Defers (12 items, 11-1 wire 시점)

1. 11-2 close-sequence-lock — cj-style 3-story 분할 2번째. 11-1 wire는 reversal ledger + H6 fix + AD-25 1-channel.
2. 11-3 snapshot-persistence-with-reverse — cj-style 3-story 분할 3번째.
3. M4 501 forward-fill route 완전 deprecation — `m4_inventory/handlers.py:356-390` 의 501 `POST /api/v1/inventory/ledger/reversal-requests` route는 11-1 wire 후 deprecation path 표시. 완전 deletion은 후속 sprint 결정.
4. 5-3 W1 production_material_consumption emit — Epic 11 BOM authority 진입 시 (5-3 carry-over).
5. 5-2 W4 `_emit_inventory_ledger_event_for_row` isolated unit tests — Epic 11 reversal 진입 시 (5-2 carry-over).
6. M14 l2-input-opening-carry.ts — 5-1 frontend toast (Epic 4 A6) wire done. 11-1 wire는 ReversalRequestForm (no conflict).
7. Epic 11 close-out retro A8 inline projection deprecation 결정.
8. Alembic 0018 reversal_log namespace 추가 — 11-1 wire는 reversal_log audit INSERT를 inventory_ledger audit_logs 테이블에 동시 emit.
9. 5-3 T12.2 test file (closing invariant TS mirror parity) ≥ 10 cases — Story 6.1 carry-over (A12 done 2026-08-07). 11-1 wire는 ≥ 9 NEW cases.
10. H6 fix carry-over (6-2 Deferral #11) — 11-1 wire = H6 fix close-out ✅ done.
11. W2 V8 `_fixture_lock_sha256` placeholder — 11-1 wire 영향 없음 (reversal sequence는 V8 input 변화 없음).
12. AD-25 publisher multi-channel 확장 — 11-1 wire 1-channel (ai_cache). 11-3 entry 시점에 channel registry 확장.
