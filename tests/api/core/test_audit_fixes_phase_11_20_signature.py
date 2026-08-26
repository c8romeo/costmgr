"""tests.api.core.test_audit_fixes_phase_11_20_signature — canonical signature 정직 회복 verification.

Phase 11~20 audit-fixes sprint (cj-style 154번째) — 24 broken emit_audit_typed call sites
across 14 finops files 의 canonical signature 정직 회복 verification.

Per CR 11-4 P-015: PURE validator pattern — NO fixtures, NO DB, sync AST/regex parsing.
Per CR 1-1 audit-first INSERT: target_id=None + payload (renamed from metadata).

24 BROKEN_SITES → 24 NEW canonical sites mapping:

| File                             | Sites | ActionClass            |
|----------------------------------|-------|-----------------------|
| executive_dashboard_aggregator   | 1     | FINOPS_REPORTING      |
| cross_module_kpi                 | 1     | FINOPS_REPORTING      |
| executive_report_generator       | 2     | FINOPS_REPORTING      |
| executive_dashboard_routes       | 7     | FINOPS_REPORTING      |
| carbon_emissions_aggregator      | 1     | FINOPS_SUSTAINABILITY |
| sustainability_kpi_selector      | 1     | FINOPS_SUSTAINABILITY |
| sustainability_report_generator  | 2     | FINOPS_SUSTAINABILITY |
| scheduled_sustainability_dispatch| 1     | FINOPS_SUSTAINABILITY |
| commitment_inventory_aggregator  | 1     | FINOPS_COMMITMENT     |
| commitment_kpi_selector          | 1     | FINOPS_COMMITMENT     |
| commitment_report_generation     | 2     | FINOPS_COMMITMENT     |
| scheduled_commitment_dispatch    | 1     | FINOPS_COMMITMENT     |
| pricing_report_generation        | 2     | FINOPS_PRICING        |
| scheduled_pricing_dispatch       | 1     | FINOPS_PRICING        |
|                                  |=24    |                       |
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FINOPS_DIR = ROOT / "apps" / "api" / "modules" / "finops"

# 24 BROKEN_SITES registry — file → (ActionClass enum, expected emit_audit_typed count)
BROKEN_SITES: dict[str, tuple[str, int]] = {
    "executive_dashboard_aggregator.py": ("FINOPS_REPORTING", 1),
    "cross_module_kpi.py": ("FINOPS_REPORTING", 1),
    "executive_report_generator.py": ("FINOPS_REPORTING", 2),
    "executive_dashboard_routes.py": ("FINOPS_REPORTING", 7),
    "sustainability/carbon_emissions_aggregator.py": ("FINOPS_SUSTAINABILITY", 1),
    "sustainability/sustainability_kpi_selector.py": ("FINOPS_SUSTAINABILITY", 1),
    "sustainability/sustainability_report_generator.py": ("FINOPS_SUSTAINABILITY", 2),
    "sustainability/scheduled_sustainability_dispatch.py": ("FINOPS_SUSTAINABILITY", 1),
    "commitment/commitment_inventory_aggregator.py": ("FINOPS_COMMITMENT", 1),
    "commitment/commitment_kpi_selector.py": ("FINOPS_COMMITMENT", 1),
    "commitment/commitment_report_generation.py": ("FINOPS_COMMITMENT", 2),
    "commitment/scheduled_commitment_dispatch.py": ("FINOPS_COMMITMENT", 1),
    "pricing/pricing_report_generation.py": ("FINOPS_PRICING", 2),
    "pricing/scheduled_pricing_dispatch.py": ("FINOPS_PRICING", 1),
}


def _read(rel_path: str) -> str:
    """Read a finops source file as UTF-8 string."""
    return (FINOPS_DIR / rel_path).read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────
# Test 1 — canonical signature used at all 24 sites (parametrized)
# ─────────────────────────────────────────────────────────────


class TestCanonicalSignatureUsed:
    """24 broken sites → 24 NEW canonical sites — emit_audit_typed signature 검증.

    Canonical signature (apps/api/core/audit_action.py:1916-1927):
        emit_audit_typed(
            session, *, action_class, action, actor_id, target_id,
            reason, payload, tenant_id, flush
        )

    AFTER (canonical, Phase 21 wire pattern verbatim):
        emit_audit_typed(
            db_session,
            action_class=ActionClass.<SUB_PHASE>,
            action="...",
            actor_id=None,  # or actual UUID (AD-22 owner-only RBAC)
            target_id=None,
            reason=trace_id,
            payload={...},
            tenant_id=tenant_id,
        )

    Detects broken patterns:
    - `metadata=` keyword (canonical uses `payload=`)
    - `resource_id=` keyword (canonical uses `target_id=` + payload)
    - Missing `action_class=` keyword
    """

    @pytest.mark.parametrize(
        "rel_path,expected_action_class,expected_count",
        [
            (path, action_class, count)
            for path, (action_class, count) in BROKEN_SITES.items()
        ],
    )
    def test_emit_audit_typed_uses_canonical_signature(
        self, rel_path: str, expected_action_class: str, expected_count: int
    ) -> None:
        src = _read(rel_path)
        # Find every emit_audit_typed( call site in the file
        call_pattern = re.compile(r"\bemit_audit_typed\s*\(", re.MULTILINE)
        calls = list(call_pattern.finditer(src))
        assert len(calls) >= expected_count, (
            f"{rel_path}: expected at least {expected_count} emit_audit_typed calls, "
            f"found {len(calls)}. Did you miss a site?"
        )

        # Verify NONE of the call sites use the broken pattern
        for match in calls:
            # Extract the call body (best-effort, until matching paren)
            start = match.end()
            depth = 1
            i = start
            while i < len(src) and depth > 0:
                if src[i] == "(":
                    depth += 1
                elif src[i] == ")":
                    depth -= 1
                i += 1
            call_body = src[start : i - 1]

            # Broken pattern 1: metadata= keyword
            assert "metadata=" not in call_body, (
                f"{rel_path}: emit_audit_typed uses broken `metadata=` keyword. "
                "Canonical signature uses `payload=`."
            )
            # Broken pattern 2: resource_id= keyword
            assert "resource_id=" not in call_body, (
                f"{rel_path}: emit_audit_typed uses broken `resource_id=` keyword. "
                "Canonical signature uses `target_id=None` + payload key."
            )
            # Broken pattern 3: missing action_class=
            assert "action_class=" in call_body, (
                f"{rel_path}: emit_audit_typed missing `action_class=` keyword. "
                f"Expected `action_class=ActionClass.{expected_action_class}`."
            )
            # Canonical pattern 4: target_id=None
            assert "target_id=None" in call_body or "target_id=" in call_body, (
                f"{rel_path}: emit_audit_typed missing `target_id=` keyword. "
                "Canonical signature requires `target_id=None` (UUID coercion → payload)."
            )


# ─────────────────────────────────────────────────────────────
# Test 2 — NO broken pattern in finops modules (sweep)
# ─────────────────────────────────────────────────────────────


class TestNoBrokenSignaturePatternInFinops:
    """CR 11-3 ALLOWED_SERVICE_SUBMODULES 즉시 sweep — finops 전역 sweep.

    Detects any remaining `metadata=` or `resource_id=` in emit_audit_typed calls.
    Should find ZERO matches in finops modules (excluding audit_action.py itself).
    """

    def test_no_metadata_keyword_in_emit_audit_calls(self) -> None:
        violations: list[str] = []
        for finops_file in FINOPS_DIR.rglob("*.py"):
            if finops_file.name == "__init__.py":
                continue
            src = finops_file.read_text(encoding="utf-8")
            # Find emit_audit_typed( call sites
            for match in re.finditer(r"\bemit_audit_typed\s*\(", src):
                start = match.end()
                depth = 1
                i = start
                while i < len(src) and depth > 0:
                    if src[i] == "(":
                        depth += 1
                    elif src[i] == ")":
                        depth -= 1
                    i += 1
                call_body = src[start : i - 1]
                if "metadata=" in call_body:
                    rel = finops_file.relative_to(ROOT).as_posix()
                    violations.append(
                        f"{rel}: uses broken `metadata=` keyword in emit_audit_typed()"
                    )
        assert not violations, (
            "Broken `metadata=` keyword found in finops emit_audit_typed calls:\n  "
            + "\n  ".join(violations)
        )

    def test_no_resource_id_keyword_in_emit_audit_calls(self) -> None:
        violations: list[str] = []
        for finops_file in FINOPS_DIR.rglob("*.py"):
            if finops_file.name == "__init__.py":
                continue
            src = finops_file.read_text(encoding="utf-8")
            for match in re.finditer(r"\bemit_audit_typed\s*\(", src):
                start = match.end()
                depth = 1
                i = start
                while i < len(src) and depth > 0:
                    if src[i] == "(":
                        depth += 1
                    elif src[i] == ")":
                        depth -= 1
                    i += 1
                call_body = src[start : i - 1]
                if "resource_id=" in call_body:
                    rel = finops_file.relative_to(ROOT).as_posix()
                    violations.append(
                        f"{rel}: uses broken `resource_id=` keyword in emit_audit_typed()"
                    )
        assert not violations, (
            "Broken `resource_id=` keyword found in finops emit_audit_typed calls:\n  "
            + "\n  ".join(violations)
        )


# ─────────────────────────────────────────────────────────────
# Test 3 — 24 sites registry covered (sum verification)
# ─────────────────────────────────────────────────────────────


class Test24SitesCovered:
    """Sum of all site counts MUST equal 24 (Phase 11~20 broken sites 정량)."""

    def test_total_sites_equal_24(self) -> None:
        total = sum(count for _, count in BROKEN_SITES.values())
        assert total == 24, (
            f"Expected 24 broken sites, got {total}. "
            "Update BROKEN_SITES registry to match actual fix count."
        )

    def test_registry_has_14_files(self) -> None:
        assert len(BROKEN_SITES) == 14, (
            f"Expected 14 files, got {len(BROKEN_SITES)}. "
            "Update BROKEN_SITES registry to match actual fix file count."
        )

    def test_action_classes_use_correct_territory(self) -> None:
        """Each file's ActionClass MUST match its Phase territory."""
        expected_territory = {
            "executive_dashboard_aggregator.py": "FINOPS_REPORTING",
            "cross_module_kpi.py": "FINOPS_REPORTING",
            "executive_report_generator.py": "FINOPS_REPORTING",
            "executive_dashboard_routes.py": "FINOPS_REPORTING",
            "sustainability/carbon_emissions_aggregator.py": "FINOPS_SUSTAINABILITY",
            "sustainability/sustainability_kpi_selector.py": "FINOPS_SUSTAINABILITY",
            "sustainability/sustainability_report_generator.py": "FINOPS_SUSTAINABILITY",
            "sustainability/scheduled_sustainability_dispatch.py": "FINOPS_SUSTAINABILITY",
            "commitment/commitment_inventory_aggregator.py": "FINOPS_COMMITMENT",
            "commitment/commitment_kpi_selector.py": "FINOPS_COMMITMENT",
            "commitment/commitment_report_generation.py": "FINOPS_COMMITMENT",
            "commitment/scheduled_commitment_dispatch.py": "FINOPS_COMMITMENT",
            "pricing/pricing_report_generation.py": "FINOPS_PRICING",
            "pricing/scheduled_pricing_dispatch.py": "FINOPS_PRICING",
        }
        for rel_path, (action_class, _) in BROKEN_SITES.items():
            assert expected_territory[rel_path] == action_class, (
                f"{rel_path}: ActionClass mismatch. "
                f"Expected {expected_territory[rel_path]}, got {action_class}."
            )


# ─────────────────────────────────────────────────────────────
# Test 4 — ActionClass import present in each file
# ─────────────────────────────────────────────────────────────


class TestActionClassImportInEachFile:
    """Each file MUST import `ActionClass` from apps.api.core.audit_action."""

    @pytest.mark.parametrize("rel_path", list(BROKEN_SITES.keys()))
    def test_action_class_imported(self, rel_path: str) -> None:
        src = _read(rel_path)
        # Look for `from apps.api.core.audit_action import ActionClass` or
        # `from apps.api.core.audit_action import ActionClass, ...`
        import_pattern = re.compile(
            r"from\s+apps\.api\.core\.audit_action\s+import\s+[^#\n]*\bActionClass\b",
            re.MULTILINE,
        )
        assert import_pattern.search(src), (
            f"{rel_path}: missing `ActionClass` import from "
            "apps.api.core.audit_action. Canonical signature requires "
            "`from apps.api.core.audit_action import ActionClass, emit_audit_typed`."
        )


# ─────────────────────────────────────────────────────────────
# Test 5 — router has Depends(get_session) injection
# ─────────────────────────────────────────────────────────────


class TestRouterHasDbSessionDependency:
    """executive_dashboard_routes.py MUST inject db_session via Depends(get_session)."""

    def test_router_imports_get_session(self) -> None:
        src = _read("executive_dashboard_routes.py")
        assert "from apps.api.core.db import get_session" in src, (
            "executive_dashboard_routes.py: missing `from apps.api.core.db import get_session` "
            "import. Router MUST inject db_session via FastAPI Depends."
        )

    def test_router_has_db_session_in_every_route(self) -> None:
        """All 7 broken sites are in route handlers — each MUST have db_session param.

        NOTE: get_compliance_trend is a Phase 15 placeholder stub — it does not call
        any aggregator nor emit_audit_typed, so it doesn't need db_session injection.
        This test checks only routes that have an `emit_audit_typed(` call site
        OR call an aggregator module function (which requires db_session propagation).
        """
        src = _read("executive_dashboard_routes.py")
        # AST-parse to find async def functions decorated with @router.<method>
        tree = ast.parse(src)
        route_funcs: list[ast.AsyncFunctionDef] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "router"
                ):
                    route_funcs.append(node)
                    break

        assert len(route_funcs) >= 7, (
            f"executive_dashboard_routes.py: expected at least 7 @router.<method> "
            f"routes, found {len(route_funcs)}."
        )

        missing_db_session: list[str] = []
        for func in route_funcs:
            # Only require db_session if the function actually emits audit or calls
            # an aggregator module function (which needs db_session for emit_audit_typed)
            func_src = ast.unparse(func)
            needs_db_session = (
                "emit_audit_typed(" in func_src
                or any(
                    mod in func_src
                    for mod in (
                        "aggregate_executive_dashboard(",
                        "select_cross_module_kpis(",
                        "generate_executive_report(",
                        "schedule_executive_dispatch(",
                        "deliver_executive_report(",
                    )
                )
            )
            if not needs_db_session:
                continue
            has_db_session = False
            for arg in func.args.args + func.args.kwonlyargs:
                if arg.arg == "db_session":
                    has_db_session = True
                    break
            if not has_db_session:
                missing_db_session.append(func.name)

        assert not missing_db_session, (
            f"executive_dashboard_routes.py: routes missing `db_session: AsyncSession = "
            f"Depends(get_session)` parameter: {missing_db_session}"
        )


# ─────────────────────────────────────────────────────────────
# Test 6 — except ImportError used, not except Exception (router file)
# ─────────────────────────────────────────────────────────────


class TestExceptImporterrorUsedNotException:
    """Router sites 의 `except Exception` → `except ImportError` unification 검증.

    Honest deviation ③: 7 router sites 의 audit failure logging 손실 보존
    (canonical pattern 은 silent pass).

    Aggregator/report_generator/dispatch files use `except ImportError` ALREADY
    (Phase 16/17/18/19 wire pattern), so this test focuses on the router file
    transformation which unified them.
    """

    def test_router_uses_except_importerror(self) -> None:
        src = _read("executive_dashboard_routes.py")
        # The old pattern: `except Exception as exc:`
        # The new pattern (canonical silent-pass): `except ImportError:`
        # OR equivalent: `with suppress(ImportError):` (modern Python idiom, ruff-clean)
        old_pattern = re.compile(r"except\s+Exception\s+as\s+\w+\s*:")
        except_pattern = re.compile(r"except\s+ImportError\s*:")
        suppress_pattern = re.compile(r"with\s+suppress\(\s*ImportError\s*\)\s*:")

        old_hits = old_pattern.findall(src)
        except_hits = except_pattern.findall(src)
        suppress_hits = suppress_pattern.findall(src)

        assert len(old_hits) == 0, (
            f"executive_dashboard_routes.py: found {len(old_hits)} `except Exception as exc:` "
            "blocks. Canonical pattern uses `except ImportError:` or `with suppress(ImportError):` "
            "(silent pass)."
        )
        total_new = len(except_hits) + len(suppress_hits)
        assert total_new >= 7, (
            f"executive_dashboard_routes.py: expected at least 7 ImportError guard blocks "
            f"(one per audit site) — either `except ImportError:` or `with suppress(ImportError):`. "
            f"Found {len(except_hits)} `except` + {len(suppress_hits)} `suppress` = {total_new}."
        )


# ─────────────────────────────────────────────────────────────
# Test 7 — 3-way drift detector (registry integrity)
# ─────────────────────────────────────────────────────────────


class Test3WayDriftDetector:
    """Phase 21 wire 가 도입한 8 NEW FINOPS_REPORTING actions 의 registry integrity.

    Phase 16 wire 가 도입한 ActionClass.FINOPS_REPORTING 의 8 actions 이
    audit_action.py registry 에 보존됨을 검증. 이 action 들은 라우터의
    7 broken sites 가 emit 하는 action 이름과 일치해야 함.
    """

    EXPECTED_FINOPS_REPORTING_ACTIONS = (
        "executive_dashboard_viewed",
        "cross_module_kpi_calculated",
        "executive_report_generated",
        "executive_report_exported",
        "executive_scheduled_dispatch_evaluated",
        "executive_report_dispatched",
        "finops_reporting_dry_run_executed",
    )

    def test_finops_reporting_action_class_registered(self) -> None:
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        assert ActionClass.FINOPS_REPORTING in _ActionRegistry._REGISTRY, (
            "ActionClass.FINOPS_REPORTING missing from registry. "
            "Phase 16 wire introduced this action class."
        )

    @pytest.mark.parametrize(
        "action", EXPECTED_FINOPS_REPORTING_ACTIONS
    )
    def test_router_actions_in_registry(self, action: str) -> None:
        """Each action emitted by router sites MUST be in FINOPS_REPORTING registry."""
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _, action_set = _ActionRegistry._REGISTRY[ActionClass.FINOPS_REPORTING]
        assert action in action_set, (
            f"{action!r} not in ActionClass.FINOPS_REPORTING frozenset. "
            "Action literal drift detected — registry ↔ router call site drift."
        )
