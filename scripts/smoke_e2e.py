"""scripts/smoke_e2e.py — MVP critical-path walking-skeleton driver.

Walking Skeleton verification sprint.

Why this exists
---------------
The repo reported "8 of 13 epics done" and "3중 게이트 FINAL CLEAN", but every
gate measured *scoped* units: ruff on touched files, pytest on focused
selections, vitest with mocked network, Playwright with `page.route()`
interception. None of them ever sent a request to a live FastAPI process
backed by a real Postgres. 86 pytest tests were skipped outright with
"DB-backed; enabled when CI shim is wired".

So the one question that decides whether this product is shippable —
*can a tenant get from monthly input to a closed period and a report?* —
had never been asked. This script asks it.

Design rules
------------
1. **Real HTTP only.** No TestClient, no ASGI shortcut, no mocking. If it
   does not work over the wire against a live server, it does not work.
2. **Never stop at the first failure.** A driver that aborts on step 3
   tells you about step 3. This one attempts every step and reports the
   whole surface, so one run yields a complete truth table.
3. **Report, do not assert.** The exit code reflects the critical path,
   but the value is the printed table: for each step, the status code and
   the AD-15 `code` from the error envelope.
4. **Zero new dependencies.** stdlib urllib only.

Usage
-----
    make smoke
    # or
    set -a; source apps/api/.env; set +a
    uv run python scripts/smoke_e2e.py --base-url http://localhost:8765

Requires: `make db-up && make db-migrate && make db-seed`, and a running
API (`make api-dev`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# The dev identity + token minting live in dev_seed so there is exactly one
# definition of "who the dev tenant is".
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dev_seed import (  # noqa: E402
    DEV_ROLE,
    DEV_TENANT_ID,
    DEV_USER_ID,
    mint_dev_token,
)

DEFAULT_BASE_URL = "http://localhost:8765"
PERIOD_KEY = "2026-08"
FISCAL_YEAR_START = "2026-01"
INDUSTRY = "manufacturing"

# ── Result recording ───────────────────────────────────────────


@dataclass
class StepResult:
    name: str
    method: str
    path: str
    status: int | None
    ok: bool
    error_code: str | None = None
    detail: str = ""
    critical: bool = True


@dataclass
class Runner:
    base_url: str
    token: str
    results: list[StepResult] = field(default_factory=list)
    # Values discovered mid-run (product ids, etc.) that later steps need.
    ctx: dict[str, Any] = field(default_factory=dict)

    def call(
        self,
        name: str,
        method: str,
        path: str,
        body: Any | None = None,
        *,
        critical: bool = True,
        expect: tuple[int, ...] = (200, 201, 204),
        raw: bool = False,
    ) -> tuple[StepResult, Any]:
        """Issue one request, record the outcome, return (result, parsed_body)."""
        url = f"{self.base_url}{path}"
        data = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Trace-Id": f"smoke-{len(self.results):03d}",
        }
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        status: int | None = None
        payload: Any = None
        error_code: str | None = None
        detail = ""

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status
                body_bytes = resp.read()
                if raw:
                    payload = body_bytes
                    detail = f"{len(body_bytes)} bytes"
                elif body_bytes:
                    try:
                        payload = json.loads(body_bytes)
                    except json.JSONDecodeError:
                        payload = None
                        detail = f"non-JSON body ({len(body_bytes)} bytes)"
        except urllib.error.HTTPError as e:
            status = e.code
            raw_body = e.read()
            try:
                payload = json.loads(raw_body)
                # AD-15 error envelope: {code, message_ko, details, trace_id}
                error_code = payload.get("code") if isinstance(payload, dict) else None
                detail = (
                    payload.get("message_ko", "")
                    if isinstance(payload, dict)
                    else ""
                ) or str(payload)[:200]
                # Walking Skeleton (2026-08-16): print full `details` blob
                # so typed-exception root causes (e.g.
                # CLOSING_GUARD_PRODUCTION_CONSUMPTION_ERROR's
                # `error_code` / `message` / `event_count`) surface in the
                # smoke summary instead of being silently hidden behind
                # the generic `message_ko`.
                if isinstance(payload, dict) and payload.get("details"):
                    detail = f"{detail} | details={json.dumps(payload['details'], default=str)[:240]}"
            except json.JSONDecodeError:
                detail = raw_body.decode("utf-8", "replace")[:200]
        except urllib.error.URLError as e:
            detail = f"CONNECTION FAILED: {e.reason}"
        except Exception as e:  # noqa: BLE001 — a driver must never crash
            detail = f"{type(e).__name__}: {e}"

        ok = status in expect
        result = StepResult(
            name=name,
            method=method,
            path=path,
            status=status,
            ok=ok,
            error_code=error_code,
            detail=detail,
            critical=critical,
        )
        self.results.append(result)
        flag = "PASS" if ok else "FAIL"
        extra = f" [{error_code}]" if error_code else ""
        print(f"  {flag:4}  {status or '---':>4}  {method:6} {path}{extra}")
        if not ok and detail:
            print(f"          ↳ {detail[:180]}")
        return result, payload


# ── The critical path ──────────────────────────────────────────


def run(r: Runner) -> None:
    print("\n[1] Liveness")
    r.call("health", "GET", "/health")

    print("\n[2] Onboarding + settings (Epic 1 — gate for [계산])")
    r.call("settings.read", "GET", "/api/v1/tenant-settings")
    r.call(
        "settings.industry",
        "POST",
        "/api/v1/tenant-settings/onboarding/industry",
        {"industry": INDUSTRY},
    )
    r.call(
        "settings.fiscal_year_start",
        "POST",
        "/api/v1/tenant-settings/onboarding/fiscal-year-start",
        {"fiscal_year_start": FISCAL_YEAR_START},
    )
    r.call(
        "settings.currency",
        "POST",
        "/api/v1/tenant-settings/onboarding/currency",
        {"currency": "KRW"},
    )
    r.call(
        "settings.language",
        "POST",
        "/api/v1/tenant-settings/onboarding/language",
        {"language": "ko-KR"},
    )
    # Completion requires >=1 direct/indirect AND >=1 fixed/variable account
    # classification (packages/services/m0_onboarding/settings_completion.py).
    r.call(
        "settings.account_classification",
        "POST",
        "/api/v1/baseline/accounts/classification",
        {
            "account_id": "smoke-account-1",
            "direct_indirect": "direct",
            "fixed_variable": "variable",
        },
    )
    # Walking Skeleton (2026-08-16): PRD §F0.2 3종 모두 저장해야
    # BaselineLoader._verify_allocation_basis이 true로 본다. 이전엔
    # `driver` 기준이 빠져서 [계산]이 항상 422 BASELINE_NOT_READY를
    # 던졌다.
    for criterion in ("direct_indirect", "fixed_variable", "drivers"):
        r.call(
            f"settings.allocation.{criterion}",
            "POST",
            "/api/v1/tenant-settings/onboarding/allocation-criteria",
            {"criterion": criterion, "count": 1},
        )

    _, completion = r.call(
        "settings.completion", "GET", "/api/v1/tenant-settings/completion"
    )
    if isinstance(completion, dict):
        is_complete = completion.get("is_complete")
        missing = completion.get("missing") or []
        print(f"          ↳ is_complete={is_complete} missing={missing}")
        r.ctx["settings_complete"] = bool(is_complete)

    print("\n[3] Master data + BOM (Epic 2)")
    # Walking Skeleton (2026-08-16): products are persistent across
    # smoke reruns. Look up existing codes first to keep the smoke
    # idempotent. If a code exists, reuse its id rather than 409
    # PRODUCT_CODE_DUPLICATE.
    _, existing_products = r.call(
        "product.list", "GET", "/api/v1/baseline/products?limit=1000"
    )
    code_to_id: dict[str, str] = {}
    if isinstance(existing_products, dict):
        for p in existing_products.get("items") or []:
            if isinstance(p, dict) and p.get("code") and p.get("id"):
                code_to_id[p["code"]] = p["id"]

    def _ensure_product(code: str, name: str, product_type: str, unit_cost_krw: int) -> str | None:
        if code in code_to_id:
            return code_to_id[code]
        _, created = r.call(
            f"product.create.{code.lower()}",
            "POST",
            "/api/v1/baseline/products",
            {
                "name": name,
                "product_type": product_type,
                "code": code,
                "unit": "EA",
                "unit_cost_krw": unit_cost_krw,
            },
            expect=(201,),
        )
        if isinstance(created, dict) and created.get("id"):
            code_to_id[code] = created["id"]
            return created["id"]
        return None

    parent_id = _ensure_product("PRD-9001", "스모크 완제품", "product", 0)
    child_a_id = _ensure_product("MAT-9001", "스모크 원재료A", "material", 1000)
    child_b_id = _ensure_product("MAT-9002", "스모크 원재료B", "material", 2000)
    children = [c for c in (child_a_id, child_b_id) if c]
    r.ctx["parent_id"] = parent_id
    parent = {"id": parent_id} if parent_id else {}

    if parent_id and len(children) == 2:
        # A6 invariant: ratios must total exactly 100.0000
        r.call(
            "bom.put",
            "PUT",
            f"/api/v1/baseline/products/{parent_id}/bom",
            {
                "lines": [
                    {"child_product_id": children[0], "ratio": "60.0000"},
                    {"child_product_id": children[1], "ratio": "40.0000"},
                ]
            },
        )
        _, bom = r.call(
            "bom.read", "GET", f"/api/v1/baseline/products/{parent_id}/bom"
        )
        if isinstance(bom, dict):
            print(
                f"          ↳ total_ratio={bom.get('total_ratio')} "
                f"is_complete={bom.get('is_complete')}"
            )
    else:
        print("  SKIP        BOM steps — parent/material creation did not succeed")

    print("\n[4] Monthly input — 6 streams (Epic 3)")
    # Walking Skeleton (2026-08-16): ordering matters. The production
    # guard verifies BOM material consumption against available stock.
    # Without prior purchases, producing 100 units of parent consumes
    # 60 units of MAT-9001 + 40 units of MAT-9002 — but those materials
    # have zero opening balance, so `production_material_consumption`
    # would go negative and the guard correctly rejects with
    # `CLOSING_GUARD_PRODUCTION_CONSUMPTION_ERROR`. To complete the
    # critical path, we record purchases FIRST (so material opening
    # stock exists), THEN produce (consumes), THEN sell (outbound).
    streams: list[tuple[str, dict[str, Any]]] = [
        ("orders", {"stream": "orders", "product_id": parent_id, "qty": "100"}),
        (
            "purchases.mat1",
            {
                "stream": "purchases",
                "product_id": children[0] if children else None,
                "qty": "200",
                "unit_price_krw": 1000,
            },
        ),
        (
            "purchases.mat2",
            {
                "stream": "purchases",
                "product_id": children[1] if len(children) > 1 else None,
                "qty": "200",
                "unit_price_krw": 2000,
            },
        ),
        ("production", {"stream": "production", "product_id": parent_id, "qty": "100"}),
        (
            "sales",
            {
                "stream": "sales",
                "product_id": parent_id,
                "qty": "80",
                "unit_price_krw": 15000,
            },
        ),
        ("expenses", {"stream": "expenses", "amount_krw": 500000}),
        (
            "labor",
            {
                "stream": "labor",
                "pay_type": "monthly",
                "workers": 3,
                "monthly_salary_basis_krw": 3000000,
                "company_burden_rate": "0.1",
            },
        ),
    ]
    for stream_name, row in streams:
        r.call(
            f"input.{stream_name}",
            "POST",
            f"/api/v2/monthly-input/{PERIOD_KEY}/rows",
            row,
        )

    _, state = r.call(
        "input.state", "GET", f"/api/v2/monthly-input/{PERIOD_KEY}/state"
    )
    if isinstance(state, dict):
        print(
            f"          ↳ is_complete={state.get('is_complete')} "
            f"is_blocked={state.get('is_blocked')} "
            f"missing={state.get('missing')}"
        )
        r.ctx["input_complete"] = bool(state.get("is_complete"))

    print("\n[5] Calculation + verification V1/V4/V7/V8 (Epic 4)")
    _, calc = r.call(
        "calc.run", "POST", "/api/v1/calc", {"period_key": PERIOD_KEY}
    )
    if isinstance(calc, dict):
        verdict = calc.get("verdict") or {}
        print(
            f"          ↳ state={calc.get('state')} "
            f"manufacturing_cost={calc.get('manufacturing_cost')} "
            f"result_hash={str(calc.get('result_hash'))[:16]}…"
        )
        print(
            f"          ↳ verification_status={verdict.get('verification_status')} "
            f"rules={[v.get('code') + ':' + v.get('status') for v in verdict.get('verifications', [])]}"
        )

    print("\n[6] Inventory ledger (Epic 5)")
    r.call(
        "ledger.period_closing",
        "GET",
        f"/api/v1/inventory/ledger/period-closing?period_key={PERIOD_KEY}",
    )

    print("\n[7] Close sequence (Epic 11)")
    r.call(
        "close.guard.attempt",
        "POST",
        "/api/v1/inventory/closing-guard/close-attempt",
        {"period_key": PERIOD_KEY},
    )
    r.call(
        "close.period.confirm",
        "POST",
        "/api/v1/inventory/closing-period/confirm",
        {"period_key": PERIOD_KEY},
    )
    # NOTE: period_key is read from the QUERY STRING by _resolve_period_key()
    # (apps/api/modules/m11_close/handlers.py:570) but is NOT declared as a
    # FastAPI parameter — so it does not appear in the OpenAPI schema at all.
    # Generated clients cannot discover it. Recorded as a contract defect.
    r.call(
        "close.sequence.initiate",
        "POST",
        f"/api/v1/close/sequence/initiate?period_key={PERIOD_KEY}",
        {},
        expect=(201,),
    )
    for step in ("divisions", "manufacturing", "abc", "common"):
        r.call(
            f"close.sequence.step.{step}",
            "POST",
            f"/api/v1/close/sequence/step-complete?period_key={PERIOD_KEY}",
            {"step_name": step},
        )
    r.call(
        "close.sequence.confirm",
        "POST",
        f"/api/v1/close/sequence/confirm?period_key={PERIOD_KEY}",
    )
    r.call(
        "close.sequence.state",
        "GET",
        f"/api/v1/close/sequence/state?period_key={PERIOD_KEY}",
    )

    print("\n[8] Monthly closing report + PDF (Epic 6)")
    _, report = r.call(
        "report.monthly_closing",
        "GET",
        f"/api/v1/inventory/monthly-closing-report?period_key={PERIOD_KEY}",
    )
    if isinstance(report, dict):
        rows = report.get("closing_per_product") or []
        print(
            f"          ↳ rows={len(rows)} "
            f"ledger_event_count={report.get('ledger_event_count')} "
            f"snapshot_count={report.get('fiscal_period_snapshot_count')}"
        )
    r.call(
        "report.v4_verdict",
        "GET",
        f"/api/v1/inventory/monthly-closing-report/v4-verdict?period_key={PERIOD_KEY}",
        critical=False,
    )
    r.call(
        "report.export_pdf",
        "POST",
        f"/api/v1/inventory/monthly-closing-report/export-pdf?period_key={PERIOD_KEY}",
        raw=True,
    )


# ── Reporting ──────────────────────────────────────────────────


def summarize(r: Runner) -> int:
    total = len(r.results)
    passed = sum(1 for x in r.results if x.ok)
    crit_failed = [x for x in r.results if not x.ok and x.critical]

    print("\n" + "=" * 74)
    print(f"  SMOKE SUMMARY — {passed}/{total} steps passed")
    print("=" * 74)

    if crit_failed:
        print(f"\n  {len(crit_failed)} CRITICAL-PATH FAILURE(S):\n")
        for x in crit_failed:
            code = f" [{x.error_code}]" if x.error_code else ""
            print(f"    ✗ {x.name}")
            print(f"        {x.method} {x.path} → {x.status}{code}")
            if x.detail:
                print(f"        {x.detail[:160]}")
    else:
        print("\n  ✅ The MVP critical path completed end to end.")

    print("\n  Derived state:")
    for k, v in r.ctx.items():
        print(f"    {k} = {v}")
    print()
    return 1 if crit_failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("SMOKE_BASE_URL", DEFAULT_BASE_URL))
    args = parser.parse_args()

    secret = os.environ.get("SUPABASE_JWT_SECRET")
    if not secret:
        print(
            "ERROR: SUPABASE_JWT_SECRET is not set. Run via `make smoke`.",
            file=sys.stderr,
        )
        return 2

    token = mint_dev_token(
        secret=secret,
        tenant_id=DEV_TENANT_ID,
        user_id=DEV_USER_ID,
        role=DEV_ROLE,
        industry=INDUSTRY,
    )

    print("=" * 74)
    print("  costmgr MVP critical-path smoke — real HTTP, real Postgres")
    print("=" * 74)
    print(f"  base_url  : {args.base_url}")
    print(f"  tenant_id : {DEV_TENANT_ID}")
    print(f"  industry  : {INDUSTRY}")
    print(f"  period_key: {PERIOD_KEY}")

    runner = Runner(base_url=args.base_url.rstrip("/"), token=token)
    run(runner)
    return summarize(runner)


if __name__ == "__main__":
    raise SystemExit(main())
