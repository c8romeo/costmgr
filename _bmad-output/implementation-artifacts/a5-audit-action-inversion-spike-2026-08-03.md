---
epic: 4
spike_id: A5
spike_title: CR 1.1 lesson — Audit-Action Inversion Single Source of Truth
date: 2026-08-03
status: design-only (research + proposal)
scope_window: Epic 4 close-out (Story 4-3과 병렬)
facilitator: Charlie (Senior Dev) + Amelia (Developer)
owners_followup: Charlie (decision) + Amelia (implementation)
time_budget: 4-8h (1 day)
constraint: research + design proposal only — 구현은 Story 4-3 이후 별도 액션
working_tree_baseline: A1 4d088f5 commit 후
related_retro_section: Epic 4 회고 §3 C2 (CR 1.1 lesson 4번째 epic 연속 재발) + §7 A5 (별도 스파이크 결정)
---

# A5 — Audit-Action Inversion Single Source of Truth (Spike)

## 1. Background

### 1.1 CR 1.1 lesson — 4번째 epic 연속 재발 패턴

Story 1.1 (2026-07-29 review)에서 처음 발견된 audit-action inversion 패턴이 **Epic 1·2·3·4 4번 연속 재발**했다. 매번 audit log의 `action` 필드에 free-form string literal을 직접 기입하면서 typed exception의 의미와 어긋나는 drift가 발생했다.

**대표 사례 — Story 1.1 industry_selected / industry_change_initial** ([`apps/api/modules/m0_onboarding/services/settings_service.py:382-387`](../../apps/api/modules/m0_onboarding/services/settings_service.py)):

```python
# CR 1.1 lesson — F-36 close-out 패치 후
# AC #1 — first-time selection writes action='industry_selected'.
# AC #4 — subsequent change within grace window writes
# action='industry_change_initial'.
if is_initial_flag:
    audit_action = "industry_selected"
    payload_reason = "industry_selected_initial"
else:
    audit_action = "industry_change_initial"
    payload_reason = "industry_change_within_grace"
```

F-36 패치(2026-08-01) **이전**에는 `industry_change_initial if is_initial else industry_selected`로 **반전된 채** shipped — AC #1 (first-time → `industry_selected`) 위반. F-36에서 if/else 양쪽을 swap하여 수정. **이 자체가 "free-form string + 수동 if/else = drift의 1차 원인" 패턴의 증거**.

### 1.2 재발 timeline

| Story | 발견 사례 | 모듈 | file:line |
|---|---|---|---|
| 1.1 | `industry_selected` vs `industry_change_initial` inversion | m0_onboarding | `settings_service.py:382-387` |
| 1.3 | `company_subblock_promoted` (tenant_settings target — 기존 `product_created` 류와 다른 JSONB aggregate target) | m10_ai | `service.py:609-628` |
| 2.1 | `product_type_changed` vs `product_updated` (type-only vs mixed PATCH 분기) | m1_baseline | `product_service.py:611-615` |
| 2.1 | `product_soft_deleted` vs `product_reactivated` (is_active toggle 분기) | m1_baseline | `product_service.py:679` |
| 4.2 | `compute` / `idempotent_skip` / `rollback` 신규 enum — CalcLog에 DB CHECK constraint로 잠금 (action_class 부재로 audit_logs 와 별개 진화) | m3_calculate | `0012_fiscal_period_snapshots.py:102` + `calc_orchestrator.py:254, 280, 468` |
| **4.3 (예정)** | `verification_passed` / `verification_failed` / `verification_skipped` 신규 enum — 별도 `verification_log` table | m3_calculate | [`4-3-verification-v1-v4-v7-v8-order.md:153`](4-3-verification-v1-v4-v7-v8-order.md) |
| **Epic 5 (예정)** | `inventory_ledger.action` enum (`ledger_created` / `ledger_reversed` / `carry_forward` 등) — TODO(epic-5) marker 4곳 | m4_inventory | `core/db_models.py:446` + `product_service.py:783` + `monthly_input_service.py:1518` + `0011_*.py:36` |
| **Epic 11 (예정)** | `reversal_log.action` enum (`commit` / `reverse` / `re-reverse`) — design-only | m11_reversal | (미구현) |

### 1.3 위험 — Epic 5 carry-over 5번째 drift 리스크

Epic 4 회고 §3 C2에서 합의된 바와 같이:

> **위험**: Epic 5/6/7/11까지 "사실상 표준" 고착화 가속 — `verification_log` / `inventory_ledger` / `reversal_log` 각자 고유 enum을 DB CHECK constraint로 잠그면, 4번째 epic (4-3)부터 audit_logs 본 테이블과 별개의 진화 경로를 탄다. Story 4.3 spec OQ5에 명시:
>
> > "신규 추가 (cj-style default) — `calc_log.action` enum 확장 (`'verification_failed'`) + 별도 `verification_log` table. A5 결정(action_class.py) 후 Charlie fix 시 일원화"
> > ([`4-3-verification-v1-v4-v7-v8-order.md:694`](4-3-verification-v1-v4-v7-v8-order.md))

**본 스파이크의 목표**: 1회 fix로 Epic 5/6/7/11 audit log 일관성 자산. Charlie 결정 시 인계 가능한 design proposal + migration plan 산출.

---

## 2. Current State — Audit Log Call Site 카탈로그

### 2.1 Core Infrastructure

| Component | Location | Notes |
|---|---|---|
| `emit_audit()` helper | [`apps/api/core/audit.py:24`](../../apps/api/core/audit.py) | `action: str` (free-form) + `target_table: str` + `payload: dict` — **typed contract 부재** |
| `AuditLog` ORM | [`apps/api/core/db_models.py:142-157`](../../apps/api/core/db_models.py) | `action: Mapped[str]` (Text, no CHECK) |
| `audit_logs` table | [`0001_tenants_users_memberships_settings.py:121-132`](../../apps/api/alembic/versions/0001_tenants_users_memberships_settings.py) | `action TEXT NOT NULL` — **DB-side enum constraint 0건** |
| Append-only trigger | `0001_tenants_users_memberships_settings.py:139-162` | UPDATE/DELETE raise — insert는 free-form |
| `CalcLog` model | [`db_models.py:692-726`](../../apps/api/core/db_models.py) | `action: Mapped[str]` + **`CheckConstraint("action IN ('compute', 'idempotent_skip', 'rollback')")`** (line 717-721) — **DB-level enum 잠금 첫 사례** |
| `calc_log` table | [`0012_fiscal_period_snapshots.py:96-107`](../../apps/api/alembic/versions/0012_fiscal_period_snapshots.py) | `action TEXT NOT NULL CHECK (action IN ('compute', 'idempotent_skip', 'rollback'))` |

### 2.2 Audit Log Call Sites (audit_logs — emit_audit)

| # | Story | Module | file:line | `target_table` | `action` value | Notes / Drift reason |
|---|---|---|---|---|---|---|
| 1 | 0.2 | `core/service_role.py` | [107](../../apps/api/core/service_role.py) | `target_table` (param) | `service_role_bypass` | Bypass guard 단일 호출. target_table은 호출 인자 — typed enum 아님 |
| 2 | 1.1 | `m0_onboarding/services/settings_service.py` | [383](../../apps/api/modules/m0_onboarding/services/settings_service.py) | `tenant_settings` | `industry_selected` | **CR 1.1 inversion site** — F-36 fix 후 first-time 분기 |
| 3 | 1.1 | same | [386](../../apps/api/modules/m0_onboarding/services/settings_service.py) | `tenant_settings` | `industry_change_initial` | F-36 fix 후 within-grace 분기 — payload `reason`은 `industry_change_within_grace` (별도 discriminator) |
| 4 | 1.2 | `m0_onboarding/services/settings_service.py` | [561](../../apps/api/modules/m0_onboarding/services/settings_service.py) | `tenant_settings` | `onboarding_field_saved` | fiscal_year_start / currency / language PATCH — payload에 `field` discriminator |
| 5 | 1.2 | same | [644](../../apps/api/modules/m0_onboarding/services/settings_service.py) | `tenant_settings` | `allocation_criterion_saved` | allocation_criteria JSONB 갱신 — payload에 `criterion` discriminator |
| 6 | 1.3 | `m10_ai/service.py` | [280](../../apps/api/modules/m10_ai/service.py) | `uploaded_documents` | `document_uploaded` | 신규 업로드. payload에 `idempotency_key` |
| 7 | 1.3 | same | [422](../../apps/api/modules/m10_ai/service.py) | `uploaded_documents` | `document_reprocess_requested` | reprocess endpoint |
| 8 | 1.3 | same | [524](../../apps/api/modules/m10_ai/service.py) | `input_drafts` | `input_draft_confirm` / `input_draft_reject` | **f-string interpolation** — `f"input_draft_{action}"`. caller (`m10_ai/handlers.py:319`)가 `Literal["confirm","reject"]` (schemas.py:103) 강제하지만 typed contract 0건 |
| 9 | 1.3 | same | [612](../../apps/api/modules/m10_ai/service.py) | `tenant_settings` | `company_subblock_promoted` | **target_table이 tenant_settings지만 `target_id`는 `document_id`** — 기존 m0 onboarding과 다른 의미 (JSONB aggregate partial update) |
| 10 | 1.3 | same | [772](../../apps/api/modules/m10_ai/service.py) | `uploaded_documents` | `document_retention_soft_deleted` | Retention cron. `target_id=rows[0].document_id` — 단일 row audit (count는 payload) |
| 11 | 2.1 | `m1_baseline/services/product_service.py` | [397](../../apps/api/modules/m1_baseline/services/product_service.py) | `products` | `product_created` | 신규 INSERT. changed_fields가 전체 필드 |
| 12 | 2.1 | same | [621](../../apps/api/modules/m1_baseline/services/product_service.py) | `products` | `product_type_changed` / `product_updated` | **conditional ternary** — type-only PATCH → `product_type_changed`, mixed → `product_updated`. changed_fields discriminator |
| 13 | 2.1 | same | [679](../../apps/api/modules/m1_baseline/services/product_service.py) | `products` | `product_soft_deleted` / `product_reactivated` | **conditional ternary** — is_active target 분기 |
| 14 | 2.2 | `m1_baseline/services/bom_service.py` | [487](../../apps/api/modules/m1_baseline/services/bom_service.py) | `bom_lines` | `bom_set` | Bulk replace. payload에 changed_ratios diff |
| 15 | 2.2 | same | [627](../../apps/api/modules/m1_baseline/services/bom_service.py) | `bom_lines` | `bom_cleared` | 전체 BOM DELETE |
| 16 | 3.1 | `m2_input/services/monthly_input_service.py` | [678](../../apps/api/modules/m2_input/services/monthly_input_service.py) | `monthly_input_rows` | `monthly_input_row_updated` | save_row의 update path (CR 1.1 idempotent skip 후) |
| 17 | 3.1 | same | [749](../../apps/api/modules/m2_input/services/monthly_input_service.py) | `monthly_input_rows` | `monthly_input_row_created` | save_row의 INSERT path |
| 18 | 3.1 | same | [839](../../apps/api/modules/m2_input/services/monthly_input_service.py) | `monthly_input_rows` | `monthly_input_row_updated` | **동일 action value 중복** — update_row의 PATCH path (line 678과 의미 동일하지만 별도 분기) |
| 19 | 3.1 | same | [897](../../apps/api/modules/m2_input/services/monthly_input_service.py) | `monthly_input_rows` | `monthly_input_row_deleted` | DELETE |
| 20 | 3.1 | same | [944](../../apps/api/modules/m2_input/services/monthly_input_service.py) | `monthly_input_periods` | `monthly_input_mode_changed` | **target_table이 periods (rows 아님)** — 다른 테이블 audit |
| 21 | 4.2 | `m3_calculate/services/calc_orchestrator.py` | (CalcLog path) | `calc_log` (NOT audit_logs) | `compute` / `idempotent_skip` | **CalcLog 자체 INSERT** — audit_logs와 별도 진화. DB CHECK constraint 3-value enum |
| 22 | 4.2 | same | (CalcLog path) | `calc_log` | `rollback` | engine error / verify-fail 시 (Story 4.3 예정 wire) |

### 2.3 Test Coverage (regression test for inversion)

| Test | Location | 검증 대상 |
|---|---|---|
| `test_service_writes_audit_row_before_settings_update` | [`tests/api/test_industry_selector.py:142-207`](../../tests/api/test_industry_selector.py) | F-36 패치 검증 — `first_added.action == "industry_selected"`, payload `reason == "industry_selected_initial"`, `version == 1` (pre-bump) |
| `test_post_calc_audit_first_commit` (예상) | `tests/api/test_calc_endpoint.py` | calc_log audit-first 순서 검증 (CR 1.1 lesson Epic 4 정착) |

### 2.4 Conventions Document

`docs/conventions.md` 현재 audit 관련 조항:

- §1 Naming — `audit_logs` snake_case 명명 (line 142)
- §4 Errors — AD-2 audit, AD-15 envelope (line 212)
- **§audit 단일 섹션 부재** — 별도 §audit 조항 0건

---

## 3. Drift Matrix — Story × Call Site × Action Value

### 3.1 Action value의 의미 차원

Audit log action은 본질적으로 **3차원 정보**:

| 차원 | 값 예시 | 의미 |
|---|---|---|
| **Verb** (CRUD-lite) | `create` / `update` / `delete` / `soft_delete` / `promote` / `set` / `clear` / `change` / `bypass` / `compute` / `skip` / `rollback` / `verify` / `carry` / `reverse` | 무엇을 했는가 |
| **Subject** (entity) | `industry` / `onboarding_field` / `allocation_criterion` / `document` / `input_draft` / `company_subblock` / `product` / `product_type` / `bom` / `monthly_input_row` / `monthly_input_mode` / `calc_log` / `verification_log` / `inventory_ledger` / `reversal_log` / `service_role` | 어떤 리소스인가 |
| **Context** (lifecycle state) | `initial` / `within_grace` / `soft_deleted` / `reactivated` / `confirm` / `reject` / `pass` / `fail` / `skip` / `idempotent` / `rollback` / `commit` / `reverse` | 어떤 lifecycle 의미인가 |

**현재 free-form string은 이 3차원을 flat string으로 collapse** — 차원 간 boundary가 코드/문서/DB 어느 곳에도 명시되지 않음.

### 3.2 Drift 사례 카탈로그

| Drift 사례 | Story | file:line | 표면 action | 잠재 3차원 분리 |
|---|---|---|---|---|
| industry inversion | 1.1 | settings_service.py:382-387 | `industry_selected` / `industry_change_initial` | verb=`update` (mutation), subject=`industry`, context=`initial` / `within_grace` |
| product PATCH 분기 | 2.1 | product_service.py:611-615 | `product_type_changed` / `product_updated` | verb=`update`, subject=`product` / `product_type`, context=`type_only` / `mixed` |
| product soft-delete toggle | 2.1 | product_service.py:679 | `product_soft_deleted` / `product_reactivated` | verb=`soft_delete` / `reactivate`, subject=`product`, context=None |
| draft confirm/reject | 1.3 | m10_ai/service.py:524 | `input_draft_confirm` / `input_draft_reject` | verb=`confirm` / `reject`, subject=`input_draft` |
| monthly_input CRUD | 3.1 | monthly_input_service.py:678, 749, 839, 897 | `monthly_input_row_{created,updated,deleted}` | verb=`create`/`update`/`delete`, subject=`monthly_input_row` |
| mode toggle | 3.1 | monthly_input_service.py:944 | `monthly_input_mode_changed` | verb=`change`, subject=`monthly_input_mode` (≠ row) |
| calc_log verbs | 4.2 | calc_orchestrator.py:254, 280, 468 | `compute` / `idempotent_skip` / `rollback` | verb=`compute` / `skip` / `rollback`, subject=`calc_log`, context=`success` / `idempotent` / `failure` |
| verification (예정) | 4.3 | 4-3 spec:153 | `verification_passed` / `verification_failed` / `verification_skipped` | verb=`verify`, subject=`verification`, context=`pass` / `fail` / `skip` |

### 3.3 중복 action 사례

- `monthly_input_row_updated` — [`monthly_input_service.py:678`](../../apps/api/modules/m2_input/services/monthly_input_service.py) (save_row update path) **AND** [839](../../apps/api/modules/m2_input/services/monthly_input_service.py) (update_row PATCH path) — 동일 string이지만 두 분기에서 emit. CR 1.1 idempotent skip 후 호출 / PATCH 직접 호출 분리.
- `company_subblock_promoted` vs `onboarding_field_saved` — 동일 `tenant_settings` target이지만 다른 JSONB subkey 갱신 의미.

### 3.4 DRIFT TYPE 분류

| Drift type | 사례 | 영향 |
|---|---|---|
| **A. Inversion (분기 반전)** | Story 1.1 industry_selected ↔ industry_change_initial | semantic invert — analytics 오역 |
| **B. Conditional ternary (action 선택 분기)** | Story 2.1 product_type_changed ↔ product_updated, product_soft_deleted ↔ product_reactivated | string 비교 시 두 분기 모두 cover 필요 — drift 표면 |
| **C. F-string interpolation** | Story 1.3 `input_draft_{action}` | caller가 Literal 강제하지만 typed contract 0건 |
| **D. Cross-table audit (target_table 일관성)** | Story 1.3 `company_subblock_promoted` (tenant_settings) — JSONB aggregate partial update 의미 | 다른 module과 의미 겹침 |
| **E. New table drift (별도 ledger 진화)** | Story 4.2 calc_log, 4.3 verification_log, Epic 5 inventory_ledger, Epic 11 reversal_log | audit_logs와 별개 진화 — DB CHECK constraint로 잠겨 단일 진실 공급원 부재 가속 |

---

## 4. Design Proposal — `apps/api/core/audit_action.py`

### 4.1 설계 원칙

1. **AD-11 hex core 준수** — `packages/cost_engine` 의존 0건 (audit은 infra layer = `apps/api/core/`)
2. **AD-22 append-only-leaning 유지** — 기존 trigger 기반 UPDATE/DELETE 차단 그대로
3. **typed literal + DB enum CHECK 동시 잠금** — Python side에서 Literal/mypy + DB CHECK constraint 양쪽 동기화
4. **점진적 도입 (migration-friendly)** — 기존 string literal 100% 호환 + 신규 신규 enum 추가 가능

### 4.2 단일 진실 공급원 — `apps/api/core/audit_action.py` 구조

```python
# apps/api/core/audit_action.py (proposed)
"""apps.api.core.audit_action — single source of truth for audit log actions.

CR 1.1 lesson (Epic 4 close-out A5 spike) — Epic 1·2·3·4 4번째 epic 연속
recurred. Action values were typed as free-form `str` literals scattered
across 17+ call sites. This module centralizes:

1. ActionClass — the audit target class (which table / aggregate)
2. AuditAction — the typed verb-subject-context union per ActionClass
3. AuditLogType — the destination ledger (audit_logs / calc_log / verification_log /
   inventory_ledger / reversal_log)
4. Helper functions — emit_audit_with_class(...) that wires (ActionClass, AuditAction)
   to the correct destination table

Per AD-11: this module is in `apps/api/core/` (infra layer). It does NOT
import `packages.cost_engine` directly.

Per AD-22: append-only-leaning preserved. Triggers in migration 0001 still
block UPDATE/DELETE on audit_logs.
"""

from __future__ import annotations

import enum
import uuid
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession


# ────────────────────────────────────────────────────────────
# 1. ActionClass — the target class (which table / aggregate)
# ────────────────────────────────────────────────────────────
class ActionClass(str, enum.Enum):
    """Audit target class. One enum value per logical target.

    Order = introduction order. Do NOT renumber — append-only.
    """
    TENANT_SETTINGS = "tenant_settings"
    SERVICE_ROLE = "service_role"
    UPLOADED_DOCUMENT = "uploaded_document"
    INPUT_DRAFT = "input_draft"
    PRODUCT = "product"
    BOM_LINE = "bom_line"
    MONTHLY_INPUT_ROW = "monthly_input_row"
    MONTHLY_INPUT_PERIOD = "monthly_input_period"
    CALC_LOG = "calc_log"
    VERIFICATION_LOG = "verification_log"     # Story 4.3 (NEW)
    INVENTORY_LEDGER = "inventory_ledger"     # Epic 5 (NEW)
    REVERSAL_LOG = "reversal_log"             # Epic 11 (NEW)


# ────────────────────────────────────────────────────────────
# 2. AuditLogType — destination ledger discriminator
# ────────────────────────────────────────────────────────────
AuditLogType = Literal[
    "audit_logs",
    "calc_log",
    "verification_log",
    "inventory_ledger",
    "reversal_log",
]


# ────────────────────────────────────────────────────────────
# 3. AuditAction — typed literal per ActionClass
# ────────────────────────────────────────────────────────────
# tenant_settings actions (m0_onboarding + m10_ai company_subblock)
TenantSettingsAction = Literal[
    "industry_selected",            # AC #1 first-time
    "industry_change_initial",      # AC #4 within-grace
    "onboarding_field_saved",       # Story 1.2 fiscal_year_start / currency / language
    "allocation_criterion_saved",   # Story 1.2 allocation_criteria JSONB
    "company_subblock_promoted",    # Story 1.3 confirmed drafts → tenant_settings JSONB
]

# service_role action
ServiceRoleAction = Literal[
    "service_role_bypass",          # AD-2 audit-first guard
]

# uploaded_document actions (m10_ai)
UploadedDocumentAction = Literal[
    "document_uploaded",
    "document_reprocess_requested",
    "document_retention_soft_deleted",
]

# input_draft actions (m10_ai)
InputDraftAction = Literal[
    "input_draft_confirm",
    "input_draft_reject",
]

# product actions (m1_baseline)
ProductAction = Literal[
    "product_created",
    "product_updated",              # mixed PATCH
    "product_type_changed",         # type-only PATCH (Story 2.3)
    "product_soft_deleted",
    "product_reactivated",
]

# bom_line actions (m1_baseline)
BOMLineAction = Literal[
    "bom_set",                      # bulk replace
    "bom_cleared",
]

# monthly_input_row actions (m2_input)
MonthlyInputRowAction = Literal[
    "monthly_input_row_created",
    "monthly_input_row_updated",    # both save_row update + update_row PATCH
    "monthly_input_row_deleted",
]

# monthly_input_period actions (m2_input)
MonthlyInputPeriodAction = Literal[
    "monthly_input_mode_changed",
]

# calc_log actions (m3_calculate) — DB CHECK constraint applied (0012)
CalcLogAction = Literal[
    "compute",
    "idempotent_skip",
    "rollback",
]

# verification_log actions (Story 4.3 NEW)
VerificationLogAction = Literal[
    "verification_passed",
    "verification_failed",
    "verification_skipped",
]

# inventory_ledger actions (Epic 5 NEW — design-only)
# TODO(epic-5): FILL_INVENTORY_LEDGER_ACTIONS when m4_inventory module ships
InventoryLedgerAction = Literal[
    # "ledger_created",            # m4_inventory TBD
    # "ledger_reversed",           # m4_inventory TBD
    # "carry_forward",             # opening_inventory auto-carry
]

# reversal_log actions (Epic 11 NEW — design-only)
# TODO(epic-11): FILL_REVERSAL_LOG_ACTIONS when m11_reversal module ships
ReversalLogAction = Literal[
    # "commit",
    # "reverse",
    # "re_reverse",
]


# Union type for type checking
AuditAction = (
    TenantSettingsAction
    | ServiceRoleAction
    | UploadedDocumentAction
    | InputDraftAction
    | ProductAction
    | BOMLineAction
    | MonthlyInputRowAction
    | MonthlyInputPeriodAction
    | CalcLogAction
    | VerificationLogAction
    | InventoryLedgerAction
    | ReversalLogAction
)


# ────────────────────────────────────────────────────────────
# 4. Mapping table — ActionClass → AuditLogType + accepted actions
# ────────────────────────────────────────────────────────────
class _ActionRegistry:
    """Internal registry — (ActionClass, AuditAction) → AuditLogType.

    Used by `emit_audit_typed()` to validate action against ActionClass
    and route to the correct destination table.
    """

    _REGISTRY: dict[ActionClass, tuple[AuditLogType, frozenset[str]]] = {
        ActionClass.TENANT_SETTINGS: ("audit_logs", frozenset(
            {"industry_selected", "industry_change_initial",
             "onboarding_field_saved", "allocation_criterion_saved",
             "company_subblock_promoted"}
        )),
        ActionClass.SERVICE_ROLE: ("audit_logs", frozenset({"service_role_bypass"})),
        ActionClass.UPLOADED_DOCUMENT: ("audit_logs", frozenset(
            {"document_uploaded", "document_reprocess_requested",
             "document_retention_soft_deleted"}
        )),
        ActionClass.INPUT_DRAFT: ("audit_logs", frozenset(
            {"input_draft_confirm", "input_draft_reject"}
        )),
        ActionClass.PRODUCT: ("audit_logs", frozenset(
            {"product_created", "product_updated", "product_type_changed",
             "product_soft_deleted", "product_reactivated"}
        )),
        ActionClass.BOM_LINE: ("audit_logs", frozenset({"bom_set", "bom_cleared"})),
        ActionClass.MONTHLY_INPUT_ROW: ("audit_logs", frozenset(
            {"monthly_input_row_created", "monthly_input_row_updated",
             "monthly_input_row_deleted"}
        )),
        ActionClass.MONTHLY_INPUT_PERIOD: ("audit_logs", frozenset(
            {"monthly_input_mode_changed"}
        )),
        ActionClass.CALC_LOG: ("calc_log", frozenset(
            {"compute", "idempotent_skip", "rollback"}
        )),
        ActionClass.VERIFICATION_LOG: ("verification_log", frozenset(
            {"verification_passed", "verification_failed", "verification_skipped"}
        )),
        # Epic 5 / Epic 11 placeholder — empty until module ships
        ActionClass.INVENTORY_LEDGER: ("inventory_ledger", frozenset()),
        ActionClass.REVERSAL_LOG: ("reversal_log", frozenset()),
    }

    @classmethod
    def validate(cls, *, action_class: ActionClass, action: str) -> AuditLogType:
        """Return destination ledger for (action_class, action). Raise if invalid."""
        if action_class not in cls._REGISTRY:
            raise ValueError(
                f"audit_action: unknown ActionClass {action_class!r}. "
                f"Add to _REGISTRY in apps/api/core/audit_action.py"
            )
        log_type, accepted = cls._REGISTRY[action_class]
        if action not in accepted:
            raise ValueError(
                f"audit_action: action {action!r} is not in ActionClass "
                f"{action_class.value!r}. Accepted: {sorted(accepted)}. "
                f"This is the CR 1.1 lesson — free-form string drift is forbidden."
            )
        return log_type


# ────────────────────────────────────────────────────────────
# 5. Helper — typed emit_audit wrapper
# ────────────────────────────────────────────────────────────
async def emit_audit_typed(
    session: AsyncSession,
    *,
    action_class: ActionClass,
    action: AuditAction,
    actor_id: uuid.UUID | None,
    target_id: uuid.UUID | None = None,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
    tenant_id: uuid.UUID | None = None,
    flush: bool = True,
) -> None:
    """Typed emit_audit wrapper. Routes to correct destination ledger.

    Args:
        action_class: Which target class (CR 1.1 single source of truth).
        action: Typed action literal. Must match action_class's accepted set.
        actor_id, target_id, reason, payload, tenant_id, flush:
            Same semantics as emit_audit (apps/api/core/audit.py).

    Raises:
        ValueError: If action not in action_class's accepted set.

    Example:
        await emit_audit_typed(
            session,
            action_class=ActionClass.TENANT_SETTINGS,
            action="industry_selected",
            actor_id=actor_id,
            target_id=tenant_id,
            payload={...},
            tenant_id=tenant_id,
        )
    """
    log_type = _ActionRegistry.validate(action_class=action_class, action=action)

    if log_type == "audit_logs":
        # delegate to existing emit_audit (apps/api/core/audit.py)
        from apps.api.core.audit import emit_audit
        await emit_audit(
            session,
            actor_id=actor_id,
            action=action,
            target_table=action_class.value,
            target_id=target_id,
            reason=reason,
            payload=payload or {},
            tenant_id=tenant_id,
            flush=flush,
        )
    elif log_type == "calc_log":
        # delegate to CalcLog insert path (m3_calculate/services/calc_orchestrator.py)
        # Note: this should call _write_calc_log via the orchestrator, not here.
        # This branch documents intent — actual wiring is the module's
        # responsibility. Story 4.3 + Epic 5 fill-in.
        raise NotImplementedError(
            f"audit_action: calc_log destination is wired through "
            f"CalcOrchestrator._write_calc_log — call site is "
            f"apps/api/modules/m3_calculate/services/calc_orchestrator.py"
        )
    elif log_type in ("verification_log", "inventory_ledger", "reversal_log"):
        # Story 4.3 / Epic 5 / Epic 11 deferred — table not shipped yet.
        # emit_audit_typed is design-only for these classes (TODO markers).
        raise NotImplementedError(
            f"audit_action: {log_type!r} table not yet shipped — "
            f"see Story 4.3 / Epic 5 / Epic 11 spec for wire contract."
        )
```

### 4.3 결정 사항 — cj-style defaults (Charlie 결정 필요)

| 결정 항목 | cj-style default (권고) | rationale |
|---|---|---|
| **ActionClass vs free-form** | ActionClass enum 강제 | 기존 free-form 17+ call sites 전부 typed wrapper로 migrate |
| **Migration 시 기존 string 호환** | 호환 (str-based fallback deprecated, no warning) | Story 1.1 회귀 테스트 0건 |
| **DB CHECK constraint 추가** | Phase 2 (calc_log → verification_log 순) | 0001 migration에 audit_logs CHECK 추가는 down-grade 위험 — 신규 table부터 |
| **Epic 5 inventory_ledger wire 시점** | Epic 5 spec 진입 시 `audit_action.INVENTORY_LEDGER` registry 채우기 | 본 스파이크 결정 후 m4_inventory spec에 명시 |
| **Epic 11 reversal_log wire 시점** | Epic 11 spec 진입 시 `audit_action.REVERSAL_LOG` registry 채우기 | 본 스파이크 결정 후 m11_reversal spec에 명시 |
| **Conventions 문서 위치** | `docs/conventions.md` §10 신규 섹션 "Audit Actions" | Epic 4 close-out 시 추가 |

### 4.4 의도적 미포함

- **Dynamic action interpolation (`input_draft_{confirm,reject}`)** — typed Literal로 분리. caller에서 `Literal["confirm","reject"]` 강제 + service에서 `AuditAction` 변환.
- **payload 내 reason discriminator** (`industry_selected_initial` / `industry_change_within_grace`) — payload 내 free-form string으로 유지. action literal과 분리되어 analytics granularity 보존.
- **`service_role_bypass` payload schema** — 본 스파이크 scope 외. AD-2 + AD-3 정합성 검증 필요 시 별도 스파이크.

---

## 5. Migration Plan — 4-Phase Rollout

### Phase 1: `audit_action.py` 도입 + 호출 사이트 typed wrapper로 migrate (no behavior change)

**Scope**: 22 call sites (audit_logs 17 + CalcLog 3 + test 2) 전부 `emit_audit_typed()` 또는 동등 wrapper로 교체. **DB schema 변경 없음.**

| Task | Owner | Estimated | Risk |
|---|---|---|---|
| 1.1 `apps/api/core/audit_action.py` 작성 | Charlie | 1h | Low — 신규 파일, 기존 emit_audit 보존 |
| 1.2 17 audit_logs call sites wrapper로 migrate (m0/m1/m2/m10) | Amelia | 2h | Medium — F-36 inversion 회귀 테스트 0건 깨뜨리지 않게 |
| 1.3 3 calc_log call sites에 `_ActionRegistry.validate()` 호출 추가 (no behavior change, just guard) | Amelia | 0.5h | Low — DB CHECK constraint와 별개 validate layer |
| 1.4 test_industry_selector.py + test_calc_endpoint.py 회귀 0건 검증 | Dana | 0.5h | Low — 기존 test로 cover |
| 1.5 `docs/conventions.md` §10 "Audit Actions" 신규 섹션 추가 | Charlie + Tech Writer | 0.5h | Low |

**Rollback**: 신규 파일 + call site 교체 → git revert. DB 변경 0건이라 rollback 안전.

### Phase 2: DB CHECK constraint 추가 — 신규 ledger부터 (verification_log, inventory_ledger)

**Scope**: Story 4.3의 `verification_log` 신규 table과 Epic 5의 `inventory_ledger` 신규 table에 Alembic 0013+에서 `CHECK (action IN (...))` 추가. 기존 `audit_logs` / `calc_log`에는 CHECK 추가하지 않음 (down-grade 위험).

| Task | Owner | Estimated | Risk |
|---|---|---|---|
| 2.1 Alembic 0013 — `verification_log` table + CHECK constraint (Story 4.3 commit 안에) | Amelia | Story 4.3 scope | Medium — Story 4.3 spec OQ3 결정 |
| 2.2 Alembic 0014+ — `inventory_ledger` table + CHECK constraint (Epic 5 spec 진입 시) | Amelia | Epic 5 scope | Low — 신규 table |
| 2.3 Alembic 0015+ — `reversal_log` table + CHECK constraint (Epic 11 spec 진입 시) | Amelia | Epic 11 scope | Low — 신규 table |

**Rollback**: Alembic downgrade path 명시. CHECK constraint는 table-level이 아닌 column-level로 두면 drop이 용이.

### Phase 3: 기존 audit_logs / calc_log에 점진적 CHECK 추가 (data-driven)

**Scope**: Production data에 등장한 action value만 enum에 포함. 미사용 value는 NOT included. 기존 데이터 0건인 경우에만 drop-and-recreate 가능한 시점에 CHECK 추가.

| Task | Owner | Estimated | Risk |
|---|---|---|---|
| 3.1 Production data 분석 — `SELECT DISTINCT action FROM audit_logs` + `calc_log` | Amelia + Dana | 1h | Low — read-only query |
| 3.2 등장 value set과 registry set 비교 | Amelia | 0.5h | Low — diff report |
| 3.3 등장 set만으로 Alembic CHECK 추가 (down-grade script 포함) | Amelia + Charlie | 2h | **High** — production data 영향. dev/staging 먼저 dry-run |
| 3.4 CI 검증: `emit_audit_typed()` registry와 DB CHECK constraint 동등성 보장 | Dana | 1h | Medium — drift detector 신규 |

**Rollback**: Alembic downgrade로 CHECK drop. 기존 string INSERT는 OK (CHECK 없으면 모두 허용). 단, 코드 측에서 reject 시작 → production error 가능. **이 Phase는 Epic 5+ production data 누적 후 실행 권고** (현재 2026-08-03 시점 production data ~0).

### Phase 4: Conventions lint + drift detector (enforcement)

**Scope**: `tests/integration/test_audit_action_consistency.py` 신규 — registry ↔ DB CHECK ↔ call sites 3-way drift 차단. `docs/conventions.md` §10 lint 추가.

| Task | Owner | Estimated | Risk |
|---|---|---|---|
| 4.1 `tests/integration/test_audit_action_consistency.py` 작성 — 3-way 검증 (registry vs DB vs code) | Dana + Amelia | 2h | Low |
| 4.2 `scripts/check_audit_actions.py` 신규 — make lint-conventions 통합 | Charlie | 1h | Low |
| 4.3 `docs/conventions.md` §10 + Story 0.4 chunk-B lint 패턴 차용 | Charlie + Tech Writer | 0.5h | Low |
| 4.4 CR 0.4 chunk-patch disable 위치 명시 (engine purity AST guard 와 동일 패턴) | Amelia | 0.5h | Low |

**Rollback**: 신규 lint script — git revert.

---

## 6. Open Questions (cj-style defaults + Charlie 결정 필요)

| # | Open question | cj-style default | Charlie 결정 필요 |
|---|---|---|---|
| OQ1 | `audit_action.py` 위치 — `apps/api/core/` vs `packages/services/audit/`? | `apps/api/core/audit_action.py` | AD-11 hex core vs `packages/services` layer 경계 — Charlie 결정 |
| OQ2 | `ActionClass` granularity — `MONTHLY_INPUT_ROW` vs `MONTHLY_INPUT_PERIOD` 분리? | 분리 유지 (line 20 참조) | row vs period 의미 차이 분명 — 유지 권고. 단일 class도 가능 |
| OQ3 | `tenant_settings` target table이 단일 class 안에서 multi-subject (industry/onboarding_field/allocation_criterion/company_subblock) — 추가 분리? | 단일 class 유지 | company_subblock는 m10_ai 모듈 — owner 분리 가능. cj-default: 단일 class |
| OQ4 | f-string interpolation (`input_draft_{action}`) typed Literal 직접 분리? | 분리 (`input_draft_confirm` / `input_draft_reject`) | service에서 Literal→action 변환 시 mapping dict 노출 필요 |
| OQ5 | Epic 5 inventory_ledger action value 선 정의? | `ledger_created` / `ledger_reversed` / `carry_forward` placeholder | Epic 5 spec 진입 시 확정. 본 스파이크는 registry slot만 생성 |
| OQ6 | Epic 11 reversal_log action value 선 정의? | `commit` / `reverse` / `re_reverse` placeholder | Epic 11 spec 진입 시 확정. 본 스파이크는 registry slot만 생성 |
| OQ7 | Conventions §10 lint — `tests/integration/test_audit_action_consistency.py` 만으로 충분? | 충분 (3-way drift detector 포함) | Story 0.4 chunk-B AST guard 와 중복 가능성 — review 후 |
| OQ8 | `emit_audit` (기존 free-form) deprecation 시점? | Phase 4 시작 시 `DeprecationWarning` + 신규 code path 강제 | 기존 call site 17+ migrate 완료 후. Phase 1 완료 시점 |
| OQ9 | `service_role_bypass` payload schema 표준화? | 본 스파이크 scope 외 | AD-2 + AD-3 정합성 검증 별도 스파이크 필요 |
| OQ10 | payload `reason` field vs `action` literal 의미 중복? | 의미 중복 허용 (reason = compound discriminator, action = high-level verb) | Epic 1~4 사례로 검증된 패턴 — 유지 |
| OQ11 | Story 4.3 verification_log spec에서 이 spike 결과 즉시 적용? | 예 (Story 4.3 commit 안에 audit_action.py 포함) | Story 4.3 spec OQ5 결정 — Charlie 즉시 결정 필요 |
| OQ12 | Epic 5 inventory_ledger spec 진입 시 audit_action.py를 import할지? | 예 (registry slot pre-fill) | m4_inventory spec 진입 시점에 TODO(epic-5) marker 채우기 |

---

## 7. 결정 사항 (본 스파이크 close-out 시 Charlie 확정 필요)

1. **본 스파이크는 design-only로 종료** — 구현은 Story 4-3 commit 안에 Phase 1+2 포함 (Amelia). Phase 3+4는 Epic 5 spec 진입 시.
2. **`apps/api/core/audit_action.py` 위치 확정** — OQ1 결정 필요.
3. **Phase 1+2 즉시 착수 가능** — Story 4-3 spec에서 verification_log 신규 table에 CHECK constraint 추가 (Epic 4 close-out 시점에 첫 wire 사례).
4. **Epic 5 carry-over TODO marker** — `packages/services/m4_inventory/` 진입 시 audit_action.py registry 채우기 명시.

---

## 8. 참고 자료

| Resource | Location | 비고 |
|---|---|---|
| CR 1.1 lesson | [`.claude/projects/.../cr-1-1-lessons.md`](../../../Users/c8rom/.claude/projects/C--Users-c8rom-desktop-costmgr/memory/cr-1-1-lessons.md) | Story 1.1 review의 close-out 교훈 |
| Epic 4 retro | [`_bmad-output/.../epic-4-retro-2026-08-03.md`](epic-4-retro-2026-08-03.md) §3 C2 + §7 A5 + §11.2 |
| Story 4.3 spec | [`_bmad-output/.../4-3-verification-v1-v4-v7-v8-order.md`](4-3-verification-v1-v4-v7-v8-order.md) | OQ5 + AC #9 |
| Story 4.2 spec | [`_bmad-output/.../4-2-single-calculation-endpoint-repeatable-read-transaction.md`](4-2-single-calculation-endpoint-repeatable-read-transaction.md) | calc_log audit-first 패턴 |
| Story 1.1 spec | [`_bmad-output/.../1-1-industry-selector-menu-auto-toggle.md`](1-1-industry-selector-menu-auto-toggle.md) line 518 | F-36 close-out inversion fix 메모 |
| Story 1.1 diff | [`_bmad-output/.../.review/story-1-1.diff`](.review/story-1-1.diff) line 874, 2554 | CR 1.1 lesson origin |
| Test regression | [`tests/api/test_industry_selector.py:142-207`](../../tests/api/test_industry_selector.py) | audit-action inversion 회귀 테스트 |
| Core infra | [`apps/api/core/audit.py`](../../apps/api/core/audit.py) + [`apps/api/core/db_models.py:142-157`](../../apps/api/core/db_models.py) | emit_audit + AuditLog ORM |
| CalcLog model | [`apps/api/core/db_models.py:692-726`](../../apps/api/core/db_models.py) + [`0012_fiscal_period_snapshots.py`](../../apps/api/alembic/versions/0012_fiscal_period_snapshots.py) | DB CHECK constraint 첫 사례 |

---

## 9. 시간 산정 (4-8h scope)

| Phase | Task | Estimated |
|---|---|---|
| 0 | 본 스파이크 작성 (research + design proposal) | **1.5h (본 문서)** |
| 1 | Phase 1 — audit_action.py + call sites migrate | 4.5h (Story 4-3 commit 안에) |
| 2 | Phase 2 — verification_log CHECK constraint | Story 4-3 scope (별도) |
| 3 | Phase 3 — 기존 audit_logs CHECK (data-driven) | Epic 5 spec 진입 시 별도 (production data 누적 후) |
| 4 | Phase 4 — Conventions lint + drift detector | 4h (Epic 5 spec 진입 시 별도) |

**총 4-8h scope = 본 스파이크 (1.5h) + Phase 1 (4.5h) + Phase 2 (Story 4-3 scope)**. Phase 3+4는 Epic 5 spec 진입 시 별도 예산.

---

## 10. Charlie 결정 체크리스트 (Epic 4 close-out 시)

- [ ] OQ1: `audit_action.py` 위치 — `apps/api/core/` 확정
- [ ] OQ2: ActionClass granularity — row/period 분리 유지 확정
- [ ] OQ3: tenant_settings 단일 class 유지 vs 분리
- [ ] OQ4: input_draft f-string → typed Literal 분리
- [ ] OQ11: Story 4.3 spec에서 본 스파이크 결과 즉시 적용 (verification_log 신규 table + CHECK constraint)
- [ ] Phase 1 즉시 착수 승인 (Story 4-3 commit 안에 audit_action.py + 22 call sites migrate)
- [ ] Epic 5 spec 진입 시 audit_action.py registry pre-fill (TODO(epic-5) marker 4곳)
- [ ] Epic 11 spec 진입 시 audit_action.py registry pre-fill (TODO(epic-11) marker)
- [ ] `docs/conventions.md` §10 "Audit Actions" 섹션 신규 추가 (Tech Writer와 협업)
- [ ] `tests/integration/test_audit_action_consistency.py` 3-way drift detector (Dana + Amelia)
- [ ] Epic 4 close-out retro §A5 follow-through에 본 스파이크 결과 명시
