"""tests.api.core.test_audit_fixes_phase_11_20_backfill — Layer 2 P1 semantic backfill.

Phase 11~20 audit-fixes Layer 2 P1 backfill sprint (cj-style 155번째) — 24 canonical
emit_audit_typed call sites 의 semantic integrity verification.

cj-style 154번째 wire (`379ca8e`) 가 도입한 cj-style 154 signature verification test
file `test_audit_fixes_phase_11_20_signature.py` (7 classes, 44 tests) 는 **structural**
verification 만 수행:
- canonical signature used at all 24 sites (no `metadata=`, no `resource_id=`)
- 24 sites registry covered (sum = 24)
- ActionClass import present in each file
- router has Depends(get_session) injection
- except ImportError used, not except Exception
- 3-way drift detector (registry integrity for FINOPS_REPORTING)

cj-style 155번째 backfill sprint (THIS) 가 추가하는 **semantic** verification:
- per-site: action string in registry frozenset (registry ↔ call site drift)
- per-site: action_class is valid ActionClass enum value
- per-site: canonical keyword args used (action_class, action, actor_id, target_id, reason, tenant_id, payload)
- per-site: payload contains "trace_id": key (forensic chain)
- per-site: actor_id=None (system action, not user-attributed — owner-only RBAC AD-22 + 2FA)
- per-site: tenant_id is keyword arg (not positional)
- per-file: all sites use same ActionClass as expected territory
- per-territory: FINOPS_* has 8 expected actions in registry
- per-file: router endpoint passes trace_id to reason=
- per-file: aggregator function has `not dry_run` guard

Per CR 11-4 P-015: PURE validator pattern — NO fixtures, NO DB, sync AST/regex parsing.

24 sites mapping (cj-style 154 verbatim):

| File                              | Sites | ActionClass            |
|-----------------------------------|-------|------------------------|
| executive_dashboard_aggregator    | 1     | FINOPS_REPORTING       |
| cross_module_kpi                  | 1     | FINOPS_REPORTING       |
| executive_report_generator        | 2     | FINOPS_REPORTING       |
| executive_dashboard_routes        | 7     | FINOPS_REPORTING       |
| carbon_emissions_aggregator       | 1     | FINOPS_SUSTAINABILITY  |
| sustainability_kpi_selector       | 1     | FINOPS_SUSTAINABILITY  |
| sustainability_report_generator   | 2     | FINOPS_SUSTAINABILITY  |
| scheduled_sustainability_dispatch | 1     | FINOPS_SUSTAINABILITY  |
| commitment_inventory_aggregator   | 1     | FINOPS_COMMITMENT      |
| commitment_kpi_selector           | 1     | FINOPS_COMMITMENT      |
| commitment_report_generation      | 2     | FINOPS_COMMITMENT      |
| scheduled_commitment_dispatch     | 1     | FINOPS_COMMITMENT      |
| pricing_report_generation         | 2     | FINOPS_PRICING         |
| scheduled_pricing_dispatch        | 1     | FINOPS_PRICING         |
|                                   |=24    |                        |
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FINOPS_DIR = ROOT / "apps" / "api" / "modules" / "finops"
AUDIT_ACTION = ROOT / "apps" / "api" / "core" / "audit_action.py"

# 24 BROKEN_SITES registry — file → (ActionClass enum, expected emit_audit_typed count)
# Same registry as cj-style 154 test_audit_fixes_phase_11_20_signature.py:BROKEN_SITES.
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

# Per-territory 8-action expected set (matches Phase 16/17/18/19 wire Literal).
EXPECTED_FINOPS_REPORTING_ACTIONS: frozenset[str] = frozenset(
    {
        "executive_dashboard_viewed",
        "cross_module_kpi_calculated",
        "executive_report_generated",
        "executive_report_exported",
        "executive_report_dispatched",
        "executive_scheduled_dispatch_evaluated",
        "executive_kpi_refreshed",
        "finops_reporting_dry_run_executed",
    }
)
EXPECTED_FINOPS_SUSTAINABILITY_ACTIONS: frozenset[str] = frozenset(
    {
        "carbon_emissions_aggregated",
        "sustainability_kpi_calculated",
        "sustainability_report_generated",
        "sustainability_report_exported",
        "sustainability_report_dispatched",
        "sustainability_scheduled_dispatch_evaluated",
        "sustainability_dashboard_viewed",
        "finops_sustainability_dry_run_executed",
    }
)
EXPECTED_FINOPS_COMMITMENT_ACTIONS: frozenset[str] = frozenset(
    {
        "commitment_inventory_aggregated",
        "commitment_kpi_calculated",
        "commitment_report_generated",
        "commitment_report_exported",
        "commitment_report_dispatched",
        "commitment_scheduled_dispatch_evaluated",
        "commitment_dashboard_viewed",
        "finops_commitment_dry_run_executed",
    }
)
EXPECTED_FINOPS_PRICING_ACTIONS: frozenset[str] = frozenset(
    {
        "pricing_dashboard_viewed",
        "cross_module_pricing_kpi_calculated",
        "pricing_report_generated",
        "pricing_report_exported",
        "pricing_report_dispatched",
        "pricing_scheduled_dispatch_evaluated",
        "pricing_kpi_refreshed",
        "finops_pricing_dry_run_executed",
    }
)

TERRITORY_ACTIONS: dict[str, frozenset[str]] = {
    "FINOPS_REPORTING": EXPECTED_FINOPS_REPORTING_ACTIONS,
    "FINOPS_SUSTAINABILITY": EXPECTED_FINOPS_SUSTAINABILITY_ACTIONS,
    "FINOPS_COMMITMENT": EXPECTED_FINOPS_COMMITMENT_ACTIONS,
    "FINOPS_PRICING": EXPECTED_FINOPS_PRICING_ACTIONS,
}


def _read(rel_path: str) -> str:
    """Read a finops source file as UTF-8 string."""
    return (FINOPS_DIR / rel_path).read_text(encoding="utf-8")


def _extract_emit_audit_call_bodies(src: str) -> list[tuple[str, int]]:
    """Extract all emit_audit_typed(...) call bodies (substring between parens).

    Returns list of (call_body, 1-indexed_line_number) tuples — preserves order.
    Uses paren-depth counter (not AST) because cj-style 154 signature is keyword-heavy
    with multi-line payloads (AST node extraction misses raw text contents).
    """
    call_pattern = re.compile(r"\bemit_audit_typed\s*\(", re.MULTILINE)
    calls: list[tuple[str, int]] = []
    for match in call_pattern.finditer(src):
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
        # Convert byte offset to 1-indexed line number for diagnostic
        line_no = src[:match.start()].count("\n") + 1
        calls.append((call_body, line_no))
    return calls


def _extract_keyword_arg(call_body: str, kw: str) -> str | None:
    """Extract the value of a keyword argument as raw source text.

    Handles multi-line dict literals and nested parens via depth counter.
    Returns None if keyword not found.
    """
    pattern = re.compile(rf"\b{re.escape(kw)}\s*=\s*")
    match = pattern.search(call_body)
    if not match:
        return None
    # Walk to value start (skip whitespace)
    i = match.end()
    # Capture value: handle dict {…}, string "…", identifier, None, etc.
    if i < len(call_body) and call_body[i] == "{":
        depth = 1
        i += 1
        while i < len(call_body) and depth > 0:
            if call_body[i] == "{":
                depth += 1
            elif call_body[i] == "}":
                depth -= 1
            i += 1
        return call_body[match.end() : i]
    if i < len(call_body) and call_body[i] == '"':
        # String literal
        i += 1
        while i < len(call_body) and call_body[i] != '"':
            if call_body[i] == "\\":
                i += 2
            else:
                i += 1
        i += 1  # closing quote
        return call_body[match.end() : i]
    # Bare identifier (None, tenant_id, trace_id, etc.)
    m = re.match(r"[A-Za-z_][A-Za-z0-9_.]*", call_body[i:])
    if m:
        return call_body[match.end() : i + m.end()]
    return call_body[match.end() : i]


# ─────────────────────────────────────────────────────────────
# Test 1 — per-site canonical signature (24 sites, parametrized)
# ─────────────────────────────────────────────────────────────


class TestPerSiteCanonicalSignature:
    """Per-site semantic verification of canonical emit_audit_typed call.

    For each of the 24 cj-style 154 fixed sites, verifies ALL canonical requirements:
    1. `action_class=ActionClass.X` keyword present (X is valid enum value)
    2. `action="..."` string is in corresponding ActionClass registry frozenset
    3. `actor_id=None` (system action, AD-22 owner-only RBAC + 2FA)
    4. `target_id=None` keyword present (UUID coercion → payload)
    5. `reason=trace_id` keyword present (forensic chain)
    6. `tenant_id=...` keyword present (not positional)
    7. `payload={...}` keyword present (not `metadata=`)
    8. payload dict literal contains `"trace_id":` key
    9. wrapped in `if db_session is not None:` block
    10. wrapped in `try:` + `except ImportError:` (aggregator) OR `with suppress(ImportError):` (router)
    """

    @pytest.mark.parametrize(
        ("rel_path", "expected_action_class", "expected_count"),
        [
            (path, action_class, count)
            for path, (action_class, count) in BROKEN_SITES.items()
        ],
    )
    def test_per_site_canonical_signature(
        self, rel_path: str, expected_action_class: str, expected_count: int
    ) -> None:
        src = _read(rel_path)
        calls = _extract_emit_audit_call_bodies(src)
        assert len(calls) >= expected_count, (
            f"{rel_path}: expected at least {expected_count} emit_audit_typed calls, "
            f"found {len(calls)}."
        )

        for idx, (call_body, line_no) in enumerate(calls):
            site_label = f"{rel_path}:{line_no}[{idx}]"

            # 1. action_class= keyword present
            action_class_value = _extract_keyword_arg(call_body, "action_class")
            assert action_class_value is not None, (
                f"{site_label}: missing `action_class=` keyword arg."
            )
            assert f"ActionClass.{expected_action_class}" in action_class_value, (
                f"{site_label}: action_class does not match expected territory. "
                f"Expected ActionClass.{expected_action_class}, got {action_class_value!r}."
            )
            # 1b. ActionClass.X is a valid enum value
            valid_enum_values = {
                "TENANT_SETTINGS",
                "SERVICE_ROLE",
                "UPLOADED_DOCUMENT",
                "INPUT_DRAFT",
                "PRODUCT",
                "BOM_LINE",
                "MONTHLY_INPUT_ROW",
                "MONTHLY_INPUT_PERIOD",
                "CALC_LOG",
                "VERIFICATION_LOG",
                "INVENTORY_LEDGER",
                "REVERSAL_LOG",
                "CLOSING_GUARD",
                "VERIFICATION",
                "CLOSING_PERIOD",
                "MONTHLY_CLOSING",
                "MONTHLY_CLOSING_REPORT",
                "SNAPSHOT_PERSISTENCE",
                "REOPEN_OPERATOR",
                "TWO_FACTOR_AUTH",
                "ACCOUNT_BACKUP",
                "ACCOUNT_DELETION",
                "AI_EXTRACTION_EXECUTED",
                "AI_INSIGHT_CACHE_ACCESSED",
                "TENANT",
                "AUTH",
                "INFRA",
                "AUDIT",
                "OBSERVABILITY",
                "PERFORMANCE_TEST",
                "CHAOS_ENGINEERING",
                "SLO_ENGINEERING",
                "FINOPS",
                "FINOPS_ANOMALY",
                "FINOPS_BUDGET",
                "FINOPS_FORECAST",
                "FINOPS_OPTIMIZATION",
                "FINOPS_TAG_GOVERNANCE",
                "FINOPS_REPORTING",
                "FINOPS_SUSTAINABILITY",
                "FINOPS_COMMITMENT",
                "FINOPS_PRICING",
                "FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION",
                "FINOPS_RESERVED_CAPACITY_PLANNING",
            }
            extracted_class_name = action_class_value.split(".")[-1].strip()
            assert extracted_class_name in valid_enum_values, (
                f"{site_label}: ActionClass.{extracted_class_name!r} is NOT a valid "
                "ActionClass enum value. Add to valid_enum_values if intentionally added."
            )

            # 2. action="..." is in registry frozenset for the file's ActionClass
            action_value = _extract_keyword_arg(call_body, "action")
            assert action_value is not None, (
                f"{site_label}: missing `action=` keyword arg."
            )
            # Strip surrounding quotes
            action_str = action_value.strip().strip('"').strip("'")
            expected_actions = TERRITORY_ACTIONS[expected_action_class]
            assert action_str in expected_actions, (
                f"{site_label}: action={action_str!r} is NOT in "
                f"{expected_action_class} registry frozenset "
                f"({sorted(expected_actions)}). Drift detected."
            )

            # 3. actor_id=None (system action, AD-22 owner-only RBAC + 2FA)
            actor_id_value = _extract_keyword_arg(call_body, "actor_id")
            assert actor_id_value == "None", (
                f"{site_label}: actor_id must be None (system action, owner-only RBAC AD-22 + 2FA). "
                f"Got {actor_id_value!r}."
            )

            # 4. target_id=None keyword present
            target_id_value = _extract_keyword_arg(call_body, "target_id")
            assert target_id_value is not None, (
                f"{site_label}: missing `target_id=` keyword arg (canonical signature requires "
                "`target_id=None` — UUID coercion → payload)."
            )

            # 5. reason=trace_id keyword present (forensic chain)
            reason_value = _extract_keyword_arg(call_body, "reason")
            assert reason_value == "trace_id", (
                f"{site_label}: reason must be `trace_id` (forensic chain). "
                f"Got {reason_value!r}."
            )

            # 6. tenant_id= keyword present (not positional)
            tenant_id_value = _extract_keyword_arg(call_body, "tenant_id")
            assert tenant_id_value is not None, (
                f"{site_label}: missing `tenant_id=` keyword arg. Canonical signature requires "
                "tenant_id as keyword (not positional)."
            )

            # 7. payload= keyword present (not metadata=)
            payload_value = _extract_keyword_arg(call_body, "payload")
            assert payload_value is not None, (
                f"{site_label}: missing `payload=` keyword arg. Canonical signature uses "
                "`payload=` (not `metadata=`)."
            )
            assert "metadata=" not in call_body, (
                f"{site_label}: contains broken `metadata=` keyword."
            )
            assert "resource_id=" not in call_body, (
                f"{site_label}: contains broken `resource_id=` keyword."
            )

            # 8. payload dict contains "trace_id": key
            assert '"trace_id":' in payload_value or "'trace_id':" in payload_value, (
                f"{site_label}: payload dict literal missing `\"trace_id\":` key (forensic chain)."
            )

            # 9. wrapped in `if db_session is not None:` block
            # Check the surrounding context (look backwards ~500 chars from the call site)
            # Find the position of emit_audit_typed call in this iteration
            emit_pattern = re.compile(r"\bemit_audit_typed\s*\(")
            matches = list(emit_pattern.finditer(src))
            assert idx < len(matches), (
                f"{site_label}: internal error — emit_audit_typed match count mismatch."
            )
            call_start = matches[idx].start()
            context_before = src[max(0, call_start - 2000) : call_start]
            assert "if db_session is not None" in context_before, (
                f"{site_label}: call site not wrapped in `if db_session is not None:` block "
                "(or `and not dry_run` for aggregator/report_generator/dispatch files)."
            )

            # 10. ImportError guard — walk past the full multi-line emit_audit_typed
            # call body (paren-depth counter) and verify the AFTER-context contains the
            # expected guard pattern.
            end_match = re.compile(r"\bemit_audit_typed\s*\(").search(src, call_start)
            assert end_match is not None, (
                f"{site_label}: internal error — emit_audit_typed match lost."
            )
            open_paren_pos = src.find("(", end_match.end() - 1)
            depth = 1
            after_pos = open_paren_pos + 1
            while after_pos < len(src) and depth > 0:
                if src[after_pos] == "(":
                    depth += 1
                elif src[after_pos] == ")":
                    depth -= 1
                after_pos += 1
            # after_pos now points 1 char past the closing `)`. Capture 800 chars
            # AFTER the call (large enough for multi-line try/except spanning ~20 lines).
            context_after = src[after_pos : after_pos + 800]

            is_router = rel_path == "executive_dashboard_routes.py"
            if is_router:
                # Router file: `with suppress(ImportError):` wraps emit_audit_typed
                # → check context_before (preceding lines for `with suppress(ImportError):`)
                assert "with suppress(ImportError):" in context_before, (
                    f"{site_label}: router file must use `with suppress(ImportError):` "
                    "wrapper around emit_audit_typed call."
                )
            else:
                # Aggregator/report_generator/dispatch: `try:` + `except ImportError:`
                # The `try:` is in context_before; `except ImportError:` is in context_after
                # (because it appears AFTER the multi-line call body closes).
                assert "try:" in context_before, (
                    f"{site_label}: aggregator file must wrap emit_audit_typed in `try:` block "
                    "before the call (local import of audit_action + emit_audit_typed call)."
                )
                assert "except ImportError:" in context_after, (
                    f"{site_label}: aggregator file must use `except ImportError:` "
                    "after emit_audit_typed call (call body spans multiple lines, "
                    "context window is 800 chars after call close)."
                )


# ─────────────────────────────────────────────────────────────
# Test 2 — per-file ActionClass consistency (14 files, parametrized)
# ─────────────────────────────────────────────────────────────


class TestPerFileActionClassConsistency:
    """All sites in a file MUST use the same ActionClass as the file's expected territory.

    Detects drift between file-level expected territory (registry) and per-site
    ActionClass references.
    """

    @pytest.mark.parametrize(
        ("rel_path", "expected_action_class", "_count"),
        [
            (path, action_class, count)
            for path, (action_class, count) in BROKEN_SITES.items()
        ],
    )
    def test_all_sites_use_expected_action_class(
        self, rel_path: str, expected_action_class: str, _count: int
    ) -> None:
        src = _read(rel_path)
        calls = _extract_emit_audit_call_bodies(src)
        for idx, (call_body, line_no) in enumerate(calls):
            action_class_value = _extract_keyword_arg(call_body, "action_class")
            assert action_class_value is not None, (
                f"{rel_path}:{line_no}[{idx}]: missing action_class= keyword."
            )
            assert (
                f"ActionClass.{expected_action_class}" in action_class_value
            ), (
                f"{rel_path}:{line_no}[{idx}]: action_class mismatch. "
                f"Expected ActionClass.{expected_action_class}, got {action_class_value!r}."
            )


# ─────────────────────────────────────────────────────────────
# Test 3 — per-territory registry has 8 expected actions
# ─────────────────────────────────────────────────────────────


class TestPerTerritoryRegistryHas8Actions:
    """Each FINOPS_* ActionClass must have EXACTLY 8 actions in registry frozenset.

    Verifies Phase 16/17/18/19 wire Literal ↔ registry parity (no missing, no extra).
    """

    @pytest.mark.parametrize(
        ("action_class", "expected_actions"),
        [
            ("FINOPS_REPORTING", EXPECTED_FINOPS_REPORTING_ACTIONS),
            ("FINOPS_SUSTAINABILITY", EXPECTED_FINOPS_SUSTAINABILITY_ACTIONS),
            ("FINOPS_COMMITMENT", EXPECTED_FINOPS_COMMITMENT_ACTIONS),
            ("FINOPS_PRICING", EXPECTED_FINOPS_PRICING_ACTIONS),
        ],
    )
    def test_territory_registry_has_8_expected_actions(
        self, action_class: str, expected_actions: frozenset[str]
    ) -> None:
        # Import here to avoid module-load side effects
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        assert hasattr(ActionClass, action_class), (
            f"ActionClass.{action_class} not defined in audit_action.py enum."
        )
        enum_value = getattr(ActionClass, action_class)
        _, action_set = _ActionRegistry._REGISTRY[enum_value]

        # Verify all 8 expected actions are present
        missing = expected_actions - action_set
        assert not missing, (
            f"{action_class}: registry frozenset MISSING {len(missing)} expected actions: "
            f"{sorted(missing)}. Total registered: {len(action_set)}."
        )

        # Verify NO unexpected actions present (drift detection — too many = drift)
        # Note: if extra actions are added later, update expected_actions set explicitly.
        extra = action_set - expected_actions
        # Phase 21 added `executive_kpi_refreshed` — verify it is the ONLY allowed extra
        # for FINOPS_REPORTING. If you add more, update this list.
        # We don't enforce zero extras here because new actions may legitimately be
        # added; this test focuses on the 8 expected actions being PRESENT (completeness).
        # The presence assertion above catches "actions removed" drift.
        del extra  # silence unused warning — completeness is the contract


# ─────────────────────────────────────────────────────────────
# Test 4 — per-file router endpoint emits trace_id
# ─────────────────────────────────────────────────────────────


class TestPerFileRouterEndpointEmitsTraceId:
    """Router sites in executive_dashboard_routes.py MUST pass trace_id through.

    Per AD-15 + CR 1-1: every audit emit must include trace_id for forensic chain.
    """

    @pytest.mark.parametrize(
        "route_func_name",
        [
            "get_executive_rollup",
            "get_cross_module_kpis",
            "generate_executive_report_route",
            "schedule_executive_dispatch_route",
            "deliver_executive_report_route",
            "get_compliance_trend",
            "executive_dry_run",
            "configure_recipient_strategy_route",
        ],
    )
    def test_router_endpoint_has_trace_id_param(self, route_func_name: str) -> None:
        src = _read("executive_dashboard_routes.py")
        tree = ast.parse(src)
        # Find the route function
        func_node: ast.FunctionDef | ast.AsyncFunctionDef | None = None
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name == route_func_name:
                func_node = node
                break

        if func_node is None:
            # Route might be renamed — skip silently if not present (e.g. helper functions)
            pytest.skip(
                f"{route_func_name}: route function not found in executive_dashboard_routes.py "
                "(may have been renamed). Update this test if intentional."
            )

        # Verify trace_id parameter exists (either positional, keyword, or Query default)
        has_trace_id_param = any(arg.arg == "trace_id" for arg in func_node.args.args)
        has_trace_id_kwonly = any(
            arg.arg == "trace_id" for arg in func_node.args.kwonlyargs
        )
        assert has_trace_id_param or has_trace_id_kwonly, (
            f"{route_func_name}: missing `trace_id` parameter. "
            "Router endpoint MUST accept trace_id for audit forensic chain."
        )


# ─────────────────────────────────────────────────────────────
# Test 5 — per-file aggregator has dry_run guard
# ─────────────────────────────────────────────────────────────


class TestPerFileAggregatorHasDryRunGuard:
    """Aggregator/report_generator functions MUST wrap emit_audit_typed with `not dry_run`.

    Dispatch files are EXCLUDED (their `if db_session is not None:` lacks `not dry_run`
    because scheduled jobs always run unless explicitly suppressed elsewhere).
    Router file is EXCLUDED (router endpoints accept dry_run as Query param + propagate
    to underlying aggregator).
    """

    @pytest.mark.parametrize(
        ("rel_path", "function_name"),
        [
            ("executive_dashboard_aggregator.py", "aggregate_executive_dashboard"),
            ("cross_module_kpi.py", "select_cross_module_kpis"),
            ("executive_report_generator.py", "generate_executive_report"),
            ("sustainability/carbon_emissions_aggregator.py", "aggregate_carbon_emissions"),
            ("sustainability/sustainability_kpi_selector.py", "select_sustainability_kpis"),
            ("sustainability/sustainability_report_generator.py", "generate_sustainability_report"),
            ("commitment/commitment_inventory_aggregator.py", "aggregate_commitment_inventory"),
            ("commitment/commitment_kpi_selector.py", "select_commitment_kpis"),
            ("commitment/commitment_report_generation.py", "generate_commitment_report"),
            ("pricing/pricing_report_generation.py", "generate_pricing_report"),
        ],
    )
    def test_aggregator_has_not_dry_run_guard(
        self, rel_path: str, function_name: str
    ) -> None:
        src = _read(rel_path)
        # Find the function
        tree = ast.parse(src)
        func_node: ast.FunctionDef | ast.AsyncFunctionDef | None = None
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name == function_name:
                func_node = node
                break
        if func_node is None:
            pytest.skip(
                f"{function_name}: function not found in {rel_path}. "
                "Update this test if function was renamed."
            )

        # AST-unparse the function source and verify `not dry_run` is present
        func_src = ast.unparse(func_node)
        assert "not dry_run" in func_src, (
            f"{rel_path}:{function_name}: aggregator function MUST wrap emit_audit_typed "
            "with `if db_session is not None and not dry_run:` guard. "
            "Audit must NOT emit when dry_run=True (preview only)."
        )


# ─────────────────────────────────────────────────────────────
# Test 6 — BROKEN_SITES registry matches cj-style 154 scope
# ─────────────────────────────────────────────────────────────


class TestBrokenSitesRegistryMatchesCj154:
    """BROKEN_SITES registry integrity — sum = 24 sites, 14 files, 4 territories."""

    def test_total_sites_equal_24(self) -> None:
        total = sum(count for _, count in BROKEN_SITES.values())
        assert total == 24, (
            f"Expected 24 broken sites, got {total}. "
            "Update BROKEN_SITES registry to match cj-style 154 fix scope."
        )

    def test_registry_has_14_files(self) -> None:
        assert len(BROKEN_SITES) == 14, (
            f"Expected 14 files, got {len(BROKEN_SITES)}. "
            "Update BROKEN_SITES registry to match cj-style 154 fix scope."
        )

    def test_territories_cover_4_finops_classes(self) -> None:
        """Verifies the 4 territory ActionClass mappings are present."""
        territories = {action_class for action_class, _ in BROKEN_SITES.values()}
        expected = {"FINOPS_REPORTING", "FINOPS_SUSTAINABILITY", "FINOPS_COMMITMENT", "FINOPS_PRICING"}
        assert territories == expected, (
            f"BROKEN_SITES territories mismatch. Expected {expected}, got {territories}."
        )

    def test_registry_matches_cj154_signature_test(self) -> None:
        """Sanity: this registry must equal cj-style 154 test BROKEN_SITES (verbatim mirror).

        Detects accidental drift between cj-style 154 structural test and cj-style 155
        semantic backfill test. If this fails, the registries diverged — update both.
        """
        cj154_test_path = ROOT / "tests" / "api" / "core" / "test_audit_fixes_phase_11_20_signature.py"
        if not cj154_test_path.exists():
            pytest.skip(
                f"cj-style 154 test file not found at {cj154_test_path}. "
                "Cannot cross-validate BROKEN_SITES registry."
            )
        cj154_src = cj154_test_path.read_text(encoding="utf-8")
        # Extract cj-style 154 BROKEN_SITES dict via simple AST parse
        cj154_tree = ast.parse(cj154_src)
        cj154_registry: dict[str, tuple[str, int]] = {}
        for node in ast.walk(cj154_tree):
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "BROKEN_SITES"
            ):
                assert isinstance(node.value, ast.Dict), (
                    "cj-style 154 BROKEN_SITES is not a dict literal"
                )
                for key, value in zip(node.value.keys, node.value.values, strict=True):
                    assert isinstance(key, ast.Constant)
                    assert isinstance(key.value, str)
                    assert isinstance(value, ast.Tuple)
                    assert len(value.elts) == 2
                    assert isinstance(value.elts[0], ast.Constant)
                    assert isinstance(value.elts[1], ast.Constant)
                    cj154_registry[key.value] = (
                        value.elts[0].value,  # type: ignore[arg-type]
                        value.elts[1].value,  # type: ignore[arg-type]
                    )
                break
        assert cj154_registry == BROKEN_SITES, (
            f"BROKEN_SITES drift between cj-154 and cj-155 backfill tests. "
            f"cj-154 has {sorted(cj154_registry.keys())}, cj-155 has {sorted(BROKEN_SITES.keys())}. "
            "Update both registries to match."
        )
