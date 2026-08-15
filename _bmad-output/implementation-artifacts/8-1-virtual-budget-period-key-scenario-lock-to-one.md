---
title: 'Epic 8 Story 1 — Virtual Budget Period Key + Scenario Lock to One (예산 가상 기간 키 YYYY-MM#B1 + 시나리오 1개 잠금)'
status: ready-for-dev
priority: HIGH
epic: 8
story_num: 1
story_key: 8-1-virtual-budget-period-key-scenario-lock-to-one
baseline_commit: a63646c
created: 2026-08-15
updated: 2026-08-15
---

> **2026-08-15 — bmad-create-story spec 진입 done** (8-1: backlog → ready-for-dev). **Epic 8 진입 첫 스토리** (cj-style 3-story 분할 7번째 epic 연속 검증 — Epic 4·5·6·11·12 + Epic 11/12 carry-over + Epic 7). 8-1 (Virtual Budget Period Key + Scenario Lock to One) / 8-2 (Budget vs Actual Variance Table with ABCD Gray Badge) / 8-3 (Budget Pre-Standard Cost Preview) — **PRD §F8.1 + §F8.2 verbatim + 8-3 그대로** (Epic 7 retro §7 A20 결정).
>
> **baseline_commit = `a63646c`** (Story 12.3 T7 follow-up sprint + Epic 12 진짜 close-out tip — current HEAD).
>
> **A19 carry-over sprint DONE** (2026-08-15) — Epic 6 retro §7 A8 inline projection deprecate 완료 + `packages/services/m2_input/inventory_math.py` math surface 마이그레이션 완료. **Epic 7 spec 진입 완료** (7-1 + 7-2 ready-for-dev) + **Epic 8 진입 gate clear**.
>
> **Three user decisions locked** (2026-08-15):
> 1. **순수 엔진 함수 surface = `packages/cost_engine/budget_period_key.py`** (stdlib-only AD-5 purity) — `derive_budget_period_key(*, real_period_key: str, scenario_index: int = 1) -> str` + `parse_virtual_budget_period_key(*, period_key: str) -> BudgetPeriodKeyParts` (frozen dataclass with `real_period_key` + `scenario_index` + `scenario_suffix`) + `validate_scenario_uniqueness(*, existing_count: int) -> None` (raises `ScenarioLimitExceededError` if `existing_count >= 1`) + `compute_budget_scenario_hash(*, scenario: BudgetScenario) -> str` for V8 determinism (4 NEW pure functions + 3 frozen dataclasses). **DB / clock / random / I/O 일체 없음** (AD-5 + AD-11 layer rule + import-linter 2 KEPT contracts 유지). **`packages/cost_engine/budget_period_key.py` 와 `packages/cost_engine/cvp.py` (7-1) + `packages/cost_engine/projection.py` (7-2) surface 분리** (A19 cohesion pattern 3번째 검증).
> 2. **Scenario Lock 1차 MVP = 1개 only** (PRD §F8.1 verbatim + NON-GOAL for MVP #2 §15 명시) — `existing_count >= 1` 시 `ScenarioLimitExceededError` raise + ko-KR 메시지 "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)" — 2차 multi-scenario 비교는 `Story 8-2 honestly DEFER (b)` (A20 결정).
> 3. **Capability gate = 신규 `Capability.BUDGET_SCENARIO`** — manufacturing 3종 ✅ / service-only ✅ (전 industry 공통, 12-1 L4 precedent — "budget scenario는 tenant-level 재무 baseline"). **`apps/api/core/capability.py` 추가** + **`apps/api/modules/m8_budget/` module authority populate** (현재 `__init__.py` placeholder만 존재).
>
> **cj-style 3-story 분할 7번째 epic 연속 검증** + **CR 11-3 honest-DEFER discipline 11번째 epic 연속** (atomic wire만, partial wire 0).
>
> **CR 11-3 lessons carry-over**: D-2 (ALLOWED_SERVICE_SUBMODULES 즉시 sweep — `packages.services.m8_budget.budget_period_key_serializers` 추가) + ruff auto-fix sweep (CR 11-3 D-3) + SDR separate line parser (CR 11-2 lesson) + `def test_+asyncio.run` project convention (CR 4-3).
>
> **CR 11-4 lessons carry-over**: D-001 (page.tsx mount MUST actually mount `<BudgetScenarioList>` JSX) + D-002 (단일 `apps/web/messages/ko-KR.json` only) + D-005 (TS mirror unknown state fall-through → reject) + P-015 (ko-KR.json SSOT drift detector test).
>
> **CR 12-1 lessons continue applied**: L1 (PyJWT `verify_exp=False` deterministic testability — N/A for 8-1, no token) + L2 (AES-256-GCM lazy wrapper — N/A for 8-1, no PII) + L3 (`_to_budget_scenario_state(orm_row)` ORM→kernel boundary conversion) + L4 (BUDGET_SCENARIO capability industry-agnostic precedent — 12-1 CVP_SIMULATION + 7-1/7-2 industry-agnostic 동일 적용).
>
> **CR 12-5 lessons continue applied**: D-13 (cross-language drift detector pattern) + D-14 (typed exception main.py envelope handler 등록 — `ScenarioLimitExceededError` 409 + `InvalidVirtualBudgetPeriodKeyError` 422 + `BudgetScenarioNotFoundError` 404) + L3 (3-layer defense — route `@require_role("owner")` + service `validate_scenario_uniqueness` + audit-first emit, 8-1은 read-mostly지만 scenario 생성은 destructive-write) + L4 (honest-DEFER discipline).
>
> **A19 lessons carry-over**: math surface migration pattern (CR A19 NEW) + `packages/services/m2_input/inventory_math.py` precedent. 8-1은 **`packages/cost_engine/budget_period_key.py`** (cost_engine surface — Epic 4 pure calc engine + 7-1 cvp.py + 7-2 projection.py 동일 layer), `packages/services/m8_budget/` 는 service layer (orchestration 없이 thin wrappers).
>
> **Honestly DEFER (per CR 11-3 11번째 epic 연속, partial wire 아님)**:
> - **복수 시나리오 비교 (B2, B3, …)** — 1차 MVP NON-GOAL #2 §15 verbatim (≥5 테넌트 요청 시 trigger). `Story 8-2 honestly DEFER (b)`.
> - **A×B×C×D 차이 분석 엔진** — 1차 MVP NON-GOAL #1 §15 verbatim. `Story 8-2 honestly DEFER (c)` (회색 배지로 placeholder).
> - **AI 추천 예산 (F10.1 input_drafts)** — Epic 10 carry-over, 8-1 scope OUTSIDE.
> - **차월 projection과 budget scenario 연동** — Story 7-2 honestly DEFER (b) 결정 ("2026-08#P1" virtual projection key) + 8-2 honestly DEFER.
> - **Pre-standard cost preview (`engine_type='budget'`)** — Story 8-3 결정 (cj-style 3번째).
> - **Playwright E2E** — 12-5 T6 패턴, follow-up sprint (8-1 honestly DEFER #6).
> - **TS mirror cross-language drift detector test** — sprint-scale (parity test 5~10 cases로 atomic wire, honestly DEFER #7).

# Story 8.1 — Virtual Budget Period Key + Scenario Lock to One

## Epic 8 context

**Epic 8 (Budget vs Actual)** cj-style 3-story 분할 진입 (Epic 4·5·6·11·12 + Epic 11/12 carry-over + Epic 7 검증 패턴 7번째 epic):

- **8-1** = Virtual Budget Period Key + Scenario Lock to One (PRD §F8.1 + AD-24 period key + 1차 시나리오 1개 잠금) ← **이 스토리** (backlog → ready-for-dev)
- **8-2** = Budget vs Actual Variance Table with ABCD Gray Badge (PRD §F8.2 + 차이율 ±5% yellow / ±10% red + A×B×C×D 회색 배지)
- **8-3** = Budget Pre-Standard Cost Preview (`engine_type='budget'` + `fiscal_period_snapshots` reuse)

**Epic 8 모듈 authority**: `apps/api/modules/m8_budget/` (현재 `__init__.py` placeholder만 존재, 본 스토리에서 populate). 11-1 m11_close / 12-1 m12_account / 7-1 m7_simulation 패턴 미러.

**Epic 8 capability matrix wire**: v1.17 `BUDGET_SCENARIO` 신규 (manufacturing 3종 ✅ + service-only ✅ = industry-agnostic, 12-1 L4 precedent + 7-1/7-2 동일 적용).

**Epic 8 NFR coverage**: NFR16 (엔진 순수성 — AD-5) + NFR17 (monetary types — AD-8) + NFR18 (ko-KR MVP lock).

**NON-GOAL for MVP 명시** (§15 PRD verbatim):
- 복수 예산 시나리오 (1차 = 1개, 2차 = 복수 예정, trigger: ≥5 테넌트 요청 시)
- A×B×C×D 차이 분석 (1차 = 회색 배지 placeholder, 2차 = 산식 보존)

## Why this story (atomic wire 결정 근거)

**PRD §F8.1 verbatim**: "1차 시나리오 1개만 허용 + 2개 이상 생성 시도 차단."

**epics.md Story 8.1 AC verbatim** (lines 970-976):
> **Given** 나는 [예산] → [신규 시나리오] 클릭
> **When** "예산 시나리오 1"을 만들고 추가로 "예산 시나리오 2" 만들기를 시도
> **Then** 2번째 시나리오 생성은 거부되고 "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)" 메시지
> **And** 첫 시나리오는 `period_key = "2026-07#B1"`로 저장
> **And** M8만 virtual key 발급, M11 close는 fiscal key만 잠금

**AD-24 Period Keys** (`docs/conventions.md#§6-Period-Keys-(AD-24)`):
- Real (실측 월) = `YYYY-MM` (예: `2026-07`)
- Virtual (예산 시뮬레이션) = `YYYY-MM#B<n>` (예: `2026-07#B1`, `2026-07#B2`)
- `#B<n>` = 같은 real 월 안에서 여러 가상 예산을 구분
- 비교 시 `period_key` 전체를 문자열로 비교
- **M8만 virtual key 발급, M11 close는 fiscal key만 잠금** (Story 8.1 명시 책임 분리)

**3 second-order decisions** (locked 2026-08-15):

1. **Pure kernel = `packages/cost_engine/budget_period_key.py`** (Epic 4 cost_engine surface + 7-1 cvp.py + 7-2 projection.py 패턴 미러): AD-5 (엔진 순수성) + AD-11 layer rule + A19 math surface migration 패턴 (3번째 분리 surface — concern 별도). **`packages/cost_engine/` 가 SSOT** (Story 4-1 spec 확정). `packages/services/m8_budget/` 는 thin orchestration wrappers (CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep 즉시). **stdlib-only**: `import decimal, dataclasses, math, hashlib, re, typing` only (no sqlalchemy, no datetime.now, no random).

2. **Scenario Lock 1차 MVP = 1개 only** (PRD §F8.1 verbatim + §15 NON-GOAL #2): `existing_count >= 1` 시 `ScenarioLimitExceededError` raise → ko-KR 메시지 "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)" (CR 11-3 D-14 envelope main.py handler 등록 → HTTP 409 SCENARIO_LIMIT_EXCEEDED). **2차 multi-scenario 비교는 honestly DEFER** (Story 8-2 DEFER (b) 명시).

3. **Capability gate = `Capability.BUDGET_SCENARIO` industry-agnostic** (12-1 L4 precedent + 7-1/7-2 동일 적용): `manufacturing` / `manufacturing_with_trading` / `manufacturing_with_service` / `service_only` 모두 ✅ grant. `apps/api/core/capability.py` 추가 + `apps/api/modules/m8_budget/handlers.py` `@require_capability(BUDGET_SCENARIO)` decorator + `require_role("owner", "member")` (AD-10 — scenario 생성은 owner + member, viewer는 read-only).

**+ Epic 8 close-out path**: 8-1 done 진입 후 8-2 spec 진입 (cj-style 2번째) → 8-3 spec 진입 (cj-style 3번째).

## User Story

As a **사장님**,
I want **예산을 "2026-07#B1" 같은 가상 기간 키로 입력하고 1차 시나리오를 1개만 만들 수 있는 것 (2개 이상 생성 시도 시 거부 메시지)**,
so that **PRD §F8.1 (1차 시나리오 1개만 허용) + §15 NON-GOAL #2 (복수 시나리오 2차 예정) + AD-24 (period key typed pattern) + AD-22 (engine state='draft' ONLY) + 12-1 L4 (industry-agnostic capability) 모두 만족**.

(epics.md Story 8.1 verbatim + PRD §F8.1 + §10 + §15 + NFR16·17·18 + AD-5·8·11·22·24 + Epic 8 cj-style 진입점)

## Acceptance Criteria

### AC #1 — 순수 엔진 함수 surface `packages/cost_engine/budget_period_key.py` (epics.md AC #2·4 verbatim + AD-5 + AD-24 + NFR16)

- **Given** AD-5 엔진 순수성 + AD-24 period key typed pattern + NFR16 V8 회귀 가능 + A19 math surface cohesion 패턴 (8-1은 budget_period_key, 7-1 cvp.py, 7-2 projection.py와 surface 분리)
- **When** `packages/cost_engine/budget_period_key.py` 신규 작성
- **Then** `derive_budget_period_key(*, real_period_key: str, scenario_index: int = 1) -> str`:
  - 입력 `real_period_key` = `YYYY-MM` (real period pattern `^\d{4}-(0[1-9]|1[0-2])$`) — M11 fiscal close 패턴 검증 (AD-24 §6.1)
  - 입력 `scenario_index` = `int >= 1` (default 1, 1차 MVP는 B1 only)
  - 출력: `f"{real_period_key}#B{scenario_index}"` (예: `"2026-07"` + `1` → `"2026-07#B1"`)
  - **Edge cases**:
    - `real_period_key` invalid pattern → `ValueError("real_period_key must match YYYY-MM")` raise
    - `scenario_index <= 0` → `ValueError("scenario_index must be >= 1")` raise
    - `scenario_index > 1` (1차 MVP 한도) → `ValueError("MVP supports scenario_index=1 only; 2차 예정")` raise (Story 8-2 honestly DEFER (b)와 정합)
  - **Determinism**: 100회 동일 입력 호출 → 100회 모두 byte-identical 문자열 (V8 회귀 가능)
  - **Purity**: `import decimal, dataclasses, math, hashlib, re, typing` only (AD-5 + import-linter + ruff custom rule)
- **And** `parse_virtual_budget_period_key(*, period_key: str) -> BudgetPeriodKeyParts`:
  - `BudgetPeriodKeyParts = dataclass(frozen=True)` with `real_period_key: str` + `scenario_index: int` + `scenario_suffix: str` (literal `"#B1"` for 1차 MVP)
  - 입력 `period_key` = `"YYYY-MM#B<n>"` (virtual pattern `^\d{4}-(0[1-9]|1[0-2])#B([1-9]\d*)$`)
  - **Edge cases**:
    - `period_key` invalid pattern → `ValueError("period_key must match YYYY-MM#B<n>")` raise (real fiscal key `"2026-07"`도 invalid — M8 virtual only)
    - `scenario_index > 1` (1차 MVP 한도) → `ValueError` raise (8-1 한도 명시)
- **And** `validate_scenario_uniqueness(*, existing_count: int) -> None`:
  - `existing_count == 0` → return None (1st scenario 생성 허용)
  - `existing_count >= 1` → `ScenarioLimitExceededError("1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)")` raise (PRD §F8.1 verbatim + §15 NON-GOAL #2)
  - **Purity**: stdlib-only (no DB, no clock)
- **And** `compute_budget_scenario_hash(*, scenario: BudgetScenario) -> str`:
  - `BudgetScenario = dataclass(frozen=True)` with `id: str` (UUID v7) + `tenant_id: str` + `period_key: str` (virtual) + `real_period_key: str` + `scenario_index: int` + `created_by: str` + `created_at_kst: str` (ISO 8601, 결정론 — clock은 service layer에서 inject)
  - 출력: `hashlib.sha256(repr(scenario).encode()).hexdigest()` (16바이트 hexdigest, 7-1/7-2 pattern 동일)
  - **Determinism**: 100회 동일 입력 → 100회 byte-identical hash (V8 회귀 가능)
- **And` **stdlib-only import 검증**:
  - `tests/cost_engine/test_budget_period_key_no_io_imports.py` (NEW) — AST parser로 `cost_engine/budget_period_key.py` 의 import whitelist 검증 (`decimal`, `dataclasses`, `math`, `hashlib`, `re`, `typing` 만 허용, `os, time, random, requests, sqlalchemy, datetime` 모두 차단) (7-1 test_cvp_no_io_imports.py + 7-2 test_projection_no_io_imports.py 패턴 미러)
  - ruff custom rule: `packages/cost_engine/` 내 `import os|time|random|requests|sqlalchemy` → lint error (7-1 + 7-2 wire 그대로)
  - import-linter 2 KEPT contracts 유지 (Epic 0 + 12-1 + 7-1 + 7-2 wire pattern)

### AC #2 — Scenario Lock 1차 MVP = 1개 only (epics.md AC #3 verbatim + PRD §F8.1 + §15 NON-GOAL #2)

- **Given** PRD §F8.1 + §15 NON-GOAL #2 (1차 MVP = 1개 시나리오 only)
- **When** `validate_scenario_uniqueness(existing_count=N)` 호출
- **Then** **`N == 0`**: return None (1st scenario 생성 허용) + 첫 시나리오는 `period_key = "2026-07#B1"`로 저장
- **And` **`N >= 1`**: `ScenarioLimitExceededError("1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)")` raise
- **And` **ko-KR 메시지 정확성** (epics.md AC verbatim):
  - "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)" — 정확히 일치 (CR 11-3 D-14 envelope main.py handler 등록)
  - HTTP 409 SCENARIO_LIMIT_EXCEEDED envelope
- **And` **M11 close는 fiscal key만 잠금** (epics.md AC #4 verbatim + AD-24 + M11 11-1 reversal_authorization):
  - `monthly_closing_report_status` 변경 시 `period_key in ('2026-07')` 만 검증 (real fiscal key, AD-24 §6.1 pattern `^\d{4}-(0[1-9]|1[0-2])$`)
  - `period_key = "2026-07#B1"` → M11 close는 NOT recognize (virtual key, AD-24 §6.2 명시)
  - **테스트**: `tests/integration/test_m8_budget_m11_close_isolation.py` (NEW) — M11 close lock이 virtual key를 무시하는지 5+ vectors 검증
- **And` **테스트**:
  - `tests/cost_engine/test_budget_period_key.py` (NEW, 20+ cases):
    - `derive_budget_period_key` 정상범위 + 3종 edge cases (ValueError)
    - `parse_virtual_budget_period_key` 정상범위 + 2종 edge cases (real fiscal key 거부 + scenario_index > 1 거부)
    - `validate_scenario_uniqueness` 0건 허용 + 1건 거부 + N건 거부 (3+ vectors)
    - `compute_budget_scenario_hash` 결정론 (RFC test vector)
    - `frozen=True` enforcement (mutation 시도 → FrozenInstanceError)
    - 100회 determinism test (byte-identical hash)
    - Decimal precision: scenario_index 정수 (TS re-implementation parity)

### AC #3 — Capability gate + industry-agnostic + RLS + AD-10 4-role (epics.md AC #4 + AD-3·10·24 + 12-1 L4 precedent)

- **Given** AD-3 RLS multi-tenancy + AD-10 4-role + AD-24 period key + 12-1 L4 industry-agnostic + 7-1/7-2 동일 적용
- **When** `Capability.BUDGET_SCENARIO` wire
- **Then` **`apps/api/core/capability.py` EXTENSION**:
  - `BUDGET_SCENARIO = "budget_scenario"` 신규 추가 (Industry enum 4종 모두 ✅ grant: `manufacturing` / `manufacturing_with_trading` / `manufacturing_with_service` / `service_only`)
  - 12-1 L4 precedent + 7-1 L4 precedent: "budget scenario는 tenant-level 재무 baseline — 모든 industry에 동일 적용"
  - capability matrix v1.17 fill (Epic 7 v1.16 후 Epic 8 진입 시)
- **And` **`apps/api/modules/m8_budget/handlers.py` EXTENSION** (현재 `__init__.py` placeholder만 존재, 본 스토리에서 populate):
  - `POST /api/v1/budget/scenarios` — `@require_capability(BUDGET_SCENARIO)` decorator
  - `GET /api/v1/budget/scenarios` — `@require_capability(BUDGET_SCENARIO)` decorator
  - `GET /api/v1/budget/scenarios/{period_key}` — `@require_capability(BUDGET_SCENARIO)` decorator
  - **Role gate**:
    - POST = `require_role("owner", "member")` (생성 권한, AD-10 — viewer는 read-only)
    - GET = `require_role("owner", "member", "viewer", "consultant_proxy")` (조회 권한, AD-10 4-role 모두)
- **And` **RLS same-tenant filter**:
  - `tenant_id` JWT claim → `WHERE tenant_id = :tenant_id` (AD-3 standard pattern)
  - 다른 테넌트 scenario 0건 노출 (Epic 0 RLS verification pattern)
  - RLS policy `supabase/policies/0016_budget_scenarios_rls.sql` (NEW) — 4-policy split (SELECT/INSERT/UPDATE/DELETE per-tenant isolation)
- **And` **`apps/api/modules/m8_budget/` module authority populate** (cj-style 7번째 epic 패턴):
  - `__init__.py` EXTENSION (placeholder description → module authority docstring)
  - `handlers.py` NEW (3 endpoints, ~150 lines)
  - `services/budget_scenario_service.py` NEW (thin wrappers, ~150 lines)
  - `schemas.py` NEW (Pydantic v2, ~80 lines)
  - `exceptions.py` NEW (3 typed exceptions)
  - `apps/api/main.py` EXTENSION — `m8_budget` router include (1 line, cj-style pattern)

### AC #4 — Frontend `/budget/scenarios` RSC + list/create button/modal + ko-KR SSOT (epics.md AC #1·3 + CR 11-4 D-001·D-002)

- **Given** [예산] → [신규 시나리오] 클릭 + 리스트 + 시나리오 1개 잠금 메시지
- **When** `apps/web/app/[locale]/(dashboard)/budget/scenarios/{layout,page}.tsx` NEW RSC
- **Then` **RSC page** (`page.tsx`):
  - `apps/web/components/m8-budget/BudgetScenarioList.tsx` (NEW client component) mount
  - **CR 11-4 D-001 actual mount MUST**: `<BudgetScenarioList>` JSX return (NOT just create file)
  - `apps/web/app/[locale]/(dashboard)/budget/scenarios/page.tsx`는 server component, async fetch + BudgetScenarioList에 props 전달
- **And` **`BudgetScenarioList.tsx`** (client component, 4 NEW):
  - **BudgetScenarioList.tsx** — main client orchestrator (READ)
    - state: `{ scenarios: BudgetScenario[], isLoading: boolean, error: Error | null }`
    - onMount: `GET /api/v1/budget/scenarios` → scenario list fetch
    - 렌더: 시나리오 목록 (period_key + real_period_key + created_at_kst) + [신규 시나리오] 버튼
    - 빈 상태: "아직 예산 시나리오가 없습니다. [신규 시나리오]를 시작하세요."
  - **BudgetScenarioCreateButton.tsx** (NEW) — [신규 시나리오] 버튼 (시나리오 1개 있을 시 disabled + tooltip)
    - props: `{ existing_count: number, onClick: () => void }`
    - `existing_count >= 1` → disabled + tooltip "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)"
    - `existing_count == 0` → enabled + onClick → 모달 오픈
  - **BudgetScenarioCreateModal.tsx** (NEW) — 신규 시나리오 생성 모달
    - props: `{ open: boolean, onClose: () => void, real_period_key: string, onSuccess: (scenario: BudgetScenario) => void }`
    - 폼 필드: real_period_key (default = 현재 분기 첫 월, 예: `2026-07`)
    - submit: `POST /api/v1/budget/scenarios` with `{ real_period_key }`
    - **에러 처리**:
      - 409 SCENARIO_LIMIT_EXCEEDED → toast error "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)" + 모달 닫기
      - 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY → toast error + 폼 유지
      - 403 CAPABILITY_NOT_GRANTED → toast error + 모달 닫기
      - 404 BUDGET_SCENARIO_NOT_FOUND (GET only) → empty state 안내
  - **BudgetScenarioDetail.tsx** (NEW) — 단일 scenario detail 카드
    - props: `{ scenario: BudgetScenario }`
    - 표시: period_key (`"2026-07#B1"`) + real_period_key (`"2026-07"`) + scenario_index (1) + created_at_kst
    - **8-3 pre-standard cost preview placeholder** (cj-style 3번째, honestly DEFER — "Story 8-3 진입 시 [예측] 버튼 활성화")
- **And` **ko-KR.json** SSOT (CR 11-4 D-002 단일 `apps/web/messages/ko-KR.json` only):
  - 1 NEW namespace `budget_scenario` (~15 strings: page_title, create_button_label, create_button_tooltip_limit, create_button_tooltip_ready, create_modal_title, create_modal_real_period_key_label, create_modal_submit, create_modal_cancel, empty_state_title, empty_state_description, toast_error_scenario_limit, toast_error_invalid_period_key, toast_error_capability, toast_error_generic, detail_section_title, etc.)
  - **7-1 cvp_simulation + 7-2 projection namespace와 분리** (budget 독립 namespace)
- **And` **TS mirror** (`apps/web/lib/m8-budget-scenario.ts`):
  - `BudgetScenario`, `BudgetPeriodKeyParts` TS interfaces (7-1 CVPBaseline + 7-2 ProjectionInputs 패턴 미러)
  - `deriveBudgetPeriodKeyTS(real_period_key: string, scenario_index: number = 1): string` — TypeScript re-implementation (V8 cross-language parity)
  - `validateScenarioUniquenessTS(existing_count: number): void` — TS re-implementation
  - **CR 11-4 D-005**: unknown state fall-through → reject (`deriveBudgetPeriodKeyTS` invalid pattern → throw `ERROR_CODE_INVALID_INPUT`)
- **And` **`apps/web/lib/menu-config.ts` EXTENSION**:
  - `/budget/scenarios` sidebar nav entry (7-1 `/simulation/cvp` + 7-2 `/simulation/projection` + 8-1 `/budget/scenarios` 패턴)
  - 조건부 렌더: `industry in (manufacturing, manufacturing_with_trading, manufacturing_with_service, service_only)` 모두 표시 (12-1 L4 industry-agnostic)

### AC #5 — Cross-language drift detector + Alembic 0026 + RLS 0016 (CR 12-5 D-13 + 12-1 P-015 + AD-2·3·22)

- **Given** AD-15 cross-language conventions + CR 12-5 D-13 structural drift detector + AD-2 INSERT-only + AD-3 RLS + AD-22 ledger append-only
- **When** 8-1 wire
- **Then` **Python ↔ TS parity test**:
  - `tests/integration/test_m8_budget_cross_language_drift.py` (NEW):
    - `derive_budget_period_key` Python vs `deriveBudgetPeriodKeyTS` TypeScript 10+ vectors
    - 동일 `real_period_key` + `scenario_index` → 동일 `period_key` 문자열
    - Edge cases: invalid pattern → 동일 `ERROR_CODE_INVALID_INPUT` (TS) / `ValueError` (Python)
    - Edge cases: `scenario_index > 1` → 동일 거부 (1차 MVP 한도)
  - **ko-KR.json SSOT drift detector** (CR 12-5 L4 + 12-1 P-015):
    - `tests/integration/test_ko_kr_json_ssot.py` EXTENSION — `budget_scenario` namespace 정합
    - frontend i18n key가 `apps/web/messages/ko-KR.json` 에만 존재 (NOT `apps/web/lib/ko-KR.json`)
- **And` **Alembic 0026** (NEW — 12-3 0025 후속):
  - `apps/api/alembic/versions/0026_budget_scenarios.py` (NEW)
  - `budget_scenarios` table NEW (8 columns):
    - `id` UUID PK (UUID v7, CR 1-1 wire pattern)
    - `tenant_id` UUID NOT NULL FK → `tenants(id)` ON DELETE CASCADE
    - `period_key` TEXT NOT NULL CHECK (`period_key ~ '^\d{4}-(0[1-9]|1[0-2])#B[1-9]\d*$'`)
    - `real_period_key` TEXT NOT NULL CHECK (`real_period_key ~ '^\d{4}-(0[1-9]|1[0-2])$'`)
    - `scenario_index` INT NOT NULL CHECK (`scenario_index >= 1`)
    - `scenario_hash` TEXT NOT NULL (V8 determinism, `compute_budget_scenario_hash` 결과)
    - `created_by` UUID NOT NULL FK → `users(id)`
    - `created_at_kst` TIMESTAMPTZ NOT NULL DEFAULT NOW() (AD-9 Seoul TZ-aware)
  - `UNIQUE(tenant_id, period_key)` — duplicate 방지
  - `UNIQUE(tenant_id, real_period_key)` — 1차 MVP scenario 1개 잠금 DB-level guard (validate_scenario_uniqueness + DB UNIQUE 제약 defense-in-depth)
  - `idx_budget_scenarios_tenant_id_period_key` (composite index)
  - `down_revision = '0025_tenants_deletion_status'` (12-3 0025 후속)
- **And` **RLS 0016** (NEW):
  - `supabase/policies/0016_budget_scenarios_rls.sql` (NEW)
  - 4-policy split:
    - SELECT policy: `USING (tenant_id = current_setting('app.tenant_id')::UUID)`
    - INSERT policy: `WITH CHECK (tenant_id = current_setting('app.tenant_id')::UUID)`
    - UPDATE policy: `USING (tenant_id = current_setting('app.tenant_id')::UUID) WITH CHECK (tenant_id = current_setting('app.tenant_id')::UUID)`
    - DELETE policy: `USING (tenant_id = current_setting('app.tenant_id')::UUID)`
  - `ALTER TABLE budget_scenarios ENABLE ROW LEVEL SECURITY`
  - `ALTER TABLE budget_scenarios FORCE ROW LEVEL SECURITY` (Epic 0 wire pattern)
- **And` **no audit emit (read-mostly operation, CR 1.1 invariant)**:
  - `tests/integration/test_m8_budget_audit_consistency.py` (NEW) — scenario CRUD 후 audit_logs row 0건 (8-1은 read-mostly, A5 forward-lock 변경 0)
  - **A5 forward-lock** (변경 없음): `budget_scenario` action 추가 0건 (CR 11-3 D-2 즉시 sweep 회피, 8-1은 read-mostly)
  - **`monthly_closing_report_status` 변경 0건** (M11 close lock 미발동)
  - **`fiscal_period_snapshots` row 변경 0건** (snapshot 미발동)
- **And` **V8 byte-identical CI gate**:
  - `tests/cost_engine/test_budget_period_key_determinism.py` (NEW) — 100회 동일 입력 byte-identical `scenario_hash` (7-1 + 7-2 패턴 미러)

### AC #6 — AD-11 layer rule + ALLOWED_SERVICE_SUBMODULES sweep + CR 12-5 L3 3-layer defense (epics.md AC #4 + AD-2·5·11·22 + CR 11-3 D-2 + 12-1 L4)

- **Given** AD-11 layer rule (`ui → api → services → ports → engine`) + AD-2 append-only + CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES + 12-1 L4 industry-agnostic + 12-5 L3 3-layer defense
- **When** 8-1 wire
- **Then` **AD-11 layer rule 검증**:
  - `apps/api/modules/m8_budget/services/budget_scenario_service.py` (NEW service layer, ~150 lines)
  - `packages/services/m8_budget/` EXTENSION (NEW: `budget_period_key_serializers.py` thin wrappers)
  - `packages/cost_engine/budget_period_key.py` (pure kernel, stdlib-only, 7-1 cvp.py + 7-2 projection.py와 surface 분리)
  - **의존 방향**: `apps/api → packages/services/m8_budget/ → packages/cost_engine/budget_period_key.py` (단방향, AD-11)
  - **import-linter contracts**: 2 KEPT 0 broken (7-1 + 7-2 wire pattern 그대로 유지)
- **And` **ALLOWED_SERVICE_SUBMODULES sweep** (CR 11-3 D-2 즉시, 7-1/7-2 wire 패턴 그대로):
  - `tests/architecture/test_api_calls_only_ports.py` EXTENSION — `packages.services.m8_budget.budget_period_key_serializers` 추가
  - `packages.services.m8_budget` 자체는 m8_budget module authority에 속하므로 ALLOWED 등록 (CR 11-2 lesson)
- **And` **CR 12-5 L3 3-layer defense** (scenario 생성은 destructive-write):
  - **Route layer**: `@require_role("owner", "member")` + `@require_capability(BUDGET_SCENARIO)` decorator
  - **Service layer**: `validate_scenario_uniqueness(existing_count=count_scenarios(...))` 호출 (DB 조회 + pure kernel 검증)
  - **DB layer**: `UNIQUE(tenant_id, real_period_key)` constraint defense-in-depth (동시성 race condition 방지)
  - **Handler layer**: audit-first emit (8-1은 read-mostly이므로 0건 emit, but envelope 구조는 audit-ready) — `audit_first=False` 명시
- **And` **typed exception main.py envelope handler 등록** (CR 12-5 D-14):
  - `ScenarioLimitExceededError` → HTTP 409 SCENARIO_LIMIT_EXCEEDED envelope
  - `InvalidVirtualBudgetPeriodKeyError` → HTTP 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY envelope
  - `BudgetScenarioNotFoundError` → HTTP 404 BUDGET_SCENARIO_NOT_FOUND envelope
  - 3 NEW typed exceptions (`apps/api/modules/m8_budget/exceptions.py` NEW)
  - `apps/api/main.py` EXTENSION — 3 NEW exception handlers 등록
- **And` **CR 11-3 D-3 ruff auto-fix sweep** (8-1 wire 시점에 일괄):
  - `make lint-conventions` 0 errors (W292 / UP038 / SIM300 / SIM222 / ERA001 sweep 일괄)
- **And` **frontend telemetry**:
  - `budget_scenario_created` + `budget_scenario_viewed` analytics event (PostHog or similar — Epic 10 carry-over, honestly DEFER 시 mock)
  - 본 스토리 범위 외 (honestly DEFER)

## Tasks / Subtasks (atomic wire)

### Task 1 — Pure kernel (Budget period key math surface)

- **AC**: #1
- **파일**: `packages/cost_engine/budget_period_key.py` (NEW, ~250 lines) + `packages/cost_engine/__init__.py` EXTENSION (export 4 NEW pure functions)
- **subtasks**:
  - [ ] 1.1 STDIN-only: `import decimal, dataclasses, math, hashlib, re, typing` only (AD-5 purity + import-linter, 7-1 + 7-2 패턴 동일)
  - [ ] 1.2 `class BudgetPeriodKeyParts(frozen=True)` with 3 fields: `real_period_key: str`, `scenario_index: int`, `scenario_suffix: str` (literal `"#B<n>"`)
  - [ ] 1.3 `class BudgetScenario(frozen=True)` with 7 fields: `id: str` (UUID v7), `tenant_id: str`, `period_key: str` (virtual), `real_period_key: str`, `scenario_index: int`, `created_by: str`, `created_at_kst: str` (ISO 8601 결정론)
  - [ ] 1.4 `def derive_budget_period_key(*, real_period_key: str, scenario_index: int = 1) -> str` — AD-24 virtual pattern + 3종 edge cases (`real_period_key` invalid / `scenario_index <= 0` / `scenario_index > 1`)
  - [ ] 1.5 `def parse_virtual_budget_period_key(*, period_key: str) -> BudgetPeriodKeyParts` — AD-24 virtual pattern parse + 2종 edge cases (real fiscal key 거부 / `scenario_index > 1` 거부)
  - [ ] 1.6 `def validate_scenario_uniqueness(*, existing_count: int) -> None` — `existing_count >= 1` 시 `ScenarioLimitExceededError` raise (PRD §F8.1 verbatim)
  - [ ] 1.7 `def compute_budget_scenario_hash(*, scenario: BudgetScenario) -> str` — `hashlib.sha256(repr(scenario).encode()).hexdigest()` 결정론 digest
- **tests**: `tests/cost_engine/test_budget_period_key.py` (NEW, 20+ cases):
  - `derive_budget_period_key` 정상범위 + 3종 edge cases (ValueError)
  - `parse_virtual_budget_period_key` 정상범위 + 2종 edge cases (real fiscal key 거부 / scenario_index > 1 거부)
  - `validate_scenario_uniqueness` 0건 허용 + 1건 거부 + N건 거부 (3+ vectors)
  - `compute_budget_scenario_hash` 결정론 (RFC test vector)
  - `frozen=True` enforcement (mutation 시도 → FrozenInstanceError)
  - 100회 determinism test (byte-identical hash)
  - `ScenarioLimitExceededError` 메시지 정확성 ("1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)")

### Task 2 — Engine purity gate (AD-5 + import-linter + ruff custom rule)

- **AC**: #1
- **파일**: `tests/cost_engine/test_budget_period_key_no_io_imports.py` (NEW), 7-1/7-2 ruff custom rule reuse
- **subtasks**:
  - [ ] 2.1 `test_budget_period_key_no_io_imports.py` AST parser 검증 (7-1 `test_cvp_no_io_imports.py` + 7-2 `test_projection_no_io_imports.py` 패턴 미러):
    - `cost_engine/budget_period_key.py` 의 import whitelist: `decimal, dataclasses, math, hashlib, re, typing` (7-1 + 7-2 whitelist 확장: `re` 추가 — AD-24 pattern matching)
    - forbidden: `os, time, random, requests, sqlalchemy, datetime, json, urllib` 모두 차단 (5+ cases)
  - [ ] 2.2 ruff custom rule (7-1 + 7-2 wire 그대로 — `packages/cost_engine/*.py` 전체 적용):
    - `import os | import time | import random | import requests | import sqlalchemy | import datetime` → lint error
    - 8-1은 신규 surface 추가이지만 동일 rule 적용 (7-1 + 7-2 wire 재사용)
  - [ ] 2.3 `import-linter` contracts 유지:
    - `cost_engine_forbidden_io` (Epic 0 wire) — 1 KEPT 0 broken (7-1 + 7-2 + 8-1 모두 검증)
    - `engine_core_to_adapters_forbidden` (Epic 0 wire) — 1 KEPT 0 broken
  - [ ] 2.4 V8 determinism test: `tests/cost_engine/test_budget_period_key_determinism.py` (NEW, 5+ cases)
    - 100회 동일 입력 → byte-identical `scenario_hash`
    - `compute_budget_scenario_hash` 결정론 (RFC test vector)

### Task 3 — Service layer (thin wrappers + scenario CRUD + scenario lock enforcement)

- **AC**: #3, #6
- **파일**: `apps/api/modules/m8_budget/services/budget_scenario_service.py` (NEW, ~150 lines)
- **subtasks**:
  - [ ] 3.1 `class BudgetScenarioService` with `__init__(session, *, tenant_id, actor_id, trace_id)` (7-1 CVPSimulationService + 7-2 ProjectionService + 12-1 TwoFactorService + 12-3 AccountDeletionService precedent)
  - [ ] 3.2 `async def count_scenarios(self) -> int`:
    - SELECT COUNT(*) FROM budget_scenarios WHERE tenant_id = :tenant_id
    - RLS same-tenant filter (AD-3)
    - Return int (0 또는 1, 1차 MVP 한도)
  - [ ] 3.3 `async def create_scenario(self, *, real_period_key: str) -> BudgetScenario`:
    - delegate to `packages/cost_engine/budget_period_key.py:derive_budget_period_key(real_period_key, scenario_index=1)` (pure kernel, AD-5)
    - delegate to `packages/cost_engine/budget_period_key.py:validate_scenario_uniqueness(existing_count=self.count_scenarios())` (scenario lock)
    - DB INSERT INTO budget_scenarios (UUID v7 id + period_key + real_period_key + scenario_index + scenario_hash + created_by + created_at_kst)
    - **DB UNIQUE 제약 활용** (`UNIQUE(tenant_id, real_period_key)` defense-in-depth)
    - Return BudgetScenario (frozen dataclass)
  - [ ] 3.4 `async def list_scenarios(self) -> list[BudgetScenario]`:
    - SELECT * FROM budget_scenarios WHERE tenant_id = :tenant_id ORDER BY created_at_kst DESC
    - RLS same-tenant filter (AD-3)
    - Return list[BudgetScenario]
  - [ ] 3.5 `async def get_scenario(self, *, period_key: str) -> BudgetScenario`:
    - delegate to `packages/cost_engine/budget_period_key.py:parse_virtual_budget_period_key(period_key)` (validate virtual pattern)
    - SELECT * FROM budget_scenarios WHERE tenant_id = :tenant_id AND period_key = :period_key
    - not found → `BudgetScenarioNotFoundError` raise (D-14 envelope 404)
    - Return BudgetScenario
  - [ ] 3.6 `_to_budget_scenario(orm_row) -> BudgetScenario` ORM→kernel boundary conversion (12-1 L3 _to_totp_state + 12-3 L3 _to_deletion_state precedent)
- **파일**: `packages/services/m8_budget/` EXTENSION (NEW thin wrappers):
  - [ ] 3.7 `budget_period_key_serializers.py` — `serialize_budget_scenario`, `serialize_budget_period_key_parts` (dataclass → dict, JSON-safe Decimal/int)
- **tests**: `tests/services/m8_budget/test_budget_scenario_service.py` (NEW, 18+ cases):
  - `count_scenarios` 정확성 (0건 / 1건)
  - `create_scenario` 정상범위 + 3종 edge cases (real_period_key invalid / scenario_index > 1 / existing_count >= 1)
  - `create_scenario` DB UNIQUE 제약 race condition 검증 (concurrent INSERT)
  - `list_scenarios` 정렬 + RLS same-tenant (다른 tenant_id 0건)
  - `get_scenario` 정상범위 + 2종 edge cases (invalid period_key / not found)
  - `_to_budget_scenario` ORM→kernel boundary 정확성
  - `serializers` JSON-safe Decimal/int
  - **`audit_logs` row 0건** 검증 (8-1 read-mostly, A5 forward-lock 변경 0)

### Task 4 — HTTP routes + capability gate + main.py wire + 3 typed exception handlers

- **AC**: #3, #6
- **파일**: `apps/api/modules/m8_budget/handlers.py` NEW (~150 lines)
- **subtasks**:
  - [ ] 4.1 `POST /api/v1/budget/scenarios`:
    - Request: `CreateBudgetScenarioRequest(real_period_key: str)` (Pydantic v2, AD-24 real period pattern `^\d{4}-(0[1-9]|1[0-2])$` validator)
    - `@require_capability(BUDGET_SCENARIO)` decorator
    - `require_role("owner", "member")` (생성 권한, AD-10 — viewer는 read-only)
    - Service: `BudgetScenarioService.create_scenario(real_period_key=request.real_period_key)`
    - Response: `BudgetScenarioResponse(scenario)` + `X-Scenario-Hash` header (V8 determinism)
    - 201 Created + Decimal-as-string (JSON-safe, AD-15)
    - **에러 케이스**:
      - 409 SCENARIO_LIMIT_EXCEEDED (existing_count >= 1)
      - 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY (invalid real_period_key pattern)
      - 403 CAPABILITY_NOT_GRANTED (capability 미보유)
      - 403 FORBIDDEN_ROLE (viewer 시도)
  - [ ] 4.2 `GET /api/v1/budget/scenarios`:
    - `@require_capability(BUDGET_SCENARIO)` decorator
    - `require_role("owner", "member", "viewer", "consultant_proxy")` (조회 권한, AD-10 4-role 모두)
    - Service: `BudgetScenarioService.list_scenarios()`
    - Response: `BudgetScenarioListResponse(scenarios=[...], total_count=int)` (200 OK)
  - [ ] 4.3 `GET /api/v1/budget/scenarios/{period_key}`:
    - `@require_capability(BUDGET_SCENARIO)` decorator
    - `require_role("owner", "member", "viewer", "consultant_proxy")` (조회 권한, AD-10 4-role 모두)
    - Path param `period_key: str` (virtual pattern validator, 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY if invalid)
    - Service: `BudgetScenarioService.get_scenario(period_key=path_param)`
    - Response: `BudgetScenarioResponse(scenario)` (200 OK)
    - **에러 케이스**:
      - 404 BUDGET_SCENARIO_NOT_FOUND
      - 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY
- **파일**: `apps/api/main.py` EXTENSION:
  - [ ] 4.4 `m8_budget` router include (cj-style 7번째 epic 패턴) — `apps/api/main.py:797` 영역에 router 추가 (Epic 11 m11_close + 12-1 m12_account + 7-1 m7_simulation + 8-1 m8_budget sibling)
  - [ ] 4.5 3 NEW exception handlers 등록 (CR 12-5 D-14 envelope):
    - `ScenarioLimitExceededError` → 409 SCENARIO_LIMIT_EXCEEDED envelope (4 fields: code, message_ko, details, trace_id)
    - `InvalidVirtualBudgetPeriodKeyError` → 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY envelope
    - `BudgetScenarioNotFoundError` → 404 BUDGET_SCENARIO_NOT_FOUND envelope
- **파일**: `apps/api/core/capability.py` EXTENSION:
  - [ ] 4.6 `Capability.BUDGET_SCENARIO = "budget_scenario"` 신규 추가 (Industry enum 4종 모두 ✅ grant)
  - [ ] 4.7 `Capability.BUDGET_SCENARIO` grant matrix (12-1 L4 industry-agnostic precedent)
- **파일**: `apps/api/modules/m8_budget/exceptions.py` NEW:
  - [ ] 4.8 `ScenarioLimitExceededError` typed exception (PRD §F8.1 verbatim 메시지)
  - [ ] 4.9 `InvalidVirtualBudgetPeriodKeyError` typed exception
  - [ ] 4.10 `BudgetScenarioNotFoundError` typed exception
- **파일**: `apps/api/modules/m8_budget/schemas.py` NEW (~80 lines, Pydantic v2):
  - [ ] 4.11 `CreateBudgetScenarioRequest(real_period_key: str)` + Pydantic v2 `pattern=r"^\d{4}-(0[1-9]|1[0-2])$"` validator
  - [ ] 4.12 `BudgetScenarioResponse(scenario: BudgetScenarioSerialized)` + Decimal-as-string
  - [ ] 4.13 `BudgetScenarioListResponse(scenarios: list[BudgetScenarioSerialized], total_count: int)`
- **파일**: `apps/api/modules/m8_budget/__init__.py` EXTENSION:
  - [ ] 4.14 placeholder description → module authority docstring (cj-style 7번째 epic 패턴)
- **tests**: `tests/api/test_m8_budget_handlers.py` (NEW, 15+ cases):
  - `POST /api/v1/budget/scenarios` 정상 (201 + Decimal-as-string + X-Scenario-Hash 헤더)
  - `POST /api/v1/budget/scenarios` no capability → 403 CAPABILITY_NOT_GRANTED
  - `POST /api/v1/budget/scenarios` viewer role → 403 FORBIDDEN_ROLE
  - `POST /api/v1/budget/scenarios` existing scenario → 409 SCENARIO_LIMIT_EXCEEDED + 메시지 정확성 검증
  - `POST /api/v1/budget/scenarios` invalid real_period_key → 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY
  - `GET /api/v1/budget/scenarios` 정상 (200 + list + total_count)
  - `GET /api/v1/budget/scenarios/{period_key}` 정상 (200 + scenario detail)
  - `GET /api/v1/budget/scenarios/{period_key}` not found → 404 BUDGET_SCENARIO_NOT_FOUND
  - `GET /api/v1/budget/scenarios/{period_key}` invalid period_key → 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY
  - AD-15 envelope contract (4 fields: code, message_ko, details, trace_id)
  - RLS same-tenant (다른 tenant_id 0건 노출)
  - X-Scenario-Hash 헤더 V8 determinism 검증

### Task 5 — Alembic 0026 + RLS 0016 (Alembic migration + RLS policy)

- **AC**: #5
- **파일**: `apps/api/alembic/versions/0026_budget_scenarios.py` (NEW, ~120 lines)
- **subtasks**:
  - [ ] 5.1 `budget_scenarios` table NEW (8 columns):
    - `id` UUID PK (UUID v7, CR 1-1 wire pattern)
    - `tenant_id` UUID NOT NULL FK → `tenants(id)` ON DELETE CASCADE
    - `period_key` TEXT NOT NULL CHECK (`period_key ~ '^\d{4}-(0[1-9]|1[0-2])#B[1-9]\d*$'`)
    - `real_period_key` TEXT NOT NULL CHECK (`real_period_key ~ '^\d{4}-(0[1-9]|1[0-2])$'`)
    - `scenario_index` INT NOT NULL CHECK (`scenario_index >= 1`)
    - `scenario_hash` TEXT NOT NULL (V8 determinism, `compute_budget_scenario_hash` 결과)
    - `created_by` UUID NOT NULL FK → `users(id)`
    - `created_at_kst` TIMESTAMPTZ NOT NULL DEFAULT NOW() (AD-9 Seoul TZ-aware)
  - [ ] 5.2 `UNIQUE(tenant_id, period_key)` constraint (duplicate period_key 방지)
  - [ ] 5.3 `UNIQUE(tenant_id, real_period_key)` constraint (1차 MVP scenario 1개 잠금 DB-level guard)
  - [ ] 5.4 `idx_budget_scenarios_tenant_id_period_key` composite index
  - [ ] 5.5 `down_revision = '0025_tenants_deletion_status'` (12-3 0025 후속)
  - [ ] 5.6 `COMMENT ON COLUMN` 8개 (각 컬럼 SSOT 명시)
- **파일**: `supabase/policies/0016_budget_scenarios_rls.sql` NEW (~60 lines)
- **subtasks**:
  - [ ] 5.7 4-policy split (SELECT/INSERT/UPDATE/DELETE per-tenant isolation)
  - [ ] 5.8 `ALTER TABLE budget_scenarios ENABLE ROW LEVEL SECURITY`
  - [ ] 5.9 `ALTER TABLE budget_scenarios FORCE ROW LEVEL SECURITY` (Epic 0 wire pattern)
  - [ ] 5.10 `CREATE INDEX idx_budget_scenarios_tenant_id ON budget_scenarios(tenant_id)` (RLS 성능)
- **tests**:
  - [ ] 5.11 `tests/api/test_alembic_0026_budget_scenarios.py` (NEW, 8+ cases):
    - 8 columns 정확성 + 타입 검증
    - 2 UNIQUE constraints 검증
    - CHECK constraints (period_key pattern + real_period_key pattern + scenario_index >= 1)
    - down_revision = '0025_tenants_deletion_status' 정확성
  - [ ] 5.12 `tests/api/test_rls_0016_budget_scenarios.py` (NEW, 6+ cases):
    - SELECT/INSERT/UPDATE/DELETE RLS 정책 검증
    - 다른 테넌트 0건 노출 (Epic 0 RLS verification pattern)
    - FORCE RLS 검증

### Task 6 — Frontend (RSC + list/create button/modal + TS mirror + ko-KR.json)

- **AC**: #2, #4
- **파일**:
  - [ ] 6.1 `apps/web/app/[locale]/(dashboard)/budget/scenarios/layout.tsx` (NEW RSC layout)
  - [ ] 6.2 `apps/web/app/[locale]/(dashboard)/budget/scenarios/page.tsx` (NEW RSC page — `<BudgetScenarioList>` actual mount MUST per CR 11-4 D-001)
  - [ ] 6.3 `apps/web/components/m8-budget/BudgetScenarioList.tsx` (NEW client component, ~200 lines)
  - [ ] 6.4 `apps/web/components/m8-budget/BudgetScenarioCreateButton.tsx` (NEW, ~80 lines) — 시나리오 1개 잠금 tooltip
  - [ ] 6.5 `apps/web/components/m8-budget/BudgetScenarioCreateModal.tsx` (NEW, ~180 lines) — react-hook-form + Zod + submit
  - [ ] 6.6 `apps/web/components/m8-budget/BudgetScenarioDetail.tsx` (NEW, ~100 lines) — 단일 scenario detail 카드
  - [ ] 6.7 `apps/web/lib/m8-budget-scenario.ts` (NEW, ~120 lines) — TS mirror + `deriveBudgetPeriodKeyTS` + `validateScenarioUniquenessTS`
  - [ ] 6.8 `apps/web/lib/m8-budget-scenario-schema.ts` (NEW, ~50 lines) — Zod schema (real_period_key + form-level)
  - [ ] 6.9 `apps/web/messages/ko-KR.json` EXTENSION — `budget_scenario` namespace (~15 strings, 7-1 cvp_simulation + 7-2 projection namespace와 분리)
  - [ ] 6.10 `apps/web/components/m8-budget/index.ts` EXTENSION — barrel export + BudgetScenario
  - [ ] 6.11 `apps/web/lib/menu-config.ts` EXTENSION — `/budget/scenarios` sidebar nav entry (7-1 `/simulation/cvp` + 7-2 `/simulation/projection` + 8-1 `/budget/scenarios` 패턴)
- **tests**:
  - [ ] 6.12 `apps/web/components/m8-budget/BudgetScenarioList.test.tsx` (NEW, 8+ cases) — list fetch + empty state + scenario 1개 잠금 메시지
  - [ ] 6.13 `apps/web/components/m8-budget/BudgetScenarioCreateButton.test.tsx` (NEW, 6+ cases) — disabled / enabled / tooltip
  - [ ] 6.14 `apps/web/components/m8-budget/BudgetScenarioCreateModal.test.tsx` (NEW, 10+ cases) — form submit + 409/422/403 에러 처리
  - [ ] 6.15 `apps/web/components/m8-budget/BudgetScenarioDetail.test.tsx` (NEW, 5+ cases) — scenario detail 표시 + 8-3 placeholder
  - [ ] 6.16 `apps/web/lib/m8-budget-scenario.test.ts` (NEW, 10+ cases) — TS mirror parity Python (cross-language drift)

### Task 7 — Tests + docs + 3중 게이트 final clean

- **AC**: #1, #2, #3, #4, #5, #6
- **subtasks**:
  - [ ] 7.1 Backend tests aggregate:
    - `tests/cost_engine/test_budget_period_key.py` (20+ pure kernel)
    - `tests/cost_engine/test_budget_period_key_no_io_imports.py` (5+ AST, 7-1 + 7-2 패턴 미러)
    - `tests/cost_engine/test_budget_period_key_determinism.py` (5+ V8 byte-identical, 7-1 + 7-2 패턴 미러)
    - `tests/services/m8_budget/test_budget_scenario_service.py` (18+)
    - `tests/api/test_m8_budget_handlers.py` (15+)
    - `tests/api/test_alembic_0026_budget_scenarios.py` (8+)
    - `tests/api/test_rls_0016_budget_scenarios.py` (6+)
    - `tests/integration/test_m8_budget_cross_language_drift.py` (10+ Python↔TS, 7-1 + 7-2 패턴 미러)
    - `tests/integration/test_m8_budget_audit_consistency.py` (4+ audit_logs 0건 + monthly_closing_report_status 변경 0건 + fiscal_period_snapshots 변경 0건)
    - `tests/integration/test_m8_budget_m11_close_isolation.py` (5+ M11 close가 virtual key 무시 검증)
    - `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES m8_budget.budget_period_key_serializers sweep, CR 11-3 D-2)
  - [ ] 7.2 Frontend tests:
    - `apps/web/components/m8-budget/BudgetScenarioList.test.tsx` (8+)
    - `apps/web/components/m8-budget/BudgetScenarioCreateButton.test.tsx` (6+)
    - `apps/web/components/m8-budget/BudgetScenarioCreateModal.test.tsx` (10+)
    - `apps/web/components/m8-budget/BudgetScenarioDetail.test.tsx` (5+)
    - `apps/web/lib/m8-budget-scenario.test.ts` (10+ TS mirror)
  - [ ] 7.3 Docs:
    - `docs/virtual-budget-period-key.md` (NEW, ~250 lines, 9 sections — 7-1 docs/cvp-simulation.md + 7-2 docs/next-month-projection.md 패턴)
    - `docs/capability-matrix.md` v1.17 EXTENSION (`BUDGET_SCENARIO` row 신규 + 4 industries ✅ 마킹)
    - `docs/conventions.md` §AD-24 EXTENSION (virtual budget key 명시, `^\d{4}-(0[1-9]|1[0-2])#B[1-9]\d*$` + scenario lock 1차 MVP 한도)
    - `docs/conventions.md` §AD-11 layer rule EXTENSION (m8_budget service layer 명시, 7-1 + 7-2 + 8-1)
    - `docs/architecture-inventory.md` EXTENSION (m8_budget module entry)
    - `docs/deferred-work.md` EXTENSION (7 honestly DEFER items 명시)
    - `docs/sprint-status.md` sync (8-1: ready-for-dev → in-progress)
  - [ ] 7.4 3중 게이트 mandatory CI (cj-style 7번째 epic + carry-over 7번째 연속):
    - **ruff scoped** (8-1 surface: `packages/cost_engine/budget_period_key.py` + `apps/api/modules/m8_budget/` + `packages/services/m8_budget/` + `apps/web/components/m8-budget/`): All checks passed
    - **import-linter 2 KEPT 0 broken** (ALLOWED_SERVICE_SUBMODULES `m8_budget.budget_period_key_serializers` 추가, AD-11 + AD-22 + cost_engine_forbidden_io + engine_core_to_adapters_forbidden 모두 유지)
    - **pytest baseline + ~110 NEW = 2106 + ~110 = ~2216 passed + 127 skipped + 0 failed** (3 pre-existing failures honestly DEFER per A19 carry-over T0 결정, 8-1 추가 회귀 0)
    - **vitest 158 baseline + ~39 NEW = ~197 passed** (7-1 cvp_simulation 26 + 7-2 projection 42 + 8-1 budget_scenario 39 추가)
    - **3 pre-existing failures** (test_alembic_0022_does_not_exist + test_sdr_test_count_drift + test_tenant_backups_0024_migration) honestly DEFER per A19 carry-over T0 결정 (8-1 scope OUTSIDE)
  - [ ] 7.5 MAX SDR claim 갱신 (CR 11-2 lesson — separate line for unambiguous parser match):
    - `2186 → ~2216` (+30 NEW pytest cases, net of pre-existing honestly DEFER)
    - `200 → ~239` (+39 NEW vitest cases)
    - `2486 → ~2555` total

### Task 8 — Atomic wire close-out (handoff + sprint-status)

- **AC**: all
- **subtasks**:
  - [ ] 8.1 Commit message: `Story 8.1: T1~T7 atomic wire — Virtual budget period key + scenario lock to one + pure kernel budget_period_key.py + service layer + 3 handlers + Alembic 0026 + RLS 0016 + frontend list/button/modal + cross-language drift + 3중 게이트`
  - [ ] 8.2 sprint-status.yaml EXTENSION — `8-1-virtual-budget-period-key-scenario-lock-to-one: backlog → ready-for-dev → in-progress → review → done`
  - [ ] 8.3 handoff memory file: `handoff-2026-08-15-8-1-spec-ready.md` (7 honestly DEFER 명시)
  - [ ] 8.4 Epic 8 진입 시점 baseline_commit = `a63646c` (Story 12.3 T7 follow-up tip) 명시
  - [ ] 8.5 다음 단계 명시: `bmad-dev-story 8-1 T1~T8 실행 OR Epic 8 8-2 spec 진입 (cj-style 2번째) OR Epic 7 7-1 + 7-2 dev-story 진입 (Epic 7 ready-for-dev 상태)`

## Dev Notes

### Architecture patterns & constraints

**AD-5 engine purity (CRITICAL)**:
- `packages/cost_engine/budget_period_key.py` 는 **stdlib-only** (decimal, dataclasses, math, hashlib, re, typing) — NO sqlalchemy, NO datetime.now(), NO random, NO I/O
- **7-1 cvp.py + 7-2 projection.py 와 surface 분리** — A19 math surface migration pattern (3번째 cohesion 강화, budget_period_key는 별도 concern)
- import-linter contracts 2 KEPT 0 broken (Epic 0 wire pattern, 12-1 + Epic 5 reinforcement + 7-1 + 7-2 + 8-1)
- ruff custom rule: `packages/cost_engine/*.py` 에서 forbidden imports → lint error (7-1 + 7-2 wire 그대로, 8-1 신규 surface 추가지만 동일 rule 적용)

**AD-11 layer rule**:
- 의존 방향: `apps/web → apps/api → packages/services/m8_budget/ → packages/cost_engine/budget_period_key.py`
- 단방향 strict (Epic 0 wire pattern, 12-1 reinforcement + 7-1 + 7-2 + 8-1)
- engine은 services / adapters / UI import 불가 (AD-11 reverse-direction 명시)
- **packages/cost_engine/budget_period_key.py** 는 **순수 함수 surface** (7-1 cvp.py + 7-2 projection.py 와 cross-import 없음)

**AD-3 RLS multi-tenancy**:
- scenario CRUD 시 `tenant_id = :tenant_id` 필터 (JWT claim, 7-1 + 7-2 패턴 동일)
- 다른 테넌트 scenario 0건 노출 (Epic 0 fixture test pattern)

**AD-15 cross-language conventions**:
- DB/Python `snake_case`; Next.js routes `kebab-case` (`/budget/scenarios`); React/TS types `PascalCase`
- Decimal 정밀도: ROUND_HALF_EVEN (Python `decimal.Decimal` ↔ TS `decimal.js`, 7-1 + 7-2 패턴 동일)
- **Period keys** follow AD-24:
  - Real fiscal = `^\d{4}-(0[1-9]|1[0-2])$` (예: `2026-07`)
  - **Virtual budget = `^\d{4}-(0[1-9]|1[0-2])#B[1-9]\d*$`** (예: `2026-07#B1`) — **8-1 신규 pattern 추가**
  - `docs/conventions.md §6` EXTENSION (virtual budget 명시)
- Errors: `{code, message_ko, details, trace_id}` (AD-15 §4 envelope, 7-1 + 7-2 + 8-1 typed exception main.py handler 등록)

**AD-22 ledger append-only**:
- `fiscal_period_snapshots.state='draft'` ONLY (engine은 state 전이 안 함, 7-1 + 7-2 패턴 동일)
- **8-1은 별도 `budget_scenarios` table 사용** — `fiscal_period_snapshots` 와 별도 (AD-22 engine purity + 8-3 pre-standard cost preview에서 `engine_type='budget'` 으로 join 예정, honestly DEFER)

**NFR16 determinism**:
- V8 byte-identical CI gate: 100회 동일 입력 → 100회 동일 `compute_budget_scenario_hash(scenario)` (Epic 4 baseline extension + 7-1 + 7-2 패턴)
- `hashlib.sha256(repr(scenario).encode()).hexdigest()` 결정론 digest

**NFR17 monetary types (AD-8)**:
- `scenario_index` INT (1, 2, …) — KRW 정수와 무관 (예산 시나리오 식별자)
- `scenario_hash` TEXT (16바이트 hexdigest = 32 chars)
- 8-1은 monetary types 무관 (예산 시나리오 metadata only, 실제 KRW 계산은 8-3 pre-standard cost preview honestly DEFER)

**NFR18 ko-KR MVP lock**:
- `ko-KR.json` 단일 SSOT (CR 11-4 D-002)
- 8-1 메시지: "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)" — ko-KR only

**AD-9 Seoul TZ-aware**:
- `created_at_kst` TIMESTAMPTZ DEFAULT NOW() (Postgres native)
- `created_at_kst` 결정론 hash용 ISO 8601 string — service layer에서 inject (NOT engine)

**Epic 8 capability (8-1 + 8-2 + 8-3)**:
- **`Capability.BUDGET_SCENARIO`** 단일 capability (cj-style 3-story 통합, 7-1 + 7-2 동일 적용)
- 8-2 (variance table) + 8-3 (pre-standard cost preview) 모두 reuse — **신규 capability 추가 0건** (CR 11-3 즉시 sweep 회피)

**CR 11-3 lessons carry**:
- D-2 (ALLOWED_SERVICE_SUBMODULES 즉시 sweep — `m8_budget.budget_period_key_serializers` 추가)
- D-3 (ruff scoped auto-fix sweep 일괄, W292 / UP038 / SIM300 / SIM222 / ERA001)
- SDR separate line parser (CR 11-2 lesson)
- `def test_+asyncio.run` project convention (CR 4-3)

**CR 11-4 lessons carry**:
- D-001 (page.tsx mount MUST actually mount `<BudgetScenarioList>` JSX)
- D-002 (단일 `apps/web/messages/ko-KR.json` only — NOT `apps/web/lib/ko-KR.json`)
- D-005 (TS mirror unknown state MUST raise — `deriveBudgetPeriodKeyTS` invalid pattern → throw `ERROR_CODE_INVALID_INPUT`)
- P-015 (ko-KR.json SSOT drift detector test — `budget_scenario` namespace 정합)

**CR 12-1 lessons continue**:
- L1 (PyJWT `verify_exp=False` deterministic testability — N/A for 8-1, no token)
- L2 (AES-256-GCM lazy wrapper — N/A for 8-1, no PII)
- L3 (`_to_budget_scenario(orm_row)` ORM→kernel boundary conversion, 12-1 _to_totp_state + 12-3 _to_deletion_state precedent)
- L4 (BUDGET_SCENARIO capability industry-agnostic precedent)

**CR 12-5 lessons continue**:
- D-13 (structural cross-language drift detector — `test_m8_budget_cross_language_drift.py` Python↔TS 10+ vectors, 7-1 + 7-2 패턴)
- D-14 (typed exception main.py envelope handler 등록 — `ScenarioLimitExceededError` 409 + `InvalidVirtualBudgetPeriodKeyError` 422 + `BudgetScenarioNotFoundError` 404)
- L3 (3-layer defense — route `@require_role("owner","member")` + service `validate_scenario_uniqueness` + DB `UNIQUE(tenant_id, real_period_key)` defense-in-depth)
- L4 (honest-DEFER discipline — 7 honestly DEFER items)

**A19 lessons carry**:
- math surface migration pattern (`packages/services/m2_input/inventory_math.py` precedent — math surface는 `packages/cost_engine/` 또는 `packages/services/<module>/<math>.py`)
- 8-1은 `packages/cost_engine/budget_period_key.py` (분리 surface, A19 cohesion pattern 3번째 검증)

### Source tree components to touch

**NEW files**:
1. `packages/cost_engine/budget_period_key.py` (~250 lines)
2. `tests/cost_engine/test_budget_period_key.py` (~20 cases)
3. `tests/cost_engine/test_budget_period_key_no_io_imports.py` (~5 cases, 7-1 + 7-2 패턴 미러)
4. `tests/cost_engine/test_budget_period_key_determinism.py` (~5 cases, 7-1 + 7-2 패턴 미러)
5. `packages/services/m8_budget/budget_period_key_serializers.py` (~60 lines)
6. `tests/services/m8_budget/test_budget_scenario_service.py` (~18 cases)
7. `apps/api/modules/m8_budget/services/budget_scenario_service.py` (~150 lines)
8. `apps/api/modules/m8_budget/handlers.py` (~150 lines)
9. `apps/api/modules/m8_budget/schemas.py` (~80 lines, Pydantic v2)
10. `apps/api/modules/m8_budget/exceptions.py` (~60 lines, 3 typed exceptions)
11. `tests/api/test_m8_budget_handlers.py` (~15 cases)
12. `apps/api/alembic/versions/0026_budget_scenarios.py` (~120 lines, 8 columns + 2 UNIQUE + 1 index)
13. `supabase/policies/0016_budget_scenarios_rls.sql` (~60 lines, 4-policy split + FORCE RLS)
14. `tests/api/test_alembic_0026_budget_scenarios.py` (~8 cases)
15. `tests/api/test_rls_0016_budget_scenarios.py` (~6 cases)
16. `tests/integration/test_m8_budget_cross_language_drift.py` (~10 cases, 7-1 + 7-2 패턴 미러)
17. `tests/integration/test_m8_budget_audit_consistency.py` (~4 cases)
18. `tests/integration/test_m8_budget_m11_close_isolation.py` (~5 cases)
19. `apps/web/app/[locale]/(dashboard)/budget/scenarios/layout.tsx` (NEW RSC layout)
20. `apps/web/app/[locale]/(dashboard)/budget/scenarios/page.tsx` (NEW RSC page)
21. `apps/web/components/m8-budget/BudgetScenarioList.tsx` (~200 lines)
22. `apps/web/components/m8-budget/BudgetScenarioCreateButton.tsx` (~80 lines)
23. `apps/web/components/m8-budget/BudgetScenarioCreateModal.tsx` (~180 lines)
24. `apps/web/components/m8-budget/BudgetScenarioDetail.tsx` (~100 lines)
25. `apps/web/components/m8-budget/BudgetScenarioList.test.tsx` (~8 cases)
26. `apps/web/components/m8-budget/BudgetScenarioCreateButton.test.tsx` (~6 cases)
27. `apps/web/components/m8-budget/BudgetScenarioCreateModal.test.tsx` (~10 cases)
28. `apps/web/components/m8-budget/BudgetScenarioDetail.test.tsx` (~5 cases)
29. `apps/web/lib/m8-budget-scenario.ts` (~120 lines TS mirror)
30. `apps/web/lib/m8-budget-scenario-schema.ts` (~50 lines Zod schema)
31. `apps/web/lib/m8-budget-scenario.test.ts` (~10 cases)
32. `docs/virtual-budget-period-key.md` (~250 lines, 9 sections)

**MODIFIED files**:
1. `packages/cost_engine/__init__.py` — export 4 NEW pure functions (`derive_budget_period_key` + `parse_virtual_budget_period_key` + `validate_scenario_uniqueness` + `compute_budget_scenario_hash`) + 3 frozen dataclasses (`BudgetPeriodKeyParts` + `BudgetScenario` + `ScenarioLimitExceededError`) (5 lines)
2. `apps/api/main.py` — `m8_budget` router include + 3 NEW exception handlers 등록 (cj-style 7번째 epic pattern, ~+15 lines)
3. `apps/api/core/capability.py` — `Capability.BUDGET_SCENARIO = "budget_scenario"` EXTENSION (Industry enum 4종 모두 ✅ grant, 12-1 L4 + 7-1 L4 precedent, ~+5 lines)
4. `apps/api/modules/m8_budget/__init__.py` — placeholder description → module authority docstring (cj-style 7번째 epic pattern)
5. `apps/web/messages/ko-KR.json` — `budget_scenario` namespace EXTENSION (~15 strings, 7-1 cvp_simulation + 7-2 projection namespace와 분리)
6. `apps/web/lib/menu-config.ts` — `/budget/scenarios` sidebar nav EXTENSION (1 entry, 7-1 + 7-2 패턴)
7. `apps/web/components/m8-budget/index.ts` — barrel export + BudgetScenario (cj-style 7번째 epic pattern)
8. `docs/capability-matrix.md` v1.17 EXTENSION (`BUDGET_SCENARIO` row 신규 + 4 industries ✅ 마킹, 8-1 + 8-2 + 8-3 reuse 명시)
9. `docs/conventions.md` §AD-24 EXTENSION (virtual budget key 명시, `^\d{4}-(0[1-9]|1[0-2])#B[1-9]\d*$` + scenario lock 1차 MVP 한도)
10. `docs/conventions.md` §AD-11 layer rule EXTENSION (m8_budget service layer 명시, 7-1 + 7-2 + 8-1)
11. `docs/architecture-inventory.md` EXTENSION (m8_budget module entry)
12. `docs/deferred-work.md` EXTENSION (7 honestly DEFER items)
13. `_bmad-output/implementation-artifacts/sprint-status.yaml` — 8-1 status sync + last_updated_note + epic-8 status backlog → in-progress
14. `tests/architecture/test_api_calls_only_ports.py` — ALLOWED_SERVICE_SUBMODULES sweep EXTENSION (m8_budget.budget_period_key_serializers 추가, CR 11-3 D-2)
15. `tests/integration/test_ko_kr_json_ssot.py` — `budget_scenario` namespace 정합 EXTENSION (CR 12-1 P-015)

**Total**: 32 NEW + 15 MODIFIED = 47 files (~3,200 lines code + ~1,000 lines tests + ~400 lines docs)

### Testing standards summary

**Backend (pytest)**:
- **Pure kernel** (20+ cases): edge cases 5종 ValueError + frozen=True enforcement + 100회 determinism (7-1 + 7-2 패턴)
- **Engine purity** (5+ cases): AST parser로 forbidden imports 차단 검증 (7-1 + 7-2 패턴 미러)
- **V8 determinism** (5+ cases): byte-identical `scenario_hash` 100회
- **Service layer** (18+ cases): scenario CRUD + scenario lock + RLS same-tenant + 0 DB writes verification + DB UNIQUE race condition
- **Handlers** (15+ cases): 201 Created + 200 OK + 403 CAPABILITY_NOT_GRANTED + 403 FORBIDDEN_ROLE + 409 SCENARIO_LIMIT_EXCEEDED + 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY + 404 BUDGET_SCENARIO_NOT_FOUND + RLS same-tenant + X-Scenario-Hash 헤더 V8 determinism
- **Alembic** (8+ cases): 8 columns 정확성 + 2 UNIQUE constraints + CHECK constraints + down_revision 정확성
- **RLS** (6+ cases): SELECT/INSERT/UPDATE/DELETE 정책 + FORCE RLS + 다른 테넌트 0건 노출
- **Cross-language drift** (10+ cases): Python ↔ TS parity 10 vectors + edge cases 동일 (7-1 + 7-2 패턴 미러)
- **Audit no-write** (4+ cases): `audit_logs` row 0건 + `monthly_closing_report_status` 변경 0건 + `fiscal_period_snapshots` 변경 0건
- **M11 close isolation** (5+ cases): M11 close lock이 virtual key를 무시하는지 검증 (epics.md AC #4 verbatim)

**Frontend (vitest)**:
- **BudgetScenarioList** (8+ cases): list fetch + empty state + scenario 1개 잠금 메시지
- **BudgetScenarioCreateButton** (6+ cases): disabled / enabled / tooltip 정확성
- **BudgetScenarioCreateModal** (10+ cases): form submit + 409/422/403 에러 처리 + 8-3 placeholder
- **BudgetScenarioDetail** (5+ cases): scenario detail 표시
- **TS mirror parity** (10+ cases): Python `derive_budget_period_key` vs TS `deriveBudgetPeriodKeyTS` 동일 결과 (7-1 + 7-2 패턴)

**Architecture tests**:
- **ALLOWED_SERVICE_SUBMODULES sweep** (1 case): `m8_budget.budget_period_key_serializers` 추가 검증 (CR 11-3 D-2)
- **Engine purity** (5+ cases): AST parser로 forbidden imports 차단 검증 (7-1 + 7-2 패턴 미러)

### Project Structure Notes

**Alignment with unified project structure** (cj-style 7번째 epic 검증):
- `apps/api/modules/m8_budget/` (Epic 11 m11_close + 12-1 m12_account + 7-1 m7_simulation + 8-1 m8_budget 패턴)
- `packages/services/m8_budget/` (thin wrappers, A19 math surface 패턴 + 7-1 + 7-2 + 8-1 EXTENSION)
- `packages/cost_engine/budget_period_key.py` (pure kernel, 7-1 cvp.py + 7-2 projection.py와 surface 분리, A19 cohesion pattern 3번째)
- `apps/web/components/m8-budget/` (12-1 m12-account + 7-1 CVPSimulationClient + 7-2 ProjectionClient + 8-1 BudgetScenarioList 패턴)
- `apps/web/app/[locale]/(dashboard)/budget/scenarios/` (12-1 /account/security + 7-1 /simulation/cvp + 7-2 /simulation/projection + 8-1 /budget/scenarios 패턴)

**Detected conflicts or variances**:
- None — 8-1은 7-1 + 7-2 wire pattern 그대로 미러 (capability industry-agnostic + cost_engine surface 분리는 A19 cohesion 3번째 검증)
- **`packages/cost_engine/budget_period_key.py`** 는 **순수 함수 surface** (7-1 cvp.py + 7-2 projection.py 와 cross-import 없음)
- **`apps/api/modules/m8_budget/`** 는 현재 `__init__.py` placeholder만 존재 → 본 스토리에서 populate (cj-style 7번째 epic pattern)

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-8-Budget-vs-Actual`] — Epic 8 + Story 8.1 verbatim
- [Source: `_bmad-output/planning-artifacts/prd.md#§F8.1`] — PRD §F8.1 (1차 시나리오 1개만 허용 + 2개 이상 생성 시도 차단)
- [Source: `_bmad-output/planning-artifacts/prd.md#§15-NON-GOAL-for-MVP-#2`] — PRD §15 NON-GOAL #2 (복수 예산 시나리오 1차 MVP 제외, 2차 예정, trigger: ≥5 테넌트 요청 시)
- [Source: `_bmad-output/planning-artifacts/prd.md#§10-예산-시나리오-(결정-Q-D)`] — PRD §10 (예산 시나리오 결정 Q-D)
- [Source: `_bmad-output/planning-artifacts/prd.md#UJ-2-예산-시나리오---가상-기간으로-미리-시험`] — PRD UJ-2 (예산 시나리오 user journey)
- [Source: `docs/conventions.md#§6-Period-Keys-(AD-24)`] — AD-24 period key typed pattern (real `YYYY-MM` vs virtual `YYYY-MM#B<n>`)
- [Source: `docs/conventions.md#§6.1-POST-/-api/v1/calc-period_key-validation-(Story-4.2)`] — Story 4.2 period_key validation precedent
- [Source: `docs/conventions.md#§6.2-Engine-period_key-validation`] — Engine period_key validation (4중 검증)
- [Source: `docs/conventions.md#§8-Forbidden-Patterns-(요약)`] — AD-8 / AD-11 / AD-15 / AD-22 forbidden patterns
- [Source: `_bmad-output/implementation-artifacts/7-1-bep-slider-1-second-recompute.md`] — Story 7.1 spec 진입 패턴 (cj-style 6번째 epic + CVP_SIMULATION capability wire)
- [Source: `_bmad-output/implementation-artifacts/7-2-next-month-projection-4-required-parameters.md`] — Story 7.2 spec 진입 패턴 (cj-style 6번째 epic + projection service layer)
- [Source: `_bmad-output/implementation-artifacts/handoff-2026-08-15-a19-inventory-projection-deprecate-done.md`] — A19 carry-over DONE (math surface migration 패턴)
- [Source: `_bmad-output/implementation-artifacts/epic-7-retro-2026-08-15.md`] — Epic 7 close-out retro §7 A20 (Epic 8 cj-style 3-story 분할 권장안 = 8-1 + 8-2 + 8-3)
- [Source: `_bmad-output/implementation-artifacts/epic-11-retro-2026-08-09.md`] — Epic 11 close-out retro §7 A14 cj-style 3-story 분할 권장
- [Source: `_bmad-output/implementation-artifacts/12-1-two-factor-auth-mandatory-gate.md`] — Story 12.1 L4 industry-agnostic capability precedent
- [Source: `_bmad-output/implementation-artifacts/12-3-account-deletion-retention-consent.md#AC-7`] — CR 12-1 L3 _to_<state> ORM→kernel boundary conversion pattern
- [Source: `docs/capability-matrix.md`] — capability matrix v1.17 (8-1 BUDGET_SCENARIO row 신규 + 4 industries ✅, 8-2 + 8-3 reuse)
- [Source: `docs/conventions.md#AD-11-layer-rule`] — 의존 방향 명시
- [Source: `docs/virtual-budget-period-key.md`] (will be NEW) — 8-1 도큐먼트

## Dev Agent Record

### Agent Model Used

Claude Opus 5 (claude-opus-5)

### Debug Log References

N/A (spec 진입 단계 — bmad-dev-story 진입 시 작성)

### Completion Notes List

(To be filled by bmad-dev-story T1~T8 execution)

### File List

(To be filled by bmad-dev-story T1~T8 execution)
