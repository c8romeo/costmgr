# costmgr — unified Makefile for lint + test entry points.
#
# Story 0.4 — `lint-conventions` target composes ruff + ESLint + custom
# money-type / migration linters. Each story adds its own target below.
#
# Usage:
#   make help                # show available targets
#   make lint-all            # run every linter
#   make test-all            # run the full test suite (excluding CI-only jobs)
#   make lint-conventions    # AD-8 + AD-15 conventions (Story 0.4)
#
# On Windows, GNU Make is required (choco install make). The targets also
# run via direct bash invocation when `make` is not available.

# ─────────────────────────────────────────────────────────────────
# Tooling — resolve to .venv binaries so paths are repo-local.
# ─────────────────────────────────────────────────────────────────
VENV_BIN := .venv/bin
VENV_SCRIPTS := .venv/Scripts
ifeq ($(OS),Windows_NT)
	PYTHON := $(VENV_SCRIPTS)/python.exe
	RUFF := $(VENV_SCRIPTS)/ruff.exe
	PYTEST := $(VENV_SCRIPTS)/pytest.exe
	PYTHONPATH := apps;packages;.
	SHELL := bash
else
	PYTHON := $(VENV_BIN)/python
	RUFF := $(VENV_BIN)/ruff
	PYTEST := $(VENV_BIN)/pytest
	PYTHONPATH := apps:packages:.
endif

export PYTHONPATH
export PYTHONIOENCODING := utf-8

# ─────────────────────────────────────────────────────────────────
# help — list available targets
# ─────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo "costmgr Makefile targets:"
	@echo ""
	@echo "  make dev-up            db-up + db-migrate + db-seed (full local bring-up)"
	@echo "  make db-up             start pinned Postgres 15 (docker compose)"
	@echo "  make db-migrate        alembic upgrade head + RLS policies (CI order)"
	@echo "  make db-seed           seed dev tenant + print dev JWT"
	@echo "  make db-down           stop Postgres (keeps volume)"
	@echo "  make db-reset          destroy volume and re-create from scratch"
	@echo "  make api-dev           run FastAPI on :8765"
	@echo "  make web-dev           run Next.js on :3000"
	@echo "  make smoke             drive the MVP critical path over real HTTP"
	@echo ""
	@echo "  make lint-deps         dependency-cruiser (Story 0.1)"
	@echo "  make lint-imports      import-linter (Story 0.1)"
	@echo "  make lint-conventions  ruff + ESLint + money-type + migration (Story 0.4)"
	@echo "  make dep-check         pnpm dep:check + check_stack_pin (Story 0.3)"
	@echo "  make lint-all          all of the above"
	@echo ""
	@echo "  make test-architecture architecture fixture tests (Story 0.1)"
	@echo "  make test-rls          RLS unit tests (no DB; CI runs full RLS)"
	@echo "  make test-conventions  convention linter tests (Story 0.4)"
	@echo "  make test-stack-pin    stack-pin check tests (Story 0.3)"
	@echo "  make test-all          all of the above (excluding live Postgres jobs)"
	@echo ""
	@echo "Tooling:"
	@echo "  PYTHON = $(PYTHON)"
	@echo "  RUFF   = $(RUFF)"

# ─────────────────────────────────────────────────────────────────
# Local runnable stack — Walking Skeleton verification sprint
#
# Until now the repo could be linted and unit-tested but never RUN:
# no compose file, no seed, and 86 DB-backed tests skipped with
# "enabled when CI shim is wired". These targets close that gap so
# "green in CI" and "works on a machine" mean the same thing.
#
# Env is sourced from apps/api/.env. pydantic-settings resolves its
# `env_file=".env"` relative to CWD, so sourcing explicitly (rather
# than relying on the file being found) is what makes running from
# the repo root work.
# ─────────────────────────────────────────────────────────────────
ENVFILE := apps/api/.env
LOAD_ENV := set -a; source $(ENVFILE); set +a;

.PHONY: db-up
db-up:
	docker compose up -d
	@echo "▶ waiting for Postgres to report healthy…"
	@for i in $$(seq 1 40); do \
		status=$$(docker inspect -f '{{.State.Health.Status}}' costmgr-postgres 2>/dev/null || echo starting); \
		if [ "$$status" = "healthy" ]; then echo "✅ Postgres healthy on :54322"; exit 0; fi; \
		sleep 2; \
	done; \
	echo "❌ Postgres did not become healthy in 80s"; docker compose logs --tail=40 postgres; exit 1

.PHONY: db-down
db-down:
	docker compose down

.PHONY: db-reset
db-reset:
	docker compose down -v
	$(MAKE) db-up

# Mirrors the CI `rls-tests` job step order exactly: alembic first, then
# the Supabase shim (auth.jwt() stub + roles), then the RLS policies.
# Local dev needs the shim because there is no real Supabase auth schema.
.PHONY: db-migrate
db-migrate:
	@$(LOAD_ENV) \
	echo "▶ alembic upgrade head" && \
	.venv/Scripts/python.exe -m alembic -c apps/api/alembic.ini upgrade head && \
	echo "▶ supabase/policies/0000_supabase_ci_shim.sql" && \
	docker exec -i costmgr-postgres psql -v ON_ERROR_STOP=1 -U postgres -d postgres < supabase/policies/0000_supabase_ci_shim.sql > /dev/null && \
	echo "▶ supabase/policies/0001_rls_policies.sql" && \
	docker exec -i costmgr-postgres psql -v ON_ERROR_STOP=1 -U postgres -d postgres < supabase/policies/0001_rls_policies.sql > /dev/null && \
	echo "✅ schema + RLS applied"

.PHONY: db-seed
db-seed:
	@$(LOAD_ENV) .venv/Scripts/python.exe scripts/dev_seed.py

.PHONY: dev-up
dev-up: db-up db-migrate db-seed
	@echo ""
	@echo "✅ local stack ready — now run 'make api-dev' and 'make web-dev' in two shells"

.PHONY: api-dev
api-dev:
	@$(LOAD_ENV) .venv/Scripts/python.exe -m uvicorn apps.api.main:app --reload --port 8765

.PHONY: web-dev
web-dev:
	cd apps/web && COSTMGR_API_URL=http://localhost:8765 pnpm dev

.PHONY: smoke
smoke:
	@$(LOAD_ENV) .venv/Scripts/python.exe scripts/smoke_e2e.py

# ─────────────────────────────────────────────────────────────────
# Story 0.1 — dependency-cruiser + import-linter
# ─────────────────────────────────────────────────────────────────
.PHONY: lint-deps
lint-deps:
	pnpm lint:deps

.PHONY: lint-imports
lint-imports:
	pnpm lint:imports

# ─────────────────────────────────────────────────────────────────
# Story 0.4 — AD-8 monetary types + AD-15 cross-language conventions
# ─────────────────────────────────────────────────────────────────
.PHONY: lint-conventions
lint-conventions:
	@echo "▶ ruff check (Python AD-15 naming + style)"
	$(RUFF) check apps/api packages
	@echo "▶ ruff format --check"
	$(RUFF) format --check apps/api packages
	@echo "▶ check_money_types.py (AD-8 float-free money cost paths)"
	$(PYTHON) scripts/check_money_types.py
	@echo "▶ check_migration_money.py (AD-8 sa.Float / sa.Numeric guard)"
	$(PYTHON) scripts/check_migration_money.py
	@echo "▶ check_migration_naming.py (AD-15 snake_case migrations)"
	$(PYTHON) scripts/check_migration_naming.py
	@echo "▶ ESLint AD-15 (TS naming + AD-8 no-restricted-types)"
	./node_modules/.bin/eslint --config .eslint.config.mjs apps/web --ext .ts,.tsx

# ─────────────────────────────────────────────────────────────────
# Story 0.3 — stack-pin check (pin lockfile + manifest)
# ─────────────────────────────────────────────────────────────────
.PHONY: dep-check
dep-check:
	pnpm dep:check
	$(PYTHON) scripts/check_stack_pin.py

# ─────────────────────────────────────────────────────────────────
# Composite — all linters in order
# ─────────────────────────────────────────────────────────────────
.PHONY: lint-all
lint-all: lint-deps lint-imports lint-conventions dep-check
	@echo "✅ All linters passed"

# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────
.PHONY: test-architecture
test-architecture:
	$(PYTEST) tests/architecture tests/cost_engine -v

.PHONY: test-rls
test-rls:
	$(PYTEST) tests/rls/test_service_role_audit.py -v

.PHONY: test-conventions
test-conventions:
	$(PYTEST) tests/integration/test_conventions_lint.py tests/integration/test_money_types.py -v

.PHONY: test-stack-pin
test-stack-pin:
	$(PYTEST) tests/integration/test_stack_pin_check.py -v

# ─────────────────────────────────────────────────────────────────
# Story 0.5 — Frontend tooling (vitest + Playwright)
# ─────────────────────────────────────────────────────────────────
.PHONY: web-test
web-test:
	cd apps/web && pnpm test --run

.PHONY: web-e2e
web-e2e:
	cd apps/web && pnpm playwright test --project=chromium

.PHONY: test-all
test-all: test-architecture test-rls test-conventions test-stack-pin
	@echo "✅ All tests passed (excluding live Postgres jobs)"

# ─────────────────────────────────────────────────────────────────
# Convenience targets
# ─────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .next .ruff_cache