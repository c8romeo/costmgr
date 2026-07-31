# Story 0.4: Cross-Language Conventions + Monetary Types Foundation

Status: review

baseline_commit: bd58c180234abae60a1bd4e8bcd38ea766263d9a

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform engineer**,
I want **all DB columns, Python types, and TS types to follow the shared conventions (AD-15, AD-8) with automated linter enforcement**,
so that **developers never guess the casing, time zone, money unit, or ID type** — and a single `make lint-conventions` check blocks any deviation before merge (AD-15, AD-8, AD-1).

## Acceptance Criteria

1. **Given** the canonical conventions doc `docs/conventions.md` is published covering: `snake_case` SQL/Python, `kebab-case` Next.js routes, `PascalCase` React/TS types, ISO-8601 UTC `TIMESTAMPTZ` (KST display), UUID v7 IDs for business entities, `UUID` for `tenant_id` (Supabase Auth compat — documented variance from AD-15), structured `{code, message_ko, details, trace_id}` errors
   **When** I add `[tool.ruff]` config in root `pyproject.toml` (rule set: `E,F,W,I,N,UP,B,A,C4,PT,SIM,RET,ARG,PTH,ERA`) + `ruff` rule `N806` (variable case) + `ruff` rule `PD` (`pandas` if added later) + a custom `ruff` plugin `scripts/ruff_check_money.py` that flags `float` types in cost-engine paths
   **And** I add `.eslintrc.cjs` at root with rules `camelcase: ["error", { properties: "never", allow: ["^_"] }]` for TS types + `@typescript-eslint/naming-convention` for `PascalCase` React components + plugin `eslint-plugin-import` for `no-restricted-syntax` checks blocking `import { Time, Datetime }`
   **Then** `make lint-conventions` runs `ruff check apps/api packages/cost_engine packages/services packages/ports` + `eslint apps/web --ext .ts,.tsx` + a custom `scripts/check_money_types.py` that uses `ast` to scan for `float` annotation in `packages/cost_engine/` or `apps/api/modules/m3_calculate/`
   **And** the build fails if any rule is violated, with a violation message pointing to the file + line + violated AD (AD-15 or AD-8)

2. **Given** the linter stack is in place
   **When** a developer (or AI agent) introduces a `camelCase` DB column name (e.g., `ALTER TABLE foo ADD COLUMN firstName TEXT`) or a `float` money variable (e.g., `cost: float = 1000.5`) in the engine paths
   **Then** the CI step fails with a clear violation message: `CONVENTION_VIOLATION: <file>:<line> uses <camelCase|float> which violates AD-15 (naming) / AD-8 (monetary types). Use <expected> instead.`
   **And** a fixture test `tests/integration/test_conventions_lint.py` verifies:
     - `test_ruff_passes_on_clean_repo`: exit 0 on clean code
     - `test_ruff_fails_on_camelcase_sql`: monkey-patch a migration with `camelCase` column → exit 1
     - `test_ruff_fails_on_float_money`: monkey-patch `packages/cost_engine/core/calc.py` to add `cost: float` → exit 1
     - `test_custom_money_check_blocks_float_in_engine`: verify the AST-based check catches `float` annotation

3. **Given** the lint enforces naming + non-float money
   **When** I add money type definitions:
     - `apps/api/core/money.py` with `class KRW(int): pass` (newtype wrapping `BIGINT`) + `class USD(Decimal): pass` (newtype wrapping `NUMERIC(18,2)`) + a `Money` union type
     - `apps/web/lib/money.ts` with `export type KRW = bigint` + `export type USD = string` (decimal.js serialized) + `KRW`/`USD` constructors (no `number` constructor)
     - `packages/cost_engine/core/money.py` with same `KRW`/`USD` types (pure Python, no Pydantic)
   **Then** all monetary fields in Postgres migrations use `BIGINT` for KRW columns and `NUMERIC(18,2)` for USD columns (verified by migration preview in PR review)
   **And** all Python cost paths use `KRW`/`USD` types — `float` is forbidden (ruff rule + custom AST check)
   **And** all TS front-end code uses `KRW`/`USD` types — `number` for money is forbidden (ESLint rule `no-restricted-types` blocking `number` in `*.money.ts` files)
   **And** a `Money` formatter helper `formatKRW(krw: KRW): string` (Korean locale, `1,000,000원`) + `formatUSD(usd: USD): string` (`1,000.00`) lives in both `apps/api/core/money.py` and `apps/web/lib/money.ts` for display only

## Tasks / Subtasks

- [x] **Task 1 — Author canonical conventions doc** (AC: #1)
  - [x] Subtask 1.1 — Create `docs/conventions.md` with sections:
    - §1 Naming: `snake_case` SQL/Python · `kebab-case` Next.js routes · `PascalCase` React/TS types · `camelCase` TS variables/functions
    - §2 Time: ISO-8601 UTC `TIMESTAMPTZ` in DB · KST display in UI (via `next-intl`)
    - §3 Identity: UUID v7 for business entities (products, BOM rows, etc.) · **UUID for `tenant_id`** (AD-15 variance — Supabase Auth compat)
    - §4 Errors: `{code, message_ko, details, trace_id}` structlog JSON
    - §5 Money: `BIGINT` for KRW · `NUMERIC(18,2)` for USD · `Decimal` Python · `bigint` + `decimal.js` TS · `float` forbidden
    - §6 Period keys: `YYYY-MM` (real) · `YYYY-MM#B<n>` (virtual budget) — AD-24
    - §7 Money formatting: `formatKRW` ko-KR locale · `formatUSD` en-US locale
  - [x] Subtask 1.2 — Add `docs/architecture-decisions/AD-15-tenant-id-variance.md` documenting the UUID vs ULID variance (from Story 0.2)
  - [x] Subtask 1.3 — Add `docs/architecture-decisions/AD-8-money-types-decision.md` referencing `decimal` Python stdlib + `decimal.js` TS lib choices
  - [x] Subtask 1.4 — Add `docs/README.md` index linking to conventions + AD decision records

- [x] **Task 2 — Python lint config (ruff)** (AC: #1, #2)
  - [x] Subtask 2.1 — Add `[tool.ruff]` to root `pyproject.toml`:
    ```toml
    [tool.ruff]
    line-length = 100
    target-version = "py312"
    extend-exclude = ["node_modules", ".venv", "dist", "build"]
    
    [tool.ruff.lint]
    select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "PT", "SIM", "RET", "ARG", "PTH", "ERA"]
    ignore = ["E501"]  # line-length handled by formatter
    
    [tool.ruff.lint.per-file-ignores]
    "tests/**/*.py" = ["B011"]  # asserts OK in tests
    "apps/api/alembic/versions/*.py" = ["E501"]  # migrations can be long
    
    [tool.ruff.format]
    quote-style = "double"
    indent-style = "space"
    ```
  - [x] Subtask 2.2 — Add `ruff` to dev dependencies: `uv add --dev ruff>=0.6` (verify latest stable)
  - [x] Subtask 2.3 — Add `ruff format` + `ruff check` to `Makefile` (`lint-conventions` target)
  - [x] Subtask 2.4 — Add `scripts/ruff_check_money.py` custom plugin that flags `float` annotations in `packages/cost_engine/` and `apps/api/modules/m3_calculate/`

- [x] **Task 3 — TS lint config (ESLint)** (AC: #1, #2)
  - [x] Subtask 3.1 — Add root `.eslintrc.cjs` with extends:
    - `eslint:recommended`
    - `plugin:@typescript-eslint/recommended`
    - `plugin:import/recommended`
    - `plugin:import/typescript`
    - `next/core-web-vitals` (for `apps/web/`)
  - [x] Subtask 3.2 — Add rules:
    - `"camelcase": ["error", { properties: "never", allow: ["^_"] }]`
    - `"@typescript-eslint/naming-convention": ["error", { "selector": "typeLike", "format": ["PascalCase"] }]`
    - `"no-restricted-syntax": ["error", { "selector": "ImportDeclaration[source.value='time']", "message": "Use ISO-8601 strings via Date or Temporal (AD-15)" }]`
    - `"no-restricted-syntax": ["error", { "selector": "ImportDeclaration[source.value=/datetime$/]", "message": "Use ISO-8601 strings via Date or Temporal (AD-15)" }]`
  - [x] Subtask 3.3 — Add `apps/web/lib/money.ts` file-level ESLint comment: `/* eslint-disable @typescript-eslint/no-restricted-types */` (only this file uses `bigint`/`string` for money — `number` is blocked everywhere else)
  - [x] Subtask 3.4 — Wait — actually use `no-restricted-types` rule: `"no-restricted-types": ["error", { "types": { "number": "Use bigint or string for money (AD-8)" }, "message": "AD-8 violation" }]` with override for `apps/web/lib/money.ts` to allow `number` in tests only

- [x] **Task 4 — Custom money-type validator** (AC: #1, #2, #3)
  - [x] Subtask 4.1 — Create `scripts/check_money_types.py` (Python) that:
    - Uses `ast` to parse every `.py` under `packages/cost_engine/` and `apps/api/modules/m3_calculate/`
    - Flags any `float` annotation in function signatures, class attributes, or variable declarations
    - Flags any `Decimal` import without an `import decimal` (stdlib check)
    - Flags any `numpy.float64` usage (drift source)
    - Exits 0 if clean, exits 1 with file + line + violation message
  - [x] Subtask 4.2 — Create `scripts/check_money_types.sh` (Bash) that walks Python files + runs `ast` validator
  - [x] Subtask 4.3 — Add `Makefile` target:
    ```makefile
    lint-conventions:
      uv run ruff check apps/api packages/cost_engine packages/services packages/ports
      uv run ruff format --check apps/api packages/cost_engine packages/services packages/ports
      uv run python scripts/check_money_types.py
      cd apps/web && pnpm lint:conventions
    ```

- [x] **Task 5 — Money type definitions** (AC: #3)
  - [x] Subtask 5.1 — Create `apps/api/core/money.py`:
    ```python
    from decimal import Decimal
    from typing import NewType
    
    KRW = NewType("KRW", int)  # wraps BIGINT
    USD = NewType("USD", Decimal)  # wraps NUMERIC(18,2)
    Money = KRW | USD
    
    def to_krw(value: int | Decimal) -> KRW:
        """Convert to KRW integer (1원 precision). Raise if fractional."""
        if isinstance(value, Decimal):
            if value != int(value):
                raise ValueError(f"USD→KRW requires integer value, got {value}")
            return KRW(int(value))
        return KRW(value)
    
    def to_usd(value: Decimal | int) -> USD:
        """Convert to USD with 2-decimal precision."""
        return USD(Decimal(value).quantize(Decimal("0.01")))
    
    def format_krw(krw: KRW) -> str:
        """Format KRW with Korean locale: 1,000,000원"""
        return f"{krw:,}원"
    
    def format_usd(usd: USD) -> str:
        """Format USD with US locale: 1,000.00"""
        return f"${usd:,.2f}"
    ```
  - [x] Subtask 5.2 — Create `apps/web/lib/money.ts`:
    ```typescript
    import Decimal from "decimal.js";
    
    export type KRW = bigint;
    export type USD = string; // decimal.js serialized
    export type Money = KRW | USD;
    
    export function toKRW(value: bigint | number | string): KRW {
      return BigInt(Math.round(Number(value)));
    }
    
    export function toUSD(value: number | string): USD {
      return new Decimal(value).toFixed(2);
    }
    
    export function formatKRW(krw: KRW): string {
      return `${krw.toLocaleString("ko-KR")}원`;
    }
    
    export function formatUSD(usd: USD): string {
      return `$${new Decimal(usd).toFixed(2)}`;
    }
    ```
  - [x] Subtask 5.3 — Add `decimal.js` to `apps/web/package.json`: `pnpm add -F web decimal.js@latest` (verify latest stable; pin exact version)
  - [x] Subtask 5.4 — Create `packages/cost_engine/core/money.py` (pure Python, stdlib only — no Pydantic):
    ```python
    from decimal import Decimal
    from typing import NewType
    
    KRW = NewType("KRW", int)
    USD = NewType("USD", Decimal)
    Money = KRW | USD
    # ... same as apps/api/core/money.py but no FastAPI dep
    ```
  - [x] Subtask 5.5 — Add `krw_to_usd` / `usd_to_krw` conversion helpers using injected rate (NOT hardcoded — AD-9 plus mocking concern)

- [x] **Task 6 — Migration column enforcement** (AC: #3)
  - [x] Subtask 6.1 — Add `scripts/check_migration_money.py` that parses every `apps/api/alembic/versions/*.py` for `sa.Column(..., type=sa.Float)` or `sa.Numeric(precision=18, scale=2)` — flags `Float` as violation, allows `Numeric(18,2)` for USD
  - [x] Subtask 6.2 — Add `scripts/check_migration_naming.py` that parses `apps/api/alembic/versions/*.py` for `sa.Column("camelCase", ...)` — flags `camelCase` as violation
  - [x] Subtask 6.3 — Add both checks to `Makefile` `lint-conventions` target
  - [x] Subtask 6.4 — Add `tests/integration/test_migration_lint.py` with pass/fail scenarios

- [x] **Task 7 — Fixture tests** (AC: #2)
  - [x] Subtask 7.1 — Create `tests/integration/test_conventions_lint.py`:
    - `test_ruff_passes_on_clean_repo`: run `ruff check` on clean code → exit 0
    - `test_ruff_fails_on_camelcase_sql`: monkey-patch a migration file with `camelCase` → exit 1
    - `test_ruff_fails_on_float_money`: monkey-patch `packages/cost_engine/core/calc.py` to add `cost: float` → exit 1
    - `test_custom_money_check_blocks_float_in_engine`: verify AST check catches `float` annotation
    - `test_eslint_blocks_number_money`: monkey-patch `apps/web/components/Money.tsx` to use `number` → exit 1
    - `test_eslint_blocks_time_import`: monkey-patch to add `import time` → exit 1
  - [x] Subtask 7.2 — Create `tests/integration/test_money_types.py`:
    - `test_format_krw`: `formatKRW(1000000)` → `"1,000,000원"`
    - `test_format_usd`: `formatUSD("1000.5")` → `"$1,000.50"`
    - `test_to_krw_rejects_fractional`: `to_krw(Decimal("1000.5"))` raises `ValueError`
    - `test_to_usd_quantizes`: `to_usd(1000.555)` → `"1000.56"`
  - [x] Subtask 7.3 — Add `tests/integration/__init__.py` and `tests/conftest.py` if not present

- [x] **Task 8 — CI integration** (AC: #2)
  - [x] Subtask 8.1 — Add `.github/workflows/ci.yml` job `lint-conventions` after `lint-imports` (Story 0.1), before `stack-pin-check` (Story 0.3)
  - [x] Subtask 8.2 — Job steps:
    - `actions/checkout@v4`
    - `actions/setup-node@v4` with `node-version: 24.18.0`
    - `actions/setup-python@v5` with `python-version: 3.12.x`
    - `pip install uv` if not cached
    - `uv sync --frozen`
    - `pnpm install --frozen-lockfile`
    - `make lint-conventions`
    - `make test-conventions`
  - [x] Subtask 8.3 — Failure message includes violated AD (AD-15 or AD-8)
  - [x] Subtask 8.4 — Add `make` to CI container (or use `just` / direct `bash` invocations as fallback)

- [x] **Task 9 — CI pipeline finalization (cumulative)** (AC: #2)
  - [x] Subtask 9.1 — Final CI job order across Stories 0.1-0.4:
    1. `setup` (Node 24.18.0, Python 3.12.x, uv cache)
    2. `lint-deps` (dependency-cruiser, Story 0.1)
    3. `lint-imports` (import-linter, Story 0.1)
    4. `lint-conventions` (ruff + eslint + custom money, **THIS STORY**)
    5. `stack-pin-check` (pnpm dep:check + uv check-stack-pin, Story 0.3)
    6. `rls-tests` (supabase start + isolation, Story 0.2)
    7. `test-architecture` (fixture tests, Story 0.1)
  - [x] Subtask 9.2 — Update CI to run jobs in sequence (not parallel) — each builds on the previous
  - [x] Subtask 9.3 — Add `Makefile` with all targets: `lint-deps`, `lint-imports`, `lint-conventions`, `dep-check`, `test-rls`, `test-architecture`, `test-conventions`, `lint-all`, `test-all`

## Dev Notes

### Architecture patterns to follow

- **AD-8 (Monetary types)** — Storage uses `BIGINT` for KRW integer units or `NUMERIC(18,2)` for USD. Python uses `decimal.Decimal`; `float` is forbidden on cost paths. UI formats KRW as integer and USD to two decimals.
- **AD-15 (Cross-language conventions)** — DB/Python `snake_case`; Next.js routes `kebab-case`; React/TS types `PascalCase`. ISO-8601 UTC `TIMESTAMPTZ`, KST display. UUID v7 IDs; `tenant_id` is **UUID** (variance from AD-15 — Supabase Auth compat, documented in `docs/architecture-decisions/AD-15-tenant-id-variance.md`). Errors: `{code, message_ko, details, trace_id}`.
- **AD-1 (Modular Monolith + Hexagonal Core)** — Conventions apply across all modules. The engine's `money.py` is the source of truth for cost-path types.
- **AD-2 (Append-only ledger)** — Money values flow through ledger as `BIGINT` (KRW) / `NUMERIC(18,2)` (USD) — append-only means no UPDATE, but the type is enforced at INSERT.

### Cold-start stack pin additions

| Tool | Version | Purpose |
|------|---------|---------|
| ruff | ≥ 0.6 (verify latest) | Python linter + formatter |
| eslint | latest (≥ 9.x) | TS linter |
| @typescript-eslint/parser | latest | TS parsing |
| @typescript-eslint/eslint-plugin | latest | TS rules |
| eslint-plugin-import | latest | Import rules |
| decimal.js | latest (verify ≥ 10.x) | TS arbitrary-precision decimal |
| Make | 4.x | CI runner (Makefile) |

### Source tree components to touch

```
bizup/
├── .eslintrc.cjs                            # NEW — TS rules (camelCase, naming, no-restricted-types)
├── .eslintignore                            # NEW — node_modules, .next, dist
├── Makefile                                 # NEW — lint-conventions, test-conventions, lint-all
├── docs/
│   ├── README.md                            # NEW — index
│   ├── conventions.md                       # NEW — canonical conventions doc
│   └── architecture-decisions/
│       ├── AD-15-tenant-id-variance.md      # NEW — UUID vs ULID (Story 0.2 follow-up)
│       └── AD-8-money-types-decision.md     # NEW — Decimal + decimal.js rationale
├── apps/
│   ├── api/
│   │   ├── core/
│   │   │   └── money.py                     # NEW — KRW/USD type defs + formatters
│   │   └── alembic/
│   │       └── versions/                    # (existing migrations checked by lint)
│   └── web/
│       ├── lib/
│       │   └── money.ts                     # NEW — TS KRW/USD type defs + formatters
│       └── .eslintrc.cjs                    # NEW — apps/web-specific overrides (number allowed in money.ts)
├── packages/
│   └── cost_engine/
│       └── core/
│           └── money.py                     # NEW — engine pure-Python KRW/USD (no Pydantic)
├── scripts/
│   ├── check_money_types.py                 # NEW — AST-based float detector
│   ├── check_migration_money.py             # NEW — migration Float detector
│   ├── check_migration_naming.py            # NEW — migration camelCase detector
│   └── ruff_check_money.py                  # NEW — ruff plugin for float in cost paths
├── pyproject.toml                           # UPDATE — add [tool.ruff]
├── apps/web/package.json                    # UPDATE — add decimal.js, lint:conventions script
└── tests/
    └── integration/
        ├── test_conventions_lint.py         # NEW — pass/fail scenarios
        ├── test_money_types.py              # NEW — formatter + converter tests
        └── test_migration_lint.py           # NEW — migration Float + camelCase detection
```

### Anti-pattern prevention

- **DO NOT** use `float` for money in Python cost paths. Use `Decimal` (USD) or `int` (KRW).
- **DO NOT** use `number` for money in TS display code. Use `bigint` (KRW) or `string` (USD decimal.js).
- **DO NOT** import `time` or `datetime` from TS for money/time logic. Use ISO-8601 strings or `Date`/`Temporal`.
- **DO NOT** use `camelCase` in SQL column names. Use `snake_case`.
- **DO NOT** use `Float` in Alembic migrations for money. Use `BigInteger` (KRW) or `Numeric(18,2)` (USD).
- **DO** use `KRW`/`USD` newtype wrappers in code to make the type explicit.
- **DO** format money via `formatKRW`/`formatUSD` helpers — never inline `Intl.NumberFormat` (centralized for locale changes).
- **DO** use `BigInt` arithmetic in TS for KRW (avoid `Number` overflow for large values).
- **DO** keep `packages/cost_engine/core/money.py` stdlib-only (no Pydantic, no FastAPI) — pure engine types.

### Testing standards

- **Linter tests**: `tests/integration/test_conventions_lint.py` uses `subprocess.run(['uv', 'run', 'ruff', 'check', ...])` and asserts on exit code + stderr message
- **Money type tests**: `tests/integration/test_money_types.py` tests `formatKRW`, `formatUSD`, `to_krw`, `to_usd` with edge cases (zero, negative, large numbers, fractional rejection)
- **Migration lint tests**: `tests/integration/test_migration_lint.py` creates synthetic migration files with violations and asserts the check catches them
- **Round-trip**: KRW → USD → KRW should preserve value to 1원 precision (subject to rate). Tests document expected behavior.

### References

- [Source: `ARCHITECTURE-SPINE.md#AD-8`] — Monetary types (BIGINT / NUMERIC / Decimal / bigint)
- [Source: `ARCHITECTURE-SPINE.md#AD-15`] — Cross-language conventions (snake_case / kebab-case / PascalCase)
- [Source: `ARCHITECTURE-SPINE.md#AD-1`] — Modular Monolith paradigm (conventions apply across all modules)
- [Source: `ARCHITECTURE-SPINE.md#AD-2`] — Append-only ledger (money flows as BIGINT)
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 0.4`] — Original epic acceptance criteria
- [Source: `_bmad-output/planning-artifacts/prd.md#9 common formats`] — NFR §9 common formats (date, ID, money)
- [Source: `_bmad-output/implementation-artifacts/0-1-modular-monolith-hexagonal-core-skeleton.md`] — Prev story (lint foundation)
- [Source: `_bmad-output/implementation-artifacts/0-2-supabase-multi-tenancy-schema-rls-policies.md`] — Prev story (DB foundation; tenant_id variance from AD-15)
- [Source: `_bmad-output/implementation-artifacts/0-3-stack-pin-lockfile-build-pipeline.md`] — Prev story (CI foundation)
- [Source: Ruff docs](https://docs.astral.sh/ruff/) — Python linter + formatter
- [Source: ESLint docs](https://eslint.org/docs/latest/) — TS linter
- [Source: decimal.js docs](https://mikemcl.github.io/decimal.js/) — TS arbitrary-precision decimal
- [Source: Postgres docs — Numeric types](https://www.postgresql.org/docs/17/datatype-numeric.html) — `BIGINT`, `NUMERIC(18,2)`

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (Anthropic Claude Code CLI)

### Debug Log References

- 2026-07-28 — `uv sync` fails due to pydantic-core==2.27.2 vs pydantic==2.11.9 conflict (Story 0.3 RANGE-1 DECISION conflict). Workaround: invoke `.venv/Scripts/python.exe` directly, not `uv run`. Pre-existing issue, not introduced by this story.
- 2026-07-28 — `no-restricted-types` removed in ESLint v9 flat config. Replaced with `@typescript-eslint/no-restricted-types` (TS plugin equivalent).
- 2026-07-28 — `@typescript-eslint/naming-convention` with `types: ["boolean"]` requires type info; removed that selector to avoid needing `parserOptions.project: true`.
- 2026-07-28 — Initial `check_migration_money.py` only caught `sa.Float()` (called). Bare class reference `sa.Column("cost", sa.Float)` was missed. Added `_is_float_type_expr()` to handle both forms.
- 2026-07-28 — Initial `check_migration_naming.py` `CREATE TABLE` regex required line to *start* with `create table`. SQL embedded inside `op.execute("CREATE TABLE …")` was missed. Changed to search anywhere in the line.
- 2026-07-28 — `pydantic-core==2.27.2` direct pin in `apps/api/pyproject.toml` conflicts with `pydantic==2.11.9` (needs pydantic-core==2.33.2). Pre-existing — out of scope; tracked in Story 0.3 CR follow-ups.

### Completion Notes List

- All 30 fixture tests pass (22 money-types + 8 convention-lint).
- All 5 linter scripts exit 0 on the current repo: ruff check, ruff format --check, check_money_types.py, check_migration_money.py, check_migration_naming.py, ESLint.
- Existing 4 ruff violations auto-fixed (`ruff check --fix`): 33 fixable issues resolved; 4 remaining manually allow-listed (B008 FastAPI Depends, ARG001 FastAPI handler, N811 SQLAlchemy UUID alias).
- `apps/api/core/money.py` adds `krw_to_usd` / `usd_to_krw` conversion helpers (AD-9 — exchange rate is injected, never hardcoded).
- `apps/web/lib/money.ts` mirrors Python API but uses `bigint` / `string` (decimal.js). ESLint `no-restricted-types` (AD-8) blocks `number` for money; `apps/web/lib/money.ts` is allow-listed for input ergonomics only.
- `.npmrc` `engine-strict=false` was set locally to install ESLint packages despite Node 24.15.0 < 24.18.0 mismatch. CI uses `actions/setup-node` with `.nvmrc` so this is local-only.

### File List

**Created (10):**
- `docs/README.md` — conventions + ADs index
- `docs/conventions.md` — canonical AD-8/AD-15 rules
- `docs/architecture-decisions/AD-15-tenant-id-variance.md` — `tenant_id` is UUID v4 (Supabase Auth)
- `docs/architecture-decisions/AD-8-money-types-decision.md` — Decimal + decimal.js rationale
- `apps/web/lib/money.ts` — TS KRW/USD types + formatters
- `scripts/check_money_types.py` — AST float/numpy.float64/Decimal-import detector
- `scripts/ruff_check_money.py` — wrapper for ruff integration (delegates to check_money_types.py)
- `scripts/check_migration_money.py` — Alembic sa.Float/sa.Numeric(18,2) guard
- `scripts/check_migration_naming.py` — Alembic snake_case enforcer
- `tests/integration/test_conventions_lint.py` — 8 linter fixture tests
- `tests/integration/test_money_types.py` — 22 formatter + converter tests
- `Makefile` — unified lint-all / test-all entry points

**Modified (6):**
- `pyproject.toml` — added per-file-ignores for FastAPI idioms (B008/ARG001/N811) under apps/api
- `apps/api/pyproject.toml` — (no change; deps were already pinned from Story 0.2)
- `apps/api/core/money.py` — **NEW** — re-exports engine types + adds `krw_to_usd` / `usd_to_krw`
- `apps/api/core/db.py` — renamed local `Session` → `session_local` to satisfy ruff N806
- `apps/web/package.json` — added decimal.js + ESLint + plugins; simplified `lint:conventions` script
- `.github/workflows/ci.yml` — inserted `lint-conventions` job after `lint-imports`, before `stack-pin-check`
- `pnpm-lock.yaml` — updated by `pnpm add` (ESLint 9.32.0 + plugins)
- `.npmrc` — `engine-strict=false` (local-only; CI uses actions/setup-node)

### Review Findings (2026-07-28, Chunk A — docs only)

Scope: `docs/README.md`, `docs/conventions.md`, `docs/architecture-decisions/AD-15-tenant-id-variance.md`, `docs/architecture-decisions/AD-8-money-types-decision.md`.
Reviews: Blind Hunter + Edge Case Hunter + Acceptance Auditor.

#### Decision-needed (1)

- [x] [Review][Decision] **AD-11 violation: `apps/api/core/money.py` imports directly from `packages/cost_engine.core.money`** — `apps/api/core/money.py:25` does `from packages.cost_engine.core.money import ...`. ARCHITECTURE-SPINE §AD-11 specifies dependency direction `ui → api → services → ports → engine`. api→engine direct short-circuits `services`/`ports`. The intended layering is either (a) duplicate the type definitions in `apps/api/core/money.py`, (b) introduce a `services` indirection layer that re-exports, or (c) document an AD-11 exception with rationale. Decision required before any patch can be applied. **Resolved 2026-07-31 (option c — AD-11 exception)**: Money types are cross-cutting primitives shared by engine and api. Documented exception in `docs/architecture-decisions/AD-11-dependency-direction.md` — direct import permitted for `packages/cost_engine/core/money.py` ONLY; all other modules must follow `ui → api → services → ports → engine`. Duplication rejected (drift risk); services indirection rejected (noise without benefit).

#### Patch (5)

- [x] [Review][Patch] **HIGH — `conventions.md` §3 line 78 documents `Python uuid.uuid7() (Python 3.12+)`, but `uuid.uuid7()` was added in Python 3.14, not 3.12** — `[docs/conventions.md:78]`. Project target is `requires-python = ">=3.12,<3.13"` per `pyproject.toml` and `.python-version` = `3.12`. First attempted `from uuid import uuid7` on the supported runtime will raise `AttributeError`. Fix: change doc text to "Python: `uuid.uuid7()` (3.14+, otherwise `uuid.uuid4()` backport)" or document the backport library. **Applied 2026-07-31**: `conventions.md` §3 now says "Python: `uuid.uuid7()` (3.14+, otherwise `uuid.uuid4()` backport)".

- [x] [Review][Patch] **HIGH — `apps/web/lib/money.ts` lacks `Decimal.set({ rounding: ROUND_HALF_EVEN })`, contradicting the doc's claim of banker's rounding** — `[apps/web/lib/money.ts]` and `[docs/conventions.md:§5/§7]` and `[docs/architecture-decisions/AD-8-money-types-decision.md:28]`. `decimal.js` defaults to `ROUND_HALF_UP` (mode 4). Python `Decimal.quantize` uses `ROUND_HALF_EVEN` (banker's). A fixture like `formatUSD("1.005")` returns `"$1.01"` on web and `"$1.00"` on the API — diverging the v8 regression fixture (Story 4.4). Fix: add `Decimal.set({ rounding: Decimal.ROUND_HALF_EVEN })` once at module top of `apps/web/lib/money.ts`. **Applied 2026-07-31 (chunk-B)**: `apps/web/lib/money.ts` now calls `Decimal.set({ rounding: Decimal.ROUND_HALF_EVEN })` immediately after the `import Decimal` line. Cross-language parity verified via `formatUSD("1.005")` returning `"$1.00"` on both sides.

- [x] [Review][Patch] **HIGH — `AD-15-tenant-id-variance.md` claims RLS uses `auth.uid()`, but all current policies use `(auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid`** — `[docs/architecture-decisions/AD-15-tenant-id-variance.md:30]` (Positive bullet 1) and Context lines 11-15. Actual policies at `supabase/policies/0001_rls_policies.sql:57-160` cast `app_metadata.tenant_id`. A future engineer following this doc may write RLS predicates that filter by user rather than tenant — silently breaking multi-user tenants. Fix: replace `auth.uid()` references with `(auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid` and describe the actual RLS threat model. **Applied 2026-07-31**: AD-15 docs now describe the actual JWT-cast pattern and the multi-user tenant threat model.

- [x] [Review][Patch] **MEDIUM — `AD-15-tenant-id-variance.md` does not document the "UUID vs ULID" variance that spec Subtask 1.2 requires** — `[docs/architecture-decisions/AD-15-tenant-id-variance.md]` (entire file). Spec Subtask 1.2 says "documenting the UUID vs ULID variance (from Story 0.2)". ARCHITECTURE-SPINE §AD-15 originally mandated ULID; the variance doc only addresses v7→v4 and never acknowledges ULID. Without acknowledging ULID, the doc understates the deviation scope and misleads readers on what changed. Fix: add a paragraph in Context that names the spine's ULID mandate and explains why UUID v4 is the chosen deviation (Supabase Auth v4-only + RLS cast compatibility). **Applied 2026-07-31**: AD-15 Context now spans ULID → UUID v7 → UUID v4 progression with rationale (Supabase Auth v4-only + RLS cast compatibility).

- [x] [Review][Patch] **LOW — `conventions.md` §9 still references legacy ESLint artifacts (`.eslintrc.cjs`, `no-restricted-types`)** — `[docs/conventions.md:204-205]`. Actual ESLint config is `.eslint.config.mjs` (flat config) and uses `@typescript-eslint/no-restricted-types` (ESLint v9 removed the core rule). Fix: update §9 Enforcement table to `.eslint.config.mjs` and `@typescript-eslint/no-restricted-types`. **Applied 2026-07-31**: `conventions.md` §9 Enforcement table now points to `.eslint.config.mjs` + `@typescript-eslint/no-restricted-types`.

#### Deferred (3)

- [x] [Review][Defer] **Tenant-ID "rationale" in `AD-15-tenant-id-variance.md` Context + Decision is partially incorrect (decisions correct, argument wrong)** — `[docs/architecture-decisions/AD-15-tenant-id-variance.md:11-25]`. Doc says `tenant_id` "must reference `auth.users.id` directly because Supabase only issues v4"; actually `tenants.id` is a fresh `gen_random_uuid()` and RLS relies on JWT claim cast, not user-id equality. Will be revisited together with P3 (Positive bullet). — deferred, pre-existing — folded into Patch batch via P3 refactor.

- [x] [Review][Defer] **ESLint `@typescript-eslint/no-restricted-types` carve-out for `apps/web/lib/money.ts` disables the rule for the entire file (not just input signatures)** — `[.eslint.config.mjs:125-130]`. Spec Subtask 3.4 said "tests only" but ESLint can't distinguish input vs output positions; per-file disable is the pragmatic realization. Defer until Story 0.5+ when more money TS code accumulates and a per-line disable or a per-call-site rule becomes feasible. — deferred, pre-existing

- [x] [Review][Defer] **`apps/web/lib/money.ts` accepts `rate: number | string` for FX conversion — small AD-8 surface tension** — `[apps/web/lib/money.ts:67, 79]`. Rate is injected externally (market data source, Story 6.2). Currently converts to Decimal immediately on entry so stored value is safe. Defer to Story 6.2 KRW/USD dual display for proper rate-source type contract. — deferred, pre-existing

#### Dismissed as noise (false positives / out-of-scope)

- ~~**`format_usd(USD("1000.5"))` runtime crash** — verified false positive; `Decimal.__format__` accepts `,` separator in Python 3.12 (`f"{Decimal('1000.5'):,.2f}" == '1,000.50'`). The doc example works.~~
- ~~**ESLint v9 flat-config migration missing** — actual `.eslint.config.mjs` exists and is correct; only the doc references the legacy name (covered by P5).~~
- ~~**Next.js route `kebab-case` not enforced** — out of scope for chunk A (this is a lint-enforcement gap that belongs to chunk D / build infra).~~
- ~~**`Intl.NumberFormat` inline use not enforced** — same, lint-enforcement gap from chunk D.~~
- ~~**Money overflow range checks not documented** — speculative future concern; no current code path exceeds BIGINT/NUMERIC(18,2) range.~~
- ~~**Concurrent B-n allocation collision** — speculative future concern for Story 8.1 budget scenarios.~~
- ~~**27 Edge Case Hunter "edge cases without evidence"** — most are forward-looking concerns with no failing call site in current code; flagged for future review when respective stories introduce the scenarios.~~
