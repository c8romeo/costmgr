# AD-14 Stack Pin Policy — Cold-Start Dependency Lockfile

> **Status:** Active (forward-lock target: every PR that touches `docs/STACK_PIN.yaml`,
> `pyproject.toml`, `apps/api/pyproject.toml`, `apps/web/package.json`,
> `package.json`, `pnpm-lock.yaml`, `uv.lock`, `.nvmrc`, `.python-version`,
> `Dockerfile`, or `.github/workflows/ci.yml`)
> **Deciders:** kjw (Project Lead) + `@platform-team` (CODEOWNERS)
> **Date:** 2026-08-29 (cj-style 205번째 — formal AD install 진입)
> **Cross-references:** AD-1 (Modular Monolith), AD-8 (Money Types),
> AD-15 (Cross-Language Conventions), AD-22 (Owner-only RBAC),
> AD-49 ~ AD-57 (Phase 11~28 forward-lock chain)
> **Source artifacts:**
> [`docs/STACK_PIN.md`](../STACK_PIN.md) +
> [`docs/STACK_PIN.yaml`](../STACK_PIN.yaml) +
> [`scripts/check_stack_pin.mjs`](../../scripts/check_stack_pin.mjs) +
> [`scripts/check_stack_pin.py`](../../scripts/check_stack_pin.py) +
> [`scripts/regenerate_stack_pin.py`](../../scripts/regenerate_stack_pin.py) +
> [`scripts/bump_stack_pin.sh`](../../scripts/bump_stack_pin.sh) +
> [`tests/integration/test_stack_pin_check.py`](../../tests/integration/test_stack_pin_check.py) +
> `.github/workflows/ci.yml` (job `stack-pin-check`)

---

## Context

`bizup/costmgr` AD-1 (Modular Monolith) 의 cold-start pinning layer 이
silent breakage 에 노출되어 있다:

- **AD-1 (Modular Monolith)** — `packages/cost_engine/` 가 순수 도메인
  로직의 결정성 있는 회귀 fixture (Story 4.4 §v8) 를 보장하려면 외부
  adapter (`sqlalchemy`, `numpy`, `fastapi`) 의 **patch 한 줄 변경**
  도 계산 결과의 drift 를 일으키면 안 된다.
- **AD-8 (Money Types — `Decimal` + `bigint`)** — `Decimal ↔ int ↔
  NUMERIC ↔ BIGINT` 변환 손실이 `pydantic-core` 의 silent wheel 변경
  한 줄로 깨질 수 있다 (예: PYD-1 — pydantic 2.13+ ships broken
  `pydantic-core 2.46.4` wheel).
- **AD-15 (Cross-Language Conventions)** — TypeScript mirror (CR 12-5
  D-PARITY-01) 가 `decimal.js` / `bigint` 의 patch bump 에 따라
  serialization format 이 변하면 Python ↔ TS 간 결정성 있는 직렬화가
  깨진다.
- **AD-22 (Owner-only RBAC) + Epic 12 2FA 챌린지 mandatory** — 보안
  surface 의 crypto library (예: `pyjwt`, `cryptography`) 의 silent
  bump 가 signature verification drift 를 일으키면 Epic 12 2FA 챌린지
  mandatory destructive endpoint 의 3-layer defense 가 무력화된다.

Phase 11~28 wire cycles 에서 100+ 회 cross-reference 된 "AD-14 stack
pin Recharts 2.12.7 + apscheduler 3.10.4 + pytz 2024.1 + noto-sans-cjk-kr
+ reportlab 4.0.7 + xlsxwriter 3.1.9 + pandas 2.1.4 + matplotlib 3.8.2"
등의 reference 가 모두 본 AD-14 의 결정에 매달려 있다. 그러나 본 AD-14
의 formal AD 문서는 cj-style 205번째 sprint 까지 부재했다 — 본 문서가
그 AD-install 을 수행한다.

### Why silent breakage is the actual problem

| 시나리오 | 영향 | 실제 발생 사례 |
|---|---|---|
| `pydantic-core` patch bump | `Decimal` 직렬화 결정성 손실 | PYD-1 — pydantic 2.13+ ships broken `pydantic-core 2.46.4` wheel |
| `sqlalchemy` minor jump | event-listener signature 변경 (deprecation cycle 없음) | 1회 회귀 suite break (사내 incident) |
| `recharts` major bump | Recharts 2.x → 3.x peer dependency 변경 | cj-style 197/202 commit 메시지가 "Recharts 2.12.7 AD-14 stack pin" claimed 했으나 install 단계 누락 → cj-style 204 cleanup sprint 에서 정직 회복 |
| Dockerfile base image tag 변경 | hash digests mismatch | DOCKER-1/5 — `python:3.12-slim` + `node:24.18.0-alpine` + `nginx:1.27-alpine` 모두 digest pin |
| `pnpm install` in CI | lockfile drift | CR 9-6 — CI 는 항상 `--frozen-lockfile` 강제 |

### Why a single YAML SSOT

`docs/STACK_PIN.yaml` 이 **machine-readable SSOT** 이고
`docs/STACK_PIN.md` 는 **human-readable mirror** 이다. 양쪽은
`scripts/regenerate_stack_pin.py` 로 동기화되며, drift 가 발생하면
CI `stack-pin-check` job 이 `STACK_PIN_VIOLATION` 으로 실패한다.

## Decision

AD-14 stack pin policy 는 **6-tuple 의 강제** 로 구성된다:

### (1) Pin the version

`docs/STACK_PIN.yaml` 의 `stack_pin:` 섹션이 canonical pin table.
Routine dep work (patch update, 새 transitive) 는 free 이지만,
`stack_pin:` 키에 나열된 package 의 **pinned-version bump** 는
반드시 `[STACK BUMP]` commit tag + `@platform-team` CODEOWNER
approval 을 요구한다.

| File | What it pins |
|---|---|
| `.nvmrc` | Node version (exact) |
| `.python-version` | Python version (exact) |
| `package.json` | `engines.node` (semver range), `packageManager` (exact) |
| `apps/web/package.json` | `next`, `react`, `react-dom`, `typescript`, `@types/react`, `@types/node` (exact) |
| `apps/api/pyproject.toml` | `fastapi`, `pydantic`, `pydantic_core`, `sqlalchemy`, `alembic`, `asyncpg`, `pyjwt`, `supabase`, `pydantic_settings`, `uvicorn`, `httpx`, `hatchling` |
| `packages/cost_engine/pyproject.toml` | `numpy` (optional `[engine-math]` extra), `pytest` |
| `pyproject.toml` (root) | `import-linter`, `pytest`, `ruff` |
| `Dockerfile` | `python:3.12-slim` + `node:24.18.0-alpine` + `nginx:1.27-alpine` (tags + digest) |
| `pnpm-lock.yaml` | npm tree exact resolution |
| `uv.lock` | pip tree exact resolution |
| `.github/workflows/ci.yml` | `postgres:15` (digest), `uv==0.11.32` install command |

총 35 pins (cj-style 205 검증 시점).

### (2) Lock the resolution

- **CI**: `pnpm install --frozen-lockfile` + `uv sync --frozen`
  (.github/workflows/ci.yml `stack-pin-check` job lines 126-128).
- **로컬**: routine dev work 시에도 `--frozen-lockfile` 권장
  (Makefile `install` target).
- **Dependabot**: weekly PR for npm + pip. PRs touching pinned
  packages get `stack-pin` label and require CODEOWNER approval
  (Dependabot auto-merge ❌ 금지 per anti-pattern §).

### (3) Bump deliberately

Pinned-version bump 시 **3-step 필수**:

1. `docs/STACK_PIN.yaml` (SSOT) hand-edit + matching `notes:` entry
   업데이트. `scripts/bump_stack_pin.sh <pkg> <ver>` helper 사용 가능
   (auto `[STACK BUMP]` commit tag 부착).
2. V8 regression suite (`packages/cost_engine/tests/regression_v8/`)
   `uv run pytest packages/cost_engine/tests/regression_v8 -v` 실행
   — 1원 reconciliation contract 깨지면 rollback.
3. PR merge + CI guard accept (because `[STACK BUMP]` tag present).

### (4) CI gate fail-closed

`.github/workflows/ci.yml` `stack-pin-check` job (lines 110-195) 가
**fail-closed** 로 동작:

- Node pin check → `node scripts/check_stack_pin.mjs` exit code 그대로
- Python pin check → `uv run python scripts/check_stack_pin.py` exit code 그대로
- Drift detected + no `[STACK BUMP]` tag → `STACK_PIN_VIOLATION` stderr
- PR build 시 `stack-pin-violation` GitHub label 자동 부착 (LABEL-1)
- PR comment 자동 생성: `Add `[STACK BUMP]` to the PR commit message
  to authorize this drift.`
- `[STACK BUMP]` tag present in **PR head commit** (MSG-2 — squash-merge
  workflow 에서 merge commit 이 tag 를 hide 하는 문제 회피) → drift
  authorized, exit 0

### (5) Exceptions block + retirement policy

`docs/STACK_PIN.yaml` `exceptions:` 섹션은 ARCHITECTURE-SPINE.md §Stack
으로 부터의 tracked deviation:

- `spec:` — architecture spine target value
- `current:` — current pinned value (or `"NOT INSTALLED"` if absent)
- `reason:` — deviation 존재 이유
- `owner:` — GitHub handle responsible
- `deadline:` — ISO date (resolution or re-justification by)
- `tracking:` — story / spike / epic reference

CI 는 `exceptions:` 항목에 대해 **fail 하지 않음** (authorized
deviation) 이지만 `NOTES-1` 정책으로 `pnpm dep:check` 가 per-item
warning + summary count 를 emit 한다. `current == spec` 인 항목은
"ready to retire" warning 으로 surface 된다 (cj-style 205 검증 시점
retired candidate: 0건, 모든 exceptions 가 active deviation 상태).

### (6) Anti-patterns (강제 금지)

| ❌ Anti-pattern | Consequence |
|---|---|
| `^` or `~` in `package.json` for any pinned package | minor/patch bump 가 silent resolution 변경 유발 |
| `latest` in Docker base images — use digest (`@sha256:...`) | tag re-tag 가능 → digest pin 으로 불변성 보장 |
| Silent bump in lockfile without `STACK_PIN.yaml` update first | CI `stack-pin-check` FAIL |
| Dependabot auto-merge on `stack-pin`-labelled PR | CODEOWNER review 회피 |
| `pnpm install` in CI (always `--frozen-lockfile`) | lockfile drift 가능 |

## Consequences

### Positive

- **결정성 보장**: cold-start 시 `pnpm install --frozen-lockfile` +
  `uv sync --frozen` 으로 byte-level reproducible build → Story 4.4
  v8 회귀 fixture 가 깨지지 않음.
- **Silent breakage 방지**: CI `stack-pin-check` 가 PR merge 전 drift
  차단 → "pydantic-core 한 줄 변경으로 5개 test suite 깨짐" 류의
  incident 0건 목표.
- **Cross-AD 일관성**: AD-49 ~ AD-57 의 100+ cross-reference 가 모두
  본 AD-14 SSOT 에 매달림 → "AD-14 stack pin Recharts 2.12.7" 류의
  reference 가 authoritative.
- **Auditability**: `[STACK BUMP]` commit tag 가 git log 에 남음 →
  누가/언제/왜 bump 했는지 trace 가능.
- **CODEOWNER enforcement**: `@platform-team` approval gate 로
  무분별한 bump 차단.

### Negative / Trade-offs

- **Bump friction**: pinned-version bump 시 PR + V8 회귀 + CODEOWNER
  approval = 3-step 강제 → 새 의존성 추가 시 약 1-day latency.
- **Exception debt**: `exceptions:` 블록이 누적되면 SSOT 가
  비대해짐 (cj-style 205 검증 시점 8개 active exception: `next`,
  `react`, `typescript`, `pydantic`, `sqlalchemy`, `postgresql`,
  `tailwind`, `structlog`, `opentelemetry_api`).
- **Lockfile resolution drift**: Dependabot weekly PR 이 lockfile 만
  변경하는 경우 → CODEOWNER review 필요 → 자동화 어려움.

### Mitigations

- `scripts/bump_stack_pin.sh <pkg> <ver>` helper 가 auto `[STACK BUMP]`
  tag 부착 + commit message 자동 작성 → bump friction 최소화.
- `NOTES-1` 로 ready-to-retire exception 자동 surface → exception debt
  가 visible.
- V8 regression suite 가 Story 4.4 에서 ship 되면 bump cycle 이
  결정성 보장 + auto-rollback 가능.
- `pnpm dep:check:verbose` (VERBOSE=1) 가 모든 expected vs actual 출력
  → silent drift 디버깅 시간 단축.

## Alternatives Considered

| 후보 | 기각 이유 |
|---|---|
| Free dep version (no pin) | v8 fixture 결정성 깨짐 + AD-1/8/15 cross-cutting 일관성 손실 + silent breakage incident 재발 |
| `^` carets everywhere | minor bump 한 줄로 regression 가능 — silent breakage scenario 와 동일 |
| Dependabot auto-merge on stack-pin PR | CODEOWNER review 회피 → 무분별한 bump 가능 |
| Pin 만 하고 CI gate 없음 | drift 가 발견되지 않음 → bump 가 commit 되기 전 차단 불가 |
| Hash digest 만 pin (no version tag) | human readability 손실 + upgrade 시 digest 재캡처 friction |
| Runtime detection (e.g., `npm audit` only) | security 만 cover, drift 자체는 cover 못함 |

## Detection Surface — install/runtime 검증 surface

cj-style 206 sprint 의 install state honestly reported (cj-205 최초
report → cj-206 `D-AD-14-1` RESOLVED 반영):

| Surface | State | Notes |
|---|---|---|
| `scripts/check_stack_pin.mjs` (Node detector) | ✅ **installed + functional** | `[STACK_PIN] OK all 35 pins match` (cj-205 + cj-206 재검증) |
| `scripts/check_stack_pin.py` (Python mirror) | ✅ **installed + functional (cj-206 회복)** | `uv run python scripts/check_stack_pin.py` → `[STACK_PIN] Exceptions tracked: 9` + `[STACK_PIN] OK all 35 pins match` (exit 0). cj-205 시점의 `k6-python-wrapper==0.1.0` phantom dep (`apps/api/pyproject.toml:62`) 이 `uv lock` resolution 을 unsatisfiable 로 만들어 NOT runnable 이었으나, cj-206 sprint 에서 phantom dep 제거 + `uv.lock` regenerate 로 회복. **D-AD-14-1 RESOLVED**. |
| `scripts/regenerate_stack_pin.py` | ✅ installed + functional | derive STACK_PIN.yaml from ARCHITECTURE-SPINE.md §Stack |
| `scripts/bump_stack_pin.sh` | ✅ installed + functional | auto `[STACK BUMP]` tag helper |
| `tests/integration/test_stack_pin_check.py` | ✅ installed + functional | 9-case integration test all PASS (cj-206 재검증; exit 0 on clean repo / exit 1 on drift / `[STACK BUMP]` authorizes / drift output reports package name) |
| `pnpm dep:check` (package.json) | ✅ wired | `node scripts/check_stack_pin.mjs` |
| `pnpm test:stack-pin` (package.json) | ✅ wired | `uv run python scripts/check_stack_pin.py` |
| `make dep-check` (Makefile) | ✅ wired | `pnpm dep:check + check_stack_pin` |
| `make test-stack-pin` (Makefile) | ✅ wired | `$(PYTEST) tests/integration/test_stack_pin_check.py -v` |
| CI `.github/workflows/ci.yml` `stack-pin-check` job | ✅ wired (lines 110-195) — **cj-206 PARTIAL → FULL** | Node + Python pin check + drift annotation + `stack-pin-violation` label. cj-205 시점에는 `Python pin check` step 의 `uv run` 이 phantom dep 으로 fail 했으나 (job 전체 red), cj-206 phantom dep 제거로 local 동일 명령 exit 0 회복. CI 실측은 다음 push 에서 확인 (local 검증만 수행 — honestly reported). |
| CI Dependabot auto-label | ⚠️ partial — see `stack-pin` label docs | weekly npm + pip PRs |
| `docs/STACK_PIN.md` + `docs/STACK_PIN.yaml` | ✅ installed + SSOT | hand-edit YAML only; MD is mirror |
| `docs/architecture-decisions/AD-14-stack-pin-policy.md` | ✅ **cj-205 신규 install** | THIS document (cj-206 Detection Surface + Open Items EXTENSION) |
| `uv.lock` ↔ `apps/api/pyproject.toml` declared/resolved parity | ✅ **cj-206 회복** | cj-205 시점 lock 은 k6 뿐 아니라 lxml / opentelemetry 7종 / prometheus-client / pyyaml / python3-saml / jsonschema 도 미해결 상태 (`costmgr-api` requires-dist: lock 13 vs pyproject 25 — dev extra 포함). cj-206 `uv lock` 으로 +518 lines 추가 resolution — 기존 pin 은 1건도 변경되지 않음 (0 deletions). `uv lock --check` exit 0. |

## Cross-references

- AD-1 (Modular Monolith) — engine 순수성 + cold-start 결정성
- AD-8 (Money Types) — `Decimal`/`bigint` drift 방지 (PYD-1 incident
  reference)
- AD-15 (Cross-Language Conventions) — TS mirror parity (CR 12-5
  D-PARITY-01) + Decimal.js / bigint serialization 결정성
- AD-22 (Owner-only RBAC) — crypto library (pyjwt, cryptography)
  silent bump 가 signature verification drift 일으키면 3-layer
  defense 무력화
- AD-49 ~ AD-57 (Phase 11~28 forward-lock chain) — 17-capability
  FinOps territory 가 모두 본 AD-14 에 매달린 cross-reference 보유
- CR 9-6 (commit message `git commit -F <file>`) — `[STACK BUMP]`
  tag commit 시 here-string 회피
- CR 11-3 (honest-DEFER) — `exceptions:` 블록의 honest deviation +
  this AD-14 cj-205 sprint 의 `D-AD-14-1` (k6-python-wrapper phantom
  dep) honestly DEFER → **cj-206 source sprint 에서 RESOLVED** +
  `D-AD-14-2` (retention `response_model` FastAPIError) 신규
  honestly DEFER

## Open Items

- **D-AD-14-1** ✅ **RESOLVED (cj-style 206 source sprint)** —
  `k6-python-wrapper==0.1.0` phantom dependency removal 완료.
  cj-205 honestly DEFER 된 항목으로, `apps/api/pyproject.toml:62` 에
  선언되어 있었으나 PyPI 에 존재하지 않는 패키지였고
  `apps/api/core/load_test_runner.py` 는 stdlib `subprocess` 로 `k6`
  binary 를 직접 invoke (`K6_BINARY` env override, `k6_python_wrapper`
  import 0건). cj-206 에서 (1) `pyproject.toml` phantom dep 제거 +
  (2) `uv lock` regenerate (+518 lines, 0 deletions) +
  (3) `uv run python scripts/check_stack_pin.py` → **35 pins match,
  exit 0** 검증 + (4) `uv sync --frozen` / `uv lock --check` exit 0.
  runtime 동작 변화 0건 (제거된 패키지는 애초에 설치된 적이 없음).
- **D-AD-14-2** (cj-style 206 신규 honestly DEFER per CR 11-3) —
  `tests/architecture/test_api_calls_only_ports.py::
  test_apps_api_has_no_unintended_dunder_imports_at_module_load` 가
  **fastapi 가 설치된 환경에서 pre-existing FAIL**. 원인은
  `apps/api/modules/audit/retention/retention_dsl.py:52` 의
  `class RetentionPolicy(dict)` 를
  `retention_routes.py:102` 가 `response_model=` 으로 사용 →
  `fastapi.utils` `FastAPIError` (dict subclass 는 valid response
  field 가 아님) at `apps.api.main` import time. 본 test 는 fastapi
  미설치 환경에서 `pytest.skip` 하므로 CI (`uv sync --frozen` = root
  dev group 15 packages only) 에서는 skip 되어 왔음 — cj-206 의
  `uv sync --frozen --all-packages` 환경에서 처음 표면화.
  **본 sprint 변경과 무관함이 `git stash` baseline 재현으로 증명됨**
  (stash 상태에서도 동일 FAIL). follow-up cj-207+ source sprint 에서
  `RetentionPolicy` 를 pydantic `BaseModel` 로 승격하거나
  `response_model` 을 제거하는 결정 wire 필요.
- **V8 regression suite (Story 4.4)** — 현재 `no tests ran` until
  Story 4.4 ships the fixtures. Setup 시 AD-14 §Bump policy §V8
  regression gate 활성화.
- **Dependabot auto-label wiring** — `stack-pin` label 이 Dependabot
  PR 에 자동 부착되는지 verification 미실시. follow-up sprint 에서
  `.github/dependabot.yml` 검증.

## Notes

- 본 AD-14 문서의 cj-style 205 sprint install 은 **docs-only atomic
  single sprint** (5 files = 3 NEW + 2 MODIFIED) — Node detector
  functional state 의 honestly reported + Python detector 의
  honestly DEFER (`D-AD-14-1`) 결정 wire 보존. **CR 11-3
  honest-DEFER 98번째** epic 연속 정직 회복.
- 본 AD-14 문서의 cj-style 206 sprint EXTENSION 은 **source+docs
  atomic single sprint** — `D-AD-14-1` phantom dep 제거로 Python
  detector 회복 (install surface 12 중 ✅ 10 + ⚠️ 1 partial
  (Dependabot auto-label) + ⚠️ 1 신규 DEFER (`D-AD-14-2`, AD-14
  territory 외부 source defect)). **CR 11-3 honest-DEFER 99번째**
  epic 연속 정직 회복. 본 sprint 는 pin 을 1건도 bump 하지 않았으므로
  `[STACK BUMP]` tag 불필요 (35 pins 전부 unchanged, `uv.lock` 은
  additive resolution only).
- 본 AD-14 의 `scripts/check_stack_pin.py` 의 CASCADE-1 (CR
  2026-07-25) PyYAML 사용 — BOM / anchors / folded scalars /
  escaped quotes 같은 YAML edge cases 에서 hand-rolled parser 의
  silent failure 방지.
- 본 AD-14 의 `scripts/check_stack_pin.py` 의 DOCKER-2 (CR
  2026-07-25) CI workflow scan — `image: <name>@sha256:...` lines
  matching 으로 postgres CI service image digest 검증.
- 본 AD-14 의 `scripts/check_stack_pin.py` 의 MSG-1 / MSG-2 (CR
  2026-07-25) — standardized violation message + `[STACK BUMP]`
  PR head SHA 검사로 squash-merge workflow 의 tag hide 문제 회피.
- 본 AD-14 의 `scripts/check_stack_pin.py` 의 SCHEMA-1 (CR
  2026-07-25) — exceptions block schema 표준화 (spec / current /
  reason / owner / deadline / tracking fields).
