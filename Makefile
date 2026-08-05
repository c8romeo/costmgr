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