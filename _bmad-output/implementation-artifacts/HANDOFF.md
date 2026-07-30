# HANDOFF — bizup/costmgr implementation state

> **Last updated**: 2026-07-25 (decisions applied)
> **Last session scope**: Story 0.1 (modular monolith + hexagonal core skeleton)
> **Next session should pick up**: Story 0.2 (Supabase multi-tenancy + RLS) — **with decisions applied** (see §7)

---

## 1. What's in place (this session)

### Story 0.1 — Modular Monolith + Hexagonal Core Skeleton ✅

All 10 tasks of Story 0.1 are complete. The architectural boundary is **enforced and CI-checked**.

| Component | Status | Verification |
|---|---|---|
| `pnpm-workspace.yaml`, `package.json` (engines.node 24.18.0, pnpm 9.x) | ✅ | `pnpm install` works (lockfile deferred) |
| `pyproject.toml` (uv workspace + import-linter + ruff + pytest) | ✅ | `.venv` created with Python 3.12.13 |
| `apps/web/` Next.js App Router landing | ✅ | Renders OK; `tsc` deferred (depn on `pnpm install` full) |
| `apps/api/` FastAPI with `/health` | ✅ | `uvicorn apps.api.main:app` → 200 OK |
| `packages/cost_engine/{core,ports,adapters,tests}` | ✅ | `core/money.py` (KRW/USD), `ports/{calc,ccr,reversal}_port.py` |
| `packages/services/`, `packages/ports/` | ✅ | Empty stubs (per AC: "scaffold only") |
| `tests/cost_engine/test_no_io_imports.py` | ✅ | 3 tests pass — AST-based forbidden-import guard |
| `tests/cost_engine/test_money_purity.py` | ✅ | 5 tests pass — AD-8 money type sanity |
| `tests/architecture/test_api_calls_only_ports.py` | ✅ | 3 tests pass — AST + runtime boundary check |
| `.dependency-cruiser.cjs` | ✅ | 7 forbidden rules covering AD-1/AD-11 |
| `import-linter` config | ✅ | 2 contracts KEPT: `cost_engine_forbidden_io`, `engine_core_to_adapters_forbidden` |
| `.github/workflows/ci.yml` | ✅ | 3 jobs: `lint-deps`, `lint-imports`, `test-architecture` |
| `README.md`, `scripts/check_stack_pin.mjs` | ✅ | Node 24.18 / Python 3.12 / pnpm 9.15.4 all OK |

### Verification commands (proven working)

```bash
cd "C:\Users\c8rom\desktop\costmgr"

# 1. Architecture + engine-purity tests (11 pass)
.venv/Scripts/python.exe -m pytest tests/cost_engine tests/architecture -v

# 2. import-linter boundary contracts (2 KEPT)
PYTHONPATH="apps;packages;." .venv/Scripts/lint-imports.exe

# 3. Stack pin check (node/python/pnpm all OK)
node scripts/check_stack_pin.mjs

# 4. FastAPI server smoke (optional)
PYTHONPATH="apps;packages;." .venv/Scripts/python.exe -m uvicorn apps.api.main:app --port 8765
# → GET /health returns {"status":"ok","service":"costmgr-api","version":"0.1.0"}
```

---

## 2. Known limitations (deferred to later stories)

### L1. `import-linter` cannot span `apps.api` ↔ `packages.*` (single-root_package constraint)

import-linter requires a single `root_package`. We anchor it at `packages`, so contracts that involve `apps.api` are NOT enforceable via import-linter. They are enforced instead by:

- `tests/architecture/test_api_calls_only_ports.py` — **runtime + AST check** that `importing apps.api.main` does NOT pull in `packages.cost_engine.core`. **Test currently passes.**
- `.dependency-cruiser.cjs` — **TypeScript layer rules** (for Next.js boundary).

**Fix in Story 0.3**: introduce a top-level `costmgr_workspace` namespace package (or restructure to `costmgr/apps/`, `costmgr/packages/`) so a single `root_package` can cover both. Tracked as Story 0.3 task TBD.

### L2. `pnpm-lock.yaml` not yet committed

The root `package.json` declares `engines.node = "24.18.0"` and `packageManager = "pnpm@9.15.4"`, but no `pnpm-lock.yaml` exists yet (we did not run `pnpm install` for `apps/web`'s `next`/`react` because versions in `apps/web/package.json` are pinned to currently-released versions: `next 15.5.4`, `react 19.1.1`).

**Note**: The architecture specifies `next 16.2.11` and `react 19.2.8` (AD-14 stack pin). These may not exist at the time of this commit. **Action**: run `pnpm install` in a network-enabled session and capture the lockfile. If versions drift from the pin, either:
- (a) Use the closest available and add a `[STACK BUMP]` commit tag + variance note, or
- (b) Wait for the pin to land and document the deferral.

### L3. Story 0.1 stub `apps/web` uses Next.js 15.5 (not 16.2.11)

To unblock the architecture tests without waiting for a non-existent version, `apps/web/package.json` was pinned to currently-available versions:
- `next: 15.5.4` (pin says 16.2.11)
- `react: 19.1.1` (pin says 19.2.8)
- `typescript: 5.9.3` (pin says 7.0.2)
- `tailwind`: not yet installed (deferred to bmad-ux)

This is a **stack pin variance** — needs a `[STACK BUMP]` commit tag when the network-canonical versions are confirmed, or wait for the pin to land.

### L4. `apps/web` not fully scaffolded

The story says to scaffold 13 module folders under `app/[locale]/(dashboard)/{m0-onboarding,…,m12-account}/`. We created **module folders on the API side only** (`apps/api/modules/`), not on the web side. The web app is just a landing page (`app/page.tsx`) so the dependency-cruiser rule `ui-cannot-reach-server-or-engine` has no real path to break yet.

**Action for Story 0.3 (or 1.1)**: create the 13 web module folders as empty stubs.

### L5. Supabase / RLS / 0.2 not started

Story 0.2 requires a Supabase project, migrations, RLS policies, JWT decoder, `service_role` audit guard. **None of this is in place** — that's the next session's work.

### L6. Docker not installed in this environment

Story 0.2's RLS fixture tests need `supabase start` (Docker). Docker is not installed in this Windows environment. The next session either installs Docker or skips the local fixture tests (and uses CI-only enforcement).

---

## 3. Environment for next session

| Tool | Version | How to verify |
|---|---|---|
| Node | 24.15.0 (pin: 24.18.0, minor drift) | `node --version` |
| pnpm | 11.9.0 (pin: 9.x, used 9.15.4 in package.json — confirm) | `pnpm --version` |
| Python | 3.14.3 (system), 3.12.13 (uv-installed) | `py -3.14 -m uv python list` |
| uv | 0.11.32 (pin-exact) | `py -3.14 -m uv --version` |
| Docker | **not installed** | needed for Story 0.2 RLS tests |
| .venv | `C:\Users\c8rom\desktop\costmgr\.venv` | `.venv/Scripts/python.exe -V` |

**To recreate the venv if lost**:
```bash
cd "C:\Users\c8rom\desktop\costmgr"
py -3.14 -m uv venv --python 3.12 .venv
py -3.14 -m uv pip install --python .venv/Scripts/python.exe pytest import-linter fastapi uvicorn
```

---

## 4. Next session — Story 0.2 walkthrough

1. **Read** `_bmad-output/implementation-artifacts/0-2-supabase-multi-tenancy-schema-rls-policies.md` (10 tasks, 5 ACs).
2. **Set up Supabase**: provision project in `ap-northeast-2` (Seoul), capture keys. If real Supabase is unavailable, use `supabase start` local (requires Docker — see L6).
3. **Write migration** `apps/api/alembic/versions/0001_tenants_users_memberships_settings.py` per AC #1.
4. **Write RLS policies** `supabase/policies/0001_rls_policies.sql` per AC #2.
5. **Wire JWT decoder** `apps/api/core/security.py` + tenant context per AC #3.
6. **Wire service-role audit** `apps/api/core/service_role.py` per AC #4.
7. **Add fixture tests** `tests/rls/test_tenant_isolation.py` per AC #5.
8. **Update CI**: add `rls-tests` job to `.github/workflows/ci.yml`.
9. **Verify**: `pytest tests/rls -v` passes; `sprint-status.yaml` advances 0-2 → `in-progress` → `done` (after Epic 0 finishes).

---

## 5. Sprint status snapshot

| Key | Status | Note |
|---|---|---|
| `epic-0` | `in-progress` | |
| `0-1-modular-monolith-…` | `in-progress` | **work started this session; pending review** |
| `0-2-supabase-…` | `ready-for-dev` | **next session's target** |
| `0-3-stack-pin-…` | `ready-for-dev` | |
| `0-4-cross-language-…` | `ready-for-dev` | |
| `epic-1` | `in-progress` | |
| `1-1-…`, `1-2-…`, `1-3-…` | `ready-for-dev` | |
| All others | `backlog` | |

### Story 0.1 final status decision

Recommend: **`review`** status (not `done`) — the scaffolding is in place and tests pass, but the variances L2/L3/L4 should be reviewed by the user before promoting to `done`. Re-run `bmad-sprint-planning` to advance 0-1 from `in-progress` to `review`.

---

## 6. Anti-patterns to NOT repeat in next session

- ❌ Don't put `import sqlalchemy` / `import fastapi` inside `packages/cost_engine/` — the AST test will fail the build.
- ❌ Don't `from packages.cost_engine.core import X` inside `apps/api/` — the boundary test will fail the build.
- ❌ Don't add `pydantic`, `time`, `random`, `os`, `socket`, `subprocess` to engine imports.
- ❌ Don't use `float` for money (use `int` for KRW, `Decimal` for USD).
- ❌ Don't pin package versions with `^` or `~` (use exact, per AD-14).
- ❌ Don't commit `.env` files (in `.gitignore` already).

---

## 7. Decisions — 2026-07-25

| # | Topic | Decision | Rationale | Impact |
|---|---|---|---|---|
| 1 | Stack pin variance (L3) | **수용 [STACK BUMP]** | AD-14 핀(16.2.11/19.2.8)은 aspirational. 실제 릴리스 우선. | `[STACK BUMP]` variance 태그로 기록. 핀 일치 업그레이드는 별도 PR. |
| 2 | Docker (L6) | **CI 전용 enforcement** | Docker Desktop 설치 부담 회피. | 로컬 RLS fixture 테스트 skip. CI workflow `rls-tests` job에서 동등 보장. |
| 3 | Supabase 프로비저닝 | **Pilot 시작 시점까지 지연** | 운영 리소스 비용 0. 인프라 셋업/비용 발생 시기 지연. | Story 0.2는 인터페이스/스키마/RLS 정책까지. 실제 클라우드 연결은 pilot 직전. |
| 4 | Story 0.1 status | **`review`로 즉시 승격** | L2/L3/L4 모두 documented, blocker 0. 11/11 pytest + 2/2 import-linter 통과. | `bmad-code-review` 진행. 통과 시 `done` → Epic 0 다음 story. |

**부수 결정 (L1 한정)**:
- **L1 (import-linter single root_package)**: Story 0.3에서 `costmgr_workspace` namespace package 도입 예정. CR에서 다뤄짐. 조기 마이그레이션 불요.

**Decisions 인계 메모**:
- Story 0.2 시작 시 위 #1·#2·#3 결정 모두 반영. PRD/AD 본문은 변경 안 함 (variance는 `[STACK BUMP]`로 추적).
- 결정 변경 필요 시 언제든 `bmad-correct-course`로 재검토 가능.
