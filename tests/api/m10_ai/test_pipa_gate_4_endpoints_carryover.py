"""tests.api.m10_ai.test_pipa_gate_4_endpoints_carryover — D-10-3-DEFER-6 해소 verification.

D-10-3-DEFER-6 (carry-over from Story 10.3 follow-up sprint):
"all 4 m10_ai endpoints must carry Depends(require_pipa_review) —
the canonical 1st-line PIPA gate before body parse."

Verified endpoints (4 cases):
  1. POST /ai/extract-monthly (10-1) — already PIPA-gated in 10-1 wire
  2. GET  /ai/insights         (10-2) — PIPA gate swept in T4 B4
  3. GET  /ai/comments         (10-3) — PIPA gate swept in T4 B4
  4. POST /ai/promote          (10-4) — PIPA gate NEW wire in T4 B3

Bonus cases:
  5. Sweep completeness: all m10_ai router routes that handle PII-adjacent
     data (drafts, extractions, insights, comments, promote) MUST have
     `Depends(require_pipa_review)` — fail-closed invariant.
  6. Layer ordering: PIPA gate must appear BEFORE capability gate in
     Depends() declaration order (1st defense line).
"""

from __future__ import annotations

import inspect

from fastapi import APIRouter

from apps.api.modules.m10_ai.handlers import router


# ── Helpers ──────────────────────────────────────────────────────


def _find_route(router: APIRouter, path: str):
    """Return the first route matching the path."""
    for r in router.routes:
        if hasattr(r, "path") and r.path == path:
            return r
    return None


def _route_depends_on_pipa(route) -> bool:
    """Inspect route.endpoint (FastAPI wraps dependencies into the endpoint
    callable's signature via `inspect.signature`). True if any Depends arg
    resolves to the `require_pipa_review` callable.
    """
    if not hasattr(route, "endpoint"):
        return False
    sig = inspect.signature(route.endpoint)
    for param in sig.parameters.values():
        if param.default is inspect.Parameter.empty:
            continue
        default = param.default
        # FastAPI Depends() wraps the callable as a `params.Depends` instance
        if hasattr(default, "dependency"):
            if getattr(default.dependency, "__name__", "") == "require_pipa_review":
                return True
    return False


# ── 1-4. Per-endpoint PIPA gate presence (4 cases) ────────────────


def test_pipa_gate_on_10_1_extract_monthly() -> None:
    """POST /ai/extract-monthly (10-1) carries Depends(require_pipa_review)."""
    route = _find_route(router, "/api/v1/ai/extract-monthly")
    assert route is not None, "POST /ai/extract-monthly not found"
    assert _route_depends_on_pipa(route) is True


def test_pipa_gate_on_10_2_insights() -> None:
    """GET /ai/insights (10-2) carries Depends(require_pipa_review)."""
    route = _find_route(router, "/api/v1/ai/insights")
    assert route is not None, "GET /ai/insights not found"
    assert _route_depends_on_pipa(route) is True


def test_pipa_gate_on_10_3_comments() -> None:
    """GET /ai/comments (10-3) carries Depends(require_pipa_review)."""
    route = _find_route(router, "/api/v1/ai/comments")
    assert route is not None, "GET /ai/comments not found"
    assert _route_depends_on_pipa(route) is True


def test_pipa_gate_on_10_4_promote() -> None:
    """POST /ai/promote (10-4 NEW) carries Depends(require_pipa_review)."""
    route = _find_route(router, "/api/v1/ai/promote")
    assert route is not None, "POST /ai/promote not found"
    assert _route_depends_on_pipa(route) is True


# ── 5. Sweep completeness (1 bonus case) ──────────────────────────


def test_pipa_gate_sweep_completeness_all_m10_ai_endpoints() -> None:
    """All m10_ai PII-adjacent endpoints MUST carry Depends(require_pipa_review).

    Sweep list (canonical m10_ai endpoint paths):
      - /api/v1/ai/extract-monthly (10-1 POST)
      - /api/v1/ai/insights         (10-2 GET)
      - /api/v1/ai/comments         (10-3 GET)
      - /api/v1/ai/promote          (10-4 POST)

    Any path added in a future story must be added to this sweep list —
    D-10-3-DEFER-6 explicitly notes the fail-closed invariant.
    """
    pii_paths = [
        "/api/v1/ai/extract-monthly",
        "/api/v1/ai/insights",
        "/api/v1/ai/comments",
        "/api/v1/ai/promote",
    ]
    for path in pii_paths:
        route = _find_route(router, path)
        assert route is not None, f"{path} not registered on m10_ai router"
        assert _route_depends_on_pipa(route) is True, (
            f"{path} is missing Depends(require_pipa_review) — "
            f"D-10-3-DEFER-6 fail-closed invariant violated"
        )


# ── 6. Layer ordering (1 bonus case) ──────────────────────────────


def test_pipa_gate_appears_before_capability_gate() -> None:
    """Layer ordering invariant: PIPA gate MUST appear BEFORE capability gate
    in the endpoint signature (1st defense line).

    Verified on the 10-4 NEW endpoint (representative — same ordering
    applies to all 4 endpoints).
    """
    route = _find_route(router, "/api/v1/ai/promote")
    assert route is not None
    sig = inspect.signature(route.endpoint)
    param_names = list(sig.parameters.keys())

    # Find the index of PIPA gate parameter and capability gate parameter
    pipa_idx = None
    cap_idx = None
    for idx, name in enumerate(param_names):
        if name.startswith("ctx_pipa"):
            pipa_idx = idx
        elif name.startswith("ctx_cap") or name == "ctx":
            cap_idx = idx

    assert pipa_idx is not None, "ctx_pipa parameter not found"
    assert cap_idx is not None, "ctx_cap (or ctx) parameter not found"
    assert pipa_idx < cap_idx, (
        f"PIPA gate (idx={pipa_idx}) must appear BEFORE capability gate "
        f"(idx={cap_idx}) — 1st defense line invariant violated"
    )