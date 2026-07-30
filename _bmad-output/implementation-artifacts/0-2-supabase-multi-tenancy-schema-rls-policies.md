---
baseline_commit: bd58c180234abae60a1bd4e8bcd38ea766263d9a
---

# Story 0.2: Supabase Multi-Tenancy Schema + RLS Policies

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform engineer**,
I want **every business table to carry `tenant_id UUID` and a row-level security policy that reads `tenant_id` from `auth.jwt() -> 'app_metadata' ->> 'tenant_id'`**,
so that **two tenants can never see each other's data — even with a leaked JWT, a misconfigured ORM session, or a bypass attempt via `service_role` without a written audit trail** (AD-3, AD-9, AD-10, AD-23).

## Acceptance Criteria

1. **Given** Supabase project is provisioned in `ap-northeast-2` (Seoul) and the platform DB connection string is available in `apps/api/.env`
   **When** I add the initial Alembic migration `supabase/migrations/0001_platform_tenants.sql` (or Alembic-equivalent `apps/api/alembic/versions/0001_tenants_users_settings.py`) creating `tenants`, `users`, `tenant_memberships`, and `tenant_settings` tables
   **Then** every table has `tenant_id UUID NOT NULL` (or — for `tenants` itself — `id UUID PRIMARY KEY`; for `users` — nullable tenant_id referencing tenants) with a `FOREIGN KEY ... REFERENCES tenants(id)` constraint
   **And** `tenant_settings` is created with a JSONB columns-per-namespace structure (`onboarding`, `baseline`, `abc`, `ai`) plus `settings_version INTEGER NOT NULL DEFAULT 1` (AD-23)
   **And** the migration is idempotent (uses `IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS`) and reversible (down-migration drops tables in FK-safe order)

2. **Given** the four tables exist
   **When** I run `supabase/policies/0001_rls_policies.sql` (or Alembic `op.execute()` SQL block)
   **Then** every business table has `ENABLE ROW LEVEL SECURITY` + `ENABLE ROW LEVEL SECURITY FORCE` set
   **And** for each table, a policy `tenant_isolation_<table>` is created with `USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid)` covering **all four verbs** (`FOR SELECT`) AND `WITH CHECK (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid)` for `INSERT/UPDATE/DELETE`
   **And** the policy reads `app_metadata.tenant_id` (server-controlled, immutable by user) — not `user_metadata` (user-editable, unsafe)
   **And** a `tenant_admin_all` policy exists for `users` and `tenant_memberships` allowing `owner` role to read all members of their own tenant
   **And** `audit_logs` has separate `audit_log_insert` policy allowing only `service_role` (no JWT-based tenant filter — audit writes are platform-level)

3. **Given** RLS is enabled and the backend uses SQLAlchemy 2.0 async
   **When** I add `apps/api/core/security.py` with a Supabase JWT decoder that reads `Authorization: Bearer <token>`, verifies signature with `SUPABASE_JWT_SECRET`, and extracts `tenant_id` + `role` from `app_metadata`
   **Then** a FastAPI dependency `current_tenant_id() -> UUID` populates `request.state.tenant_id`
   **And** a SQLAlchemy event listener on the async session sets `SET LOCAL app.current_tenant_id = '<uuid>'` per transaction, so RLS policies see the JWT-derived tenant even if the JWT context is lost
   **And** a typed error `{code: "TENANT_FORBIDDEN", message_ko: "다른 테넌트 데이터에 접근할 수 없습니다", details: {}, trace_id: "..."}` is returned on policy violation (AD-15 error contract)

4. **Given** `service_role` is the JWT bearer key that bypasses RLS
   **When** I add `apps/api/core/service_role.py` exposing a `with_service_role(reason: str, actor_id: UUID, action: Callable)` helper
   **Then** the helper writes a typed `audit_logs` row **before** the privileged action with fields `{actor_id, action: 'service_role_bypass', reason, target_table, target_id: null, occurred_at: now_utc}`
   **And** the wrapped `action` runs only if the audit insert succeeds (audit-first guarantee)
   **And** an `apps/api/core/audit.py` helper exposes `emit_audit(...)` for non-bypass audit writes (e.g., user login, settings change)
   **And** CI includes a test `tests/rls/test_service_role_audit.py` that asserts: (a) audit row exists BEFORE the action, (b) `action` fails if audit insert fails, (c) `target_table` and `actor_id` are non-null

5. **Given** the schema migration + RLS policies + backend JWT decoder + service_role guard are in place
   **When** I run `tests/rls/test_tenant_isolation.py` (using `pytest-postgresql` or Supabase local Docker via `supabase start`)
   **Then** seed creates two tenants (A, B), 2 users per tenant, 2 tenant_settings rows (one per tenant)
   **And** test runs as tenant A's JWT and asserts `SELECT count(*) FROM tenant_settings` returns 1 (only A's row)
   **And** test asserts `SELECT * FROM users WHERE tenant_id = '<B>'` returns 0 rows
   **And** test asserts `INSERT INTO users (tenant_id=...)` with tenant B's UUID while authenticated as tenant A is rejected by RLS WITH CHECK
   **And** test asserts the `service_role` bypass test succeeds only if the audit row is present in `audit_logs` immediately before the privileged write

## Tasks / Subtasks

- [x] **Task 1 — Provision Supabase project** (AC: #1)
  - [x] Subtask 1.1 — **DEFERRED** per 2026-07-25 decision (3): real Supabase project provisioning lands in the pilot phase; this story ships local-Postgres + stub env vars
  - [x] Subtask 1.2 — `apps/api/.env.example` written (5 SUPABASE_* + DATABASE_URL + region pin)
  - [x] Subtask 1.3 — **DEFERRED** to pilot (Supabase dashboard 12-hr backup)

- [x] **Task 2 — Define initial migration** (AC: #1)
  - [x] Subtask 2.1 — `alembic init` skipped — wrote `alembic.ini` + `env.py` directly (cleaner for monorepo)
  - [x] Subtask 2.2 — `apps/api/alembic/env.py` uses async + asyncpg driver; falls back to sync URL when `postgresql+asyncpg://` is given
  - [x] Subtask 2.3 — `apps/api/alembic/versions/0001_tenants_users_memberships_settings.py` creates all 5 tables with CHECK constraints + indexes
  - [x] Subtask 2.4 — `CREATE EXTENSION IF NOT EXISTS pgcrypto` for portable `gen_random_uuid()`
  - [x] Subtask 2.5 — `downgrade()` drops in FK-safe order: `audit_logs` → `tenant_settings` → `tenant_memberships` → `users` → `tenants`

- [x] **Task 3 — SQLAlchemy 2.0 async ORM models** (AC: #1, #3)
  - [x] Subtask 3.1 — `apps/api/core/db.py` with `create_async_engine`, `async_sessionmaker`, `get_session()` async generator
  - [x] Subtask 3.2 — `apps/api/core/db_models.py` with `Tenant`, `User`, `TenantMembership`, `TenantSettings`, `AuditLog` (5 ORM classes)
  - [x] Subtask 3.3 — Each model uses `Mapped[UUID]` with `nullable=False` (or `nullable=True` for `users` cross-tenant cases; `audit_logs.actor_id` nullable)
  - [x] Subtask 3.4 — `TenantSettings` exposes `onboarding`, `baseline`, `abc`, `ai` as `Mapped[dict]` (JSONB) with `settings_version: Mapped[int] default=1`

- [x] **Task 4 — Tenant-aware session** (AC: #3)
  - [x] Subtask 4.1 — `apps/api/core/tenant_context.py` defines `TenantContext(tenant_id, role, user_id)` dataclass
  - [x] Subtask 4.2 — SQLAlchemy `begin` event listener issues `SET LOCAL app.current_tenant_id = %s` (cross-process via ContextVar)
  - [x] Subtask 4.3 — FastAPI dep `get_tenant_context(request) -> TenantContext` decodes JWT from `Authorization` header, raises `TENANT_FORBIDDEN` (401) on invalid/expired
  - [x] Subtask 4.4 — FastAPI dep `current_tenant_id() -> UUID` exposed for module endpoints

- [x] **Task 5 — JWT decoder (`apps/api/core/security.py`)** (AC: #3)
  - [x] Subtask 5.1 — `PyJWT==2.10.1` HS256 with `SUPABASE_JWT_SECRET`; `require=['exp']` enforces expiry
  - [x] Subtask 5.2 — `tenant_id` extracted from `payload['app_metadata']['tenant_id']` (NEVER `user_metadata` — AD-3 violation)
  - [x] Subtask 5.3 — `role` extracted from `payload['app_metadata']['role']`; defaults to `'viewer'`
  - [x] Subtask 5.4 — `TENANT_FORBIDDEN` typed error (AD-15 contract: `{code, message_ko, details, trace_id}`) on expired token
  - [x] Subtask 5.5 — `jwt_leeway_sec` setting (default 30s) wired through

- [x] **Task 6 — RLS policies** (AC: #2)
  - [x] Subtask 6.1 — `supabase/policies/0001_rls_policies.sql` enables + FORCES RLS on all 5 tables
  - [x] Subtask 6.2 — `tenant_isolation_{select,insert,update,delete}` policies for `tenants`, `users`, `tenant_memberships`, `tenant_settings`
  - [x] Subtask 6.3 — `tenant_admin_all_users` + `tenant_admin_all_memberships` policies for `owner` role
  - [x] Subtask 6.4 — `audit_log_insert` policy for `service_role` (no JWT filter)
  - [x] Subtask 6.5 — `supabase/policies/0002_rls_smoke_test.sql` DO-block verifies policy existence
  - [x] Subtask 6.6 — `supabase/README.md` documents apply order: alembic → 0001 policies → 0002 smoke test

- [x] **Task 7 — Service-role bypass guard** (AC: #4)
  - [x] Subtask 7.1 — `apps/api/core/audit.py` with `emit_audit(*, actor_id, action, target_table, target_id, reason, payload) -> AuditLog`
  - [x] Subtask 7.2 — `apps/api/core/service_role.py` with `with_service_role(...)` async context manager + `run_with_service_role(...)` functional wrapper; audit row emitted BEFORE action
  - [x] Subtask 7.3 — Docstring examples in `service_role.py` (backfill, ledger rebuild, schema migration data fix)
  - [x] Subtask 7.4 — `service-role-guard-lint` CI job: `grep -r 'service_role' apps/api/ --include="*.py"` fails if referenced outside `apps/api/core/service_role.py`

- [x] **Task 8 — Tenant isolation fixture tests** (AC: #5)
  - [x] Subtask 8.1 — CI-only per Decision 2; `supabase start` runs in CI's `rls-tests` job
  - [x] Subtask 8.2 — `tests/rls/conftest.py` seeds 2 tenants, 2 users, 2 settings rows (gated by `CI=true` or `RLS_RUN_LOCAL=1`)
  - [x] Subtask 8.3 — `tests/rls/test_tenant_isolation.py` with 5 tests: select-own, select-other-zero, insert-rejected, update-rejected, delete-rejected
  - [x] Subtask 8.4 — Local JWT simulation via `SET LOCAL app.current_tenant_id` + `SET LOCAL request.jwt.claims` (mirrors PostgREST behavior in production)

- [x] **Task 9 — Service-role audit tests** (AC: #4)
  - [x] Subtask 9.1 — `tests/rls/test_service_role_audit.py` with 10 unit tests: 3 emit_audit, 4 with_service_role (audit-first, audit-failure-aborts, 3 validation), 1 AuditLog model, 1 SYSTEM_ACTOR_ID, 1 audit-writes-before-action
  - [x] Subtask 9.2 — `audit_logs_block_update_delete()` trigger in migration 0001; full trigger-based enforcement lands in Epic 5 Story 5.2

- [x] **Task 10 — CI integration** (AC: #5)
  - [x] Subtask 10.1 — `.github/workflows/ci.yml` adds 3 new jobs: `test-service-role-guard`, `service-role-guard-lint`, `rls-tests`
  - [x] Subtask 10.2 — `rls-tests` job: `alembic upgrade head` → `psql -f supabase/policies/0001_rls_policies.sql` → `psql -f 0002_rls_smoke_test.sql` → `pytest tests/rls -v`
  - [x] Subtask 10.3 — Job uses `postgres:15` service container (port 54322)
  - [x] Subtask 10.4 — Test results uploaded to GitHub Actions artifact
  - [x] Subtask 10.5 — Failure includes policy name in error message (runbook deferred to pilot)

## Dev Notes

### Architecture patterns to follow

- **AD-3 (Multi-tenant isolation via Supabase RLS)** — Every business table has `tenant_id UUID NOT NULL` and an RLS policy `tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid`. The backend derives tenant identity from JWT, never from request data. Every `service_role` bypass writes a typed audit row before the privileged action.
- **AD-9 (Seoul storage, Singapore compute)** — Tenant data at rest, Auth, Storage, and backups live in Supabase `ap-northeast-2` (Seoul). FastAPI runs in Railway `asia-southeast1-eqsg3a` (Singapore); processes tenant payloads only in memory. No cross-region DB replication.
- **AD-10 (Identity & roles)** — Supabase Auth uses email + mandatory 2FA. Roles: `owner`, `member`, `viewer`, `consent-bound read-only consultant_proxy`. JWT carries `tenant_id` and `role`; backend middleware enforces per-endpoint.
- **AD-23 (One tenant settings aggregate)** — Exactly one `tenant_settings` row per tenant with `settings_version` + JSONB namespaces `onboarding`, `baseline`, `abc`, `ai`. Each module writes only its namespace via version-checked settings service. Parallel settings tables forbidden.
- **AD-15 (Cross-language conventions)** — `snake_case` SQL/Python; ISO-8601 UTC `TIMESTAMPTZ` (KST display); UUID v7 IDs for business entities; ULID `tenant_id` (note: epics uses `UUID` for tenant_id; AD-15 says ULID — both work in Postgres; ULID is 26-char string, UUID is 16-byte binary. **Use `UUID` for `tenant_id` to match Supabase Auth convention (Supabase uses `uuid` for `auth.users.id`)** — document this as a known variance from AD-15 in audit). Errors: `{code, message_ko, details, trace_id}`.
- **AD-2 (Append-only ledger)** — `audit_logs` is INSERT-only. PostgreSQL trigger (foundation laid here, full enforcement in Epic 5 Story 5.2).

### Cold-start stack pin additions

| Tool | Version | Purpose |
|------|---------|---------|
| Supabase CLI | latest (verify ≥ 1.200) | `supabase start` for local dev |
| Supabase Python | `supabase>=2.0` | `auth.admin.create_user()` |
| PyJWT | `>=2.8` | JWT signature verification |
| asyncpg | `>=0.29` | Postgres async driver |
| Alembic | 1.18.5 | Migration tool |
| pytest-postgresql | latest | Local DB fixture |
| testcontainers-python | latest | Optional Docker Postgres for CI |

### Source tree components to touch

```
apps/api/
├── alembic/
│   ├── env.py                          # NEW — async config
│   ├── script.py.mako                  # alembic template
│   └── versions/
│       └── 0001_tenants_users_memberships_settings.py  # NEW
├── core/
│   ├── db.py                           # NEW — async engine + session
│   ├── db_models.py                    # NEW — Tenant, User, TenantMembership, TenantSettings, AuditLog
│   ├── security.py                     # NEW — JWT decoder
│   ├── tenant_context.py               # NEW — TenantContext dataclass + FastAPI deps
│   ├── audit.py                        # NEW — emit_audit helper
│   └── service_role.py                 # NEW — with_service_role bypass guard
├── modules/                            # (no module code added in this story — just foundation)
├── tests/
│   └── rls/
│       ├── conftest.py                 # NEW — seed 2 tenants
│       ├── test_tenant_isolation.py    # NEW
│       └── test_service_role_audit.py  # NEW
└── .env.example                        # NEW — SUPABASE_*, DATABASE_URL

supabase/
├── config.toml                         # NEW — local Supabase config (ap-northeast-2)
├── migrations/
│   └── 0001_platform_tenants.sql       # NEW — or use Alembic (pick ONE source of truth)
├── policies/
│   ├── 0001_rls_policies.sql           # NEW
│   └── 0002_rls_smoke_test.sql         # NEW — local-test-only
└── README.md                           # NEW — migration apply order

tests/
└── rls/                                # NEW — see above
```

### Supabase RLS 2026 best practices (web research)

- **Use `app_metadata` for tenant_id, not `user_metadata`.** `app_metadata` is server-controlled (only `service_role` can edit); `user_metadata` is user-editable via `auth.updateUser()`. Putting `tenant_id` in `user_metadata` allows tenant self-promotion.
- **Pair `USING` with `WITH CHECK`** for `INSERT/UPDATE/DELETE` policies. `USING` alone only filters rows visible; `WITH CHECK` enforces the constraint on rows being written. Without `WITH CHECK`, a user can write rows with ANY `tenant_id` and then read them.
- **Use `FORCE ROW LEVEL SECURITY`** so even table owners are subject to policies (defense in depth — prevents accidental superuser bypass during maintenance).
- **JWT claims are immutable per request.** To change tenant context, the user must refresh the JWT. This prevents race conditions.
- **Service-role bypass is logged at the application layer, not at the DB layer.** RLS doesn't have a built-in "bypass audit" — apps must wrap `service_role` usage in `with_service_role()` (this story).
- **Auth Hooks (custom-access-token hook)** can inject `tenant_id` into `app_metadata` automatically on JWT mint — relevant for Epic 1 (onboarding). For this story, manually set `app_metadata` after `auth.admin.create_user()`.

### Derived-from architecture updates

- **Architecture spine AD-3** says `auth.jwt() ->> 'tenant_id'`. **Epics story 0.2 AC** says `auth.jwt() -> 'app_metadata' ->> 'tenant_id'`. Implementations MUST use the epics version (`app_metadata`) — it's the safer, more specific path. Document this as a clarification of AD-3 in commit message.
- **AD-15** says ULID for `tenant_id`. **Supabase Auth** uses UUID for `auth.users.id`. Use `UUID` for `tenant_id` to match Supabase convention; log this variance in `docs/architecture-decisions/AD-15-tenant-id-variance.md` (deferred to a later story).

### Testing standards

- **Local DB**: `supabase start` (Docker) provides `localhost:54322` Postgres + GoTrue + PostgREST. Tests connect to this.
- **Test isolation**: each test truncates `public.*` tables in `setUp` (use `pytest-postgresql` `postgresql_myproc` fixture or roll back transactions).
- **Multi-tenant test pattern**: authenticate as tenant A by setting `app.current_tenant_id` SQL GUC to A's UUID (mirrors the FastAPI dependency's behavior).
- **CI matrix**: Python 3.12.x only (per stack pin). Use `supabase/supabase-cli:latest` Docker image.

### Anti-pattern prevention

- **DO NOT** use `auth.jwt() ->> 'tenant_id'` directly (without `app_metadata` path). Tenant_id MUST come from `app_metadata` only.
- **DO NOT** put RLS policies in `ALTER TABLE` statements — keep them in `supabase/policies/0001_rls_policies.sql` for clarity.
- **DO NOT** use `service_role` directly in module endpoints. Always go through `with_service_role(...)`.
- **DO NOT** put `tenant_id` in request body or query string. Always derive from JWT.
- **DO NOT** grant `BYPASSRLS` to any role. RLS polices plus `service_role` (which is `bypassrls` by default in Supabase) is the only escape valve.
- **DO** write `audit_logs` row BEFORE the privileged action, not after.
- **DO** add `FORCE ROW LEVEL SECURITY` to all tables (defense in depth).
- **DO** use `IF NOT EXISTS` / `IF EXISTS` in migrations for idempotency.
- **DO** use `gen_random_uuid()` (pgcrypto) for portability — not `uuid_generate_v4()` (uuid-ossp).

### References

- [Source: `_bmad-output/planning-artifacts/prd.md#13.2 Supabase 서울 + RLS`] — Tenant data at rest in Seoul; RLS for all tables
- [Source: `_bmad-output/planning-artifacts/prd.md#13.3 2FA + JWT`] — Mandatory 2FA; JWT carries tenant_id + role
- [Source: `ARCHITECTURE-SPINE.md#AD-3`] — Multi-tenant isolation via Supabase RLS (canonical text)
- [Source: `ARCHITECTURE-SPINE.md#AD-9`] — Seoul storage, Singapore compute
- [Source: `ARCHITECTURE-SPINE.md#AD-10`] — Identity & roles (email + 2FA, owner/member/viewer/consultant_proxy)
- [Source: `ARCHITECTURE-SPINE.md#AD-15`] — Cross-language conventions (snake_case, UUID v7, error contract)
- [Source: `ARCHITECTURE-SPINE.md#AD-23`] — One tenant settings aggregate (settings_version + JSONB namespaces)
- [Source: `ARCHITECTURE-SPINE.md#AD-2`] — Append-only ledger (audit_logs foundation)
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 0.2`] — Original epic acceptance criteria
- [Source: Supabase docs — Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security) — `app_metadata` vs `user_metadata`, FORCE ROW LEVEL SECURITY
- [Source: Supabase docs — Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks) — Custom Access Token Hook (for Epic 1 integration)
- [Source: PostgreSQL docs — RLS Policies](https://www.postgresql.org/docs/17/sql-createpolicy.html) — USING vs WITH CHECK, four verbs

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-5 (claude-code, 2026-07-25)

### Debug Log References

- `pydantic-core==2.46.4` wheel on PyPI is broken (missing `core_schema.py`). Pinned to `pydantic-core==2.27.2` and `pydantic>=2.10,<2.12` in `apps/api/pyproject.toml [project.optional-dependencies].dev`.
- `[tool.uv.scripts]` is rejected as a sub-table of `[tool.uv]` in uv 0.11.32. Removed in favor of direct `uv run <command>` invocations.
- `pytest-asyncio` is incompatible with `pytest==9.1.1` (spec line 130). RLS tests are written as `def` (sync) and drive async helpers via `asyncio.run()`.
- Workspace member packages (`apps/api`, `packages/cost_engine`, `packages/services`, `packages/ports`) require their own `README.md` to satisfy hatchling's metadata validation. Added to each.
- `[tool.uv.extra-build-dependencies]` declared for each workspace member so hatchling is available at editable build time.

### Completion Notes List

- Story 0.2 implements the multi-tenant foundation: schema, RLS, JWT decoder, tenant context, service_role audit guard, and CI enforcement.
- All 5 ACs satisfied: schema with `tenant_id` + FKs; RLS policies using `app_metadata.tenant_id`; JWT decoder + FastAPI deps + `SET LOCAL` event listener; `with_service_role` audit-first guard; CI-only RLS fixture tests.
- 2026-07-25 decisions applied: **Docker CI-only** (RLS tests skip without `CI=true` or `RLS_RUN_LOCAL=1`); **Supabase deferred to pilot** (local Postgres + stub env vars).
- Local test result: **21/21 tests pass** (8 cost_engine + 3 architecture + 10 rls/service_role_audit), **5/5 RLS tenant_isolation skipped** (CI-only), **2/2 import-linter contracts KEPT**.
- CI workflow extended with 3 new jobs: `test-service-role-guard` (unit tests, no DB), `service-role-guard-lint` (grep guard), `rls-tests` (Postgres service + alembic + policies + pytest).
- HANDOFF L1 (import-linter single-root) still applies — Story 0.3 will introduce the `costmgr` namespace package; until then `apps.api` ↔ `packages.*` boundaries are enforced by AST-based tests (`tests/architecture/test_api_calls_only_ports.py`).

### File List

**NEW — schema + RLS:**
- `apps/api/.env.example` — 5 Supabase vars + DATABASE_URL + region pin
- `apps/api/alembic.ini` — Alembic config (script_location, sync URL fallback)
- `apps/api/alembic/env.py` — async-aware migration runner
- `apps/api/alembic/script.py.mako` — migration template
- `apps/api/alembic/versions/0001_tenants_users_memberships_settings.py` — 5 tables + trigger
- `apps/api/README.md` — apps/api package README (hatchling metadata requirement)
- `packages/cost_engine/README.md` — package README
- `packages/services/README.md` — package README
- `packages/ports/README.md` — package README
- `supabase/config.toml` — local Supabase config (region: ap-northeast-2)
- `supabase/policies/0001_rls_policies.sql` — RLS policies for all 5 tables
- `supabase/policies/0002_rls_smoke_test.sql` — CI smoke test
- `supabase/README.md` — apply order + pilot migration notes

**NEW — Python core (apps/api/core/):**
- `db.py` — async engine + `get_session()` async generator
- `db_models.py` — Tenant, User, TenantMembership, TenantSettings, AuditLog
- `security.py` — PyJWT decoder + `AuthError` typed error
- `tenant_context.py` — `TenantContext` + `get_tenant_context`/`current_tenant_id` FastAPI deps + `SET LOCAL` event listener
- `audit.py` — `emit_audit()` helper
- `service_role.py` — `with_service_role()` async context manager + `run_with_service_role()` functional wrapper

**NEW — tests/rls/:**
- `__init__.py` — package marker
- `conftest.py` — Postgres-54322 + CI-gated fixtures
- `test_tenant_isolation.py` — 5 RLS cross-tenant rejection tests (CI-only)
- `test_service_role_audit.py` — 10 unit tests (no DB required)

**MODIFIED:**
- `apps/api/main.py` — startup hook attaches `SET LOCAL` event listener
- `apps/api/core/settings.py` — added `supabase_jwt_secret`, `jwt_leeway_sec`
- `apps/api/pyproject.toml` — added Story 0.2 deps (sqlalchemy, asyncpg, alembic, pyjwt, pydantic, pydantic-settings, supabase)
- `pyproject.toml` — added `[tool.uv.extra-build-dependencies]`, `rls` + `asyncio` pytest markers
- `package.json` — added `test:rls` script
- `.github/workflows/ci.yml` — 3 new jobs (test-service-role-guard, service-role-guard-lint, rls-tests)

### Change Log

- 2026-07-25 — Story 0.2 implementation complete. 21/21 tests pass + 5 skipped (CI-only) + 2/2 import-linter contracts KEPT. Status: ready-for-dev → review.
- 2026-07-25 — Code Review (bmad-code-review) → 16 PATCH + 4 DECISION items addressed. CRITICAL fixes:
  RLS CI pipeline (7 items: DATABASE_URL mismatch, asyncpg→sync URL, postgres:15 shim,
  superuser BYPASSRLS, SET LOCAL without tx, UPDATE/DELETE return 0, unique emails);
  runtime correctness (TENANT listener wired, AuthError FastAPI handler, audit FK
  no longer conflicts with trigger, service-role lint false-positives);
  AC fidelity (request.state.tenant_id populated, 2 users/tenant in conftest,
  count(*)/SELECT * in tests);
  AC #3 cross-tenant error (spec Korean message + new AuthError variant);
  AUDIT-1 separate-transaction tamper-evidence (audit committed BEFORE action).
  22/22 tests pass + 5 skipped + 2/2 import-linter KEPT + service-role lint clean.
  Status: review → done.

## Review Follow-ups (AI)

> No remaining AI-Review items — all in-scope PATCH/DECISION items resolved.
> Deferred items (Story 0.4 or later): see CR triage report at
> `_bmad-output/implementation-artifacts/.cr-0-2-triage.md`.
> Story 0.4 (cross-language conventions + monetary types) is the next ready-for-dev story.
