"""cj-319 A-0 wire — CORS middleware 회귀 방지 (Track A F2 정직 회복).

배경 (cj-318 Track A 진입 시 정직 인정):
  `vercel.json` 의 CSP `connect-src ... https://*.railway.app` 는 브라우저가
  Vercel(web) origin 에서 Railway(API) origin 으로 **직접 cross-origin 호출**
  하는 구조를 전제한다. `docs/deployment-account-setup.md` §4.4 에는
  `CORS_ORIGINS` env var row 가 이미 존재했으나 **소스 wiring 이 없었다** →
  운영자가 Railway 에 CORS_ORIGINS 를 채워도 무효 + Track A-4 live signup
  smoke test 실패 확정. 본 테스트는 그 회귀를 잠근다.

검증 대상:
  1. `parse_cors_origins` fail-closed 파싱 (빈 값 / 공백 / wildcard 거부)
  2. CORSMiddleware 가 middleware stack **최외곽** (= 마지막 등록) 배치
  3. allowlist origin 의 preflight + 실제 요청에 Access-Control-* 부착
  4. 비허용 origin 은 allow-origin 헤더 미부착 (fail-closed)
  5. 4xx 오류 응답에도 CORS 헤더 부착 (최외곽 배치의 실익)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.main import (
    DEFAULT_CORS_ORIGINS,
    app,
    parse_cors_origins,
)

# 테스트에서 쓸 임의 origin (실제 배포 도메인과 무관한 고정값).
ALLOWED_ORIGIN = "https://costmgr-pilot.vercel.app"
DENIED_ORIGIN = "https://not-allowed.example.com"


# ── 1. parse_cors_origins fail-closed 파싱 ────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, DEFAULT_CORS_ORIGINS),
        ("", DEFAULT_CORS_ORIGINS),
        ("   ", DEFAULT_CORS_ORIGINS),
        (",,", DEFAULT_CORS_ORIGINS),
        # wildcard 는 allow_credentials=True 와 병용 불가 → 무시 후 default.
        ("*", DEFAULT_CORS_ORIGINS),
        (ALLOWED_ORIGIN, [ALLOWED_ORIGIN]),
        # comma-separated + 공백 trim.
        (
            f" {ALLOWED_ORIGIN} , https://staging.example.com ",
            [ALLOWED_ORIGIN, "https://staging.example.com"],
        ),
        # wildcard 가 섞여 있어도 나머지 origin 만 살린다.
        (f"*,{ALLOWED_ORIGIN}", [ALLOWED_ORIGIN]),
    ],
)
def test_parse_cors_origins_fail_closed(raw: str | None, expected: list[str]) -> None:
    assert parse_cors_origins(raw) == expected


def test_parse_cors_origins_never_returns_empty() -> None:
    """빈 allowlist 는 CORSMiddleware 를 무력화하므로 절대 반환되지 않는다."""
    for raw in (None, "", "   ", "*", ",  , *"):
        assert parse_cors_origins(raw), f"empty allowlist for raw={raw!r}"


# ── 2. middleware stack 배치 ──────────────────────────────────────


def test_cors_middleware_is_outermost() -> None:
    """CORS 가 최외곽이어야 preflight/오류 응답에도 헤더가 붙는다.

    `app.user_middleware` 는 outermost-first 순서다.
    """
    names = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in names, f"CORSMiddleware 미등록: {names}"
    assert names[0] == "CORSMiddleware", f"CORS 가 최외곽이 아님: {names}"


# ── 3~5. 실제 요청 동작 ───────────────────────────────────────────


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _configured_origin() -> str:
    """현 프로세스의 실제 allowlist 첫 origin (import 시점 env 반영)."""
    from apps.api.main import CORS_ALLOWED_ORIGINS

    return CORS_ALLOWED_ORIGINS[0]


def test_preflight_allows_configured_origin(client: TestClient) -> None:
    origin = _configured_origin()
    res = client.options(
        "/api/v1/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == origin
    allow_methods = res.headers.get("access-control-allow-methods", "")
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        assert method in allow_methods, f"{method} 누락: {allow_methods}"


def test_preflight_rejects_unknown_origin(client: TestClient) -> None:
    res = client.options(
        "/api/v1/health",
        headers={"Origin": DENIED_ORIGIN, "Access-Control-Request-Method": "GET"},
    )
    assert res.headers.get("access-control-allow-origin") is None


def test_error_response_still_carries_cors_headers(client: TestClient) -> None:
    """404/401 에도 CORS 헤더가 붙어야 브라우저가 본문을 읽을 수 있다."""
    origin = _configured_origin()
    res = client.get("/api/v1/__cj_319_nonexistent__", headers={"Origin": origin})
    assert res.status_code == 404
    assert res.headers.get("access-control-allow-origin") == origin


def test_trace_id_header_is_exposed(client: TestClient) -> None:
    """Phase 7 tracing 의 X-Trace-Id 를 브라우저 JS 가 읽을 수 있어야 한다."""
    origin = _configured_origin()
    res = client.get("/api/v1/__cj_319_nonexistent__", headers={"Origin": origin})
    expose = res.headers.get("access-control-expose-headers", "")
    assert "X-Trace-Id" in expose, f"X-Trace-Id 미노출: {expose!r}"


def test_unknown_origin_gets_no_cors_header_on_real_request(
    client: TestClient,
) -> None:
    res = client.get("/api/v1/__cj_319_nonexistent__", headers={"Origin": DENIED_ORIGIN})
    assert res.headers.get("access-control-allow-origin") is None
