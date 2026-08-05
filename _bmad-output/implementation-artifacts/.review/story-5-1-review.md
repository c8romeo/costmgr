---
review_target: 5-1-opening-inventory-auto-carry-chain
baseline_commit: 80f4494
review_commit: b4b84da
reviewer_mode: full
review_date: 2026-08-04
spec_file: _bmad-output/implementation-artifacts/5-1-opening-inventory-auto-carry-chain.md
diff_output: _bmad-output/implementation-artifacts/.review/story-5-1.diff
review_layers:
  - blind-hunter (bmad-review-adversarial-general)
  - edge-case-hunter (bmad-review-edge-case-hunter)
  - acceptance-auditor (manual)
failed_layers: []
---

# Story 5.1 Code Review — Triage Report

> **Review target**: Story 5.1 (5-1-opening-inventory-auto-carry-chain)
> **Baseline**: `80f4494` (Story 4.4 tip) → **Review commit**: `b4b84da` (Story 5.1 dev-story T1~T8)
> **Diff stats**: 20 files / +2953 / -19 / 3219 lines
> **3 reviewer 병렬**: Blind Hunter (25 findings) + Edge Case Hunter (30 findings) + Acceptance Auditor (9 findings)
> **Raw 합계**: 64 findings → **Unique (after dedup)**: 36 findings → **Survived triage**: **33 findings**

## Raw → Unique Dedup Map

| # | Finding | Sources | Location |
|---|---|---|---|
| 1 | Capability gate 미 wire (`require_role("owner")` only) | Blind F-7/F-24 + AA HIGH-1 | `apps/api/modules/m4_inventory/handlers.py:91` |
| 2 | `recompute_opening_on_prev_change` T3.3 hook NEVER wired | Blind F-2 + AA HIGH-2 | `apps/api/modules/m2_input/services/monthly_input_service.py:765-781` (grep 결과 정의만, 호출처 0) |
| 3 | Concurrency race on `auto_carry_on_get_state` (no SELECT FOR UPDATE) | Blind F-3 + ECH-13 + ECH-16 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:275-334` |
| 4 | Manual edit envelope `<pending>` placeholder + missing `auto_carried_value` | Blind F-4 + AA MEDIUM-3 | `apps/api/modules/m2_input/services/monthly_input_service.py:833` + `apps/api/main.py:682-685` |
| 5 | Service-layer tests all skipped (DB-backed CI shim) | Blind F-6 + ECH-27 + ECH-28 | `tests/api/test_opening_carry.py` (전체 `pytest.mark.skip`) |
| 6 | A5 drift detector skip-gated (m4_inventory call sites unchecked) | Blind F-10 + ECH-29 | `tests/integration/test_audit_action_consistency.py` skip |
| 7 | `_decode_opening_jsonb` silent `continue` on malformed values | Blind F-11 + ECH-5/6/7/8/9/11/18/21 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1266-1283` |
| 8 | 12-period chain limit NOT guarded in auto carry path | ECH-2 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:275-334` |
| 9 | Pure resolver `resolve_opening_balance` drops lock metadata | ECH-4 | `packages/services/m2_input/opening_carry.py` `resolve_opening_balance` |
| 10 | Empty carry decisions while current non-empty erases balances | ECH-19 | `apps/api/modules/m4_inventory/services/opening_carry_service.py` `auto_carry_on_get_state` |
| 11 | Audit action class drift (INVENTORY_LEDGER → MONTHLY_INPUT_PERIOD deferral) | Blind F-1/F-20/F-21 + AA MEDIUM-1 | `apps/api/core/audit_action.py:124-131` |
| 12 | Recompute propagation 1-step not chain (AC #3 explicit "chain") | Blind F-9 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1470+` `recompute_opening_on_prev_change` |
| 13 | Pydantic Literal not used for `opening_inventory` reject | Blind F-13 + AA MEDIUM-4 | `apps/api/modules/m2_input/services/monthly_input_service.py:534-541` |
| 14 | Manual trigger idempotent no-op violation (CR 1.1) | ECH-3 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1317-1359` |
| 15 | Period key validation gaps (month 00/13) | ECH-10/11/22 | `_prev_period_key` / `_next_period_key` |
| 16 | Hardcoded `baseline_revision=1` lookup | ECH-14 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1552-1562` |
| 17 | Service instantiated for service-only industry (capability 미 enforced in service) | ECH-15 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1304-1315` |
| 18 | Lock audit + transaction coupling gaps | ECH-17/24 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1439-1467` |
| 19 | Malformed JSONB shape drift (`_locked=true` without `_lock_reason_ko`) | ECH-18 | `_validate_kernel_lock_consistency` |
| 20 | Mixed UUID/string product identifiers | ECH-20 | `packages/services/m2_input/opening_carry.py:2385-2389` |
| 21 | Quantity input non-Decimal type (int/float/string/None) | ECH-21 | `packages/services/m2_input/opening_carry.py:2389-2411` |
| 22 | Audit writer error handling (rollback coupling) | ECH-23 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1624-1653` |
| 23 | Decimal serialization allows arbitrary strings | Blind F-8 | `apps/api/modules/m2_input/schemas.py:387-390` |
| 24 | Lock operation may raise before audit (no try/except around mutation) | Blind F-14 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1423-1467` |
| 25 | `auto_carry` audit missing `prev_old_value`/`prev_new_value` | Blind F-17 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1625-1650` |
| 26 | TS mirror file missing | Blind F-5 + AA MEDIUM-5 + ECH-29 | `apps/web/lib/l2-input-opening-carry.ts` (not in diff) |
| 27 | `m4_inventory/schemas.py` not extracted (T4.2 violation) | AA MEDIUM-7 | `apps/api/modules/m4_inventory/handlers.py:50-78` (inline) |
| 28 | 4 missing MODIFY files (drift detectors + TODO marker) | AA MEDIUM-2 | spec MODIFY list 미반영 |
| 29 | Test count mismatch (35 pass vs spec 50+) | Blind F-23 + AA LOW-1 | SDR |
| 30 | Settings lookup error handling | ECH-25 | `apps/api/modules/m4_inventory/handlers.py:1044-1050` |
| 31 | Response validation (decision non-string) | ECH-26 | `apps/api/modules/m4_inventory/handlers.py:1058-1074` |
| 32 | Chain depth counter doesn't detect actual carry applied | Blind F-12 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1733-1752` |
| 33 | m4 → m0 import reverse-dependency (AD-11) | Blind F-16 | `apps/api/modules/m4_inventory/handlers.py:38-41` |
| 34 | Chain depth error hardcodes "12" | Blind F-18 | `apps/api/main.py:725-730` |
| 35 | Async test pattern (CR 4-3 F-1 / A7 carry) | Blind F-19 | `tests/api/test_opening_carry.py` |
| 36 | Manual edit reject bypass via bulk import | Blind F-22 | SQL-level CHECK 없음 |
| 37 | `_run_carry_chain` cycle guard (depth only, not chain walk) | Blind F-25 | `apps/api/modules/m4_inventory/services/opening_carry_service.py:1733-1752` |
| 38 | Capability matrix service-only ❌ test missing | AA LOW-3 | `tests/integration/test_opening_carry_capability.py` |
| 39 | Industry fallback hides new-tenant bug | Blind F-15 | `apps/api/modules/m4_inventory/handlers.py:1044-1050` |

> Note: Original reviewers reported 64 raw findings (25 + 30 + 9). After dedup with cross-source merge → 39 unique findings. After triage (DISMISS count) → **33 survived**.

## Triage — Route별 분류

### 🔴 DECISION_NEEDED (2건)

#### D1. Audit action class drift — INVENTORY_LEDGER vs MONTHLY_INPUT_PERIOD (H11, AA-M1, Blind-F1/F20/F21)
- **Severity**: MEDIUM (spec literal deviation, deferral 보존 결정과 충돌)
- **Spec literal (AC #6)**: `ActionClass.INVENTORY_LEDGER` 의 `_ActionRegistry` accepted set 채움 (5-1 actions 3개 + 5-2 forward-fill 3개 stub = 6 values)
- **Code actual**: `ActionClass.MONTHLY_INPUT_PERIOD` Literal에 2 actions wire (`monthly_input_period_opening_carried` + `monthly_input_period_opening_locked`)
- **Deferral 결정 보존**: `cr-5-1-lessons §(3)` — "INVENTORY_LEDGER class는 5-2 (append-only ledger table)와 함께 등장하는 게 자연스러움. A5 partial done 패턴 — 새 enum class 추가는 Epic 단위 책임"
- **Trade-off**:
  - **(a) Deferral 보존 (현재 상태)**: 5-2 spec 진입 시 `ActionClass.INVENTORY_LEDGER` 신설 + 6 values wire. INVENTORY_LEDGER class placeholder slot은 5-2 진입까지 비어있음.
  - **(b) Spec literal 복원**: 5-1에서 `INVENTORY_LEDGER` 신설 + 6 values wire (live 2 + stub 4). Epic 4 close-out retro A5 forward-lock 패턴 그대로 (Story 4-4 V8 entry와 동일).
  - **(c) Spec patch (bmad-correct-course)**: 5-1 spec을 deferral 결정 반영하여 update.
- **Decision 입력 필요**: 어느 옵션 채택?

#### D2. Service-layer tests all skipped (H5, AA-M2, Blind-F6)
- **Severity**: HIGH (CR 1.1 idempotent no-op 미검증, 9 tests 모두 skip — DB-backed path 미커버)
- **Test surface**: `tests/api/test_opening_carry.py` 9 tests (1 placeholder + 8 reference async) 모두 `pytest.mark.skip`
- **Spec test claim**: "50+ new tests pass" — actual 35 pass + 11 skip (CR 4-3 F-2 SDR overclaim)
- **Trade-off**:
  - **(a) 현재 skip 유지**: A6 Story 0.5 plumbing 진입 시 일괄 활성화 (Epic 4 close-out retro A6 결정 그대로).
  - **(b) m4_inventory entry-point 동기 테스트 추가**: `unittest.mock.AsyncMock`으로 AsyncSession mock + pure logic 검증 (Story 0.5 plumbing 없이 가능).
  - **(c) Async test pattern으로 즉시 활성화**: CR 4-3 F-1 fix (`asyncio.run()` wrapper) 적용 후 활성화. 단, DB-shim gate는 여전히 필요.
- **Decision 입력 필요**: 어느 옵션 채택?

### 🟡 PATCH (24건 — 자동 fix)

#### HIGH severity PATCH (9건)

##### H1. Capability gate not wired in handlers.py ⚠️
- **File**: `apps/api/modules/m4_inventory/handlers.py:91`
- **Code actual**: `_role: None = Depends(require_role("owner"))` (capability check 없음)
- **AC violation**: AC #1 + AC #6 — "service-only tenant → 403 `INDUSTRY_NOT_SUPPORTED` typed envelope" 미 wire
- **Fix**:
  ```python
  capability: None = Depends(require_capability("opening_inventory")),
  _role: None = Depends(require_role("owner")),
  ```
- **Effort**: 1 line change + verify `require_capability` signature

##### H2. `recompute_opening_on_prev_change` T3.3 hook NEVER wired ⚠️
- **File**: `apps/api/modules/m2_input/services/monthly_input_service.py:765-781`
- **Verified**: grep 결과 정의만, 호출처 0 (`apps/api/modules/m4_inventory/services/opening_carry_service.py` 단일 매치)
- **AC violation**: AC #3 + T3.3 — stale-value auto-recompute trigger 미구현
- **Fix**: `lock_opening_after_first_row` 호출 직후 추가:
  ```python
  await carry_svc.recompute_opening_on_prev_change(
      prev_period_key=<prev_period_key>,  # period_key의 prev 계산
      actor_id=actor_id,
  )
  ```
- **Effort**: ~10 lines (chain propagation 진입점)

##### H3. Concurrency race on `auto_carry_on_get_state`
- **File**: `apps/api/modules/m4_inventory/services/opening_carry_service.py:275-334`
- **Issue**: bare SELECT → no atomic guard → two `get_state` calls both emit audit + UPDATE
- **Fix**: `await self.session.execute(select(MonthlyInputPeriod).where(...).with_for_update())` 추가 + 같은 transaction에서 UPDATE
- **Effort**: ~5 lines

##### H4. Manual edit envelope `<pending>` placeholder + missing `auto_carried_value`
- **File**: `apps/api/modules/m2_input/services/monthly_input_service.py:833` + `apps/api/main.py:682-685`
- **Issue**: `period_key="<pending>"` literal stub + `auto_carried_value` field 미존재
- **Fix**: `_validate_stream_shape(period_key: str)` signature 추가 + exception에 `auto_carried_value=str(period.opening_inventory.get(product_id))` 추가
- **Effort**: ~10 lines

##### H6. A5 drift detector skip-gated
- **File**: `tests/integration/test_audit_action_consistency.py` + `tests/services/test_audit_action_centralization.py`
- **Issue**: AST-grep drift detector skip → raw `emit_audit(` 추가 시 감지 못함 (CR 1.1 4번째 epic 연속 발생 시 방어 실패)
- **Fix**: AST pattern (`emit_audit(`) doesn't require DB → skip 제거
- **Effort**: ~3 lines (`pytestmark` 조정)

##### H7. `_decode_opening_jsonb` silent `continue` on malformed
- **File**: `apps/api/modules/m4_inventory/services/opening_carry_service.py:1266-1283`
- **Issue**: malformed JSONB silently dropped → carry chain silently drops entry
- **Fix**: NaN/Infinity/null/non-string 키 → `MonthlyInputOpeningLockViolationError` (500 AD-15 envelope)
- **Effort**: ~15 lines (defensive guard 추가)

##### H8. 12-period chain limit NOT guarded in auto path
- **File**: `apps/api/modules/m4_inventory/services/opening_carry_service.py:275-334` (`auto_carry_on_get_state`)
- **Issue**: `trigger_carry_chain_for_period` (line 598)는 chain depth guard 있지만 `auto_carry_on_get_state`는 silent skip
- **Fix**: auto path에 chain depth guard 추가 + manual trigger 안내 (PRD §F4.1)
- **Effort**: ~10 lines

##### H9. Pure resolver `resolve_opening_balance` drops lock metadata
- **File**: `packages/services/m2_input/opening_carry.py`
- **Issue**: `_locked` + `_lock_reason_ko` markers dropped on resolve
- **Fix**: `lock_state` parameter 보존 + apply logic 추가
- **Effort**: ~10 lines

##### H10. Empty carry decisions while current non-empty erases balances
- **File**: `apps/api/modules/m4_inventory/services/opening_carry_service.py` `auto_carry_on_get_state` line 318-319
- **Issue**: `if not decisions: return []` → silent erase of existing balances
- **Fix**: current_decoded and not decisions → no-op (silent) + audit log warning
- **Effort**: ~5 lines

##### H12. Recompute propagation 1-step not chain
- **File**: `apps/api/modules/m4_inventory/services/opening_carry_service.py:1470+` `recompute_opening_on_prev_change`
- **Issue**: `next_period` 한 단계만 walk, 그 후 exit (AC #3 "chain" 미충족)
- **Fix**: `while depth < INVENTORY_PERIOD_CHAIN_LIMIT:` loop + cycle guard
- **Effort**: ~15 lines

#### MEDIUM severity PATCH (12건)

| ID | Finding | Effort |
|---|---|---|
| M1 | Pydantic Literal not used for `opening_inventory` reject | ~5 lines |
| M2 | Manual trigger idempotent no-op violation (CR 1.1) | ~10 lines |
| M3 | Period key validation gaps (month 00/13) | ~10 lines |
| M4 | Hardcoded `baseline_revision=1` lookup | ~5 lines (multi-revision) |
| M5 | Service instantiated for service-only industry (capability 미 enforced) | ~5 lines (defense-in-depth) |
| M6 | Lock audit + transaction coupling gaps | ~10 lines |
| M7 | Malformed JSONB shape drift | ~5 lines |
| M8 | Mixed UUID/string product identifiers | ~5 lines |
| M9 | Quantity input non-Decimal type | ~5 lines (TypeError raise) |
| M10 | Audit writer error handling (rollback coupling) | ~10 lines |
| M11 | Decimal serialization allows arbitrary strings | ~5 lines (Pydantic validator) |
| M13 | `auto_carry` audit missing `prev_old_value`/`prev_new_value` | ~10 lines |

#### LOW severity PATCH (5건)

| ID | Finding | Effort |
|---|---|---|
| L1 | Test count mismatch (35 vs spec 50+) | SDR 정정 (1 line) |
| L2 | Settings lookup error handling | ~5 lines |
| L3 | Response validation (decision non-string) | ~5 lines |
| L6 | Chain depth error hardcodes "12" | ~3 lines (use constant) |
| L9 | `_run_carry_chain` cycle guard | ~5 lines |
| L10 | Capability matrix service-only ❌ test missing | ~10 lines (1 test case) |
| L11 | Industry fallback hides new-tenant bug | ~5 lines (rejection if industry=None) |

### 🔵 DEFER (5건)

| ID | Finding | Defer target | Reason |
|---|---|---|---|
| M14 | TS mirror file missing | Story 5.3 spec 진입 시 | Epic 4 close-out retro A6 결정 (5-3 진입 전 별도 Story 0.5 plumbing) |
| M15 | `m4_inventory/schemas.py` not extracted | Story 5.1.1 follow-up 또는 5-2 진입 시 | Module boundary convention |
| M16 | 4 missing MODIFY files (drift detectors + TODO marker) | Story 5.2 spec 진입 시 | inventory_ledger table 진입 시 inline projection deprecation marker 갱신 |
| L4 | Chain depth counter doesn't detect actual carry applied | Epic 5 close-out A8+ 결정 | Architectural follow-up |
| L5 | m4 → m0 import reverse-dependency (AD-11) | Epic 5+ architecture follow-up | Cross-module coupling |
| L7 | Async test pattern (CR 4-3 F-1 / A7 carry) | A7 wire 시 (Epic 5 carry 결정) | Epic 4 close-out retro A7 |
| L8 | Manual edit reject bypass via bulk import | Story 0.5 plumbing 후 SQL CHECK 추가 | SQL-level defense |

### ⚪ DISMISS (1건)

| ID | Finding | Reason |
|---|---|---|
| D1 | `capability-matrix.md` v1.5 date placeholder (`2026-08-03` vs spec `2026-08-XX`) | Cosmetic, spec intentionally used placeholder |

## Summary

- **Raw**: 64 findings (25 blind + 30 edge + 9 acceptance)
- **After dedup**: 39 unique findings
- **After triage**: 33 survived (2 DECISION + 24 PATCH + 7 DEFER, 1 DISMISS)
- **Verdict basis**: 2 DECISION_NEEDED (D1 audit action class drift + D2 service-layer tests) + 9 HIGH PATCH (H1 capability gate, H2 recompute hook, H3 concurrency, H4 manual edit envelope, H6 A5 drift, H7 decode silent continue, H8 chain limit auto path, H9 pure resolver lock metadata, H10 empty decisions erase, H12 chain propagation 1-step) = **11 HIGH/MEDIUM blockers**

## CR 1.1 + CR 4.3 Lessons Applied

- **CR 1.1 (audit-first + idempotent no-op)**: M2, M6, M13, M14 highlight gaps in audit-first enforcement + idempotent behavior
- **CR 2.1 (capability gate + cross-lang)**: H1 (capability gate not wired), L10 (capability matrix test missing)
- **CR 4.3 (Industry enum SSOT + A5 forward-lock)**: D1 (audit action class drift), H6 (drift detector skip), F-19 in Blind (async test pattern)
- **CR 4-4 (V8 + tenant-scoped)**: L11 (industry fallback for tenant context)

## Epic 4 close-out A7 carry — 이번 CR에서 검출

- **(a) async test pattern (CR 4-3 F-1)**: L7 + Blind F-19 — `tests/api/test_opening_carry.py`에 `async def` + `@pytest.mark.skip` 패턴 존재. `tests/cost_engine/test_no_async_decorator.py` AST guard는 이미 wire (Epic 4 close-out A7 follow-through)
- **(b) SDR overclaim detector (CR 4-3 F-2)**: L1 — SDR claim "35 passed + 11 skipped" vs spec "50+". A7 detector wire 시 본 CR finding도 자동 capture 가능

## Next steps

1. **User 답변 대기**: D1 + D2 (cj-style 결정)
2. **PATCH 적용**: 24건 (HIGH 9 + MEDIUM 12 + LOW 7) — `bmad-dev-story` action=apply-review-fixes 또는 batch commit
3. **sprint-status forward**: `5-1 → done` (PATCH 적용 + DECISION 해결 후)
4. **Epic 5 5-2 spec 진입**: baseline_commit = b4b84da (PATCH 후). 5-2 spec 진입 시 D1 deferral option (a) 채택 시 `ActionClass.INVENTORY_LEDGER` 신설 + 6 values wire + inventory_ledger table + inline projection deprecation marker 명시.
5. **A6 Story 0.5 plumbing 별도 Story**: D2 결정에 따라 진입 시점 결정 (5-2 dev-story 진행 중 또는 5-3 진입 직전).

## Adjacent docs

- `_bmad-output/implementation-artifacts/5-1-opening-inventory-auto-carry-chain.md` (spec)
- `_bmad-output/implementation-artifacts/.review/story-5-1.diff` (diff)
- `_bmad-output/implementation-artifacts/epic-4-retro-close-out-2026-08-03.md` (Epic 4 close-out 결정)
- `_bmad-output/implementation-artifacts/a5-audit-action-inversion-spike-2026-08-03.md` (A5 spike)
- Memory: `cr-5-1-lessons.md`, `epic-4-close-out-decisions.md`
