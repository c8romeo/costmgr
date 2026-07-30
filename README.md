# bizup / costmgr

> **원가 관리 SaaS** — modular monolith + hexagonal core (AD-1, AD-5, AD-11)
> 
> - PRD: `_bmad-output/planning-artifacts/prd.md` (v2.0 final)
> - Architecture: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md`
> - Epics: `_bmad-output/planning-artifacts/epics.md` (13 Epic · 42 Story)
> - Sprint status: `_bmad-output/implementation-artifacts/sprint-status.yaml`
> - Handoff: `_bmad-output/implementation-artifacts/HANDOFF.md`

---

## Quick start (Story 0.1 in place)

```bash
# 1) Toolchain
nvm use                                  # Node 24.18.0 (per .nvmrc)
py -3.12 -m uv --version                 # uv 0.11.32

# 2) Install
pnpm install --frozen-lockfile
py -3.12 -m uv sync

# 3) Lint (architecture boundaries)
pnpm lint:deps                           # dependency-cruiser (TS layer rules)
py -3.12 -m uv run import-linter         # import-linter (Python layer rules)

# 4) Tests (architecture + engine purity)
py -3.12 -m uv run pytest tests/architecture tests/cost_engine -v
```

If any of these fails, the boundary has been broken. The build blocks PRs on failure.

---

## Architecture at a glance

```
apps/web   (Next.js App Router)  ─┐
                                  ├─→ ports (typed contracts)
apps/api   (FastAPI monolith)    ─┤
                                  ├─→ services (orchestration)
                                  │
                                  └─→ packages.cost_engine
                                       ├─ ports      (Protocol types)
                                       ├─ core       (pure: no I/O, no DB, no clock)
                                       └─ adapters   (DB, REST, CSV/Excel — empty in 0.1)
```

**Direction is enforced by CI**:

- `dependency-cruiser` (`.dependency-cruiser.cjs`) for TypeScript / Next.js
- `import-linter` (`pyproject.toml [tool.importlinter]`) for Python

**Engine purity is enforced by AST tests**:

- `tests/cost_engine/test_no_io_imports.py` — no `sqlalchemy`, `fastapi`, `requests`, `time`, `random`, `os`, etc. inside `packages/cost_engine/`
- `tests/cost_engine/test_money_purity.py` — KRW/USD type sanity (AD-8)

**API↔engine boundary is enforced at runtime**:

- `tests/architecture/test_api_calls_only_ports.py` — `apps.api` may only import `packages.cost_engine.ports`, never `core` or `adapters` directly

---

## Source tree (Story 0.1)

```
costmgr/
├── apps/
│   ├── web/                          Next.js 15.5 App Router (stub: landing page)
│   │   ├── app/{layout,page}.tsx
│   │   ├── package.json              (pinned: next 15.5, react 19.1)
│   │   └── tsconfig.json
│   └── api/                          FastAPI (stub: /health)
│       ├── main.py
│       ├── core/                     (settings/security/db/audit land in Story 0.2)
│       ├── modules/                  13 module folders (m0_onboarding…m12_account)
│       └── pyproject.toml
├── packages/
│   ├── cost_engine/                  PURE Python — hexagonal core
│   │   ├── core/money.py             (KRW/USD, AD-8)
│   │   ├── ports/                    (calc_port, ccr_port, reversal_port)
│   │   ├── adapters/                 (empty — Story 0.2+ populates)
│   │   └── tests/regression_v8/      (placeholder — Story 4.4)
│   ├── services/                     (orchestration — empty in 0.1)
│   └── ports/                        (cross-module contracts — empty in 0.1)
├── tests/
│   ├── architecture/                 (API↔engine boundary tests)
│   └── cost_engine/                  (engine-purity tests)
├── scripts/
│   └── check_stack_pin.mjs           (stack pin drift check — Story 0.3 expands)
├── .github/workflows/ci.yml          (lint-deps, lint-imports, test-architecture)
├── .dependency-cruiser.cjs
├── .nvmrc · .python-version · .npmrc
├── package.json · pnpm-workspace.yaml
├── pyproject.toml                    (uv workspace + import-linter + ruff + pytest)
└── README.md
```

---

## Status (as of 2026-07-29)

| | |
|---|---|
| Story 0.1 | ✅ Done — modular monolith + hexagonal core |
| Story 0.2 | ✅ Done — Supabase multi-tenancy + RLS |
| Story 0.3 | ✅ Done — stack-pin lockfile build pipeline |
| Story 0.4 | 🔍 Review — cross-language conventions + linters |
| **Story 1.1** | ✅ **Done — industry selector + menu auto-toggle** |
| Story 1.2 | ⏳ Pending — settings wizard (calculation block) |
| Story 1.3 | ⏳ Pending — AI document extraction + confidence badge |
| Epic 1 | 🔄 In progress |

See `_bmad-output/implementation-artifacts/sprint-status.yaml` for the full tracker.

---

## Onboarding flow (Story 1.1)

신규 가입 후 첫 로그인 시 자동으로 4지선다(업종 선택) 화면으로 이동합니다:

```
[Story 0.2: signup]
   │
   ▼
[Story 1.1: /onboarding/industry  ── 4지선다]
   │   ① 제조업         ② 서비스업
   │   ③ 제조+서비스     ④ 제조+서비스+기타
   │
   ▼ POST /api/v1/tenant-settings/onboarding/industry
[Story 1.1: tenant_settings.onboarding JSONB updated]
   │
   ▼ GET /api/v1/tenant-settings
[Story 1.1: /dashboard (sidebar filtered by industry)]
```

### 핵심 결정사항 (locked, 2026-07-29)

1. **7-day grace period**: 첫 선택 후 7일 이내 `is_initial=false` 변경 허용
   (응답에 `X-Onboarding-Warning: initial-change-allowed-for-7-days` 헤더 첨부).
   7일 경과 또는 첫 계산 후 → `409 INDUSTRY_LOCKED` (A7 전진법).
2. **업종 라벨**: PRD §4.1 정식 셋 (`제조업 / 서비스업 / 제조+서비스 / 제조+서비스+기타`).
3. **역할 게이트**: `owner`만 업종 변경 가능 (`member`/`viewer`/`consultant_proxy` → `403 FORBIDDEN_ROLE`).
4. **서비스업 메뉴**: BOM + 기초재고 + 수불부 숨김 (epics AC explicit — PRD §4.1 wording은 짧은 리스트지만 AC가 더 포괄적).

### 업종별 노출 메뉴 (PRD §4.1 표)

| 업종 | 노출 메뉴 | 비고 |
|---|---|---|
| ① 제조업 | BOM·기초재고·수불부·품목·계정·... | 원가풀·활동·동인 **숨김** |
| ② 서비스업 | 원가풀·활동·동인·계정·... | BOM·기초재고·수불부 **숨김** |
| ③ 제조+서비스 | 모두 노출 + **카브아웃 분할** | §7.3 [A10] 재무제표 업로드 필수 |
| ④ 제조+서비스+기타 | ③과 동일 + 격리 버킷 | '기타' 부문은 m3_calculate 내부에서 격리 |

단일 진실 공급원은 `packages/services/m0_onboarding/industry_menu.py` (Python),
TypeScript 미러는 `apps/web/lib/menu-config.ts`. 드리프트는
`tests/integration/test_menu_config_consistency.py`가 차단합니다.

자세한 내용: [`docs/onboarding-flow.md`](docs/onboarding-flow.md).

---

## Anti-pattern checklist (do NOT do these)

- ❌ `import sqlalchemy` inside `packages/cost_engine/` (AD-1, AD-5)
- ❌ `import fastapi` inside `packages/cost_engine/` (AD-5)
- ❌ `from packages.cost_engine.core import ...` inside `apps/api/` (use `packages.cost_engine.ports`)
- ❌ `from packages.cost_engine.adapters import ...` inside `packages/cost_engine/core/` (AD-11)
- ❌ `import time` / `import random` inside `packages/cost_engine/` (AD-5)
- ❌ `import os` / `os.environ` inside `packages/cost_engine/` (config flows via constructor)
- ❌ `float` for KRW/USD values (use `int` for KRW, `Decimal` for USD — AD-8)
- ❌ `^`, `~`, or `>=` in pinned package versions (use exact `==` — AD-14)
- ❌ Celery, Kafka, Redis as persistent queue (1-operator constraint)
