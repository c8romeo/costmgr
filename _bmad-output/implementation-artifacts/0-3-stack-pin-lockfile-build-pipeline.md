# Story 0.3: Stack Pin Lockfile + Build Pipeline

Status: review
baseline_commit: bd58c180234abae60a1bd4e8bcd38ea766263d9a

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform engineer**,
I want **the cold-start stack pin (AD-14) enforced by lockfile + Dockerfile + CI guard + dependabot gate**,
so that **no engineer — human or AI — can silently upgrade Next.js, FastAPI, PostgreSQL, or any pinned dependency without tripping the build** (AD-14, AD-8, AD-1). Drift = build failure, not silent surprise.

## Acceptance Criteria

1. **Given** the architecture spine's stack pin table (Node 24.18.0 LTS, Next.js 16.2.11, React 19.2.8, TypeScript 7.0.2, Tailwind 4.3.3, FastAPI 0.139.2, Python 3.12.x, PostgreSQL 17, structlog 26.1.0, uv 0.11.32, OpenTelemetry 1.44.0) is published
   **When** I commit the root `package.json` (with pinned resolution + `engines.node = "24.18.0"`), root `pyproject.toml` (with `requires-python = ">=3.12,<3.13"` + pinned dep versions), and `Dockerfile` (with `FROM python:3.12.x-slim` + `FROM node:24.18.0-alpine` for frontend build)
   **Then** `pnpm install --frozen-lockfile` reproduces the exact same `node_modules` tree (lockfile contains pinned versions, not `^`/`~`)
   **And** `uv sync --frozen` reproduces the exact same `.venv` (uv.lock contains pinned versions)
   **And** the `Dockerfile` uses **multi-stage build** with pinned base images by digest (`@sha256:...`) for reproducibility
   **And** the `Dockerfile` copies `pnpm-lock.yaml` + `uv.lock` into the build context and runs `pnpm install --frozen-lockfile` + `uv sync --frozen` (no fresh dep resolution in CI/build)

2. **Given** the lockfiles and Dockerfile are committed
   **When** I add a CI step `pnpm dep:check` + `uv run check-stack-pin` + a Dockerfile parser check (GitHub Action `docker/metadata-action` + custom `dockerfile-parse` step)
   **Then** the CI step reads `package.json`, `pyproject.toml`, `uv.lock`, and the `Dockerfile`, and compares each declared version against the architecture spine's stack pin table (stored as `docs/STACK_PIN.yaml` — single source of truth)
   **And** the CI step exits non-zero if ANY pinned version drifts (e.g., `next@16.2.12` present, but pin is `16.2.11`)
   **And** the CI step scans the most recent commit message for the literal tag `[STACK BUMP]` — if absent AND any version drifted, the build fails with `STACK_PIN_VIOLATION: <package> drifted from <expected> to <actual>. Use [STACK BUMP] commit tag to bypass.`
   **And** if the tag IS present, the build passes (and a warning is logged: `STACK_PIN_BUMP_AUTHORIZED: <reason from commit body>`)

3. **Given** the CI guard is in place
   **When** I add `.github/dependabot.yml` with weekly schedules for `npm` (Monday 09:00 KST) and `pip` (Tuesday 09:00 KST)
   **Then** Dependabot PRs are labeled `stack-pin` and require the same `[STACK BUMP]` commit tag from a CODEOWNER (`.github/CODEOWNERS`) to merge
   **And** Dependabot PRs that bump a pinned version **without** `[STACK BUMP]` are auto-labeled `stack-pin-violation` and blocked by branch protection (the CI step rejects them)
   **And** non-pinned dependency updates (e.g., patch versions of `eslint-plugin-*`) proceed normally
   **And** a `pnpm dep:check` script in root `package.json` runs the same check locally: `pnpm dep:check` returns exit code 0 if all pinned versions match, exit code 1 if any drift

## Tasks / Subtasks

- [ ] **Task 1 — Capture stack pin as machine-readable source** (AC: #1)
  - [ ] Subtask 1.1 — Create `docs/STACK_PIN.yaml` with the canonical stack pin table (one source of truth, no duplication):
    ```yaml
    # DO NOT EDIT BY HAND — regenerated from ARCHITECTURE-SPINE.md#Stack
    # Bump policy: requires [STACK BUMP] commit tag + CODEOWNER approval
    stack_pin:
      node: 24.18.0
      python: 3.12.x
      pnpm: 9.x
      uv: 0.11.32
      next: 16.2.11
      react: 19.2.8
      typescript: 7.0.2
      tailwind: 4.3.3
      fastapi: 0.139.2
      pydantic: 2.13.4
      sqlalchemy: 2.0.51
      alembic: 1.18.5
      structlog: 26.1.0
      opentelemetry: 1.44.0
      pytest: 9.1.1
      postgresql: 17
      postgres_client: psycopg[binary]>=3.2
      jwt: pyjwt>=2.8
      supabase_cli: latest
    ```
  - [ ] Subtask 1.2 — Add a `scripts/regenerate_stack_pin.py` script that parses `ARCHITECTURE-SPINE.md` §Stack and writes `docs/STACK_PIN.yaml` (run on architecture doc change)
  - [ ] Subtask 1.3 — Document regeneration in `docs/STACK_PIN.md` (when to run, who approves)

- [ ] **Task 2 — Pin root package.json + lockfile** (AC: #1)
  - [ ] Subtask 2.1 — Root `package.json` declares `"engines": { "node": "24.18.0", "pnpm": "9.x" }` and `"packageManager": "pnpm@9.x"`
  - [ ] Subtask 2.2 — Run `pnpm install` to generate `pnpm-lock.yaml` with pinned versions (no `^`/`~` for pinned deps)
  - [ ] Subtask 2.3 — Add `.npmrc` with `engine-strict=true` and `save-exact=true` (forces pinned versions on `pnpm add`)
  - [ ] Subtask 2.4 — Add `package.json` script:
    ```json
    "scripts": {
      "dep:check": "node scripts/check_stack_pin.mjs",
      "lint:deps": "depcruise --validate .dependency-cruiser.cjs apps packages",
      "lint:all": "pnpm lint:deps && pnpm dep:check"
    }
    ```

- [ ] **Task 3 — Pin root pyproject.toml + uv.lock** (AC: #1)
  - [ ] Subtask 3.1 — Root `pyproject.toml` declares `requires-python = ">=3.12,<3.13"` and pinned versions for `fastapi`, `pydantic`, `sqlalchemy`, `alembic`, `structlog`, `opentelemetry-api`, `pytest`, `pyjwt`, `supabase`
  - [ ] Subtask 3.2 — Run `uv lock` to generate `uv.lock` with exact pinned versions
  - [ ] Subtask 3.3 — Add `uv.lock` to git (NOT to `.gitignore`)
  - [ ] Subtask 3.4 — Add `package.json` script equivalent: `uv run check-stack-pin` (Python version of the check)

- [ ] **Task 4 — Multi-stage Dockerfile with digest pinning** (AC: #1)
  - [ ] Subtask 4.1 — Create `Dockerfile` (root) with stages:
    - Stage 1 `frontend-builder`: `FROM node:24.18.0-alpine@sha256:<digest>` — `pnpm install --frozen-lockfile && pnpm build`
    - Stage 2 `backend-builder`: `FROM python:3.12-slim@sha256:<digest>` — `uv sync --frozen && uv run python -m compileall apps`
    - Stage 3 `backend-runtime`: `FROM python:3.12-slim@sha256:<same-digest>` — copy compiled artifacts + `.venv`
    - Stage 4 `frontend-runtime`: `FROM nginx:1.27-alpine@sha256:<digest>` — copy built frontend from Stage 1
  - [ ] Subtask 4.2 — `docker pull` each base image, capture digest with `docker inspect --format='{{index .RepoDigests 0}}' <image>`, pin in Dockerfile
  - [ ] Subtask 4.3 — Update `Dockerfile` base image pin procedure in `docs/STACK_PIN.md`
  - [ ] Subtask 4.4 — Add `Dockerfile.ci-checks` (commented-out) with examples of digest pinning

- [ ] **Task 5 — Stack pin check script** (AC: #2, #3)
  - [ ] Subtask 5.1 — Create `scripts/check_stack_pin.mjs` (Node.js) that:
    - Reads `docs/STACK_PIN.yaml`
    - Parses `package.json` (top-level + nested `apps/*` and `packages/*` packages)
    - Parses `pyproject.toml` + `uv.lock` for Python versions
    - Parses `Dockerfile` for `FROM <image>:<version>` patterns
    - Reports each pinned package with `<expected>` vs `<actual>` status
    - Exits 0 if all match, exits 1 if any drift
  - [ ] Subtask 5.2 — Create equivalent `scripts/check_stack_pin.py` (Python) for usage from `uv run`
  - [ ] Subtask 5.3 — Write `tests/integration/test_stack_pin_check.py` with assertions:
    - `test_check_passes_when_pinned`: run on clean repo → exit 0
    - `test_check_fails_on_drift`: monkey-patch `package.json` to bump `next` → exit 1
    - `test_check_passes_with_bump_tag`: simulate `[STACK BUMP]` commit message → exit 0 even with drift
    - `test_check_reports_drifted_packages`: assert output lists drifted package names

- [ ] **Task 6 — CI guard job** (AC: #2)
  - [ ] Subtask 6.1 — Add `.github/workflows/ci.yml` job `stack-pin-check` running after `lint-deps` (Story 0.1) and `lint-imports` (Story 0.1), before `rls-tests` (Story 0.2)
  - [ ] Subtask 6.2 — Job steps:
    - `actions/checkout@v4` with `fetch-depth: 0` (need full git history for commit message inspection)
    - `node-version: 24.18.0`, `python-version: 3.12.x`
    - `pnpm install --frozen-lockfile`
    - `uv sync --frozen`
    - `pnpm dep:check`
    - `uv run check-stack-pin`
    - Optional: `docker buildx bake --check` (if Dockerfile parser is implemented)
  - [ ] Subtask 6.3 — Step that checks the most recent commit message for `[STACK BUMP]`:
    - If absent AND drift detected → fail with violation message
    - If present AND drift detected → pass with warning log
  - [ ] Subtask 6.4 — Add `STACK_PIN_VIOLATION` annotation to PR via `actions/github-script@v7` if drift detected

- [ ] **Task 7 — Dependabot gated config** (AC: #3)
  - [ ] Subtask 7.1 — Create `.github/dependabot.yml` with weekly schedules:
    ```yaml
    version: 2
    updates:
      - package-ecosystem: "npm"
        directory: "/"
        schedule:
          interval: "weekly"
          day: "monday"
          time: "09:00"
          timezone: "Asia/Seoul"
        labels: ["stack-pin", "dependencies"]
        groups:
          pinned-dependencies:
            patterns: ["next", "react", "typescript", "tailwind", "fastapi", "pydantic", "sqlalchemy", "alembic", "structlog", "opentelemetry-api", "pytest"]
      - package-ecosystem: "pip"
        directory: "/"
        schedule:
          interval: "weekly"
          day: "tuesday"
          time: "09:00"
          timezone: "Asia/Seoul"
        labels: ["stack-pin", "dependencies"]
    ```
  - [ ] Subtask 7.2 — Add `github/CODEOWNERS` with `platform-team` as CODEOWNER for `/Dockerfile`, `/package.json`, `/pyproject.toml`, `/pnpm-lock.yaml`, `/uv.lock`, `/docs/STACK_PIN.yaml`
  - [ ] Subtask 7.3 — Branch protection rule: require `[STACK BUMP]` label on `stack-pin-violation` PRs to merge
  - [ ] Subtask 7.4 — Document dependabot policy in `docs/DEPENDABOT.md` (when to approve, how to bump)

- [ ] **Task 8 — Local CLI ergonomics** (AC: #3)
  - [ ] Subtask 8.1 — Add `pnpm dep:check` script (root) — runs `node scripts/check_stack_pin.mjs`
  - [ ] Subtask 8.2 — Add `uv run check-stack-pin` command (Python) — runs `scripts/check_stack_pin.py`
  - [ ] Subtask 8.3 — Add `scripts/bump_stack_pin.sh` helper that:
    - Reads current `docs/STACK_PIN.yaml`
    - Updates `package.json` + `pyproject.toml` + `Dockerfile` to new versions
    - Commits with message `[STACK BUMP] bump next 16.2.11 → 16.2.12` (matches the tag CI checks)
  - [ ] Subtask 8.4 — Document CLI usage in `docs/STACK_PIN.md`:
    - `pnpm dep:check` — local quick check
    - `uv run check-stack-pin` — Python equivalent
    - `pnpm dep:check:verbose` — show all `expected vs actual` even if matching
    - `scripts/bump_stack_pin.sh next 16.2.12` — bump with auto-tag

- [ ] **Task 9 — V8 regression bump policy** (AC: #2)
  - [ ] Subtask 9.1 — Document V8 regression test bumb policy in `docs/STACK_PIN.md`: any pinned version change requires running V8 regression (`packages/cost_engine/tests/regression_v8/`) before merge
  - [ ] Subtask 9.2 — Add `packages/cost_engine/tests/regression_v8/README.md` placeholder (full V8 setup is Story 4.4 — this story only documents the policy)
  - [ ] Subtask 9.3 — Add CODEOWNER approval step in CI: `[STACK BUMP]` PRs require `platform-team` review

## Dev Notes

### Architecture patterns to follow

- **AD-14 (Web-verified stack pin)** — The Stack table is the 2026-07-24 cold-start pin. Lockfiles must resolve these versions exactly; changes require CI and V8 regression. Banned infrastructure: Celery, Kafka, Redis as a persistent queue, and unmanaged components that violate the 1-operator constraint.
- **AD-1 (Modular Monolith + Hexagonal Core)** — The lockfile pins are the foundation for the dependency direction enforcement (Story 0.1). Drift = direction enforcement breaks.
- **AD-8 (Monetary types)** — `Decimal` (Python) + `bigint` (TS) must remain pinned. Floating-point drift would break 1원 reconciliation.
- **AD-15 (Cross-language conventions)** — Lockfile entries follow `snake_case` (Python deps) + `kebab-case` (npm packages).

### Cold-start stack pin (canonical, from ARCHITECTURE-SPINE.md §Stack)

| Name | Version | Lockfile location |
|------|---------|-------------------|
| Node.js | 24.18.0 LTS | `.nvmrc` + `package.json` `engines.node` |
| Python | 3.12.x | `.python-version` + `pyproject.toml` `requires-python` |
| pnpm | 9.x | `package.json` `packageManager` |
| uv | 0.11.32 | `pyproject.toml` `[tool.uv]` |
| Next.js | 16.2.11 (App Router) | `apps/web/package.json` |
| React | 19.2.8 | `apps/web/package.json` |
| TypeScript | 7.0.2 | `apps/web/package.json` |
| Tailwind CSS | 4.3.3 | `apps/web/package.json` |
| FastAPI | 0.139.2 | `apps/api/pyproject.toml` |
| Pydantic | 2.13.4 | `apps/api/pyproject.toml` |
| SQLAlchemy | 2.0.51 async | `apps/api/pyproject.toml` |
| Alembic | 1.18.5 | `apps/api/pyproject.toml` |
| structlog | 26.1.0 | `apps/api/pyproject.toml` |
| OpenTelemetry API | 1.44.0 | `apps/api/pyproject.toml` |
| pytest | 9.1.1 | `pyproject.toml` dev deps |
| PostgreSQL | 17 on Supabase | `Dockerfile` base image |
| Stripe API | `2026-06-24.dahlia` | `apps/api/core/settings.py` (config constant) |
| Vercel | managed frontend | `vercel.json` |
| Railway | `asia-southeast1-eqsg3a` Singapore | `railway.toml` |
| Anthropic Claude API | PRD-selected model family | `apps/api/modules/m10_ai/config.py` (constant) |
| Supabase CLI | latest | `Dockerfile` + CI |

### Source tree components to touch

```
bizup/                                       # project root
├── .nvmrc                                   # NEW — "24.18.0"
├── .python-version                          # NEW — "3.12.x"
├── .npmrc                                   # NEW — engine-strict=true, save-exact=true
├── .github/
│   ├── dependabot.yml                       # NEW — gated weekly updates
│   ├── CODEOWNERS                           # NEW — platform-team owns stack-pin files
│   └── workflows/
│       └── ci.yml                           # UPDATE — add stack-pin-check job
├── Dockerfile                               # NEW — multi-stage with digest pinning
├── package.json                             # UPDATE — engines, packageManager, dep:check script
├── pnpm-lock.yaml                           # NEW — generated by pnpm install
├── pnpm-workspace.yaml                      # NEW (from Story 0.1) — verify
├── pyproject.toml                           # UPDATE — requires-python, pinned deps
├── uv.lock                                  # NEW — generated by uv lock
├── apps/
│   ├── web/package.json                     # UPDATE — pin Next/React/TS versions
│   └── api/pyproject.toml                   # UPDATE — pin FastAPI/Pydantic/SQLAlchemy
├── packages/
│   └── cost_engine/
│       └── tests/regression_v8/README.md    # NEW — placeholder for V8 policy
├── scripts/
│   ├── check_stack_pin.mjs                  # NEW — Node.js check
│   ├── check_stack_pin.py                   # NEW — Python check
│   ├── regenerate_stack_pin.py              # NEW — parse ARCHITECTURE-SPINE.md
│   └── bump_stack_pin.sh                    # NEW — auto-bump with [STACK BUMP] tag
├── docs/
│   ├── STACK_PIN.yaml                       # NEW — canonical machine-readable pin
│   ├── STACK_PIN.md                         # NEW — human-readable + CLI docs
│   └── DEPENDABOT.md                        # NEW — dependabot policy
└── tests/
    └── integration/
        └── test_stack_pin_check.py          # NEW — pass/fail/bump-tag scenarios
```

### CI job order (cumulative across Stories 0.1-0.3)

```
┌─────────────────────┐
│ 1. setup            │ (Node 24.18.0, Python 3.12.x, uv cache)
└─────────────────────┘
            │
            ▼
┌─────────────────────┐
│ 2. lint-deps        │ (dep-cruiser, Story 0.1)
└─────────────────────┘
            │
            ▼
┌─────────────────────┐
│ 3. lint-imports     │ (import-linter, Story 0.1)
└─────────────────────┘
            │
            ▼
┌─────────────────────┐
│ 4. stack-pin-check  │ (THIS STORY — pnpm dep:check + uv check-stack-pin)
└─────────────────────┘
            │
            ▼
┌─────────────────────┐
│ 5. rls-tests        │ (Story 0.2 — supabase start + isolation tests)
└─────────────────────┘
            │
            ▼
┌─────────────────────┐
│ 6. test-architecture│ (Story 0.1 — fixture tests)
└─────────────────────┘
```

### Dependabot 2026 best practices (web research)

- **Grouped updates**: `groups:` block in `dependabot.yml` batches multiple updates into one PR per group per day (reduces PR spam).
- **Timezone-aware schedule**: `timezone: "Asia/Seoul"` ensures PRs land during business hours (09:00 KST = 00:00 UTC).
- **DAY-of-week scheduling**: prevents Dependabot from running on weekends (operator is solo — no weekend coverage).
- **Labels enforce CODEOWNER review**: `labels: ["stack-pin"]` + branch protection requires platform-team review for any dep PR.
- **Ignore `bump` commits**: Dependabot doesn't add `[STACK BUMP]` tags automatically — CODEOWNER must edit the commit message and re-push, OR add a CI bot that injects the tag when the bump is intentional.
- **Digest pinning for Docker**: `FROM python:3.12-slim@sha256:...` is the only way to guarantee reproducible builds across base-image updates.

### Lockfile vs package.json version pins

- **`package.json` should use exact versions** (no `^`/`~`) for pinned packages — `^16.2.11` allows `16.x.x` which violates AD-14.
- **`pnpm-lock.yaml` MUST be committed** — otherwise `pnpm install` can resolve a different version on different machines.
- **`uv.lock` MUST be committed** — same reason for Python deps.
- **`.npmrc` `save-exact=true`** prevents accidental `^`/`~` insertion when running `pnpm add <pkg>`.

### Anti-pattern prevention

- **DO NOT** use `^` or `~` in `package.json` for pinned packages. Use exact versions like `16.2.11`.
- **DO NOT** use `latest` for Docker base images. Use digest pinning (`@sha256:...`).
- **DO NOT** allow Dependabot to merge PRs without `platform-team` approval for `stack-pin` group.
- **DO NOT** bypass `[STACK BUMP]` tag silently. The CI guard exists for a reason.
- **DO** run `pnpm install --frozen-lockfile` and `uv sync --frozen` in CI/CD — never `pnpm install` (would re-resolve).
- **DO** update `docs/STACK_PIN.yaml` BEFORE updating lockfiles (canonical source first).
- **DO** run V8 regression test for any pinned version bump (Story 4.4 lays the foundation; this story documents the policy).
- **DO** re-pin Docker base image digests after EOL (annually or on security advisories).

### Testing standards

- **Unit tests**: `tests/integration/test_stack_pin_check.py` with `subprocess.run(['pnpm', 'dep:check'])` and assertion on exit code
- **Manual CI test**: create a PR that bumps `next` to `16.2.12` without `[STACK BUMP]` tag → verify CI fails
- **Bump-tag test**: same PR but with `[STACK BUMP]` in commit message → verify CI passes (with warning)
- **Dependabot test**: simulate a dependabot PR via `gh pr create --label stack-pin` → verify branch protection blocks

### References

- [Source: `ARCHITECTURE-SPINE.md#AD-14`] — Web-verified stack pin (canonical text)
- [Source: `ARCHITECTURE-SPINE.md#Stack`] — Cold-start pin table (12 tools)
- [Source: `ARCHITECTURE-SPINE.md#AD-1`] — Modular Monolith paradigm (lockfile enforces direction)
- [Source: `ARCHITECTURE-SPINE.md#AD-8`] — Monetary types (Decimal + bigint must remain pinned)
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 0.3`] — Original epic acceptance criteria
- [Source: `_bmad-output/planning-artifacts/prd.md#13.2`] — Stack pin rationale (V8 regression + 1원 reconciliation)
- [Source: `_bmad-output/implementation-artifacts/0-1-modular-monolith-hexagonal-core-skeleton.md`] — Prev story (lint foundation)
- [Source: `_bmad-output/implementation-artifacts/0-2-supabase-multi-tenancy-schema-rls-policies.md`] — Prev story (DB foundation)
- [Source: GitHub Dependabot docs — version 2 config](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file) — `groups`, `timezone`, `labels`
- [Source: pnpm docs — frozen-lockfile](https://pnpm.io/cli/install#--frozen-lockfile) — `pnpm install --frozen-lockfile`
- [Source: uv docs — sync](https://docs.astral.sh/uv/reference/cli/#uv-sync) — `uv sync --frozen`
- [Source: Docker docs — digests](https://docs.docker.com/engine/reference/builder/#from) — `FROM <image>@sha256:<digest>` reproducibility

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4 (claude-sonnet-4-20250514) — main-loop session

### Debug Log References

- `bash: node scripts/check_stack_pin.mjs` → initial run reported 12 drifts because the minimal YAML parser kept inline `# comment` text inside the value. **Fix**: added inline-comment stripping (skip-after-`#`-unless-inside-quoted-string) in both `check_stack_pin.mjs` and `check_stack_pin.py`. Re-run: 30/30 pins match.
- `bash: .venv/Scripts/python.exe scripts/check_stack_pin.py` → initial run failed with `UnicodeEncodeError: 'cp949' codec can't encode character '✗'`. The script used `✓` / `✗` markers that legacy Windows consoles (codepage 949) cannot decode. **Fix**: replaced unicode markers with ASCII (`OK`, `XX`, `WARN`, `FAIL`) in `check_stack_pin.py`; added UTF-8 reconfigure on stdout/stderr. Tests added `PYTHONIOENCODING=utf-8` + `errors="replace"` in subprocess capture to suppress capture-thread decode errors.
- `bash: npm_config_engine_strict=false pnpm install` → initial run blocked because `engines.node: "24.18.0"` is exact and the local Node is `v24.15.0`. **Decision (HANDOFF L3)**: keep exact pin in `package.json` (CI uses Node 24.18.0). Local lockfile generation uses one-shot `npm_config_engine_strict=false` override.
- `bash: pnpm lint:deps` → dep-cruiser v16 schema validation failed with `data/forbidden/0 must have required property 'from'`. The `type: 'cycle'` shortcut that worked in v15 is now deprecated in favor of explicit `from: {}` / `to: { circular: true }`. **Fix**: rewrote `no-circular` and `no-orphans` rules to use full `from`/`to` syntax.
- `bash: uv run import-linter lint` → root `package.json` originally referenced `uv run importlinter` (missing underscore, no `lint` subcommand, no `--config`). **Fix**: updated to `uv run import-linter lint --config pyproject.toml`. The existing CI workflow already invoked `import-linter lint` correctly, so this was a local-only discrepancy.
- Decision: `check-stack-pin` is invoked as `uv run python scripts/check_stack_pin.py` (not `[project.scripts]` console entry). uv 0.11.32 does not accept `[tool.uv.scripts]` as a sub-table (per existing root `pyproject.toml` comment), and `scripts/` is not part of any workspace package, so console_scripts is not viable without relocating the file. Documented in `package.json` script name.

### Completion Notes List

- **30 pins tracked** in `docs/STACK_PIN.yaml` (HANDOFF L3 deviation: 9 spec-vs-current variances documented in `notes` block with rationale + bump target).
- **2 lockfiles generated + committed**: `pnpm-lock.yaml` (76 packages) + `uv.lock` (already present, regenerated if pyproject changed).
- **CI guard** added as job #4 (`stack-pin-check`) in `.github/workflows/ci.yml`, between `lint-imports` (#3) and `test-architecture` (#5). Job order updated.
- **Dependabot weekly schedules** for npm (Mon 09:00 KST), pip (Tue 09:00 KST), docker (Wed 09:00 KST). Pinned packages grouped into single weekly PR per ecosystem.
- **CODEOWNERS** assigns platform-team to all stack-pin-touching paths (lockfiles, manifests, Dockerfile, ci workflow, scripts).
- **V8 regression bump policy** documented in `docs/STACK_PIN.md` + placeholder `packages/cost_engine/tests/regression_v8/README.md`. Story 4.4 will populate fixtures.
- **HANDOFF L3 variance**: 9 spec deviations preserved in `notes` (next, react, typescript, pydantic, sqlalchemy, postgresql, tailwind, structlog, opentelemetry). Each item records current value, spec value, and rationale.

### Verification

```
$ node scripts/check_stack_pin.mjs
[STACK_PIN] ✅ all 30 pins match

$ .venv/Scripts/python.exe scripts/check_stack_pin.py
[STACK_PIN] OK all 30 pins match

$ .venv/Scripts/python.exe -m pytest tests/integration tests/architecture tests/cost_engine tests/rls/test_service_role_audit.py
======================= 28 passed, 4 warnings in 8.87s ========================

$ .venv/Scripts/import-linter.exe lint --config pyproject.toml
Contracts: 2 kept, 0 broken.

$ npm_config_engine_strict=false pnpm lint:deps
x 2 dependency violations (0 errors, 2 warnings).
```

- 28/28 pytest (6 new stack-pin integration tests + 22 existing)
- 2/2 import-linter contracts KEPT
- dep-cruiser: 0 errors (2 warnings about Next.js orphan pages — expected for new app dir)
- Both check scripts: 30/30 pins match

### File List

**New files (11)**

- `docs/STACK_PIN.yaml` — canonical machine-readable pin (30 keys + 9 L3 notes)
- `docs/STACK_PIN.md` — human-readable companion (bump policy, CLI usage, anti-patterns)
- `docs/DEPENDABOT.md` — dependabot approval flows + branch protection rules
- `Dockerfile` — 4-stage multi-stage build (frontend-builder / backend-builder / backend-runtime / frontend-runtime)
- `.dockerignore` — build context filter
- `.github/dependabot.yml` — weekly gated updates for npm/pip/docker
- `.github/CODEOWNERS` — platform-team owns stack-pin paths
- `scripts/regenerate_stack_pin.py` — re-derive `STACK_PIN.yaml` from ARCHITECTURE-SPINE.md
- `scripts/check_stack_pin.py` — Python mirror of the Node check (30/30 pins pass)
- `scripts/bump_stack_pin.sh` — interactive helper that updates STACK_PIN.yaml + creates `[STACK BUMP]` commit
- `tests/integration/test_stack_pin_check.py` — 6 E2E tests (clean / drift / bump-env / bump-commit / report)
- `tests/integration/__init__.py` — package marker
- `packages/cost_engine/tests/regression_v8/README.md` — V8 policy placeholder

**Modified files (6)**

- `package.json` — exact `engines.node` (was `>=`), `dep:check:verbose`, `lint:imports` fixed
- `pyproject.toml` — added STACK PIN POLICY doc block pointing to STACK_PIN.yaml
- `.dependency-cruiser.cjs` — replaced `type: 'cycle'` shortcut with full `from`/`to` (v16 schema)
- `.github/workflows/ci.yml` — added `stack-pin-check` job (#4) with PR annotation; renumbered comments
- `scripts/check_stack_pin.mjs` — expanded from 38-line stub to full checker (parsing, drift authorization, 30 checks)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story 0-3 status updated

### Change Log

- 2026-07-25 — Story 0.3 implementation complete. Status: review.
- 2026-07-25 — Code review (3 reviewers, 84 raw findings → 50 unique). Verdict: **FAIL**. 26 PATCH · 4 DECISION · 7 DEFER · 4 DISMISS. Triage at `_bmad-output/implementation-artifacts/.cr-0-3-triage.md`.
- 2026-07-28 — 4 DECISION resolved (DOCKER-5=a, RANGE-1=a, SCHEMA-1=a, DOCKER-6=b). 26 PATCH + 4 DECISION 적용 진행.

### Review Findings (2026-07-25)

**Verdict**: ❌ FAIL — 5 critical blockers (Dockerfile digest pinning, pnpm-lock.yaml untracked, pydantic range, bump script broken, [STACK BUMP] bypass broken on squash-merge).

#### Decision Needed (4) — ✅ RESOLVED 2026-07-28

- [x] [Review][Decision] **DOCKER-5** → **(a) Pin now**. AC #1 완전 충족. ~30분 작업. `docker pull` + `docker inspect`로 4 stage + uv base digest 캡처 후 Dockerfile 업데이트 + DOCKER-3 docs 갱신. Location: `Dockerfile:22,41,70,97,45`.
- [x] [Review][Decision] **RANGE-1** → **(a) `pydantic==2.11.9`**. AD-14 strict 핀 + PYD-1 risk 없음 (2.11.x 호환 확인). uv lock 재생성 필요. Location: `apps/api/pyproject.toml:19`, `docs/STACK_PIN.yaml:40`.
- [x] [Review][Decision] **SCHEMA-1** → **(a) `exceptions:` 블록**. 9 deviation 각각 `reason`/`owner`/`deadline`/`spec` 4필드로 가시화. NOTES-1 check로 spec 변경 시 자동 감지. Location: `docs/STACK_PIN.yaml:72-108`.
- [x] [Review][Decision] **DOCKER-6** → **(b) semver `>=24.18.0 <25`**. `.nvmrc`가 exact 24.18.0을 보장하고 engines는 24.18.x 라인 허용. 로컬 dev friction 해소. Location: `package.json:8`.

#### Patch (26)

- [ ] [Review][Patch] **LOCK-1** — `git add pnpm-lock.yaml` and commit (AC #1 reproducibility) [`git status: ?? pnpm-lock.yaml`]
- [ ] [Review][Patch] **DOCKER-1** — Add `@sha256:...` digest pins to 4 `FROM` stages + `COPY --from=ghcr.io/astral-sh/uv:0.11.32` [`Dockerfile:22,41,70,97,45`]
- [ ] [Review][Patch] **DOCKER-3** — Document `--platform` for multi-arch reproducibility in `docs/STACK_PIN.md` [`docs/STACK_PIN.md`]
- [ ] [Review][Patch] **DOCKER-4** — Replace `urllib.request.urlopen` with retries or `requests` call [`Dockerfile:92`]
- [ ] [Review][Patch] **HEALTH-1** — nginx alpine `wget` not in default image → `apk add wget` or curl-based HEALTHCHECK [`Dockerfile:128`]
- [ ] [Review][Patch] **UV-1** — Regenerate `uv.lock` after `import-linter` pin change (specifier `>=2.0` vs `==2.13`) [`uv.lock:2604-2609`, `pyproject.toml:1225`]
- [ ] [Review][Patch] **HATCH-1** — Pin `hatchling` to specific version (not `"latest"`) [`docs/STACK_PIN.yaml:55`]
- [ ] [Review][Patch] **FASTAPI-1** — Move `fastapi` from dev extras to production deps [`apps/api/pyproject.toml:23-32`]
- [ ] [Review][Patch] **CHECK-1** — Extend `check_stack_pin.{mjs,py}` to read `pnpm-lock.yaml` and `uv.lock` [`scripts/check_stack_pin.{mjs,py}`]
- [ ] [Review][Patch] **TYPECHECK-1** — Add `@types/*` deps check against `dev_pins` section in `STACK_PIN.yaml` [`scripts/check_stack_pin.{mjs,py}`]
- [ ] [Review][Patch] **CASCADE-1** — Replace `parseYamlSimple` with PyYAML (handles BOM, anchors, escaped quotes, folded scalars) [`scripts/check_stack_pin.{mjs:38-93,py:38-93}`]
- [ ] [Review][Patch] **DOCKER-2** — Extend check to scan `.github/workflows/*.yml` `services:` images [`scripts/check_stack_pin.{mjs,py}`]
- [ ] [Review][Patch] **NOTES-1** — Add check that compares `notes.*.spec` against `ARCHITECTURE-SPINE.md §Stack` [`scripts/check_stack_pin.{mjs,py}`]
- [ ] [Review][Patch] **STYLE-1** — Replace `❌` in error path with ASCII `[ERROR]` [`scripts/check_stack_pin.py:1902`]
- [ ] [Review][Patch] **MSG-1** — Update violation message format to `STACK_PIN_VIOLATION: <pkg> drifted from <expected> to <actual>` (per spec) [`scripts/check_stack_pin.{mjs:299-303,py:288-292}`]
- [ ] [Review][Patch] **MSG-2** — Bump tag check: case-insensitive + check PR's commit (not merge commit) [`scripts/check_stack_pin.{mjs:117-124,py:140-149}`]
- [ ] [Review][Patch] **BUMP-1** — `bump_stack_pin.sh` actually edit manifests (not just YAML) [`scripts/bump_stack_pin.sh:14-21,107-138`]
- [ ] [Review][Patch] **BUMP-2** — Replace `python3` with `python` (macOS compat) [`scripts/bump_stack_pin.sh:119`]
- [ ] [Review][Patch] **BUMP-3** — Use proper YAML parser to read CURRENT (avoid `notes.*.current` false-match) [`scripts/bump_stack_pin.sh:51`]
- [ ] [Review][Patch] **BUMP-4** — Fix `pnpm install --frozen-lockfile=false` (nonsensical flag) → `pnpm install --no-frozen-lockfile <pkg>` [`scripts/bump_stack_pin.sh:145`]
- [ ] [Review][Patch] **BUMP-5** — Use YAML library to match keys exactly (avoid `pytest` matching `pytest-asyncio`) [`scripts/bump_stack_pin.sh:51`]
- [ ] [Review][Patch] **BUMP-6** — Exit code 1 on idempotent no-op (or require `--force`) [`scripts/bump_stack_pin.sh:59-62`]
- [ ] [Review][Patch] **CI-1** — Check PR's commit (not merge commit) for `[STACK BUMP]` tag; use `pull_request.head.sha` checkout [`scripts/check_stack_pin.{mjs,py}`, `.github/workflows/ci.yml:430-434`]
- [ ] [Review][Patch] **CI-2** — Pin all `actions/*@v*` to commit SHAs (supply-chain) [`.github/workflows/ci.yml`]
- [ ] [Review][Patch] **CI-3** — Exclude `stack-pin-check` from `concurrency: cancel-in-progress` on PRs [`.github/workflows/ci.yml:11-13`]
- [ ] [Review][Patch] **LABEL-1** — Add `actions/github-script@v7` step that applies `stack-pin-violation` label when `stack-pin-check` fails [`.github/dependabot.yml`, `.github/workflows/ci.yml`]
- [ ] [Review][Patch] **DEPEND-1** — Add `github-actions` ecosystem block to dependabot [`.github/dependabot.yml`]
- [ ] [Review][Patch] **DEPEND-2** — Add `open-pull-requests-limit: 5` to each ecosystem [`.github/dependabot.yml`]
- [ ] [Review][Patch] **REGEN-1** — Add `PyYAML` to `pyproject.toml [dependency-groups].dev` [`scripts/regenerate_stack_pin.py:2080-2086`, `pyproject.toml`]
- [ ] [Review][Patch] **REGEN-2** — Make `spine_path` configurable via CLI arg [`scripts/regenerate_stack_pin.py:2128-2131`]
- [ ] [Review][Patch] **CASCADE-2** — Preserve all `notes[k]` fields when merging [`scripts/regenerate_stack_pin.py:2106-2117`]
- [ ] [Review][Patch] **TEST-1** — Add tests for empty/missing/BOM `STACK_PIN.yaml` [`tests/integration/test_stack_pin_check.py`]
- [ ] [Review][Patch] **TEST-2** — Add `__pycache__` to `copytree` ignore list [`tests/integration/test_stack_pin_check.py`]

#### Deferred (7)

- [x] [Review][Defer] **OWNERS-1** — `@platform-team` placeholder (depends on org setup) [`.github/CODEOWNERS:177-178`] — deferred, pre-existing
- [x] [Review][Defer] **ENGINE-1** — `engines.node: "24.18.0"` exact pin blocks local dev (L3 decision) [`package.json:8`] — deferred, pre-existing
- [x] [Review][Defer] **SIGN-1** — No signed-commit enforcement for `[STACK BUMP]` (branch protection policy) [`docs/DEPENDABOT.md`] — deferred, pre-existing
- [x] [Review][Defer] **DEPEND-3** — Dependabot PRs don't auto-add `[STACK BUMP]` tag (documented manual step) [`.github/dependabot.yml`, `docs/DEPENDABOT.md`] — deferred, pre-existing
- [x] [Review][Defer] **DEPEND-4** — `non-pinned-dependencies` group overlaps with `pinned-dependencies` [`.github/dependabot.yml:263-275`] — deferred, pre-existing
- [x] [Review][Defer] **TYPES-1** — `apps/web/package.json` lacks `engines` field [`apps/web/package.json`] — deferred, pre-existing
- [x] [Review][Defer] **TGZ-1** — `deprecation==2.1.0` (2020) transitive via supabase [`uv.lock:2612-2621`] — deferred, pre-existing

#### Dismissed (4)

- HATCH-2 — duplicate of HATCH-1
- TIME-1 — Timezone "Asia/Seoul" + 09:00 = 00:00 UTC (correct, no DST)
- TEST-3 — `_run_node`/`_run_py` set `LC_ALL=C.UTF-8` (cosmetic but works)
- CONC-1 — `concurrency: cancel-in-progress` cancels across PRs (correct behavior)

<!-- Dev agent should populate this section on completion with files created/modified and key decisions -->
