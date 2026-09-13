"""tests.api.m6_verification.test_router_disposition_and_service — M6 router decision wire.

Source health 갭 회복 wire (순서 2, cj-style 307번째 정직 회복) — M6 router decision:

**결정 wire**: M6 Verification 모듈은 dedicated router 를 가지지 **않는다**.
Epic 4 (M3 + M4 territory) 의 closing_period_service 안으로 fold 되었다
(architecture file-churn decision, m6_verification/__init__.py line 1 verbatim).

**근거 (Rationale)**:
- V4 closing-period consistency 검증은 post-emit consistency check 이다
  (closing_snapshot INSERT 직후 dispatch).
- 사용자 facing HTTP endpoint 가 아니다 — internal service-level
  verification 이다.
- `ClosingPeriodSnapshotInconsistencyError` 는 main.py 의 typed exception
  envelope 에서 import 만 되고 (line 132), router 등록은 0건.
- `ClosingPeriodSnapshotVerifier` 는 M4_inventory 의
  `ClosingPeriodService.confirm_closing_period` 안에서 호출된다.

**검증 항목**:

1. **M6 router disposition** — `m6_verification.__init__` 에 `router` attribute 0건
   (drift-detector friendly: 새 router 추가 시 즉시 실패)

2. **M6 main.py registration** — main.py 에 `m6_verification` router include 0건
   (folded architecture 정합 보존)

3. **ClosingPeriodSnapshotVerifier class export** — service module 에서
   `ClosingPeriodSnapshotVerifier` + `ClosingPeriodSnapshotInconsistencyError` 노출

4. **ClosingPeriodSnapshotInconsistencyError attributes** — typed exception 의
   tenant_id + period_key + failures + trace_id attribute 보존
"""
from __future__ import annotations

import inspect
import re
import uuid
from pathlib import Path


# ── Test 1 — M6 router disposition (m6_verification/__init__.py) ───────


def test_m6_verification_init_does_not_export_router():
    """M6 router decision: m6_verification/__init__.py 는 router 를 export 하지 않는다.

    Architecture 결정 (m6_verification/__init__.py line 1):
    "M6 Verification module — folded into Epic 4 (per architecture
     file-churn decision)."

    만약 누군가 실수로 m6_verification/router.py 를 추가하고 __init__ 에서
    re-export 하면 이 테스트가 실패 → drift-detector 역할.
    """
    import apps.api.modules.m6_verification as m6_pkg

    # `router` attribute 가 module-level 에 없거나, None 이어야 한다
    router_attr = getattr(m6_pkg, "router", None)
    assert router_attr is None, (
        f"M6 router decision: m6_verification must NOT export a router "
        f"(folded into Epic 4). Got router={router_attr!r}"
    )

    # __all__ 리스트에 router 가 없어야 한다 (drift-detector friendly)
    all_exports = getattr(m6_pkg, "__all__", None)
    if all_exports is not None:
        assert "router" not in all_exports, (
            f"M6 router decision: __all__ must not include 'router'. "
            f"Got __all__={all_exports}"
        )


def test_m6_verification_init_docstring_states_folded_decision():
    """m6_verification/__init__.py docstring 이 "folded into Epic 4" 결정을 verbatim 보존.

    결정 wire 보존 = drift detector 가 disposition 을 강제. 누군가 docstring 을
    변경하여 의도가 흐려지면 즉시 정합 위반 감지.
    """
    from apps.api.modules.m6_verification import __doc__ as m6_doc

    assert m6_doc is not None, "m6_verification must have a module docstring"
    assert "folded into Epic 4" in m6_doc, (
        f"M6 router decision drift: docstring must mention 'folded into Epic 4' "
        f"to preserve architectural decision wire. Got docstring: {m6_doc!r}"
    )


# ── Test 2 — M6 main.py registration (folded architecture 정합) ──────


def test_m6_verification_no_router_include_in_main_py():
    """main.py 에 m6_verification router include 0건 (folded architecture).

    `from apps.api.modules.m6_verification import router` 또는
    `m6_verification.router` / `app.include_router(...m6_verification...)` 패턴
    검색 — 0건이어야 한다.
    """
    main_py_path = Path("apps/api/main.py")
    main_source = main_py_path.read_text(encoding="utf-8")

    # router include 패턴 (cj-style drift-detector regex friendly)
    router_include_patterns = [
        r"include_router\s*\([^)]*m6_verification",  # include_router(m6_verification_router)
        r"from\s+apps\.api\.modules\.m6_verification\s+import\s+router",  # from ... import router
        r"m6_verification\.router",  # m6_verification.router attribute access
    ]

    matches = []
    for pattern in router_include_patterns:
        if re.search(pattern, main_source):
            matches.append(pattern)

    assert matches == [], (
        f"M6 router decision violated: main.py contains router references "
        f"for folded module. matches={matches}"
    )


def test_m6_verification_exception_only_imported_in_main_py():
    """main.py 는 m6_verification 의 exception 만 import (router 등록 0건).

    M6 architecture 의 contract: V4 verifier 의 typed exception 은
    exception envelope 매핑용으로 import 되지만 router 는 0건.
    """
    main_py_path = Path("apps/api/main.py")
    main_source = main_py_path.read_text(encoding="utf-8")

    # `from apps.api.modules.m6_verification...` 라인만 검색
    m6_import_lines = [
        line for line in main_source.splitlines() if "m6_verification" in line
    ]

    assert len(m6_import_lines) > 0, (
        "main.py 는 최소한 m6_verification 의 typed exception 을 import 해야 한다"
    )

    # 모든 m6_verification import 가 exception (또는 services) 만 참조
    for line in m6_import_lines:
        # router 참조 / include_router 호출 0건 확인
        assert "router" not in line, (
            f"M6 router decision violated: main.py imports 'router' from "
            f"m6_verification: {line.strip()}"
        )
        assert "include_router" not in line, (
            f"M6 router decision violated: main.py includes router for "
            f"m6_verification: {line.strip()}"
        )


# ── Test 3 — ClosingPeriodSnapshotVerifier class export ──────────────


def test_closing_period_snapshot_verifier_class_exports():
    """closing_period_snapshot_verifier service module 의 exports 검증.

    M6 의 single service: `ClosingPeriodSnapshotVerifier` (class) +
    `ClosingPeriodSnapshotInconsistencyError` (typed exception).
    둘 다 module-level export + `__all__` 리스트에 포함.
    """
    from apps.api.modules.m6_verification.services import (
        closing_period_snapshot_verifier as svc,
    )

    # class export
    assert hasattr(svc, "ClosingPeriodSnapshotVerifier"), (
        "M6 service module must export ClosingPeriodSnapshotVerifier class"
    )
    assert inspect.isclass(svc.ClosingPeriodSnapshotVerifier), (
        "ClosingPeriodSnapshotVerifier must be a class"
    )

    # exception export
    assert hasattr(svc, "ClosingPeriodSnapshotInconsistencyError"), (
        "M6 service module must export ClosingPeriodSnapshotInconsistencyError"
    )
    assert inspect.isclass(svc.ClosingPeriodSnapshotInconsistencyError), (
        "ClosingPeriodSnapshotInconsistencyError must be a class"
    )

    # __all__ 리스트 검증
    all_exports = getattr(svc, "__all__", None)
    assert all_exports is not None, "M6 service module must define __all__"
    assert "ClosingPeriodSnapshotVerifier" in all_exports
    assert "ClosingPeriodSnapshotInconsistencyError" in all_exports


def test_closing_period_snapshot_verifier_init_signature():
    """ClosingPeriodSnapshotVerifier.__init__ signature 검증.

    signature: (session, *, tenant_id, trace_id, industry=None).
    industry 는 optional — service-only tenant 의 경우 None 가능.
    """
    from apps.api.modules.m6_verification.services.closing_period_snapshot_verifier import (
        ClosingPeriodSnapshotVerifier,
    )

    sig = inspect.signature(ClosingPeriodSnapshotVerifier.__init__)
    params = sig.parameters

    # 필수 parameters
    assert "session" in params, (
        f"ClosingPeriodSnapshotVerifier.__init__ must accept 'session' parameter. "
        f"got parameters={list(params.keys())}"
    )
    assert "tenant_id" in params, (
        f"ClosingPeriodSnapshotVerifier.__init__ must accept 'tenant_id' keyword"
    )
    assert "trace_id" in params, (
        f"ClosingPeriodSnapshotVerifier.__init__ must accept 'trace_id' keyword"
    )

    # industry 는 optional (default None)
    industry_param = params.get("industry")
    assert industry_param is not None, (
        "ClosingPeriodSnapshotVerifier.__init__ should accept 'industry' parameter"
    )
    assert industry_param.default is None, (
        f"industry parameter must default to None (service-only tenant support). "
        f"got default={industry_param.default!r}"
    )


# ── Test 4 — ClosingPeriodSnapshotInconsistencyError attributes ───────


def test_closing_period_snapshot_inconsistency_error_attributes():
    """Typed exception 이 HTTP envelope 매핑에 필요한 attributes 보존.

    Required attrs: tenant_id (UUID) + period_key (str) + failures (list) +
    trace_id (str). main.py 의 exception envelope 핸들러가 이 attributes 를
    읽어 response body 에 포함.
    """
    from apps.api.modules.m6_verification.services.closing_period_snapshot_verifier import (
        ClosingPeriodSnapshotInconsistencyError,
    )

    tenant_id = uuid.uuid4()
    period_key = "2026-09"
    failures = [
        {"product_id": "PRD-001", "expected": "1000", "actual": "0"},
        {"product_id": "PRD-002", "expected": "500", "actual": "0"},
    ]
    trace_id = "test-trace-001"

    err = ClosingPeriodSnapshotInconsistencyError(
        tenant_id=tenant_id,
        period_key=period_key,
        failures=failures,
        trace_id=trace_id,
    )

    # attributes preserved
    assert err.tenant_id == tenant_id
    assert err.period_key == period_key
    assert err.failures == failures
    assert err.trace_id == trace_id

    # message must reference period_key + failure count (for log diagnosis)
    msg = str(err)
    assert period_key in msg, (
        f"Exception message must include period_key for log diagnosis. got={msg!r}"
    )
    assert "2" in msg, (
        f"Exception message must include failure count. got={msg!r}"
    )
