---
baseline_commit: b4b84da
target_key: 5-2-inventory-ledger-append-only-events
epic: 5
story_id: 5.2
title: Inventory Ledger Append-Only Events
status: review
---

# Story 5.2: Inventory Ledger Append-Only Events

Status: review

> Epic 5 두 번째 스토리 — `inventory_ledger` 신규 테이블 + PostgreSQL `BEFORE UPDATE OR DELETE` row-level trigger로 append-only 강제. AD-2 (append-only ledger) + AD-6 (close lock 부재 — lock 없으면 ledger row INSERT 가능) + AD-18 (single product identity) + AD-22 (reversal entrypoint forward-fill). Story 5.1의 `monthly_input_periods.opening_inventory` JSONB carry chain과 별도 path = 새 테이블. Story 5.1의 inline projection deprecation 시점 = **본 스토리 commit 안에 `LEDGER_REFERENCE_QUERY_STUB` swap + Epic 3.3 inline projection 제거** (Epic 4 close-out A3 cj-style 결정).
>
> **baseline_commit = b4b84da** (Story 5.1 dev-story tip, 5-2 즉시 진입 기준). A5/A7 wire done (D1 deferral 해결: `ActionClass.INVENTORY_LEDGER` 6 values 채움). A6 Story 0.5 plumbing = 5-3 진입 전 별도 Story (5-2 backend-only).

<!-- dev-context: Story 0-2 (2026-07-29) — RLS 인프라 + audit_logs INSERT-only with `BEFORE UPDATE OR DELETE` trigger 패턴이 Epic 0에서 이미 wire됨. AD-3 tenant_id policy + AD-2 append-only trigger 패턴 SSOT.
                    Story 3.1 (2026-08-01) — `monthly_input_periods` + `monthly_input_rows` 테이블 (Alembic 0009), RLS 보존. 5-2는 `inventory_ledger` table 신규 (별도 schema story 5-1 JSONB의 immutable 누적 발행 carrier와 별개).
                    Story 3.3 (2026-08-01) — `monthly_input_periods.opening_inventory` JSONB column (Alembic 0011) + `packages/services/m2_input/inventory_projection.py::LEDGER_REFERENCE_QUERY_STUB: Final[str] = ""` + `TODO(epic-5)` marker + `TODO(epic-5-5-2)` marker (Story 5-1 spec 본문에서 5-2 진입 시 inline projection deprecation marker로 승격). **5-2 commit 안에 swap 확정** (Epic 4 close-out A3 cj-style 결정 = 5-2 commit + 1 epic maintenance 후 Epic 6 close-out 시점에 Epic 3.3 inline projection 완전 제거).
                    Story 4.1 (2026-08-02) — engine returns `state='draft'` (AD-22 boundary strengthening). 5-2 inventory_ledger = service layer ownership (engine은 ledger 절대 모름).
                    Story 4.2 (2026-08-03) — REPEATABLE READ + audit-first (CR 1.1) + calc_log + AD-22 state transition (service layer responsibility). 5-2 inventory_ledger row INSERT는 별도 path — calc_orchestrator와 monthly_input_service 양쪽에서 호출.
                    Story 4.3 (2026-08-03) — Industry enum SSOT (4 values: manufacturing / manufacturing_service / service / manufacturing_service_other) + verification_log CHECK constraint (Alembic 0013) + V7 ABC integrity. 5-2 `INVENTORY_LEDGER` capability gate = service-only ❌.
                    Story 4.4 (2026-08-03, commit 80f4494) — A5 forward-lock (verify_v8_golden_match + Alembic 0014 verification_log CHECK 4-value expansion). 5-2 INVENTORY_LEDGER forward-lock 동일 패턴 적용.
                    Story 5.1 (2026-08-04, commit b4b84da) — opening_carry_chain wire + 4 hooks into monthly_input_service + 2 audit actions under ActionClass.MONTHLY_INPUT_PERIOD (carried + locked) + INVENTORY_LEDGER class placeholder 전가 (5-2 spec 진입 시 6 values 채움). 5-1 carry chain 결정이 5-2 inventory_ledger event로 라우팅 전환.
                    Epic 4 close-out retro (2026-08-03) A3 cj-style — 3-story 분할 유지 (5-1 → 5-2 → 5-3) + inline projection deprecation timeline = 5-2 spec에서 명시 (5-2 commit + 1 epic maintenance). **5-2 commit 안에 Epic 3.3 inline projection 제거 + LEDGER_REFERENCE_QUERY_STUB swap = 본 spec 진입 필수**.
                    Epic 4 close-out retro A5 — A5 Full Phase 1+2+4 done 상태. 5-2 spec은 A5 SSOT 패턴 따라감 (D1 deferral 해결).
                    Epic 4 close-out retro A6 — 0.5 plumbing = 5-3 진입 전 별도 Story (5-2 backend-only 진행 가능).
                    Epic 4 close-out retro A7 — Epic 4 carry done (AST guard + SDR overclaim detector). 5-2 패턴 동일 적용.
                    AD-2 (append-only ledger) — `inventory_ledger` table의 INSERT-only 보장을 PostgreSQL `BEFORE UPDATE OR DELETE` row-level trigger로 강제. UPDATE/DELETE attempt → `append-only violation` typed exception.
                    AD-6 (close lock) — period locked_by_calculation=true 시 ledger INSERT은 허용 (ledger는 원장, close lock은 fiscal_period_snapshot 소유). reverse-direction = Epic 11 reversal_log 위임.
                    AD-11 (layer rule) — pure helpers = `packages/services/m4_inventory/ledger.py` (NEW per cr-5-1-lessons §(1)). service layer = `apps/api/modules/m4_inventory/services/ledger_service.py` (NEW). engine = 건드리지 않음. inventory_projection.py는 pure helper 경유 (≠ engine).
                    AD-15 (cross-language parity) — TS mirror drift detector `tests/integration/test_inventory_ledger_label_consistency.py` NEW. Decimal serialization parity.
                    AD-18 (single product identity) — `inventory_ledger.product_id` (UUID v7) = PRODUCT(product_id) SSOT. product_id 다른 identity 사용 불가.
                    AD-22 (append-only-leaning + reversal) — correction = (1) sign-negating reversal row + (2) optional corrected row. original 절대 mutation 없음. M4 calls `request_reversal(event_id, reason)`. M11 authorizes + writes sequence (Epic 11). 5-2 commit = entrypoint wire + audit marker + reversal_requested stub. 실제 sequence insert = Epic 11.
                    PRD §F4.1 (기초재고 자동 이월) — 5-1 carry chain을 5-2 ledger event로 라우팅.
                    PRD §F4.2 (음수 기말 차단) — 5-3 close-time block. 5-2는 closing 음수 event도 ledger에 INSERT (V3 fire signal = ledger row 자체, not closing auto-reject).
                    PRD §6.2 (수불부) — opening + inbound - outbound = closing. 5-2는 모든 stream의 inbound/outbound row를 ledger event로 누적. opening prev period carry도 ledger event ('opening_carried').
                    0.5 plumbing — 5-2 backend-only 진행. Epic 5 5-3 frontend toast 진입 전 A6 done 필수. -->

## Story

As a **platform engineer**,
I want **수불부(inventory_ledger)가 INSERT-only이고 PostgreSQL `BEFORE UPDATE OR DELETE` 트리거가 UPDATE/DELETE 시 `append-only violation`을 raise하며, 수정 필요 시 AD-22 reversal sequence(부호 반전 row + corrected row)로만 처리되고, 모든 row가 `(tenant_id, product_id, period_key, event_type, qty, trace_id)` 컬럼을 가지는 것**,
so that **회계 감사 시 원본이 절대 안 바뀌고, 행위별 시점·수량·trace가 immutable 누적 발행 carrier로 보존되어 Epic 11 reversal + Epic 6 reporting이 ledger row를 read-only로 안전 조회할 수 있다** — AD-2 (append-only ledger) · AD-6 (close lock 부재 — 원장은 close lock 미적용) · AD-18 (single product identity) · AD-22 (reversal entrypoint forward-fill) · A5 forward-lock (inventory_ledger class 6 values 신규 채움) · A11 (오류의 가시화 — append-only violation 500 typed envelope).

## Acceptance Criteria

1. **Given** Epic 0-2의 `audit_logs` INSERT-only with `BEFORE UPDATE OR DELETE` trigger + RLS 인프라 + AD-2 append-only invariant SSOT
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 책임 분리가 유지된다:
     - **Pure kernel** (NEW `packages/services/m4_inventory/ledger.py`) — `InventoryLedgerEvent` NamedTuple + `build_event_payload(product_id, period_key, event_type, qty, *, trace_id, **metadata) -> dict[str, Any]` + `validate_event_type(event_type) -> None` + `validate_event_shape(event) -> None` + `append_only_violation_message(original_op, event_id) -> str`. stdlib-only (no DB, no clock, no random). banker's rounding via `QTY_QUANTUM` import from `inventory_projection`. 1 typed exception (`AppendOnlyLedgerError`, NO HTTP mapping — pure helper owns domain semantics).
     - **Pure kernel #2** (NEW `packages/services/m4_inventory/ledger_query.py`) — `build_period_closing_query() -> LedgerQuery` (read-only SELECT, SQL builder — service binds via `text().bindparams()`) + `build_carry_chain_query(depth: int = 12) -> LedgerQuery` (chain walk) + `LedgerQuery` NamedTuple `(sql: str, params: tuple, description: str)` (SQL builder shape, NOT value object). **Spec/code drift (D1+D2 review resolution 2026-08-04)**: original spec literal `(period_key, product_id, closing_qty)` was a value object; actual ships SQL builder (better engineering, service layer binds parameters). Same pure kernel filename pattern as 5-1 (`opening_carry.py`).
     - **Service layer** (NEW `apps/api/modules/m4_inventory/services/ledger_service.py`) — `LedgerService` class with 5 operations: `append_event(session, *, ...)` (audit-first INSERT), `query_period_closing(session, *, period_key) -> dict[UUID, Decimal]` (read-only, replaces Epic 3.3 inline projection for service-layer callers), `query_carry_chain(session, *, period_key, *, depth=12) -> list[dict]` (chain read, returns SQL-alchemy row-as-dict), `request_reversal(session, *, event_id, *, reason, *, actor_id)` (Epic 11 forward-fill — M4 entrypoint 위임, audit marker INSERT only, actual sequence insert = Epic 11 module authority), `validate_append_only_invariant(session, *, tenant_id) -> None` (defense-in-depth guard — DB triggers are the gate; service layer is early-fail).
     - **Capability gate** (`apps/api/core/capability.py::Capability.INVENTORY_LEDGER` — already exists from Story 5.1 v1.5 pre-fill). `require_capability("inventory_ledger")` dependency를 handlers에 wire. service-only tenant → 403 `INDUSTRY_NOT_SUPPORTED` typed envelope (AD-15 §4).
     - **Wire trigger** (NEW `apps/api/modules/m4_inventory/handlers.py` extension) — 4 routes: (a) `POST /api/v1/inventory/ledger/events` (operator manual INSERT — recovery / backfill), (b) `GET /api/v1/inventory/ledger/period-closing?period_key=...` (read-only closing projection = Epic 3.3 inline projection 교체 진입점), (c) `GET /api/v1/inventory/ledger/carry-chain?period_key=...&depth=N` (read-only chain walk = 5-1 `validate_opening_lock_consistency` 강화), (d) `POST /api/v1/inventory/ledger/reversal-requests` (M4 reverse-entrypoint forward-fill — Epic 11 module authority owns actual sequence insert; 5-2 only writes the audit marker + queues the request). ALL routes require capability gate `INVENTORY_LEDGER` (manufacturing 3종 ✅ / service-only ❌).
     - **A5 forward-lock** (`apps/api/core/audit_action.py`) — `ActionClass.INVENTORY_LEDGER` accepted frozenset 6 values 신규 채움 (5-1 spec의 placeholder 6 values → 실제 wire). CR 5-1 D1 deferral 보존 결정 일치.

2. **Given** AC #1 pure kernel + service layer + wire trigger + A5 forward-lock
   **When** Alembic migration `0015_inventory_ledger.py` 본 스토리 commit 안 ship
   **Then** 다음 schema + invariant wire (AC #2 — PostgreSQL `BEFORE UPDATE OR DELETE` trigger 핵심 invariant):
     - **신규 테이블 `inventory_ledger`**:
       ```sql
       CREATE TABLE inventory_ledger (
           event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
           tenant_id UUID NOT NULL REFERENCES tenants(id),
           product_id UUID NOT NULL REFERENCES products(id),  -- AD-18 single product identity
           period_key VARCHAR NOT NULL,  -- AD-24 typed period-key ('YYYY-MM')
           event_type VARCHAR NOT NULL,  -- CHECK constraint (AC #2)
           qty NUMERIC(18, 4),  -- nullable for non-quantitative events
           trace_id UUID NOT NULL,
           reverses_event_id UUID,  -- AD-22 reversal row marker
           reversal_of_period_key VARCHAR,  -- AD-22 reversal context
           correction_group_id UUID,  -- AD-22 corrected row shared group
           payload JSONB NOT NULL DEFAULT '{}',
           created_at TIMESTAMPTZ NOT NULL DEFAULT now()
       );
       ```
     - **`BEFORE UPDATE OR DELETE` row-level trigger** (PostgreSQL — append-only invariant):
       ```sql
       CREATE FUNCTION _inventory_ledger_append_only() RETURNS trigger AS $$
       BEGIN
           RAISE EXCEPTION 'append-only violation: inventory_ledger table forbids UPDATE/DELETE (event_id=%, op=%)',
               COALESCE(OLD.event_id::text, '<new>'), TG_OP
               USING ERRCODE = 'P0001';  -- custom SQLSTATE
       END;
       $$ LANGUAGE plpgsql;

       CREATE TRIGGER inventory_ledger_append_only
           BEFORE UPDATE OR DELETE ON inventory_ledger
           FOR EACH ROW EXECUTE FUNCTION _inventory_ledger_append_only();
       ```
     - **CHECK constraint on `event_type`** (10 values + 1 reversal marker = 11):
       - `'opening_carried'` — 5-1 carry chain 결과 (auto/manual)
       - `'opening_carried_stale_overwrite'` — 5-1 AC #3 silent overwrite
       - `'purchase_inbound'` — monthly_input_rows stream='purchases' PRD §6.2 입고
       - `'sales_outbound'` — monthly_input_rows stream='sales' PRD §6.2 출고
       - `'production_output_inbound'` — monthly_input_rows stream='production' (output product_qty)
       - `'production_material_consumption'` — monthly_input_rows stream='production' (input material 사용량)
       - `'adjustment_positive'` — 직접 조정 (+) — Epic 5+ 후속 (Epic 11 close 시 write)
       - `'adjustment_negative'` — 직접 조정 (−) — Epic 5+ 후속
       - `'reversal_negating'` — AD-22 부호 반전 row (Epic 11 module authority insert)
       - `'reversal_corrected'` — AD-22 corrected row (Epic 11 module authority insert)
       - `'closing_snapshot'` — periodic close 시점에서 closing_balance materialization (Epic 11)
     - **Unique constraint**: `(tenant_id, reverses_event_id)` WHERE `reverses_event_id IS NOT NULL` (AD-22 — duplicate reversal 방지).
     - **Partial unique index**: `(tenant_id, period_key, created_at)` — append-only natural ordering for V8-style determinism + idempotent re-call detection.
     - **RLS policy**: `tenant_id = (auth.jwt() ->> 'tenant_id')::uuid` (AD-3 SSOT, Story 0-2 정책 그대로).
     - **3-way drift detector** (`tests/integration/test_audit_action_consistency.py` extension) — registry ↔ DB CHECK ↔ call sites 검증 pass (CR 4-3 lesson + Epic 4 close-out retro A5 pattern 동일).

3. **Given** AC #2 trigger install + 5-1 opening_carry + Story 3.3 monthly_input_rows inbound/outbound
   **When** 운영자가 기존 `inventory_ledger` row를 UPDATE 또는 DELETE 시도
   **Then** 다음 append-only enforcement 발동 (AC #3 — `append-only violation` typed envelope):
     - **DB trigger first gate** — PostgreSQL raises exception `append-only violation` with custom SQLSTATE `P0001`. Connection error raised → SQLAlchemy wraps as `SQLAlchemyError`.
     - **Service layer second gate** — `apps/api/main.py` registered exception handler catches `SQLAlchemyError` + custom SQLSTATE `P0001` → 500 `APPEND_ONLY_LEDGER_VIOLATION` typed envelope: `{error_code: "APPEND_ONLY_LEDGER_VIOLATION", message_ko: "수불부는 원장만 기록 가능하며 수정·삭제 불가합니다", details: {event_id: str, attempted_op: "UPDATE"|"DELETE", source: "service_role"|"user", actor_id: UUID, trace_id: UUID, db_trigger_message: str}}` (AD-15 §4 envelope).
     - **Audit log emission** (CR 1.1 audit-first) — `audit_logs.action='inventory_ledger_event_rejected'` (ActionClass.INVENTORY_LEDGER, NEW) payload: `{event_id: str, period_key: str, attempted_op: "UPDATE"|"DELETE", actor_id: UUID, tenant_id: UUID, trace_id: UUID, db_trigger_sqlstate: "P0001"}` — INSERT succeeds (audit_logs는 별도 table, AD-2 append-only 보존) + revert-only path.
     - **Defense in depth** — `LedgerService.validate_append_only_invariant(session, *, tenant_id)` helper = Ast-grep scan for UPDATE/DELETE on inventory_ledger across the codebase (CR 4-3 pattern). Failed scan = service-layer gate. 5-2 commit 안에서 `tests/architecture/test_inventory_ledger_no_mutate.py` NEW = AST guard pass.

4. **Given** AC #2 + #3 trigger + RLS + CHECK constraint + audit-first wire
   **When** 운영자가 신규 `inventory_ledger` row를 INSERT 시도 (carry-chained opening, monthly_input_rows inbound/outbound, manual backfill)
   **Then** 다음 append-only INSERT path 발동 (AC #4 — primary INSERT path):
     - **Service layer audit-first** — `LedgerService.append_event(session, *, product_id, period_key, event_type, qty, **metadata)` 진입점:
       1. `validate_event_type(event_type)` — pure kernel CHECK constraint SSOT 11 values.
       2. `validate_event_shape(event)` — Decimal quantization QTY_QUANTUM.
       3. `session.add(InventoryLedger(...))` + `flush()` — INSERT to ledger.
       4. **`emit_audit_typed(action_class=ActionClass.INVENTORY_LEDGER, action='inventory_ledger_event_appended', ..., payload={event_id, period_key, event_type, qty, ...metadata})`** INSERT to audit_logs (CR 1.1 audit-first).
       5. `session.commit()`.
     - **5-1 carry chain hook integration** — `OpeningCarryService.run_chain(period)` (5-1 AC #2) 끝점에서 carry chain 결정별로 `ledger_service.append_event(event_type='opening_carried' | 'opening_carried_stale_overwrite', ...)` 호출. 즉, opening_carry_service는 더 이상 `audit_logs.action='opening_inventory_auto_carried'` emit 안 함 — 5-2 wire 후엔 `inventory_ledger_event_appended` (event_type='opening_carried') + `audit_logs.action='inventory_ledger_event_appended'` 두 행 동시 emit (AD-2 SSOT: 둘 다 immutable).
     - **MonthlyInputService hook integration** — Story 3.3 inline projection + 5-1 hook 위에 additive ledger event emit: `MonthlyInputService.save_row` (T3 5-1의 4 hooks 확장) → row INSERT 성공 후 → `ledger_service.append_event(event_type='purchase_inbound'|'sales_outbound'|'production_output_inbound', product_id, period_key, qty, ...)`. **production_material_consumption emit deferred to Story 5.3+ BOM module authority per Deferral #9 (**D3 review resolution 2026-08-04**)** — 5-2 ships single-emit (output only). 11-value whitelist includes `production_material_consumption` for forward-fill (D3 amend); actual emit = Story 5.3+ BOM-aware reconciliation. **이 wire가 Epic 3.3 inline projection deprecation 시점** (per A3 cj-style 결정).
     - **Idempotent re-INSERT** (CR 1.1 lesson) — `append_event` 가 동일 `(tenant_id, product_id, period_key, event_type, trace_id)` 4-tuple 입력 받으면 `inventory_ledger_event_appended` audit emit skip + no INSERT. 기존 row만 natural ordering에 따라 노출.
     - **Audit log payload** (CR 1.1 self-describing) — `{event_id, product_id, period_key, event_type, qty, trace_id, source: "carry_chain"|"monthly_input"|"manual_backfill"|"reversal_request", reverses_event_id?: UUID, correction_group_id?: UUID, metadata: dict}`. payload keys snake_case (AD-15).

5. **Given** AC #1~#4 trigger + service + INSERT path + audit-first + Epic 3.3 inline projection deprecation timeline
   **When** Story 5-2 commit 안에서 `LEDGER_REFERENCE_QUERY_STUB` swap + Epic 3.3 inline projection 제거
   **Then** 다음 deprecation swap 발동 (AC #5 — Epic 4 close-out A3 cj-style 결정 = **5-2 commit 안에 swap 완료**, 1 epic maintenance window 후 Epic 6 close-out 시점에 완전 제거):
     - **`packages/services/m2_input/inventory_projection.py::LEDGER_REFERENCE_QUERY_STUB: Final[str] = ""` → new SQL fragment**:
       ```python
       LEDGER_REFERENCE_QUERY_STUB: Final[str] = """
       -- Story 5.2 wire: inventory_ledger read.
       -- SELECT product_id, SUM(qty) AS closing_qty FROM inventory_ledger
       -- WHERE tenant_id = :tenant_id AND period_key = :period_key
       -- GROUP BY product_id
       """
       ```
       줄 끝 marker:
       ```python
       # DEPRECATION TIMELINE (Story 5.2 spec AC #5):
       # - Story 5.2 commit = LEDGER_REFERENCE_QUERY_STUB filled + TODO marker REMOVED.
       # - Epic 5 maintenance window: callers (MonthlyInputService) read via
       #   LedgerService.query_period_closing (NEW in Story 5.2).
       # - Epic 6 close-out retro: this marker + build_inventory_projection
       #   legacy path REMOVED entirely.
       ```
     - **MonthlyInputService inline projection swap** — `MonthlyInputService._compute_inventory_projection_for_state` 가 `build_inventory_projection(rows, opening_balance)` (Epic 3.3 legacy) 호출 대신 → `LedgerService.query_period_closing(session, period_key)` 호출. 결과 동일 shape (dict[UUID, Decimal])이지만 source = inventory_ledger row aggregate (`SUM(qty)` per product).
     - **build_inventory_projection 함수 보존** (1 epic maintenance) — Epic 5 maintenance window에서 호출처가 모두 ledger service로 swap될 때까지 보존. Epic 6 close-out 시점에 한꺼번에 제거.
     - **`TODO(epic-5-5-2)` marker → closed marker**:
       ```python
       # TODO(epic-5-5-2): CLOSED in Story 5.2 commit. Replace inline projection
       # with inventory_ledger read.
       # - LEDGER_REFERENCE_QUERY_STUB = filled SQL fragment (above)
       # - MonthlyInputService._compute_inventory_projection_for_state now reads
       #   via LedgerService.query_period_closing (AC #5)
       # - Epic 5 maintenance window: callers migrated case-by-case.
       # - Epic 6 close-out: this marker + legacy path REMOVED.
       ```
     - **drift detector** (`tests/integration/test_inventory_projection_ledger_swap.py` NEW) — assertion `MonthlyInputService._compute_inventory_projection_for_state` source = `LedgerService.query_period_closing` (regex on call graph). Failed = maintenance window violation.

6. **Given** AC #1~#5 trigger + INSERT path + audit + inline projection deprecation
   **When** 본 스토리 본문에서 Epic 11 reversal sequence forward-fill
   **Then** 다음 M4 reversal entrypoint wire (AC #6 — AD-22 reversal entrypoint forward-fill, Epic 11 module authority 완성 후 actual reversal write):
     - **`LedgerService.request_reversal(session, *, event_id, *, reason, *, actor_id)` 진입점** — Epic 11 module ships 전까지는 audit marker only:
       1. SELECT event row FOR UPDATE — event_id inventory_ledger row lock.
       2. validate_event_shape 후 `audit_logs INSERT` with `action='inventory_ledger_reversal_requested'` (ActionClass.INVENTORY_LEDGER NEW) payload: `{original_event_id, period_key, event_type, qty, reason, actor_id, tenant_id, trace_id, requested_at, status: "pending"}`.
       3. **No INSERT to inventory_ledger** — actual reversal sequence insert = Epic 11 module authority (`m11_reversal` module decision). 본 스토리는 M4 entrypoint wire + audit marker + queue status만 ownership.
     - **Defensive: `inventory_ledger_reversal_logged` + `inventory_ledger_reversal_rejected`** Epic 11 forward-fill stubs — registered in `apps/api/core/audit_action.py` `_ActionRegistry._REGISTRY[INVENTORY_LEDGER]` accepted set. 6 values total:
       ```python
       # 5-2 immediate (this story)
       "inventory_ledger_event_appended",      # primary INSERT path
       "inventory_ledger_event_rejected",      # append-only violation (DB trigger raised)
       "inventory_ledger_reversal_requested",  # M4 request_reversal entrypoint (forward-fill)
       # Epic 11 forward-fill stubs (Epic 11 reversal module authority owns actual write)
       "inventory_ledger_reversal_logged",     # M11 authority approved reversal sequence
       "inventory_ledger_reversal_rejected",   # M11 authority denied reversal request
       "inventory_ledger_reprojection_triggered",  # Epic 6 close-out maintenance (forward-fill)
       ```
     - **Sequence uniqueness** — `(tenant_id, reverses_event_id)` unique constraint enforced at INSERT (AC #2 schema). 5-2 forward-fill ensures Epic 11 module cannot violate the constraint.

7. **Given** AC #1~#6 trigger + service + audit + deprecation + reversal entrypoint
   **When** 본 스토리 commit 안
   **Then** 다음 tests wire (AC #7 — 3중 게이트 + drift detector + A7 wire):
     - **Pure kernel** (`tests/services/m4_inventory/test_ledger.py` NEW — ~25 cases):
       - `build_event_payload(product_id, period_key, event_type, qty, *, trace_id, **metadata)` 11 cases — 11 event_type × payload shape 검증. banker's rounding via `QTY_QUANTUM` (CR 0-4 lesson + AD-15 parity).
       - `validate_event_type` 11 cases — 11 valid + 3 invalid (empty / unknown / malformed).
       - `validate_event_shape` 5 cases — Decimal quantization + nullable qty (non-quantitative events).
       - `append_only_violation_message` 2 cases — UPDATE / DELETE message shape.
       - `build_period_closing_query` 3 cases — SQL fragment + parameter substitution.
       - `build_carry_chain_query` 3 cases — chain depth limit + parameter substitution.
       - Determinism: 100x byte-identical build_event_payload output (CR 4-3 lesson).
     - **Pure kernel #2** (`tests/services/m4_inventory/test_ledger_query.py` NEW — ~10 cases):
       - `build_period_closing_query` SQL fragment = deterministic SELECT + GROUP BY shape. 3 cases (single product / multi product / empty period).
       - `build_carry_chain_query` chain walk SQL = recursive CTE shape (PostgreSQL WITH RECURSIVE). 3 cases (single depth / 12 depth / >12 reject guard).
       - `LedgerQuery` NamedTuple construction 4 cases (closing dict + chain list).
     - **Service layer** (`tests/api/m4_inventory/test_ledger_service.py` NEW — ~15 cases, mock_session):
       - `append_event` happy path (AC #4) + idempotent re-INSERT skip (CR 1.1) + invalid event_type reject + audit log emission verification.
       - `query_period_closing` shape = dict[UUID, Decimal] + Decimal serialization + empty period.
       - `query_carry_chain` depth limit enforcement + chain list shape.
       - `request_reversal` happy path = audit only (no inventory_ledger INSERT) + idempotent + reason validation.
       - `validate_append_only_invariant` defense-in-depth AST guard.
     - **3-way consistency drift detector** (`tests/integration/test_audit_action_consistency.py` extension) — A5 pattern 동일 적용:
       - registry ↔ DB CHECK constraint: 6 values (ActionClass.INVENTORY_LEDGER accepted frozenset) ↔ 11 values (PostgreSQL CHECK constraint on event_type) — note these are DIFFERENT groups (action enum vs event_type enum); drift detector verifies BOTH groups individually + cross-consistency (registry SSOT-owned action literals = N/A for event_type; event_type only DB-owned).
       - call sites AST-grep: `emit_audit(` raw calls in `apps/api/modules/m4_inventory/` = 0 (5-2 + 5-1 모두 typed).
       - verified DB constraint contents match published alembic migration file.
     - **Capability gate** (`tests/integration/test_inventory_ledger_capability.py` NEW — 4 cases):
       - manufacturing / manufacturing_service / manufacturing_service_other → 200 OK (INVENTORY_LEDGER grant).
       - service-only → 403 `INDUSTRY_NOT_SUPPORTED` typed envelope.
     - **TS mirror parity** (`tests/integration/test_inventory_ledger_label_consistency.py` NEW — 6 cases, **DEFERRED to Story 5.3** vitest wire — placeholder file only, 0 active tests):
       - Korean message parity + Decimal serialization parity (string-coerced).
       - Deferred marker: `pytest.mark.skip(reason="Story 5.3 frontend + Story 0.5 vitest plumbing 진입 시 활성화")`.
     - **Append-only AST guard** (`tests/architecture/test_inventory_ledger_no_mutate.py` NEW — 5 cases):
       - AST-grep `apps/api/` for `session.execute(update(InventoryLedger...))` or `session.execute(delete(InventoryLedger...))` = 0건.
       - pytest-asyncio 미사용 (CR 4-3 F-1 + A7 wire pattern).
       - pure kernel = no DB import (stdlib-only).
     - **3중 게이트 (mandatory CI)**:
       - `uv run ruff check packages/services/m4_inventory/ apps/api/modules/m4_inventory/ apps/api/core/audit_action.py 0 errors`
       - `uv run import-linter lint` — ledger.py + ledger_query.py pure helper = `packages/` allowed. m4_inventory service layer = `apps/api/modules/m4_inventory/` allowed (no `packages.cost_engine` import — AD-11).
       - `uv run pytest` (full) — 50+ new tests pass + Story 5-1 accumulated 35 + Epic 1-4 누적 회귀 0건. A7 SDR overclaim detector pass (test count = 50+ 매칭 필수).

8. **Given** AC #1~#7 trigger + service + tests + drift detector + capability gate + A5 forward-lock + A7 wire
   **When** 본 스토리 9 task (T1-T9) 실행
   **Then** 다음 docs wire (AC #8 — operator/dev 가이드 + Epic 6 close-out 결정 가이드):
     - `docs/inventory-ledger.md` (NEW): operator/dev guide — inventory_ledger table schema + append-only trigger 정책 + AD-22 reversal sequence 진입점 + Epic 11 reversal module dispatch + RLS + event_type 11 values + carry chain wire + Epic 3.3 inline projection deprecation timeline + Epic 6 close-out maintenance window 가이드. 7-section 운영 매뉴얼.
     - `docs/monthly-input.md` §Story 5.2 추가: ledger event wire contract (`event_type` 11 values + payload shape + audit action 6 literal) + carry chain → ledger event routing + monthly_input_rows → ledger event routing + ADR-22 reversal entrypoint.
     - `docs/opening-inventory-carry.md` §Story 5.2 추가: carry chain 결정이 더 이상 `audit_logs` direct emit 안 하고 → `inventory_ledger` + `audit_logs` 두 행 동시 emit (5-1 migration 단계 명시).
     - `docs/architecture-inventory.md` (5-1 spec NEW) §Story 5.2 추가: `inventory_ledger` table module diagram + Epic 5 3-story 분할 5-1+5-2 wire + Epic 11 reversal entrypoint wire.
     - `docs/capability-matrix.md` v1.6 (2026-08-XX) — Changelog:
       - v1.6 (Story 5.2) — `INVENTORY_LEDGER` capability wire + `ActionClass.INVENTORY_LEDGER` 6 values 채움 + `inventory_ledger` table + append-only trigger + Epic 3.3 inline projection deprecation timeline (5-2 commit + Epic 6 close-out 시점에 완전 제거). Capability 행 자체 변경 없음 (5-1 v1.5에서 이미 pre-fill됨).
     - `docs/conventions.md` §10.6 (NEW) inventory ledger append-only policy: "`inventory_ledger` table은 AD-2 append-only invariant SSOT. UPDATE/DELETE attempt는 DB trigger + service-layer guard + audit log emission 3중 방어. 수정 필요 시 AD-22 reversal sequence (sign-negating row + corrected row) — Epic 11 module authority owns actual write. 5-2 spec에서 3중 게이트 와이어됨."
     - `docs/conventions.md` §10.5 갱신 (5-1 opening auto-carry policy): "carry chain 결정은 본 스토리 wire 후엔 `audit_logs.action='inventory_ledger_event_appended'` + `inventory_ledger.event_type='opening_carried'` 두 행 동시 emit."

## Tasks / Subtasks

### T1. Pure kernel — `packages/services/m4_inventory/ledger.py` (NEW)
- T1.1 `InventoryLedgerEvent` NamedTuple — `(event_id: UUID, tenant_id: UUID, product_id: UUID, period_key: str, event_type: str, qty: Decimal | None, trace_id: UUID, reverses_event_id: UUID | None, payload: dict[str, Any])`. AD-15 snake_case. cross-language mirrorable.
- T1.2 `build_event_payload(product_id, period_key, event_type, qty, *, trace_id, **metadata) -> dict[str, Any]` — INSERT 직렬화용 dict 생성. Decimal → str 변환 (json-serializable). banker's rounding via `QTY_QUANTUM` from `inventory_projection`.
- T1.3 `validate_event_type(event_type: str) -> None` — 11 values whitelist strict check. raise `AppendOnlyLedgerError` (typed exception, NO HTTP mapping — pure helper owns domain semantics).
- T1.4 `validate_event_shape(event: InventoryLedgerEvent) -> None` — Decimal QTY_QUANTUM quantization + nullable qty (non-quantitative events: `closing_snapshot` etc. may have NULL qty) + period_key AD-24 typed pattern (`'YYYY-MM'`) + product_id UUID v7 (AD-15).
- T1.5 `append_only_violation_message(original_op: str, event_id: UUID) -> str` — service-layer error message builder (Korean + structured).
- T1.6 `AppendOnlyLedgerError(Exception)` typed exception — pure helper domain semantics. NO HTTP envelope (service layer wraps).
- T1.7 stdlib-only import set: `uuid`, `decimal`, `re`, `datetime`. NO `sqlalchemy`, NO `fastapi`, NO `pydantic`, NO DB client.

### T2. Pure kernel #2 — `packages/services/m4_inventory/ledger_query.py` (NEW)
- T2.1 `LedgerQuery` NamedTuple — `(sql: str, params: tuple, description: str)` SQL builder shape (NOT value object — **D1 review resolution 2026-08-04 spec/코드 drift**). Service layer binds via SQLAlchemy `text().bindparams()`.
- T2.2 `build_period_closing_query() -> LedgerQuery` — SQL fragment: `SELECT product_id, SUM(qty) AS closing_qty FROM inventory_ledger WHERE tenant_id = :tenant_id AND period_key = :period_key GROUP BY product_id`. Paramless signature; service binds `tenant_id` + `period_key` at execute time (**D2 review resolution 2026-08-04**). Deterministic ORDER BY `product_id`.
- T2.3 `build_carry_chain_query(*, depth: int = 12) -> LedgerQuery` — recursive CTE: `WITH RECURSIVE chain AS (SELECT ... UNION ALL SELECT ... WHERE depth < :max_depth)`. Paramless signature; service binds `tenant_id` + `period_key` at execute time. depth bounded.
- T2.4 stdlib-only (string templating + dataclass). NO actual SQL execution (service layer binds).

### T3. Service layer — `apps/api/modules/m4_inventory/services/ledger_service.py` (NEW)
- T3.1 `LedgerService.append_event(session, *, product_id: UUID, period_key: str, event_type: str, qty: Decimal | None, **metadata) -> InventoryLedgerEvent` — primary INSERT path:
  - pure kernel `validate_event_type` + `validate_event_shape` dispatch.
  - `session.add(InventoryLedger(...))` + `flush()` — INSERT.
  - `emit_audit_typed(action_class=ActionClass.INVENTORY_LEDGER, action='inventory_ledger_event_appended', ..., payload={event_id, period_key, event_type, qty, trace_id, source, ...metadata})` AFTER INSERT (audit-first guarantee).
  - Idempotent: `SELECT 1 FROM inventory_ledger WHERE tenant_id=:tenant_id AND product_id=:product_id AND period_key=:period_key AND event_type=:event_type AND trace_id=:trace_id` 검출 시 skip.
- T3.2 `LedgerService.query_period_closing(session, *, period_key: str) -> dict[UUID, Decimal]` — read-only SELECT via pure kernel `build_period_closing_query`. Replaces Epic 3.3 inline projection (AC #5).
- T3.3 `LedgerService.query_carry_chain(session, *, period_key: str, *, depth: int = 12) -> list[LedgerQuery]` — read-only recursive CTE via pure kernel `build_carry_chain_query`.
- T3.4 `LedgerService.request_reversal(session, *, event_id: UUID, *, reason: str, *, actor_id: UUID) -> None` — Epic 11 forward-fill entrypoint:
  - SELECT event row FOR UPDATE — `SELECT ... FROM inventory_ledger WHERE event_id = :event_id FOR UPDATE` (AD-4 concurrency).
  - `audit_logs INSERT` with `action='inventory_ledger_reversal_requested'` + payload `{original_event_id, period_key, event_type, qty, reason, actor_id, tenant_id, trace_id, requested_at, status: "pending"}`.
  - NO `inventory_ledger INSERT` — Epic 11 module authority owns actual reversal sequence write.
- T3.5 `LedgerService.validate_append_only_invariant(session, *, tenant_id: UUID) -> None` — defense-in-depth AST-grep scan (CR 4-3 pattern). Failed = service-layer gate raise `AppendOnlyLedgerError` before DB trigger fires. 5-2 commit 안에서 AST guard wired via `tests/architecture/test_inventory_ledger_no_mutate.py`.
- T3.6 SQLAlchemy AsyncSession + `emit_audit_typed` wire (raw `emit_audit(` 0건). 5-1 opening_carry_service pattern 동일 적용 (CR 1.1 audit-first).
- T3.7 4 typed exceptions (`AppendOnlyLedgerError` 500 AD-15 envelope mapping in main.py — distinct from pure helper type for layer boundary).

### T4. Wire trigger — `apps/api/modules/m4_inventory/handlers.py` extension + monthly_input_service hook
- T4.1 `apps/api/modules/m4_inventory/handlers.py` extension — 4 routes (AC #1 wire trigger):
  - T4.1.1 `POST /api/v1/inventory/ledger/events` — operator manual INSERT (recovery / backfill entry). Body = `LedgerEventCreateRequest` (Pydantic). AD-15 envelope + capability gate.
  - T4.1.2 `GET /api/v1/inventory/ledger/period-closing?period_key=...` — read-only closing projection. Returns `PeriodClosingResponse` dict[product_id_str, Decimal_str].
  - T4.1.3 `GET /api/v1/inventory/ledger/carry-chain?period_key=...&depth=N` — read-only chain walk. Returns `CarryChainResponse` (list of LedgerQuery + depth).
  - T4.1.4 `POST /api/v1/inventory/ledger/reversal-requests` — M4 reversal entrypoint forward-fill. Body = `ReversalRequestCreate` (event_id + reason). Epic 11 module dispatch.
- T4.2 `apps/api/modules/m2_input/services/monthly_input_service.py` hook — `save_row` after each INSERT (5-1 4 hooks 위에 additive):
  - `stream='purchases'` INSERT 성공 후 → `ledger_service.append_event(event_type='purchase_inbound', product_id, period_key, qty)`.
  - `stream='sales'` INSERT 성공 후 → `ledger_service.append_event(event_type='sales_outbound', product_id, period_key, qty)`.
  - `stream='production'` INSERT 성공 후 → `ledger_service.append_event(event_type='production_output_inbound', product_id, period_key, qty)`. **5-2 ships single-emit (output only) per D3 review resolution 2026-08-04. `production_material_consumption` emit deferred to Story 5.3+ BOM-aware reconciliation (Deferral #9).**
  - `stream='orders'|'expenses'|'labor'` → 무변경 (재고 무관, AC #5).
- T4.3 `apps/api/modules/m4_inventory/services/opening_carry_service.py` (5-1) extension — `OpeningCarryService._run_chain` 끝점에서 carry chain 결정마다 `ledger_service.append_event(event_type='opening_carried' | 'opening_carried_stale_overwrite', ...)` 호출. 5-1 AC #6의 `audit_logs.action='opening_inventory_auto_carried'` emit은 그대로 유지 (AD-2 audit-first), 추가적으로 `audit_logs.action='inventory_ledger_event_appended'` 동시 emit (two parallel immutable logs — D1 wire 결정).
- T4.4 `apps/api/main.py` route 등록 (4 NEW routes) + AD-15 envelope exception handlers (T3.7 4 typed exceptions).
- T4.5 `apps/api/core/audit_action.py` — `InventoryLedgerAction` Literal 6 values 채움 (T5.1) + `_ActionRegistry._REGISTRY[ActionClass.INVENTORY_LEDGER]` accepted frozenset 6 values fill (T5.2). 5-1 spec placeholder complete fill. **D1 deferral 해결**.

### T5. Schema — Alembic migration + db_models + response schemas (NEW + extension)
- T5.1 `apps/api/alembic/versions/0015_inventory_ledger.py` (NEW) — `down_revision: 0014_verification_log_v8_audit`:
  - `op.create_table('inventory_ledger', ...)` 11 columns + 3 constraints (PK + CHECK + unique on reverses).
  - `op.execute("CREATE FUNCTION _inventory_ledger_append_only() ...")` + `CREATE TRIGGER inventory_ledger_append_only ...`.
  - `op.execute("CREATE INDEX ...") 3 indexes — (tenant_id, period_key, created_at) natural ordering + (tenant_id, product_id, period_key) closing query + (reverses_event_id) WHERE NOT NULL.
  - RLS policy `supabase/policies/0007_inventory_ledger_rls.sql` (NEW — tenant_id predicate).
  - Downgrade: drop trigger + function + table + policies.
- T5.2 `apps/api/core/db_models.py` extension — `InventoryLedger` ORM class (T5.1 schema 1:1 mirror) + `__table_args__` with CHECK constraint + RLS hint comment.
- T5.3 `apps/api/modules/m4_inventory/schemas.py` extension — `LedgerEventCreateRequest` (Pydantic + extra='forbid') + `PeriodClosingResponse` (dict[str, str] keys) + `CarryChainResponse` (list[LedgerQueryResponse]) + `ReversalRequestCreate` (event_id + reason). `extra='forbid'` 보존 (CR 2.3 lesson).
- T5.4 `apps/api/modules/m2_input/services/monthly_input_service.py` extension — `MonthlyInputStateResponse` 4 fields → 5 NEW fields: `ledger_events_count: int` + `ledger_period_closing: dict[str, str]` + `inventory_ledger_enabled: bool` + `reversal_request_enabled: bool`. 5-1 3 fields (`opening_inventory` + `opening_inventory_locked` + `opening_inventory_lock_reason_ko`) 그대로 유지.

### T6. Audit-action wire (A5 forward-lock + D1 deferral 해결)
- T6.1 `apps/api/core/audit_action.py` — `InventoryLedgerAction = Literal["inventory_ledger_event_appended", "inventory_ledger_event_rejected", "inventory_ledger_reversal_requested", "inventory_ledger_reversal_logged", "inventory_ledger_reversal_rejected", "inventory_ledger_reprojection_triggered"]`. 6 values 명시 (placeholder Literal 제거).
- T6.2 `_ActionRegistry._REGISTRY[ActionClass.INVENTORY_LEDGER] = ("inventory_ledger", frozenset({...6 values...}))` — empty frozenset fill.
- T6.3 `AuditAction` Union type auto-sync (registry guard 시 검증됨).
- T6.4 `tests/integration/test_audit_action_consistency.py` extension — A5 3-way drift detector pass:
  - `ActionClass.INVENTORY_LEDGER` accepted set = 6 values (registry SSOT).
  - DB CHECK constraint on `verification_log.action` (4 values from Story 4.4 — verification_log is not 5-2 scope, but `inventory_ledger.event_type` is 11 values) — cross-verify both.
  - call sites AST-grep `emit_audit(` raw in `apps/api/modules/m4_inventory/` + `apps/api/modules/m2_input/services/` = 0 (5-2 + 5-1 모두 typed).
- T6.5 `tests/services/test_audit_action_centralization.py` extension — 5-2 actions 6개 모두 registry set 포함 검증. drift count = 0 유지.

### T7. Capability gate — `apps/api/core/capability.py` (no change) + handlers wire
- T7.1 `Capability.INVENTORY_LEDGER` already added from Story 5.1 v1.5 pre-fill. `_INDUSTRY_CAPABILITIES` 4 industries 매트릭스 그대로 (manufacturing 3종 ✅ / service-only ❌).
- T7.2 `require_capability("inventory_ledger")` dependency를 4 NEW routes (T4.1)에 wire. service-only tenant → 403 `INDUSTRY_NOT_SUPPORTED` typed envelope.
- T7.3 `tests/integration/test_inventory_ledger_capability.py` (NEW) — 4 cases (3 industries ✅ + 1 service-only ❌).

### T8. Epic 3.3 inline projection deprecation swap (AC #5 wire)
- T8.1 `packages/services/m2_input/inventory_projection.py` — `LEDGER_REFERENCE_QUERY_STUB: Final[str] = ""` → filled SQL fragment (`build_period_closing_query` 결과와 동일 shape). `TODO(epic-5-5-2)` marker → closed marker (Epic 6 close-out 시점에 완전 제거 가이드).
- T8.2 `MonthlyInputService._compute_inventory_projection_for_state` — `build_inventory_projection(rows, opening_balance)` 호출 제거 → `LedgerService.query_period_closing(session, period_key)` 호출로 swap. AC #5 wire.
- T8.3 `build_inventory_projection` pure helper 보존 (Epic 5 maintenance window — Epic 6 close-out 시점에 한꺼번에 제거).
- T8.4 `tests/integration/test_inventory_projection_ledger_swap.py` (NEW) — drift detector: regex on call graph `MonthlyInputService._compute_inventory_projection_for_state` source = `LedgerService.query_period_closing`. Failed = maintenance window violation.

### T9. Tests + docs + 3중 게이트 (T1-T8 동반 + T9 commit-msg finalize)
- T9.1 `tests/services/m4_inventory/test_ledger.py` (NEW) — 25 pure cases.
- T9.2 `tests/services/m4_inventory/test_ledger_query.py` (NEW) — 10 pure cases.
- T9.3 `tests/api/m4_inventory/test_ledger_service.py` (NEW) — 15 service cases (mock_session pattern, pytest-asyncio 미사용 per CR 4-3 F-1 + A7 wire).
- T9.4 `tests/integration/test_inventory_ledger_capability.py` (NEW) — 4 capability gate cases.
- T9.5 `tests/integration/test_inventory_projection_ledger_swap.py` (NEW) — T8.4 drift detector.
- T9.6 `tests/architecture/test_inventory_ledger_no_mutate.py` (NEW) — 5 AST guard cases (UPDATE/DELETE on inventory_ledger = 0).
- T9.7 `tests/integration/test_audit_action_consistency.py` extension — T6.4 3-way drift detector 6 cases.
- T9.8 `tests/services/test_audit_action_centralization.py` extension — T6.5 5-2 actions 6개 registry set 검증.
- T9.9 `tests/integration/test_inventory_ledger_label_consistency.py` (NEW) — TS mirror placeholder (Story 5.3 vitest wire 후 활성화). 0 active tests at 5-2 commit.
- T9.10 `tests/integration/test_m2_input_label_consistency.py` extension — `inventory_ledger` wire 메시지 label 5 cases (event_type / payload shape).
- T9.11 `docs/inventory-ledger.md` (NEW) — operator/dev guide 7 sections.
- T9.12 `docs/monthly-input.md` §Story 5.2 추가 + `docs/opening-inventory-carry.md` §Story 5.2 추가 + `docs/architecture-inventory.md` §Story 5.2 추가 + `docs/capability-matrix.md` v1.6 + `docs/conventions.md` §10.6 inventory ledger append-only policy.
- T9.13 3중 게이트 (mandatory CI) — ruff 0 errors / import-linter 2 KEPT / pytest full (skip 옵션 없음) — V8 regression 838+ cases + Story 5.1 35 cases + Story 5.2 50+ cases 누적 pass. A7 SDR overclaim detector pass (test count = 50+ 매칭 필수).

## Open Questions

### OQ1. Append-only trigger 정책 — DB trigger + service-layer guard 3중 방어 vs DB trigger only
**Options**:
1. (cj-style default) 3중 방어: (a) DB trigger (PostgreSQL `BEFORE UPDATE OR DELETE` row-level, AC #2), (b) service-layer `validate_append_only_invariant` AST guard (AC #3 + T9.6), (c) audit log emission on rejection (CR 1.1 audit-first). 3중 defense-in-depth 보존.
2. DB trigger only (simplest) — service-layer guard + audit skip. Simple but observability 낮음.
3. Service-layer guard only (no DB trigger) — DB-level constraint 부재. 실수로 raw SQL 경유 시 우회 가능.

**Cj-style default**: **Option 1 (3중 방어)**. AD-2 append-only invariant SSOT + Epic 0 audit_logs INSERT-only 패턴과 동일 (service_role bypass도 audit-first). service-layer defense = dev-time 빠른 fail. DB trigger = production gate. audit log = observability.

### OQ2. Qty 컬럼 nullable — 모든 event는 qty 필수 vs 일부 event는 nullable (closing_snapshot 등)
**Options**:
1. (cj-style default) qty NUMERIC(18,4) NULLABLE — non-quantitative events (`closing_snapshot`, `adjustment_positive` / `adjustment_negative` materialized snapshot 등) 허용. pure helper `validate_event_shape` nullable 분기.
2. qty NOT NULL 강제 — 모든 event가 qty 가짐. closing_snapshot 등 materialized snapshot도 qty=0 또는 summary qty 가져야 함.

**Cj-style default**: **Option 1 (nullable qty)**. AD-2 append-only invariant = 모든 row가 INSERT-only 보장 ≠ 모든 row가 qty 가짐. closing_snapshot event_type은 period closing balance materialize용 summary event — qty 의미 없음. NULL 허용이 schema 정합.

### OQ3. Event_type 11 values 결정 — 5-2 ship 시점 vs Epic 5 close-out 회고 후
**Options**:
1. (cj-style default) 5-2 ship 시점에 11 values 명시 + DB CHECK constraint wire. AC #2 schema. 미래 event_type 추가는 5-2 commit 후 alembic migration으로 확장.
2. 5-2 ship 시점엔 5-2 immediate 6 values만 (`opening_carried` + `opening_carried_stale_overwrite` + `purchase_inbound` + `sales_outbound` + `production_output_inbound` + `production_material_consumption`) + Epic 11 결정 후 추가.

**Cj-style default**: **Option 1 (11 values 명시)**. 5-2 CHECK constraint의 event_type coverage가 5-2 본 스토리 + Epic 11 reversal + Epic 6 close-out까지 forward-fill. Alembic 추가는 production data 누적 후 부담 (CR 0-2 lesson) — pre-emptive 11 values 명시가 더 안전.

### OQ4. Epic 3.3 inline projection deprecation timeline — 5-2 commit 안에 swap vs Epic 6 close-out 시점에 swap
**Options**:
1. (cj-style default, Epic 4 close-out A3) **5-2 commit 안에 swap + Epic 6 close-out 시점 완전 제거**. Epic 5 maintenance window 동안 양쪽 path 병존 (build_inventory_projection legacy + LedgerService.query_period_closing wire). Epic 6 close-out retro에서 build_inventory_projection + LEDGER_REFERENCE_QUERY_STUB 한꺼번에 제거.
2. Epic 6 close-out retro 시점에 swap (5-2 commit은 LEDGER_REFERENCE_QUERY_STUB 채우기만, swap은 Epic 6 결정). 5-2는 inventory_ledger table + trigger wire + audit-first만. Epic 3.3 inline projection 보존.

**Cj-style default**: **Option 1 (5-2 commit 안에 swap + Epic 6 close-out 시점에 완전 제거)**. Epic 4 close-out A3 cj-style 결정 = "5-2 commit + 1 epic maintenance 후 Epic 6 close-out 시점에 제거". Inline projection → ledger read의 wire change가 5-2 commit 안에 완료되어야 Epic 6 charts/reporting이 ledger as single source of truth를 read.

### OQ5. Reversal entrypoint wire — 5-2 spec에서 M4 entrypoint + audit marker + Epic 11 forward-fill vs 5-2 skip (Epic 11 별도)
**Options**:
1. (cj-style default) 5-2 spec에서 M4 entrypoint + audit marker (`inventory_ledger_reversal_requested`) wire + Epic 11 module decision pending. 실제 reversal sequence INSERT = Epic 11 module ships (`m11_reversal` 모듈). 5-2 commit 안에서 service layer entrypoint + audit log emission + unique constraint 미리 wire.
2. 5-2 skip — Epic 11 reversal spec에서 M4 + M11 모두 wire. 5-2 spec은 inventory_ledger table + append-only + INSERT path만 ownership.

**Cj-style default**: **Option 1 (5-2 forward-fill + Epic 11 module authority)**. AD-22 reversal entrypoint forward-fill 패턴 (Epic 4 close-out A5 forward-lock + D1 deferral 결정 보존). Epic 11 module ships 전에도 M4 entrypoint 호출은 audit marker 기록되어 idempotent trace 가능. Epic 11 module auth 후 actual sequence insert. 5-1 spec의 `opening_inventory_unlocked` forward-fill 동일 패턴.

### OQ6. Capability gate — `INVENTORY_LEDGER` service-only ❌ 정책 (manufacturing 3종 ✅ vs 4 industries all)
**Options**:
1. (cj-style default) service-only ❌ 그대로 (manufacturing 3종 ✅). PRD §F4.1 + §6.2 manufacturing 도메인. service tenant = Epic 9 ABC 라우팅 (재고 추적 불필요).
2. 4 industries all ✅ — service tenant도 inventory_ledger wire 가능 (service billing inventory 추적).

**Cj-style default**: **Option 1 (service-only ❌)**. Capability matrix v1.6 + Story 5.1 v1.5 footnote 정합. CR 5-1 §(7) lesson 재확인 — service tenant은 Epic 9 ABC costing path.

### OQ7. Append-only enforcement 대상 — row-level trigger vs statement-level trigger
**Options**:
1. (cj-style default) row-level `FOR EACH ROW` — 각 row 단위 발동. multi-row UPDATE attempt도 모든 row마다 trigger raised.
2. statement-level `FOR EACH STATEMENT` — SQL statement 단위 발동. multi-row 일괄 시 한 번만 raised. row-level보다 약함.

**Cj-style default**: **Option 1 (row-level)**. AD-2 append-only invariant는 모든 row 보장. 단일 statement로 multi-row UPDATE 시도 시에도 모든 row reject. row-level trigger = strict enforcement.

## Deferrals (5-3 / Epic 11 / Epic 6 close-out 진입점 명시)

1. **Frontend TS mirror wire + toast** — Story 5.3 spec 진입 시. 0.5 plumbing (sonner) + vitest wire 후 `apps/web/lib/l2-input-inventory-ledger.ts` helper + `tests/integration/test_inventory_ledger_label_consistency.py` vitest 활성화. 5-2 spec은 backend wire + TS mirror placeholder helper (skipped test)만.
2. **E2E (Playwright) ledger event visualization** — Story 0.5 plumbing + 5-3 frontend 통합 후. 5-2 backend-only.
3. **`inventory_ledger_reversal_logged` + `inventory_ledger_reversal_rejected` + `inventory_ledger_reprojection_triggered` 실제 emit** — Epic 11 reversal module ships 후. 5-2 spec은 placeholder Literal + accepted frozenset 등록만.
4. **build_inventory_projection pure helper 완전 제거 + LEDGER_REFERENCE_QUERY_STUB 제거** — Epic 6 close-out retro 시점. Epic 5 maintenance window (Epic 5 5-2/5-3 dev-story + Epic 5 close-out) 동안 양쪽 path 병존. Epic 6 진입 시 ledger as single source of truth 확정 + Epic 3.3 inline projection legacy path 한꺼번에 제거.
5. **Cross-industry inventory_ledger (예: manufacturing_service → manufacturing_service_other tenant 전환 시 ledger row preservation)** — Epic 5 close-out 회고 A8 결정 후 별도 story.
6. **V8 fixture ledger coverage 확장** — V8 골든 byte-identical CI gate (Story 4-4 12 fixture matrix)에 inventory_ledger event wire 추가. 별도 story.
7. **`inventory_ledger_event_overlay_violation` future event_type** (현재 11 values에서 제외) — Epic 6 close-out + Epic 11 reversal module + 5-3 frontend 통합 후 spec 추가 시 alembic CHECK constraint 확장.
8. **MonthlyInputStateResponse `reversal_request_enabled` field 실제 activation** — Epic 11 module ships 후 Pydantic adapter 추가. 5-2는 field placeholder (always False).
9. **Production row INSERT 시 output + consumption 동시 emit 정책** — 5-2 spec AC #4 wire. Epic 5 maintenance window 중 production row INSERT 경로에서 production output (outbound) + production material consumption (inbound) 양방향 emit 확인 필요. Edge case (production output qty ≠ consumption qty → 차이는 `adjustment_positive`/`adjustment_negative` event) = Epic 5 close-out 후속 story 또는 Epic 11 reversal 진입점.

## Architecture Binds

| AD/FR/NFR | Wire in 5-2 |
|---|---|
| AD-2 (append-only ledger) | `BEFORE UPDATE OR DELETE` row-level trigger + 3중 방어 (DB trigger + service-layer guard + audit log emission) + CHECK constraint on event_type 11 values. corrections via AD-22 reversal sequence only. |
| AD-3 (RLS) | `supabase/policies/0007_inventory_ledger_rls.sql` NEW. tenant_id predicate. service_role bypass audit-first (Epic 0 pattern). |
| AD-6 (close lock 부재) | period locked_by_calculation=true 시 ledger INSERT은 허용 (ledger는 immutable 누적, close lock은 fiscal_period_snapshot 소유). reversal/correction은 Epic 11 module authority 별도 entrypoint. |
| AD-11 (layer rule) | `packages/services/m4_inventory/ledger.py` + `ledger_query.py` (NEW per cr-5-1-lessons §(1)) = pure helpers in `packages/services/`, no DB. `apps/api/modules/m4_inventory/services/ledger_service.py` (NEW) = service layer SQLAlchemy + emit_audit_typed. Engine unchanged. |
| AD-15 (cross-language parity) | TS mirror helper `apps/web/lib/l2-input-inventory-ledger.ts` (5-3 entry, 5-2 spec placeholder). drift detector `tests/integration/test_inventory_ledger_label_consistency.py` (5-2 placeholder + 5-3 vitest wire 후 active). Decimal serialization parity + Korean message parity. |
| AD-18 (single product identity) | `inventory_ledger.product_id` (UUID v7) = PRODUCT(product_id) SSOT. 다른 identity (item_id, cost_object_id) 사용 불가. |
| AD-22 (reversal entrypoint) | `request_reversal(event_id, reason)` in `LedgerService.request_reversal` (5-2 forward-fill, audit marker only). M11 authority owns actual reversal sequence insert (Epic 11 module ships 후). unique constraint `(tenant_id, reverses_event_id)` enforced at INSERT (5-2 schema). |
| AD-24 (period key) | `inventory_ledger.period_key` = `'YYYY-MM'` typed pattern (real fiscal keys only). M8 virtual budget keys (`YYYY-MM#B<n>`) 별도 ledger table 또는 Epic 8 follow-up. |
| A5 forward-lock (CR 4-3 F-6) | `ActionClass.INVENTORY_LEDGER` accepted set 6 values 신규 채움 (D1 deferral 해결). `tests/integration/test_audit_action_consistency.py` 3-way drift detector extension. |
| A7 wire (CR 4-3 F-1 / F-2 + Epic 4 close-out retro A7) | `tests/architecture/test_inventory_ledger_no_mutate.py` NEW AST guard (no `@pytest.mark.asyncio`). SDR overclaim detector (`tests/integration/test_sdr_test_count_drift.py`) 5-2 test count = 50+ 매칭 필수. |
| PRD §F4.1 (기초재고 자동 이월) | 5-1 carry chain을 5-2 inventory_ledger event로 라우팅 (4.3 five hooks 위에 additive). closing → next opening 자동 전파가 ledger row 누적. |
| PRD §F4.2 (음수 기말 차단) | 5-2는 closing 음수 event도 ledger에 INSERT (V3 fire signal = ledger row 자체, not closing auto-reject). 5-3 close-time block 진입점. |
| PRD §6.2 (수불부) | `opening + inbound - outbound = closing`의 모든 stream을 ledger event로 누적: `purchase_inbound` + `sales_outbound` + `production_output_inbound` + `production_material_consumption` + `opening_carried` (5-1 chain propagation) + `adjustment_*` (Epic 11 close 시). |
| PRD §A11 (오류의 가시화) | append-only violation 시 500 `APPEND_ONLY_LEDGER_VIOLATION` typed envelope + audit log emission (CR 1.1 audit-first). 5-3 frontend toast 진입점 = manual INSERT reject 시에도 메시지 + 경고. |

## CR Lessons Applied

| Lesson | 5-2 Application |
|---|---|
| CR 1.1 (audit-first + idempotent no-op) | T3.1 append_event = audit-first (INSERT 직후 audit emit) + idempotent re-INSERT skip (CR 1.1 pattern). `emit_audit_typed(action_class=ActionClass.INVENTORY_LEDGER, action='inventory_ledger_event_appended', ...)` 6 values 명시. |
| CR 0-2 (TS/Python parity) | T9.9 TS mirror parity tests placeholder + 5-3 vitest wire 후 활성화. Decimal serialization parity (string-coerced). Korean message parity (`apps/web/lib/l2-input-inventory-ledger.ts`). |
| CR 0-3 (spec mirror) | T9.11~T9.12 docs 6 file (inventory-ledger.md / monthly-input.md §5.2 / opening-inventory-carry.md §5.2 / architecture-inventory.md §5.2 / capability-matrix.md v1.6 / conventions.md §10.6) — spec 본문 ↔ doc 1:1 mirror. |
| CR 0-4 (banker's rounding) | T1.2 build_event_payload Decimal quantization via QTY_QUANTUM (NUMERIC(18,4)) + ROUND_HALF_EVEN. Test cases 5+ 자릿수 값으로 작성 (banker's rounding 결정 자릿수). |
| CR 2.1 (capability-gated type subset) | T7 capability gate wire (manufacturing 3종 ✅ / service-only ❌). capability-matrix.md v1.6 footnote 정합. |
| CR 2.3 (extra='forbid') | T5.3 Pydantic schema 4 NEW types 모두 `extra='forbid'` 보존. `LedgerEventCreateRequest` + `PeriodClosingResponse` + `CarryChainResponse` + `ReversalRequestCreate`. |
| CR 4-3 F-1 (async test pattern) | T9.3 `tests/api/m4_inventory/test_ledger_service.py` mock_session pattern — `asyncio.run` wrapper 보존 (sync tests) + A7 wire (`tests/cost_engine/test_no_async_decorator.py`) pass. |
| CR 4-3 F-2 (SDR overclaim) | T9.13 3중 게이트 exact count 명시 (50+ new tests) — SDR 작성 시 actual pytest count = 50+ 매칭 필수. A7 SDR overclaim detector pass. |
| CR 4-3 F-4 (V8 STORY_4_4 fill marker) | 본 스토리는 V8 marker 아님 (V8 = Story 4.4 own scope). 5-2 wire에서 V8 fixture 확장 시점 = 별도 Story §Deferral 6. |
| CR 4-3 F-5 (Industry enum SSOT) | T7 capability gate 매트릭스 — Industry enum 4 values exact match (`manufacturing_service` / `manufacturing_service_other` canonical). |
| CR 4-3 F-6 (A5 forward-lock) | T6.4 drift detector extension — `emit_audit_typed` wire + raw `emit_audit(` 0건 + registry set 6 values 채움 (D1 deferral 해결). 3-way consistency pass. |
| cr-0-2-lessons (RLS 인프라) | T5.1 inventory_ledger table RLS policy = Story 0-2 SSOT (`tenant_id = (auth.jwt() ->> 'tenant_id')::uuid`). service_role bypass audit-first (Epic 0 pattern 그대로). |
| cr-1-1-lessons (BigInteger + audit payload self-describing) | T3.1 audit payload = `{event_id, product_id, period_key, event_type, qty, trace_id, source: "carry_chain"|"monthly_input"|"manual_backfill"|"reversal_request", reverses_event_id?, correction_group_id?, metadata: dict}` — self-describing + idempotent skip payload 동일. |
| cr-4-3-lessons (Industry enum SSOT + async test F-1 + V8 STORY_4_4 fill marker + A5 forward-lock base) | T7 Industry canonical names parity + T9.3 async test pattern + T9.13 3중 게이트 명시 + T6.4 A5 drift detector extension. |
| cr-4-4-lessons (V8 골든 매트릭스 + tenant-scoped result_hash + A5 forward-lock partial) | T6 A5 forward-lock 6 values fill (D1 deferral 해결) + T9.13 V8 regression marker 838+ cases 누적 회귀 0건. |
| cr-5-1-lessons (pure kernel + service layer + 4 hooks wire + A5 forward-lock + 12-period chain limit + banker's rounding parity + DB-backed CI-shim + INVENTORY_LEDGER forward-fill 결정) | T1+T2 pure kernel m4_inventory/ledger.py + ledger_query.py (NEW per §(1)) + T3 service layer + T4 4 hooks + T6.1 INVENTORY_LEDGER forward-fill 6 values (D1 deferral 해결 per §(3)) + QTY_QUANTUM banker's rounding parity §(5) + 5-2/5-3 DB-backed CI-shim 패턴 §(6). |
| cr-epic-4-close-out (A3/A4/A5/A6/A7 cj-style) | A3 inline projection deprecation timeline = 5-2 commit 안에 swap + Epic 6 close-out 시점에 완전 제거 (T8). A4 0.5 plumbing NOT blocking for 5-2 (backend-only, A6 별도 Story 진입 후 5-3 frontend). A5 A5 forward-lock = D1 deferral 해결 (T6). A6 Story 0.5 plumbing 별도 (5-3 진입 전). A7 Epic 5 carry (async test + SDR overclaim detector). |

## Critical Path / A5 / A6 Gate

### A5 Gate (Epic 4 close-out retro A5 결정)
- **본 spec 진입 가능 조건**: Epic 4 close-out A5 Full Phase 1+2+4 done (2026-08-03).
- **D1 deferral 해결 시점 (cj-style default = 5-2 spec 진입 시 wire)**: `ActionClass.INVENTORY_LEDGER` accepted frozenset 6 values fill = 5-2 T6.1.
- **검증 결과**: 5-1 spec placeholder 6 values 본 스토리 6 values 채움과 1:1 매핑 (5-1 spec의 두 opening carry 관련 value는 5-1에서 `MONTHLY_INPUT_PERIOD` class 아래 wire; 5-2는 inventory_ledger 도메인 자체 6 values). drift detector extension으로 3-way consistency 검증.

### 0.5 Plumbing Gate (Epic 4 close-out retro A4/A6 결정)
- **5-2 backend-only**: pure kernel + service layer + handler + alembic + drift detector + capability gate + tests + docs 모두 backend. 5-2 frontend 영향: 없음 (TS mirror placeholder helper + skipped test 6 cases).
- **5-3 frontend toast 진입 전** 별도 Story (A6 NEW 결정) — `apps/web/lib/l2-input-inventory-ledger.ts` + sonner wire + vitest 활성화. 5-3 spec은 A6 done 후 진입.
- **본 스토리 영향**: TS mirror helper 작성 + skipped test 6 cases placeholder. 5-2 dev-story 완료 후 5-3 spec 진입 가능.

## File List (예상 변경/추가)

### NEW
- `packages/services/m4_inventory/__init__.py` (NEW — m4_inventory subpackage)
- `packages/services/m4_inventory/ledger.py` (NEW — pure kernel, stdlib-only, ~150 lines)
- `packages/services/m4_inventory/ledger_query.py` (NEW — pure kernel #2, stdlib-only, ~80 lines)
- `apps/api/modules/m4_inventory/services/ledger_service.py` (NEW — 5 operations + 4 typed exceptions, ~250 lines)
- `apps/api/alembic/versions/0015_inventory_ledger.py` (NEW — table + trigger + indexes + RLS, ~150 lines)
- `supabase/policies/0007_inventory_ledger_rls.sql` (NEW — tenant_id RLS, ~25 lines)
- `tests/services/m4_inventory/__init__.py` (NEW)
- `tests/services/m4_inventory/test_ledger.py` (NEW — 25 pure cases, ~400 lines)
- `tests/services/m4_inventory/test_ledger_query.py` (NEW — 10 pure cases, ~150 lines)
- `tests/api/m4_inventory/__init__.py` (NEW)
- `tests/api/m4_inventory/test_ledger_service.py` (NEW — 15 service cases, mock_session, ~300 lines)
- `tests/integration/test_inventory_ledger_capability.py` (NEW — 4 capability gate cases, ~100 lines)
- `tests/integration/test_inventory_projection_ledger_swap.py` (NEW — drift detector, ~80 lines)
- `tests/integration/test_inventory_ledger_label_consistency.py` (NEW — TS mirror placeholder 6 skipped cases, ~120 lines)
- `tests/architecture/test_inventory_ledger_no_mutate.py` (NEW — 5 AST guard cases, ~100 lines)
- `apps/web/lib/l2-input-inventory-ledger.ts` (NEW — TS mirror placeholder helper, ~80 lines)
- `docs/inventory-ledger.md` (NEW — operator/dev guide 7 sections, ~400 lines)

### MODIFY
- `apps/api/modules/m4_inventory/handlers.py` (extension — T4.1 4 NEW routes + Pydantic models)
- `apps/api/modules/m4_inventory/services/opening_carry_service.py` (extension — T4.3 carry chain decision → ledger event)
- `apps/api/modules/m2_input/services/monthly_input_service.py` (extension — T4.2 4 stream → ledger event + T5.4 state response 4 NEW fields + T8.2 swap to query_period_closing)
- `apps/api/modules/m2_input/schemas.py` (extension — T5.4 4 NEW fields + extra='forbid')
- `apps/api/modules/m4_inventory/schemas.py` (5-1 NEW, extension — T5.3 4 NEW Pydantic types)
- `apps/api/core/db_models.py` (extension — T5.2 InventoryLedger ORM)
- `apps/api/core/audit_action.py` (extension — T6.1/T6.2 6 values fill + D1 deferral 해결)
- `apps/api/main.py` (route 등록 — T4.4 4 NEW routes + 4 NEW exception handlers)
- `packages/services/m2_input/inventory_projection.py` (extension — T8.1 LEDGER_REFERENCE_QUERY_STUB fill + closed marker)
- `tests/integration/test_audit_action_consistency.py` (extension — T6.4 3-way drift detector 6 cases)
- `tests/services/test_audit_action_centralization.py` (extension — T6.5 5-2 actions 6개 registry set 검증)
- `tests/integration/test_m2_input_label_consistency.py` (extension — T9.10 inventory_ledger wire 메시지 label 5 cases)
- `tests/architecture/test_api_calls_only_ports.py` (extension — `packages.services.m4_inventory.ledger` + `packages.services.m4_inventory.ledger_query` + `packages.services.m4_inventory` add to ALLOWED_SERVICE_SUBMODULES)
- `docs/opening-inventory-carry.md` (§Story 5.2 추가 — carry chain → ledger event routing)
- `docs/monthly-input.md` (§Story 5.2 추가 — ledger event wire contract)
- `docs/architecture-inventory.md` (§Story 5.2 추가 — inventory_ledger table diagram)
- `docs/capability-matrix.md` (v1.6 — Changelog)
- `docs/conventions.md` (§10.6 NEW + §10.5 갱신)

### NOT MODIFIED (engine purity preserved)
- `packages/cost_engine/core/period_cost.py` (Story 4.1 그대로).
- `packages/cost_engine/ports/calc_port.py` (그대로).
- `packages/cost_engine/core/money.py` (AD-8 cross-cutting primitive — 보존).
- `apps/api/core/capability.py` (Capability.INVENTORY_LEDGER already added 5-1 v1.5 — 변경 0회).
- `apps/api/core/pipa_gate.py` (Epic 3 회고 A1, Story 4-1 spec 진입 게이트 — 보존).

## Dev Agent Record

### Implementation Plan
1. **T1 (Pure kernel)**: `packages/services/m4_inventory/ledger.py` — `InventoryLedgerEvent` NamedTuple + `build_event_payload` + `validate_event_type` + `validate_event_shape` + `append_only_violation_message` + `AppendOnlyLedgerError`. stdlib-only. banker's rounding via `QTY_QUANTUM`.
2. **T2 (Pure kernel #2)**: `packages/services/m4_inventory/ledger_query.py` — `LedgerQuery` NamedTuple + `build_period_closing_query` + `build_carry_chain_query`. stdlib-only.
3. **T3 (Service layer)**: `apps/api/modules/m4_inventory/services/ledger_service.py` — `LedgerService` 5 operations + 4 typed exceptions + AD-15 envelope mapping. SQLAlchemy AsyncSession + `emit_audit_typed` wire (raw `emit_audit(` 0건) + SELECT FOR UPDATE (AD-4).
4. **T4 (Wire trigger)**: `apps/api/modules/m4_inventory/handlers.py` 4 NEW routes + `monthly_input_service.py` 4 stream → ledger event + `opening_carry_service.py` carry decision → ledger event + `main.py` route + 4 exception handlers + `audit_action.py` T6 + D1 deferral 해결.
5. **T5 (Schema)**: Alembic 0015 + db_models InventoryLedger ORM + Pydantic 4 NEW types + MonthlyInputStateResponse 4 NEW fields.
6. **T6 (Audit-action + A5 forward-lock + D1 deferral 해결)**: `InventoryLedgerAction` Literal 6 values + `_ActionRegistry._REGISTRY[ActionClass.INVENTORY_LEDGER]` accepted set 6 values fill + drift detector extension (3-way).
7. **T7 (Capability gate)**: `require_capability("inventory_ledger")` dependency 4 routes에 wire (service-only ❌).
8. **T8 (Epic 3.3 inline projection deprecation swap)**: `LEDGER_REFERENCE_QUERY_STUB` fill + `_compute_inventory_projection_for_state` swap to `query_period_closing` + closed TODO marker + drift detector.
9. **T9 (Tests + docs + 3중 게이트)**: 9 NEW test files + 5 existing test extensions + 6 NEW/MODIFY docs + 3중 게이트 mandatory.

### Completion Notes
(Story 5.2 dev-story execute 후 populate)

### Debug Log
(placeholder)

### File List
(Story 5.2 dev-story execute 후 populate — NEW + MODIFY + NOT MODIFIED)

### Change Log
(Story 5.2 dev-story execute 후 populate)

### Status
**Status: ready-for-dev** (2026-08-04 — bmad-create-story 진입. bmad-dev-story 진입 전 게이트 해소 확인 필요: A5 done ✅ + A7 wire done ✅ + A6 진행 중 OK (backend-only).)

### 3중 게이트 (mandatory CI)
- `uv run ruff check` — 0 errors on Story 5.2 scope (pure kernel 2 + service layer + alembic + drift detectors + tests)
- `uv run import-linter lint` — 2 contracts KEPT (inventory_ledger pure helper = `packages/services/m4_inventory/`, m4_inventory service = `apps/api/modules/m4_inventory/`, no `packages.cost_engine` import — AD-11)
- `uv run pytest` (full, no skip) — V8 regression marker 838+ cases + Story 5.1 35 cases + Story 5.2 50+ cases 누적 pass

### Critical Files to Read Before Implementation
- `packages/services/m2_input/inventory_projection.py` — T8.1 LEDGER_REFERENCE_QUERY_STUB fill 진입점 + `build_inventory_projection` legacy path 보존.
- `apps/api/modules/m4_inventory/services/opening_carry_service.py` (5-1) — T4.3 carry decision → ledger event routing 진입점.
- `apps/api/modules/m2_input/services/monthly_input_service.py` — T4.2 4 stream → ledger event + T8.2 _compute_inventory_projection_for_state swap 진입점.
- `apps/api/core/audit_action.py` — T6 INVENTORY_LEDGER forward-fill 6 values + D1 deferral 해결 진입점. `_ActionRegistry._REGISTRY[ActionClass.INVENTORY_LEDGER]` empty frozenset → 6 values fill.
- `apps/api/core/db_models.py` — T5.2 InventoryLedger ORM 추가 진입점.
- `apps/api/alembic/versions/0014_verification_log_v8_audit.py` — T5.1 alembic 0015 down_revision = '0014_verification_log_v8_audit' 패턴.
- `supabase/policies/0006_products_rls.sql` (Story 2.1) — T5.1 inventory_ledger RLS policy 0007 reference pattern.
- `apps/api/core/capability.py::Capability.INVENTORY_LEDGER` — T7 capability gate wire (no change — already added 5-1 v1.5).
- `packages/services/m2_input/opening_carry.py` (5-1 pure kernel) — T1/T2 m4_inventory subpackage 신규 pure helper 진입점 (AD-11 layer rule 같은 pattern).
- `_bmad-output/implementation-artifacts/5-1-opening-inventory-auto-carry-chain.md` — 5-1 spec 전체 (5-2 wire 진입점 + service layer pattern + 4 hooks pattern + INVENTORY_LEDGER forward-fill placeholder 결정).
- `_bmad-output/implementation-artifacts/.review/story-5-1-review.md` — 5-1 CR D1 audit action class drift 결정 (deferral 보존 → 5-2 spec 진입 시 wire = 본 spec T6).
- `_bmad-output/implementation-artifacts/epic-4-retro-close-out-2026-08-03.md` §6 A3 cj-style 결정 (Epic 3.3 inline projection deprecation timeline = 5-2 commit 안에 swap).
- `docs/capability-matrix.md` v1.5 (Story 5.1) — T7 capability gate 매트릭스 footnote 정합.
- `docs/conventions.md` §0.4 (Korean message parity) + §10.5 (5-1 opening auto-carry policy) + §10.6 (5-2 NEW inventory ledger append-only policy).
- `apps/api/modules/m4_inventory/schemas.py` (5-1 NEW) — T5.3 4 NEW Pydantic types extension pattern.

## Review Findings (bmad-code-review 2026-08-04)

> Range reviewed: b4b84da..HEAD (8 commits, 7,769 raw lines, 37 files).
> Layers: Blind Hunter (40) + Edge Case Hunter (33) + Acceptance Auditor (8 ACs).
> Raw findings: 81 → deduped 64 clusters → severity-routed to **23 surviving** (3 decision-needed + 16 patch + 4 defer) + 6 dismissed.
> Triage file: `_bmad-output/implementation-artifacts/.review/story-5-2-triage.md`.

### decision-needed

- [x] [Review][Decision] LedgerQuery NamedTuple shape spec/código drift [packages/services/m4_inventory/ledger_query.py:60-73] — Spec literal defines `LedgerQuery(period_key, product_id, closing_qty)` value object. Actual ships `LedgerQuery(sql, params, description)` SQL builder. Both work; code is better engineering. **Decision**: amend spec to reflect actual. **Resolution**: spec T2.1 + AC #1 Pure kernel #2 amended to `LedgerQuery(sql: str, params: tuple, description: str)`.
- [x] [Review][Decision] build_period_closing_query signature spec/código drift [packages/services/m4_inventory/ledger_query.py:77-103] — Spec literal: `build_period_closing_query(tenant_id, period_key) -> str`. Actual: `build_period_closing_query() -> LedgerQuery`. Service binds via SQLAlchemy `text().bindparams()`. **Decision**: amend spec to reflect actual. **Resolution**: spec T2.2 + AC #1 amend to `build_period_closing_query() -> LedgerQuery` (paramless; service binds via `text().bindparams()`).
- [x] [Review][Decision] `production_material_consumption` event_type emit — spec AC #4 vs Deferral #9 conflict [apps/api/modules/m2_input/services/monthly_input_service.py] — AC #4 requires output+consumption dual emit. Deferral #9 defers to Story 5.3+ BOM. Code matches Deferral #9; whitelist includes the value but no caller invokes it. **Decision**: accept deferral (code matches Deferral #9). **Resolution**: AC #4 amended to gate dual-emit on Story 5.3+ BOM module authority; 5-2 ships single-emit (output only).

### patch

- [ ] [Review][Patch] event_id missing DEFAULT gen_random_uuid() [apps/api/alembic/versions/0015_inventory_ledger.py:63] — Add `DEFAULT gen_random_uuid()` to event_id PRIMARY KEY for DB-level safety net.
- [ ] [Review][Patch] qty >= 0 CHECK contradicts PRD §6.2 signed qty [apps/api/alembic/versions/0015_inventory_ledger.py:121-122] — CHECK blocks negative qty for outbound events. Change to event_type-aware CHECK.
- [ ] [Review][Patch] AD-22 UNIQUE constraint missing (INDEX only) [apps/api/alembic/versions/0015_inventory_ledger.py:177-181] — Change `idx_inventory_ledger_reverses_event_id` to `UNIQUE INDEX` with `(tenant_id, reverses_event_id)` to prevent double-reversal.
- [ ] [Review][Patch] Idempotency partial unique index missing [apps/api/alembic/versions/0015_inventory_ledger.py] — Add `UNIQUE INDEX uq_inventory_ledger_idempotency ON (tenant_id, product_id, period_key, event_type, trace_id) WHERE trace_id IS NOT NULL` for race-safe idempotency.
- [ ] [Review][Patch] Carry-chain CTE date/text join mismatch (broken query) [packages/services/m4_inventory/ledger_query.py:142] — `cc.period_key = (e.period_key || '-01')::date - INTERVAL '1 month'` compares text vs date, never matches. Fix to text-to-text comparison via `to_char(to_date(...))`.
- [ ] [Review][Patch] Carry-chain CTE missing `opening_carried_stale_overwrite` filter [packages/services/m4_inventory/ledger_query.py:130,143] — Both seed and recursive terms filter `event_type = 'opening_carried'` only. Add `opening_carried_stale_overwrite` to both.
- [ ] [Review][Patch] Carry-chain CTE recursion depth + ORDER BY direction [packages/services/m4_inventory/ledger_query.py:144-149] — Recursion has no depth bound in SQL; `ORDER BY period_key ASC LIMIT 12` returns earliest, not nearest. Add `WHERE depth < :max_depth` + `ORDER BY period_key DESC` + parameterized bound.
- [ ] [Review][Patch] append_event uses uuid.uuid4() violating AD-15 UUID v7 SSOT [apps/api/modules/m4_inventory/services/ledger_service.py:259] — Service layer mints v4. Use `uuid.uuid7()` (Python 3.12+) or `uuid_generate_v7()` postgres extension.
- [ ] [Review][Patch] _assert_not_modifying AST guard is dead code [apps/api/modules/m4_inventory/services/ledger_service.py:514-541] — Method defined but NEVER invoked from any operation. AC #3 2nd axis of 3중 방어 silently degraded. Either invoke via wrap or document as future hardening + remove from AC #3 claims.
- [ ] [Review][Patch] Substring error parsing couples service to kernel message wording [apps/api/modules/m4_inventory/services/ledger_service.py:276,282] — `"11-value whitelist" in err.message` and `"YYYY-MM" in err.message` are fragile. Add `error_code` attribute to AppendOnlyLedgerError; use isinstance or error_code dispatch.
- [ ] [Review][Patch] supabase/policies/0007_inventory_ledger_rls.sql MISSING [supabase/policies/0007_inventory_ledger_rls.sql] — Spec required NEW RLS policy file. `0007` is occupied by `bom_lines`. Create `0008_inventory_ledger_rls.sql` mirroring `0009_monthly_input_rls.sql` structure (4-policy split: tenant SELECT/INSERT + service_role bypass).
- [ ] [Review][Patch] ALTER TABLE inventory_ledger ENABLE ROW LEVEL SECURITY missing [apps/api/alembic/versions/0015_inventory_ledger.py] — Migration does not enable RLS on the new table. Add `op.execute("ALTER TABLE inventory_ledger ENABLE ROW LEVEL SECURITY")` before downgrade().
- [ ] [Review][Patch] MonthlyInputStateResponse 4 NEW ledger fields MISSING [apps/api/modules/m2_input/schemas.py:343-391] — Spec T5.4 required `ledger_events_count` + `ledger_period_closing` + `inventory_ledger_enabled` + `reversal_request_enabled`. None present. Add 4 fields + populate in `monthly_input_service.py:1110` get_state.
- [ ] [Review][Patch] A7 wire SDR drift detector FAILING (drift 82) [tests/integration/test_sdr_test_count_drift.py:172] — Actual pytest collection = 1105; MAX SDR claim = 1023 (from `epic-4-retro-close-out-2026-08-03.md:408`); tolerance = 50; drift = 82. Update SDR MAX claim to 1105+ with cushion.
- [ ] [Review][Patch] _compute_inventory_projection_for_state dead append + unused param [apps/api/modules/m2_input/services/monthly_input_service.py:1763-1785] — `out.append(...)` at line 1763 immediately overwritten by `out[-1] = ...` at line 1780. Remove first append, remove `opening_balance` param.
- [ ] [Review][Patch] test_audit_action_centralization.py extension missing [tests/services/test_audit_action_centralization.py] — Spec T6.5/T9.8 requires verification that all 6 INVENTORY_LEDGER actions are registered. Current file only pins symbol + scans for legacy calls. Add explicit assertions for all 6 actions in `_REGISTRY[ActionClass.INVENTORY_LEDGER]`.

### defer

- [x] [Review][Defer] production_material_consumption emit deferred [apps/api/modules/m2_input/services/monthly_input_service.py] — Spec Deferral #9: deferred to Story 5.3+ BOM-aware reconciliation. pre-existing, spec-mandated.
- [x] [Review][Defer] TS mirror file `apps/web/lib/l2-input-inventory-ledger.ts` missing [] — Spec placeholder; TS mirror wire deferred to 5-3 vitest activation. pre-existing, spec-mandated (Epic 4 close-out A6).
- [x] [Review][Defer] TS mirror parity tests (`test_inventory_ledger_label_consistency.py`) 6 skipped [] — Spec placeholder; deferred to 5-3 vitest wire (A6 plumbing). pre-existing, spec-mandated.
- [x] [Review][Defer] _emit_inventory_ledger_event_for_row / _emit_ledger_events_for_decisions no isolated unit tests [tests/api/m4_inventory/test_ledger_service.py] — Integration test `test_inventory_projection_ledger_swap.py` covers via call graph. Acceptable for 5-2 scope. pre-existing, integration coverage sufficient.

### dismiss

- [x] [Review][Dismiss] _assert_not_modifying substring false-positive risk — Dead code (see patch P9); no caller exercises the substring match. Fix P9 first.
- [x] [Review][Dismiss] Trigger function OLD.event_id reference garbles message — False positive: trigger uses `COALESCE(OLD.event_id::text, '<new>')` (migration line 206) explicitly handling INSERT path.
- [x] [Review][Dismiss] _validate_uuid7 accepts v4 — By design: pure-kernel comment line 322 "Anything else (including UUID v4) is permitted in MVP". Service layer still uses v4 (patch P8 catches this).
- [x] [Review][Dismiss] EXTRA_FORBIDDEN_CONFIG module-level constant — False positive: no module-level constant exists; each Pydantic model sets `model_config = ConfigDict(extra="forbid")` independently.
- [x] [Review][Dismiss] InventoryLedger.inserted_at comment mismatch — False positive: ORM comment correctly states "set on INSERT via DB DEFAULT NOW()" matching migration.
- [x] [Review][Dismiss] PeriodClosingResponse naming collision single vs multi-product — Verified working: handlers wrap single-product (line 251) and multi-product (line 284) correctly.
