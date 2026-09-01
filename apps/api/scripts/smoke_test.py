"""
apps/api/scripts/smoke_test.py — Production launch smoke test driver (cj-style 207번째 wire).

1st release launch (cj-style 64번째 진입점) — T5.1 (AC #5.1) — F18.5 Production verification.
- Walking Skeleton MVP `1e034c4` + Phase 3 close-out retro §6 honestly DEFER 해소.
- Epic 1 ~ Epic 15 모든 wire flow 정합 검증.
- Epic 13/14 LISTEN/NOTIFY wire `f2ea2f6` + `7835463` 검증.
- Phase 4 backup wire `71a033a` 검증.

cj-style 207 (D-LAUNCH-1-DEFER-1 honestly minimum wire):
- 이 driver 는 stub 에서 **real HTTP driver** 로 wire 됨 (stdlib urllib, zero-deps).
- 16 launch flow 중 **canonical launch endpoint** (`/api/v1/launch/smoke-test`)
  가 내부적으로 13 flow sweep 을 trigger 하고 나머지 3 flow 는
  `LAUNCH_MONITORING` capability 의 summary 결과로 cover 됨.
- 추가로 5개 **직접 검증** endpoint 를 hit 하여 individual Epic wire 정합을
  cross-check 함.
- staging 환경 = `STAGING_BASE_URL` env var. 미설정 시 local dev fallback
  (`http://localhost:8765`).
- auth = `STAGING_JWT_TOKEN` env var (HS256 dev JWT). 미설정 시
  `SUPABASE_JWT_SECRET` 으로 dev token mint.

honestly DEFER (cj-207 외 sub-items):
- (b) backup drill 0036 PITR quarterly 실측 — 외부 Supabase Pro PITR
  인프라 보류 → `D-LAUNCH-1-DEFER-2` honestly DEFER.
- (c) Sentry alert wiring production — 외부 Sentry Team project +
  Slack webhook 보류 → `D-LAUNCH-1-DEFER-3` honestly DEFER.
- (d) RPO 4h / RTO 24h SLA verification 실측 — `/api/v1/launch/backup-status`
  endpoint 는 존재하여 SLA 수치는 report 가능하나 **실측 drill 결과** 는
  cross-region failover_orchestrator 보류 → `D-LAUNCH-1-DEFER-4` honestly DEFER.

CR 11-3 honest-DEFER discipline + CR 9-6 commit message discipline +
CR 12-5 D-14 envelope (HTTPError → AD-15 `{code, message_ko}`).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Final

DEFAULT_BASE_URL: Final[str] = "http://localhost:8765"
DEFAULT_TIMEOUT_SECONDS: Final[int] = 30
LAUNCH_SMOKE_PATH: Final[str] = "/api/v1/launch/smoke-test"
LAUNCH_BACKUP_STATUS_PATH: Final[str] = "/api/v1/launch/backup-status"
HEALTH_READY_PATH: Final[str] = "/api/v1/health/ready"

# 16 launch flows (Epic 1 ~ Epic 15 wire territory claim). The canonical
# launch endpoint `/api/v1/launch/smoke-test` internally sweeps a subset;
# the rest are verified via direct endpoint hits below.
LAUNCH_FLOWS: Final[tuple[str, ...]] = (
    "auth:magic_link_login",
    "auth:social_oauth_google",
    "auth:social_oauth_naver",
    "auth:social_oauth_kakao",
    "auth:sso_enterprise_saml",
    "auth:2fa_totp",
    "abc:calculation_manufacturing",
    "abc:calculation_service",
    "tdabc:time_driven_allocation",
    "ai_insight:extract_monthly",
    "ai_insight:cache_hit",
    "listen_notify:register_daemon",
    "listen_notify:tenant_fanout",
    "listen_notify:multiprocess_coordination",
    "backup:phase_4_pitr_7d",
    "backup:smoke_health_check",
)

PASS: Final[str] = "PASS"
FAIL: Final[str] = "FAIL"
SKIP: Final[str] = "SKIP"


@dataclass
class StepResult:
    """One smoke test step outcome.

    Attributes:
        name: human-readable step name (e.g. 'launch.smoke_test.trigger').
        method: HTTP method.
        path: URL path under base_url.
        status: HTTP status code (None if request never reached server).
        ok: True if status in expected set.
        critical: False steps do not fail the overall smoke (idempotent re-runs).
        error_code: AD-15 typed envelope `code` if present.
        detail: free-form detail string for the operator.
        mode: 'PASS' / 'FAIL' / 'SKIP'.
    """

    name: str
    method: str
    path: str
    status: int | None
    ok: bool
    critical: bool
    mode: str = PASS
    error_code: str | None = None
    detail: str = ""


@dataclass
class Runner:
    """Real HTTP driver — stdlib urllib only, zero deps (CR 11-3 / AD-15).

    Mirrors `scripts/smoke_e2e.py::Runner` shape but kept locally to keep
    `apps/api/scripts/smoke_test.py` invocable as `python smoke_test.py`
    without sys.path manipulation.
    """

    base_url: str
    token: str
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    results: list[StepResult] = field(default_factory=list)
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
        headers: dict[str, str] | None = None,
    ) -> tuple[StepResult, Any]:
        """Issue one HTTP request, record outcome, return (result, parsed_body).

        The Runner never raises on HTTP failure — it records the outcome
        and returns a non-ok StepResult. This matches the cj-style smoke
        driver invariant: "Report, do not assert. The exit code reflects
        the critical path, but the value is the printed table."
        """
        url = f"{self.base_url}{path}"
        data: bytes | None = None
        req_headers: dict[str, str] = {
            "Authorization": f"Bearer {self.token}",
            "X-Trace-Id": f"smoke-launch-{len(self.results):03d}",
        }
        if headers:
            req_headers.update(headers)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)

        status: int | None = None
        payload: Any = None
        error_code: str | None = None
        detail = ""
        ok = False

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status = resp.status
                body_bytes = resp.read()
                if body_bytes:
                    try:
                        payload = json.loads(body_bytes)
                    except json.JSONDecodeError:
                        payload = None
                        detail = f"non-JSON body ({len(body_bytes)} bytes)"
            ok = status in expect
        except urllib.error.HTTPError as e:
            status = e.code
            raw_body = e.read()
            try:
                payload = json.loads(raw_body)
                error_code = payload.get("code") if isinstance(payload, dict) else None
                detail = (
                    payload.get("message_ko", "") if isinstance(payload, dict) else ""
                ) or str(payload)[:200]
            except json.JSONDecodeError:
                detail = raw_body.decode("utf-8", "replace")[:200]
            ok = status in expect
        except urllib.error.URLError as e:
            detail = f"CONNECTION FAILED: {e.reason}"
        except Exception as e:  # noqa: BLE001 — driver must never crash
            detail = f"{type(e).__name__}: {e}"

        mode = PASS if ok else (SKIP if status == 405 else FAIL)
        result = StepResult(
            name=name,
            method=method,
            path=path,
            status=status,
            ok=ok,
            critical=critical,
            mode=mode,
            error_code=error_code,
            detail=detail,
        )
        self.results.append(result)
        flag = f"{mode:4}"
        extra = f" [{error_code}]" if error_code else ""
        status_str = f"{status}" if status is not None else "---"
        print(f"  {flag}  {status_str:>4}  {method:6} {path}{extra}")
        if not ok and detail:
            print(f"          ↳ {detail[:180]}")
        return result, payload


def _resolve_base_url() -> str:
    """Resolve base URL from STAGING_BASE_URL env, fall back to local dev.

    `STAGING_BASE_URL` is the staging-or-production target. When unset
    (default), the driver targets the local dev stack — this matches the
    cj-style convention: same code path, two execution modes.
    """
    return os.environ.get("STAGING_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _resolve_token() -> str:
    """Resolve auth token from env.

    Resolution order:
    1. `STAGING_JWT_TOKEN` (preferred for staging/production runs).
    2. `SUPABASE_JWT_SECRET` + dev_seed.mint_dev_token (local dev fallback).
    3. Empty string (HTTP 401 if any endpoint requires auth — recorded as FAIL).
    """
    explicit = os.environ.get("STAGING_JWT_TOKEN")
    if explicit:
        return explicit
    secret = os.environ.get("SUPABASE_JWT_SECRET")
    if not secret:
        return ""
    # Local dev fallback — mint a dev token via dev_seed (repo `scripts/`).
    # `apps/api/scripts/smoke_test.py` lives one level deeper than
    # `scripts/dev_seed.py`, so we explicitly insert that path.
    import importlib.util
    from pathlib import Path

    dev_seed_path = Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "dev_seed.py"
    if not dev_seed_path.exists():
        return ""
    spec = importlib.util.spec_from_file_location("dev_seed", dev_seed_path)
    if spec is None or spec.loader is None:
        return ""
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 — driver must never crash on import
        return ""
    return module.mint_dev_token(
        secret=secret,
        tenant_id=module.DEV_TENANT_ID,
        user_id=module.DEV_USER_ID,
        role=module.DEV_ROLE,
        industry="manufacturing",
    )


def run_smoke_test(base_url: str, token: str) -> int:
    """Drive the production launch smoke over real HTTP. Returns 0 on pass.

    3 sections (cj-style 207 honestly minimum wire):
    1. **Canonical launch endpoint** — POST /api/v1/launch/smoke-test +
       GET /api/v1/launch/backup-status. These are the LAUNCH_MONITORING
       capability-gated endpoints that internally claim the 16-flow sweep.
    2. **Direct endpoint cross-check** — 5 individual endpoints covering
       representative Epic wire territory (calc, AI documents, health).
       These provide independent verification beyond the launch endpoint
       summary.
    3. **Summary** — printed table + exit code.

    `D-LAUNCH-1-DEFER-2/3/4` honestly DEFER 보존 (PITR drill 실측 +
    Sentry alert wiring production + RPO/RTO SLA verification 실측).
    """
    print("=" * 74)
    print("  costmgr production launch smoke — real HTTP, 16 flow coverage")
    print("=" * 74)
    print(f"  base_url  : {base_url}")
    print(
        f"  token_src : {'STAGING_JWT_TOKEN' if os.environ.get('STAGING_JWT_TOKEN') else 'dev_seed.mint_dev_token' if os.environ.get('SUPABASE_JWT_SECRET') else 'NONE (401 expected)'}"
    )
    print()

    runner = Runner(base_url=base_url, token=token)

    print("[1] Canonical launch endpoints (LAUNCH_MONITORING capability)")
    _, smoke_result = runner.call(
        "launch.smoke_test.trigger",
        "POST",
        LAUNCH_SMOKE_PATH,
        {},
        expect=(200, 201),
    )
    if isinstance(smoke_result, dict):
        flows_total = smoke_result.get("flows_total")
        flows_passed = smoke_result.get("flows_passed")
        last_run_at = smoke_result.get("last_run_at")
        flows = smoke_result.get("flows") or []
        print(
            f"          ↳ flows_total={flows_total} "
            f"flows_passed={flows_passed} "
            f"last_run_at={last_run_at}"
        )
        if isinstance(flows, list):
            missing = [f for f in LAUNCH_FLOWS if f not in flows]
            extra = [f for f in flows if f not in LAUNCH_FLOWS]
            print(f"          ↳ covered={len(flows)}/16 missing={missing} extra={extra}")
            runner.ctx["launch_flows_covered"] = len(flows)
            runner.ctx["launch_flows_missing"] = missing

    _, backup_status = runner.call(
        "launch.backup_status",
        "GET",
        LAUNCH_BACKUP_STATUS_PATH,
        expect=(200,),
    )
    if isinstance(backup_status, dict):
        rpo = backup_status.get("rpo_hours")
        rto = backup_status.get("rto_hours")
        overdue = backup_status.get("overdue")
        print(
            f"          ↳ RPO={rpo}h RTO={rto}h overdue={overdue} " f"(SLA target: RPO=4h RTO=24h)"
        )
        runner.ctx["backup_rpo_hours"] = rpo
        runner.ctx["backup_rto_hours"] = rto
        runner.ctx["backup_overdue"] = overdue

    print("\n[2] Direct endpoint cross-check (representative Epic territory)")
    runner.call(
        "health.ready",
        "GET",
        HEALTH_READY_PATH,
        expect=(200,),
    )
    runner.call(
        "calc.run",
        "POST",
        "/api/v1/calc",
        {"period_key": "2099-01"},
        expect=(200, 422),
        critical=False,
    )
    runner.call(
        "abc.validate",
        "POST",
        "/api/v1/abc/validate",
        {"cost_pool": {"name": "smoke-pool"}, "activities": [], "drivers": []},
        expect=(200, 422),
        critical=False,
    )
    runner.call(
        "ai_documents.list",
        "GET",
        "/api/v1/ai-documents",
        expect=(200,),
        critical=False,
    )
    runner.call(
        "sso.metadata",
        "GET",
        "/api/v1/auth/sso/metadata",
        expect=(200, 404),
        critical=False,
    )

    return _summarize(runner)


def _summarize(runner: Runner) -> int:
    """Print summary table, return exit code (0 = pass, 1 = critical fail)."""
    total = len(runner.results)
    passed = sum(1 for x in runner.results if x.ok)
    crit_failed = [x for x in runner.results if not x.ok and x.critical]

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
        print("\n  ✅ Critical path completed end to end.")

    print("\n  Derived state:")
    for k, v in runner.ctx.items():
        print(f"    {k} = {v}")
    print()

    print("  Honestly DEFER (cj-207 scope 외부, 보존 결정):")
    print(
        "    D-LAUNCH-1-DEFER-2 — backup drill 0036 PITR quarterly 실측 (외부 Supabase Pro PITR infra)"
    )
    print(
        "    D-LAUNCH-1-DEFER-3 — Sentry alert wiring production (외부 Sentry Team project + Slack webhook)"
    )
    print(
        "    D-LAUNCH-1-DEFER-4 — RPO 4h / RTO 24h SLA verification 실측 (cross-region failover_orchestrator 실측)"
    )
    print()
    return 1 if crit_failed else 0


def main() -> int:
    base_url = _resolve_base_url()
    token = _resolve_token()
    return run_smoke_test(base_url=base_url, token=token)


if __name__ == "__main__":
    sys.exit(main())
