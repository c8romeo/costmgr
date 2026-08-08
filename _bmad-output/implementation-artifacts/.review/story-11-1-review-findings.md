## Review Findings (bmad-code-review R4 triage — 2026-08-08)

### Decision-Resolved (사용자 결정 완료 — patch 로 전환)

- [x] [Review][Decision→Patch] **D1 AD-22 partial unique index conflict** — corrected row의 `reverses_event_id=target_event.event_id` 가 0015 PARTIAL UNIQUE INDEX 와 모순. 사용자 결정: **(a) corrected row에서 `reverses_event_id` 제거** → negating row만 `reverses_event_id=target_event.event_id`, corrected row는 `correction_group_id` link 만으로 표적 연결. ECH #4.
- [x] [Review][Decision→Patch] **D2 9 EXTENSION files scope** — 9 EXTENSION files (main.py + audit_action.py + capability.py + pydantic_schemas.py + ledger_service.py + closing_period_service.py + m4_inventory/handlers.py + db_models.py + test_api_calls_only_ports.py) missing. 사용자 결정: **(a) 11-1 carry-over massive**.
- [x] [Review][Decision→Patch] **D3 Audit ActionClass** — REVERSAL_LOG 5 NEW values fill. 사용자 결정: **(a) REVERSAL_LOG 5 NEW values fill** + `MonthlyInputPeriodAction` extension (`opening_inventory_unlocked` 1 value). BH #10 / AA #7.
- [x] [Review][Decision→Patch] **D4 Migration 0019 unique index** — 0015 가 이미 만든 `uq_inventory_ledger_reverses_event_id` 를 0019 에서 중복 CREATE 시도. 사용자 결정: **(a) 0019 에서 중복 CREATE 제거** + `IF NOT EXISTS` guard 추가. ECH #5.

### Patch (carry-over massive, 사용자 결정 D1-D4 → patch 전환)

**Wire integration — 9 EXTENSION files (D2 결정)**:
- [ ] [Review][Patch] main.py — `m11_close_router` include + 5 NEW exception handlers (REVERSAL_COMPLETED 201 / REVERSAL_REJECTED 403 / REVERSAL_UNAUTHORIZED 403 / REVERSAL_DUPLICATE 422 / LOCKED_PERIOD_REVERSAL_REJECTED 422) [apps/api/main.py]
- [ ] [Review][Patch] audit_action.py — `ReversalLogAction` 5 values fill + `MonthlyInputPeriodAction` extension + `_ActionRegistry._REGISTRY[REVERSAL_LOG]` frozenset empty → 5 values fill + `_REGISTRY[MONTHLY_INPUT_PERIOD]` accepted 3 → 4 values fill (D3 결정) [apps/api/core/audit_action.py:173,355]
- [ ] [Review][Patch] capability.py — `Capability.REVERSAL_REQUEST` 신규 정의 (manufacturing 3종 ✅ / service-only ❌) + `_INDUSTRY_CAPABILITIES` 매트릭스 entry [apps/api/core/capability.py]
- [ ] [Review][Patch] pydantic_schemas.py — `ReversalRequest + ReversalResponse + ReversalCorrectedEvent + CacheInvalidationReceipt` Pydantic v2 schemas (or inline in handlers if spec deviation accepted) [apps/api/core/pydantic_schemas.py (NEW)]
- [ ] [Review][Patch] ledger_service.py — `LedgerService.count_period_events(period_key, *, event_type=None)` + `LedgerService.query_period_closing_snapshot_all(period_key)` 2 NEW methods 추가 (pure kernel dispatch) [apps/api/modules/m4_inventory/services/ledger_service.py]
- [ ] [Review][Patch] closing_period_service.py — lines 528/531 정합 (new LedgerService methods 호출) [apps/api/modules/m4_inventory/services/closing_period_service.py:528,531]
- [ ] [Review][Patch] m4_inventory/handlers.py — 501 forward-fill route deprecation 표시 (summary update + `Deprecation` header + redirect comment to M11) [apps/api/modules/m4_inventory/handlers.py:356-390]
- [ ] [Review][Patch] db_models.py — `InventoryLedger.reversal_of_period_key` mapped_column 추가 [apps/api/core/db_models.py:759-810]
- [ ] [Review][Patch] test_api_calls_only_ports.py — `ALLOWED_SERVICE_SUBMODULES` frozenset extension: `packages.services.m11_close` + `packages.services.m5_ledger` 추가 [tests/architecture/test_api_calls_only_ports.py:134-170]

**AD-22 fix (D1 결정 — corrected row 에서 `reverses_event_id` 제거)**:
- [ ] [Review][Patch] reversal_corrected.py — `build_reversal_corrected_event` 에서 `reverses_event_id` 제거 (None), corrected row는 `correction_group_id` link 만 [packages/services/m11_close/reversal_corrected.py:246]
- [ ] [Review][Patch] reversal_service.py — corrected row INSERT 시 `reverses_event_id=None` 으로 dispatch + `validate_reversal_corrected_constraints` cross-check with negating correction_group_id [apps/api/modules/m11_close/services/reversal_service.py]

**Migration fix (D4 결정 — 중복 제거 + IF NOT EXISTS)**:
- [ ] [Review][Patch] 0019 migration — `CREATE UNIQUE INDEX uq_inventory_ledger_reverses_event_id` 라인 제거 (0015 가 이미 만듦) + 모든 DDL 에 `IF NOT EXISTS` guard 추가 [apps/api/alembic/versions/0019_m11_reversal_ledger.py:58-141]

**Audit-first + REVERSAL_LOG emit (D3 결정 + CR 1.1)**:
- [ ] [Review][Patch] reversal_service.py — 5 NEW audit helpers (emit BEFORE data INSERT) + `opening_inventory_unlocked` MonthlyInputPeriodAction emit [apps/api/modules/m11_close/services/reversal_service.py:478-500]

**Concurrency (CR 4-2 + ECH #12-14)**:
- [ ] [Review][Patch] reversal_kernel_adapter.py — `fetch_target_event` SELECT 에 `.with_for_update()` 추가 [apps/api/modules/m11_close/services/reversal_kernel_adapter.py:49-68]
- [ ] [Review][Patch] reversal_service.py — `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` 명시적 transaction 시작 + PG `40001` serialization failure retry (3x exponential backoff) [apps/api/modules/m11_close/services/reversal_service.py:225-330]

**Other backend patches**:
- [ ] [Review][Patch] cache_invalidation_publisher.py — `datetime.utcnow()` → `datetime.now(tz=UTC)` (EC-8 + ECH #16) [apps/api/core/cache_invalidation_publisher.py]
- [ ] [Review][Patch] handlers.py — `datetime.utcnow()` → `datetime.now(tz=UTC)` + `TenantContext` 에 `trace_id` fallback (BH #5 + ECH #16) [apps/api/modules/m11_close/handlers.py:197,318,357]
- [ ] [Review][Patch] handlers.py — `corrected_qty` Pydantic Field 에 `ge=Decimal("0")` + `decimal_places=4` + `max_digits=18` 제약 (ECH #34) [apps/api/modules/m11_close/handlers.py:79-86]
- [ ] [Review][Patch] 0019 migration — `cache_invalidation_log.correction_group_id` NULLABLE 로 변경 (ECH #35) [apps/api/alembic/versions/0019_m11_reversal_ledger.py:121-133]

**Frontend EXTENSION (3 files)**:
- [ ] [Review][Patch] ko-KR.json — 9 NEW strings (reversal_request_dialog_title + reversal_request_reason_label + reversal_request_reason_placeholder + reversal_request_corrected_qty_label + reversal_request_corrected_period_key_label + reversal_request_submit + reversal_request_cancel + reversal_request_success_ko + reversal_request_error_ko) [apps/web/messages/ko-KR.json]
- [ ] [Review][Patch] closing-period.ts — `ReversalRequestTrigger` interface export 추가 [apps/web/lib/closing-period.ts]
- [ ] [Review][Patch] MonthlyInputTabs.tsx — `ReversalRequestButton` wire (ClosingPeriodConfirmationPanel + MonthlyClosingReportPanel + ReversalRequestButton 3-component vertical stack) [apps/web/components/m2-input/MonthlyInputTabs.tsx]

**Tests rewrite**:
- [ ] [Review][Patch] test_reversal_service.py — corrected_qty=None 케이스 + audit-first ordering verify (CR 1.1) + REVERSAL_LOG 5 values drift [tests/api/m11_close/test_reversal_service.py]
- [ ] [Review][Patch] test_reversal_handlers.py — wire integration tests [tests/api/m11_close/test_reversal_handlers.py]
- [ ] [Review][Patch] test_audit_action_m11_extension.py — ActionClass.REVERSAL_LOG 5 values + MonthlyInputPeriodAction 4 values 검증 + Capability.REVERSAL_REQUEST 매트릭스 [tests/api/test_audit_action_m11_extension.py]
- [ ] [Review][Patch] test_ledger_service_h6_extension.py — count_period_events + query_period_closing_snapshot_all 정상 케이스 + closing_period_service.py:528/531 정합 [tests/api/test_ledger_service_h6_extension.py]

### Defer (carry-over to 11-1 follow-up sprint)

- [x] [Review][Defer] **W1 M4 forward-fill route 완전 deletion** — deprecation path 표시만 wire. 완전 deletion 은 11-3 이후 결정. ECH #9. Deferred, pre-existing.
- [x] [Review][Defer] **W2 Pydantic schemas inline (handlers.py:75-176)** — `pydantic_schemas.py` 중앙화 vs inline 둘 다 가능. m4_inventory 도 동일 패턴 사용. Spec deviation but functionally working. BH #19. Deferred, pre-existing pattern.
- [x] [Review][Defer] **W3 reversal_log dead table** — 0019 migration 이 `reversal_log` table 만들었지만 service code 가 INSERT 안 함. 11-3 entry 시점에 reversal_log 단독 namespace 결정. ECH #15. Deferred.
- [x] [Review][Defer] **W4 pydantic_schemas.py NEW file** — spec EXTENSION #8 이지만 inline 으로도 작동. 11-3 또는 0.5 plumbing follow-up 에서 중앙화 결정. AA. Deferred, spec-deviation.
- [x] [Review][Defer] **W5 pg_advisory_xact_lock 미적용** — SELECT FOR UPDATE 로 충돌 방지 충분. 추가 advisory lock 은 over-engineering. ECH #12. Deferred, low priority.
- [x] [Review][Defer] **W6 zero-qty target + negative-zero rounding edge** — `qty=0` reversal 시 DB CHECK 위반 가능. Edge case defense 추가. ECH #7-8. Deferred, edge case.
- [x] [Review][Defer] **W7 Capability.INVENTORY_LEDGER + Capability.REVERSAL_REQUEST 4-tier gate** — spec 은 4 capability 모두 검증. 현재 capability_granted 단일 bool. Future 추가 가능. Deferred.
- [x] [Review][Defer] **W8 _emit_cache_invalidation_audit 의 ActionClass.SYSTEM 결정** — 11-3 entry 시점에 SYSTEM vs AI_CACHE_INVALIDATION 결정. AA LOW. Deferred.
- [x] [Review][Defer] **W9 target_id audit convention inconsistency** — m11 audit 의 `target_id=correction_group_id` vs INVENTORY_LEDGER audit 의 `target_id=row.event_id`. Cross-system observability 보강. ECH #23,25-26. Deferred, observability.
- [x] [Review][Defer] **W10 ReversalResponse NamedTuple vs pydantic schema** — BH #17 spec-deviation. m4_inventory 와 동일 패턴. Deferred.
- [x] [Review][Defer] **W11 TenantContext.trace_id extension** — fleet-wide latent bug (m4_inventory 도 동일 패턴). Fleet-wide fix required. BH #5. Deferred, pre-existing.
- [x] [Review][Defer] **W12 onboarding-incomplete tenant silent deny** — `industry=None` 시 capability_granted=False 처리. Error message misleading. BH #15 + ECH #20. Deferred.

### Dismiss

- BH #13 redundant self-reversal check — defense-in-depth, dead code 면서 safety net. 유지.
- ECH #28 published_at caller override — 의도적 security (caller-controlled timestamp 방지).
- ECH #29 ALLOWED_CHANNELS FROZENSET testability — by design (channel sprawl 방지).
