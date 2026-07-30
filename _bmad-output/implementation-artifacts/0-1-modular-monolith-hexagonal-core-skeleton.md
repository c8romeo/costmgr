---
baseline_commit: bd58c180234abae60a1bd4e8bcd38ea766263d9a
---
# Story 0.1: Modular Monolith + Hexagonal Core Skeleton

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform engineer**,
I want **the monorepo to enforce the `ui → api → services → ports → engine` dependency direction from day one (with `packages/cost_engine/` importing only stdlib + `decimal` + `numpy`) and CI to fail any import that violates this rule**,
so that **no module accidentally couples the cost engine to DB drivers, web frameworks, the system clock, or randomness — preserving 1원 unit deterministic regression (V8) and the hexagonal isolation promise (AD-1·AD-5·AD-11)**.

## Acceptance Criteria

1. **Given** the bizup monorepo is initialized at `{project-root}/` (Greenfield — no source files yet)
   **When** I scaffold `apps/web/` (Next.js 16.2.11), `apps/api/` (FastAPI 0.139.2), `packages/cost_engine/`, `packages/services/`, and `packages/ports/`
   **Then** each workspace has its own `package.json` (TS) or `pyproject.toml` (Python) declaring explicit, restricted import boundaries
   **And** `packages/cost_engine/` declares dependencies restricted to Python stdlib + `decimal` + `numpy` (read-only math), with no DB/web/clock/randomness modules allowed in its dependency list or import surface

2. **Given** the lint tools `dependency-cruiser` (TypeScript) and `import-linter` (Python) are installed
   **When** I add `.dependency-cruiser.cjs` enforcing `apps/web → apps/api → packages/services → packages/ports → packages/cost_engine/core` and `import-linter` enforcing `packages/cost_engine/` cannot import `sqlalchemy`, `fastapi`, `starlette`, `requests`, `httpx`, `psycopg`, `asyncpg`, `pydantic` (except as a type-only `pydantic.BaseModel` for pure dataclasses), `time`, `datetime`, `random`, `os.environ`, `socket`
   **Then** a CI lint step (`pnpm lint:deps` + `uv run lint:imports`) runs on every PR
   **And** the build fails (non-zero exit) if any disallowed import is detected
   **And** a fixture negative test (`tests/cost_engine/test_no_io_imports.py`) verifies that all forbidden modules are absent from the engine's bytecode/import graph

3. **Given** the `apps/api/` FastAPI module is scaffolded
   **When** I add a `services/` layer and a `ports/` interface module
   **Then** `apps/api/` may import only from `packages/ports/` interfaces (typed ports) and never from `packages/cost_engine/core/` internals
   **And** `apps/api/` registers `packages/cost_engine.adapters.db` as the concrete adapter implementing the port
   **And** an architectural fixture test (`tests/architecture/test_api_calls_only_ports.py`) imports the API module and asserts via `importlib` that no submodule of `cost_engine.core` is referenced

4. **Given** the monorepo is scaffolded with restricted imports and CI enforcement
   **When** a developer (or AI agent) attempts to `import sqlalchemy` or `from fastapi import Request` inside `packages/cost_engine/`
   **Then** the CI lint step blocks the PR with a clear violation message naming the file + line + forbidden module
   **And** the violation points to the specific AD (AD-1 / AD-5 / AD-11) being violated
   **And** the developer can run `pnpm lint:deps` and `uv run lint:imports` locally to reproduce the failure before pushing

## Tasks / Subtasks

- [ ] **Task 1 — Initialize monorepo workspaces** (AC: #1)
  - [ ] Subtask 1.1 — Create root `package.json` with pnpm workspaces (`apps/*`, `packages/*`)
  - [ ] Subtask 1.2 — Create root `pyproject.toml` with uv workspace members (`apps/api`, `packages/cost_engine`, `packages/services`, `packages/ports`)
  - [ ] Subtask 1.3 — Create root `pnpm-workspace.yaml` listing `apps/*` and `packages/*`
  - [ ] Subtask 1.4 — Add `.gitignore`, `.editorconfig`, `.nvmrc` (Node 24.18.0), `.python-version` (3.12.x), root `README.md` with AD-1/AD-11 references

- [ ] **Task 2 — Scaffold `apps/web/` Next.js frontend** (AC: #1)
  - [ ] Subtask 2.1 — Run `pnpm create next-app@16.2.11 apps/web --typescript --tailwind --app --src-dir --import-alias "@/*"` (App Router)
  - [ ] Subtask 2.2 — Pin React 19.2.8, TypeScript 7.0.2, Tailwind 4.3.3 in `apps/web/package.json`
  - [ ] Subtask 2.3 — Add empty module folders: `apps/web/app/[locale]/(dashboard)/{m0-onboarding,m1-baseline,m2-input,m3-calculate,m4-inventory,m5-reports,m6-verification,m7-simulation,m8-budget,m9-abc,m10-ai,m11-close,m12-account}/`
  - [ ] Subtask 2.4 — Add placeholder `apps/web/app/layout.tsx` with ko-KR locale, Pretendard font fallback (design token hook deferred to UX epic)

- [ ] **Task 3 — Scaffold `apps/api/` FastAPI backend** (AC: #1, #3)
  - [ ] Subtask 3.1 — Run `uv init apps/api` with FastAPI 0.139.2, Pydantic 2.13.4, SQLAlchemy 2.0.51 async, structlog 26.1.0, OpenTelemetry API 1.44.0
  - [ ] Subtask 3.2 — Create module folders `apps/api/modules/{m0_onboarding,m1_baseline,m2_input,m3_calculate,m4_inventory,m5_reports,m6_verification,m7_simulation,m8_budget,m9_abc,m10_ai,m11_close,m12_account,core}/` — empty `__init__.py` files
  - [ ] Subtask 3.3 — Create minimal `apps/api/main.py` mounting a single `/health` endpoint returning `{"status":"ok"}` — no business logic yet
  - [ ] Subtask 3.4 — Add `apps/api/core/` with `settings.py` (Pydantic Settings reading env vars per AD-9: `SUPABASE_URL`, `DATABASE_URL`)

- [ ] **Task 4 — Scaffold `packages/cost_engine/` pure Python core** (AC: #1, #2)
  - [ ] Subtask 4.1 — Create `packages/cost_engine/pyproject.toml` with dependencies = `["decimal (stdlib)", "numpy>=2.0"]` (numpy optional, gated by `[engine-math]` extra) and dev-dependencies = `["pytest>=9.1.1"]`
  - [ ] Subtask 4.2 — Create package structure: `packages/cost_engine/{core,ports,adapters/{db,rest,csv_excel},tests/regression_v8}/`
  - [ ] Subtask 4.3 — Create empty `packages/cost_engine/core/__init__.py` with module docstring citing AD-1 + AD-5
  - [ ] Subtask 4.4 — Create empty port interfaces in `packages/cost_engine/ports/`: `calc_port.py`, `ccr_port.py`, `reversal_port.py` — all using `typing.Protocol` (no I/O, no Pydantic models in core)
  - [ ] Subtask 4.5 — Create empty `packages/cost_engine/adapters/__init__.py` (db/rest/csv_excel adapters created in later stories)

- [ ] **Task 5 — Scaffold `packages/services/` and `packages/ports/`** (AC: #3)
  - [ ] Subtask 5.1 — Create `packages/services/pyproject.toml` (orchestration layer; depends on `ports` + `cost_engine` ports only)
  - [ ] Subtask 5.2 — Create `packages/ports/pyproject.toml` (pure interface definitions; depends only on stdlib + typing)
  - [ ] Subtask 5.3 — Empty service stubs: `packages/services/{month_input_adapter,calc_orchestrator,verification_runner,reversal_handler}.py`

- [ ] **Task 6 — Configure `dependency-cruiser` for TypeScript** (AC: #2)
  - [ ] Subtask 6.1 — `pnpm add -D -w dependency-cruiser@latest`
  - [ ] Subtask 6.2 — Create root `.dependency-cruiser.cjs` enforcing:
    - `apps/web` → may not import `apps/api`, `packages/*`
    - `apps/api` (TS portion) → may import `packages/ports` types only, never `packages/cost_engine/**`
    - `packages/services` → may import `packages/ports`, `packages/cost_engine/ports/**`
    - `packages/ports` → may import only stdlib/typing — no DB/web/clock/random
  - [ ] Subtask 6.3 — Add `pnpm lint:deps` script in root `package.json` running `depcruise --validate .dependency-cruiser.cjs apps packages`

- [ ] **Task 7 — Configure `import-linter` for Python** (AC: #2)
  - [ ] Subtask 7.1 — Add dev dep `import-linter>=2.0` to root `pyproject.toml`
  - [ ] Subtask 7.2 — Create `.import-linter.ini` (or `[tool.importlinter]` in root `pyproject.toml`) with contracts:
    - `cost_engine_forbidden_io` — `packages.cost_engine` must NOT import `sqlalchemy`, `fastapi`, `starlette`, `requests`, `httpx`, `psycopg`, `asyncpg`, `pydantic` (allowed: `pydantic.BaseModel` only in `ports/` for input dataclasses), `time`, `datetime.datetime.now`, `random`, `os.environ`, `socket`, `subprocess`
    - `api_calls_only_ports` — `apps.api` must import `packages.cost_engine` only via `packages.cost_engine.ports` module
    - `engine_to_adapters_forbidden` — `packages.cost_engine.core` must NOT import `packages.cost_engine.adapters`
  - [ ] Subtask 7.3 — Add `uv run lint:imports` script using `lint-imports` (import-linter CLI) — fails on contract violation

- [ ] **Task 8 — Add architectural fixture tests** (AC: #2, #3)
  - [ ] Subtask 8.1 — Create `tests/cost_engine/test_no_io_imports.py` using `ast` to parse every `.py` under `packages/cost_engine/` and assert no `ForbiddenImports` set
  - [ ] Subtask 8.2 — Create `tests/architecture/test_api_calls_only_ports.py` using `importlib` to import `apps.api.main` and assert `cost_engine.core` is NOT in `sys.modules` references
  - [ ] Subtask 8.3 — Wire fixture tests into root `pyproject.toml` `[tool.pytest.ini_options]` `testpaths = ["tests"]`

- [ ] **Task 9 — CI lint pipeline** (AC: #2, #4)
  - [ ] Subtask 9.1 — Create `.github/workflows/ci.yml` with jobs: `lint-deps` (Node), `lint-imports` (Python), `test-architecture` (pytest tests/architecture + tests/cost_engine/test_no_io_imports.py)
  - [ ] Subtask 9.2 — Each job runs on every PR + push to `main`; failures block merge
  - [ ] Subtask 9.3 — CI message on failure points to the violated AD (AD-1 / AD-5 / AD-11)

- [ ] **Task 10 — Local dev verification** (AC: #4)
  - [ ] Subtask 10.1 — Document `pnpm install`, `uv sync`, `pnpm lint:deps`, `uv run lint:imports`, `uv run pytest tests/architecture tests/cost_engine/test_no_io_imports.py` in root `README.md`
  - [ ] Subtask 10.2 — Add a "Try to break the rule" snippet to README showing the intentional negative import + expected failure output (developer onboarding aid)

## Dev Notes

### Architecture patterns to follow

- **AD-1 (Modular Monolith + Hexagonal Core)** — `packages/cost_engine/` is a **hexagonal core**: pure Python domain, ports for inbound/outbound, adapters at the boundary. The SaaS shell (auth, billing, multi-tenancy, reporting UI) is a **modular monolith**: one FastAPI deployable on Railway, module boundaries enforced by directory structure and import rules. The frontend is a Next.js App Router monolith on Vercel.
- **AD-5 (Cost-engine purity)** — Engine functions are pure `f(inputs: dataclass) -> dataclass`. **No I/O, no DB, no clock, no randomness, no global state, no snapshot writes, no logs** inside the engine. Everything that touches the outside world lives in `adapters/` (db/rest/csv_excel).
- **AD-11 (Dependency direction)** — `ui → api → services → ports → engine`. Adapters implement ports. Engine-to-adapter/service/UI imports and direct adapter-to-engine imports are **forbidden and CI-checked**.
- **AD-15 (Cross-language conventions)** — DB/Python `snake_case`; Next.js routes `kebab-case`; React/TS types `PascalCase`. ISO-8601 UTC `TIMESTAMPTZ`, KST display. UUID v7 IDs; ULID `tenant_id`. `{code, message_ko, details, trace_id}` errors.

### Cold-start stack pin (AD-14)

| Tool | Version | Source |
|------|---------|--------|
| Node.js | 24.18.0 LTS | `.nvmrc` |
| Python | 3.12.x | `.python-version` |
| pnpm | latest 9.x | root devDep |
| uv | 0.11.32 | workspace root |
| Next.js | 16.2.11 (App Router) | `apps/web/package.json` |
| React | 19.2.8 | `apps/web/package.json` |
| TypeScript | 7.0.2 | `apps/web/package.json` |
| Tailwind CSS | 4.3.3 | `apps/web/package.json` |
| FastAPI | 0.139.2 | `apps/api/pyproject.toml` |
| Pydantic | 2.13.4 | `apps/api/pyproject.toml` |
| SQLAlchemy | 2.0.51 async | `apps/api/pyproject.toml` |
| structlog | 26.1.0 | `apps/api/pyproject.toml` |
| OpenTelemetry API | 1.44.0 | `apps/api/pyproject.toml` |
| pytest | 9.1.1 | root devDep |
| dependency-cruiser | latest (verify ≥ 16.x) | root devDep |
| import-linter | ≥ 2.0 | root devDep |

**Banned infrastructure**: Celery, Kafka, Redis as persistent queue, anything that violates the 1-operator constraint (G2: 새벽에 혼자 고칠 수 있는 시스템).

### Source tree components to touch (from Architecture Spine §Structural Seed)

```
bizup/
├── apps/
│   ├── web/                       # Next.js 16 App Router
│   │   ├── app/[locale]/(dashboard)/
│   │   │   ├── m0-onboarding/  ... m12-account/    (13 module folders)
│   │   ├── components/
│   │   └── lib/
│   └── api/                       # FastAPI modular monolith
│       ├── modules/
│       │   ├── m0_onboarding/ ... m12_account/     (13 module folders)
│       │   └── core/
│       └── main.py                # FastAPI app entry (this story: /health only)
├── packages/
│   ├── cost_engine/               # PURE Python — no I/O, no DB, no clock
│   │   ├── core/
│   │   ├── ports/                 # calc_port, ccr_port, reversal_port (Protocol)
│   │   ├── adapters/
│   │   │   ├── db/                # SQLAlchemy adapter (Epic 4+)
│   │   │   ├── rest/              # FastAPI integration (later)
│   │   │   └── csv_excel/         # Excel upload (Epic 3+)
│   │   └── tests/regression_v8/   # V8 golden files (Epic 4+)
│   ├── services/                  # orchestration layer
│   └── ports/                     # interface definitions
├── supabase/
│   ├── migrations/                # (Epic 0.2)
│   └── policies/                  # RLS (Epic 0.2)
├── tests/
│   ├── architecture/              # fixture tests for dependency direction
│   └── cost_engine/
│       └── test_no_io_imports.py  # AST-based forbidden-import guard
├── .dependency-cruiser.cjs
├── .github/workflows/ci.yml
├── pyproject.toml                 # uv workspace root
├── package.json                   # pnpm workspace root
├── pnpm-workspace.yaml
├── .nvmrc
├── .python-version
└── README.md
```

### Testing standards summary

- **Architectural fixture tests are the primary deliverable for this story** (Story 0.1 has no business logic — its tests prove the boundary holds).
- Use `pytest >= 9.1.1` with `ast` (stdlib) for static analysis. No runtime mocks needed for boundary tests.
- CI must run on every PR — architecture violations are merge-blockers.
- Future V8 regression suite (Epic 4) will live in `packages/cost_engine/tests/regression_v8/` and be invoked from `apps/api/`. This story only scaffolds the folder.

### Project Structure Notes

- **Alignment with unified project structure**: matches Architecture Spine §Structural Seed (apps/web, apps/api, packages/cost_engine, packages/services, packages/ports, supabase). 13 module folders in both web (`m0-onboarding`...`m12-account`) and api (`m0_onboarding`...`m12_account`) — kebab-case vs snake_case per AD-15.
- **Detected conflicts or variances**: None — this story is the **first Greenfield commit**, so the structural seed is the source of truth.
- **Open question deferred to bmad-ux**: Design tokens (color/spacing) for Tailwind 4.3.3 — Story 0.4 covers naming conventions, but visual design system is post-CE. UX epic will populate `apps/web/tailwind.config.ts` with Pretendard + 클리어블루/옐로우/화이트 palette.
- **Deferred to later stories**: `apps/api/core/settings.py` Pydantic Settings will be wired with real Supabase + Stripe keys in Epic 12 (auth/backup/billing) — this story leaves it reading from env vars only.

### Library/Framework Requirements (specific)

- **dependency-cruiser** — verify ≥ 16.x (latest stable). Config syntax: CommonJS `.dependency-cruiser.cjs` at root. Use `forbidden` rule type for engine purity; `allowed` rule for direction flow.
- **import-linter** ≥ 2.0 — use `[tool.importlinter]` table in root `pyproject.toml`. Define 3 contracts:
  1. `cost_engine_forbidden_io` (forbidden import set, layers contract)
  2. `api_calls_only_ports` (independence contract — `apps.api` cannot import `cost_engine.core` directly)
  3. `engine_to_adapters_forbidden` (independence contract — `cost_engine.core` cannot import `cost_engine.adapters`)
- **pytest** 9.1.1 — use `tmp_path` fixture for any future I/O tests; this story has none.

### Anti-pattern prevention

- **DO NOT** put FastAPI/Starlette/Pydantic imports inside `packages/cost_engine/core/` — adapters in `packages/cost_engine/adapters/db/` may import SQLAlchemy, but **never** the core.
- **DO NOT** use `datetime.now()`, `time.time()`, or `random.random()` inside `packages/cost_engine/` — pure functions only (AD-5).
- **DO NOT** import `os.environ` inside engine — config flows in via constructor parameters.
- **DO NOT** add Celery, Kafka, Redis, or any persistent queue — 1-operator constraint.
- **DO** keep `apps/api/main.py` minimal — only `/health` route in this story. Domain endpoints added by Epic 4+.

### Testing Standards

| Layer | Tool | Test path |
|-------|------|-----------|
| TypeScript architecture | `dependency-cruiser` | `pnpm lint:deps` |
| Python architecture | `import-linter` | `uv run lint:imports` |
| Python boundary AST | `pytest` + `ast` | `tests/cost_engine/test_no_io_imports.py` |
| Python API/port contract | `pytest` + `importlib` | `tests/architecture/test_api_calls_only_ports.py` |
| Future V8 regression | `pytest` (Epic 4) | `packages/cost_engine/tests/regression_v8/` |

### References

- [Source: `_bmad-output/planning-artifacts/prd.md#1.2 Greenfield 선언`] — 런타임 의존성 0, 원본 5파일은 참조용
- [Source: `_bmad-output/planning-artifacts/prd.md#13.2 기술 스택`] — Next.js + Tailwind + FastAPI + Supabase
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-1`] — Modular Monolith + Hexagonal Core paradigm
- [Source: `ARCHITECTURE-SPINE.md#AD-5`] — Cost-engine purity
- [Source: `ARCHITECTURE-SPINE.md#AD-11`] — Dependency direction with mermaid diagram
- [Source: `ARCHITECTURE-SPINE.md#AD-14`] — Web-verified stack pin table (cold-start)
- [Source: `ARCHITECTURE-SPINE.md#AD-15`] — Cross-language conventions
- [Source: `ARCHITECTURE-SPINE.md#Structural Seed`] — Source tree with bizup/ root layout
- [Source: `ARCHITECTURE-SPINE.md#Capability → Architecture Map`] — Module folder naming
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic 0 Story 0.1`] — Original epic acceptance criteria

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

<!-- Dev agent should populate this section on completion with files created/modified and key decisions -->

### Review Findings (2026-07-25 code review)

#### Decision needed
(none)

#### Patch
- [x] [Review][Patch] CI `lint-imports` job broken: `import-linter` not declared in `pyproject.toml` or `uv.lock` [pyproject.toml, uv.lock]
- [x] [Review][Patch] `datetime` missing from `FORBIDDEN_TOP_LEVEL` — `import datetime; datetime.datetime.now()` bypasses AD-5 [tests/cost_engine/test_no_io_imports.py:32-45]
- [x] [Review][Patch] `>=` specifiers in `apps/api/pyproject.toml` violate AD-14 exact-pin [apps/api/pyproject.toml:11-17, packages/cost_engine/pyproject.toml:13-14, packages/services/pyproject.toml, packages/ports/pyproject.toml]
- [x] [Review][Patch] `no-deprecated-core` rule severity is `warn`, not `error` — apps→core boundary is non-blocking [.dependency-cruiser.cjs:28-33]
- [x] [Review][Patch] hatch wheel `packages = ["modules", "core"]` is malformed — production wheel will not include `main.py` [apps/api/pyproject.toml:23-24]
- [x] [Review][Patch] `apps/api/core/settings.py` missing (Subtask 3.4) — add minimal Pydantic Settings stub [apps/api/core/]
- [x] [Review][Patch] `packages/services/*.py` 4 service stubs missing (Subtask 5.3) [packages/services/]
- [x] [Review][Patch] `uv run lint:imports` not wired — spec literal command does not work [pyproject.toml, package.json:14]
- [x] [Review][Patch] `[project.optional-dependencies]` named `math` but spec says `engine-math` (Subtask 4.1) [packages/cost_engine/pyproject.toml:13-14, packages/services/pyproject.toml, packages/ports/pyproject.toml]
- [x] [Review][Patch] `lint:imports` script uses Windows-only `py -3.12`; CI is ubuntu [package.json:14]
- [x] [Review][Patch] Anti-pattern checklist does not mention `>=` [README.md:117-128]
- [x] [Review][Patch] `test_engine_core_does_not_import_adapters` has redundant `or "adapters" in top` clause (false-positive risk) [tests/cost_engine/test_no_io_imports.py:109]
- [x] [Review][Patch] `.editorconfig` missing (Subtask 1.4) — add at root
- [x] [Review][Patch] Unused `USD` import in `calc_port.py` [packages/cost_engine/ports/calc_port.py:17]

#### Deferred
- [x] [Review][Defer] `pnpm-lock.yaml` missing (HANDOFF L2) — deferred, pre-existing
- [x] [Review][Defer] apps/web stack pin variance Next 15.5/React 19.1 (HANDOFF L3) — deferred, pre-existing, [STACK BUMP] accepted
- [x] [Review][Defer] apps/web 13 module folders missing (HANDOFF L4) — deferred, pre-existing
- [x] [Review][Defer] `import-linter` cannot span apps.api ↔ packages.* (HANDOFF L1) — deferred to Story 0.3 `costmgr_workspace` namespace
- [x] [Review][Defer] Pretendard CDN without SRI in layout.tsx — deferred to Story 0.4 (design tokens) for `next/font/local` migration
- [x] [Review][Defer] dep-cruiser rules vacuous for Python targets (api-calls-only-ports, services-only-via-ports, engine-core-no-adapters, ports-stdlib-only) — deferred, Story 0.3 covers
- [x] [Review][Defer] CI re-installs deps per job instead of using setup cache — deferred, low impact at current scale
- [x] [Review][Defer] `.gitattributes` missing (CRLF warnings) — deferred, cosmetic
- [x] [Review][Defer] `apps/__init__.py` and `packages/__init__.py` unnecessary for uv workspace — deferred, harmless
- [x] [Review][Defer] Money type guards (BIGINT overflow, bool KRW, USD NaN/Infinity, mixed currencies) — deferred, current scope is basic types; Story 4+ adds validation
- [x] [Review][Defer] test_no_io_imports - `__import__`/importlib bypass — deferred, no current violation
- [x] [Review][Defer] test_no_io_imports - relative adapter import detection — deferred, test passes today
- [x] [Review][Defer] test_api_calls_only_ports runtime check covers core but not adapters — deferred, static AST test covers adapters
- [x] [Review][Defer] .dependency-cruiser.cjs - computed dynamic import, bare specifier coverage — deferred, no current violation
- [x] [Review][Defer] ci.yml - no workflow-policy test (job rename detection) — deferred, low priority
- [x] [Review][Defer] apps/api/modules - no canonical 13-folder assert — deferred, current state OK
- [x] [Review][Defer] apps/web/app/page.tsx - 13 route stub dirs missing (L4) — deferred, L4
- [x] [Review][Defer] check_stack_pin.mjs pnpm version not exact — deferred, Story 0.3 expands
- [x] [Review][Defer] layout.tsx inline font-family style — deferred, Tailwind not installed yet
- [x] [Review][Defer] CI no branch-protection reference — deferred, org-level concern

#### Dismissed (noise / false positive / already handled)
- README trailing whitespace — cosmetic
- apps/api/main.py docstring forward-ref to ports_bridge — forward-looking, harmless
- Diff preamble CRLF warnings — artifact of `git diff`, not file
- test_no_io_imports - syntax error path — test handles it (line 62-63)
- test_api_calls_only_ports - syntax error path — test handles it (line 34-35)
- test_api_calls_only_ports - FastAPI absent skip — test handles via pytest.skip (line 109)
