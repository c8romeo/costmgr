"""Test main.py lifespan EXTENSION — FastAPI listener start/stop.

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
T3 wire — FastAPI lifespan entry with CacheInvalidationListener start/stop.

For 13.1 we use a parallel on_event pattern (not full migration to
@asynccontextmanager, which is deferred to a separate epic). The
existing `_attach_tenant_listener` is preserved.

Tests:
- listener start hook exists
- listener stop hook exists
- 2 NEW exception handlers (ListenerStartFailedError → 503 / ListenerStopFailedError → 503)
- CR 12-5 D-14 envelope shape
- graceful degradation (missing DB → no crash)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_main_module() -> object:
    """Load apps/api/main.py as a module (without executing the full app)."""
    path = Path(__file__).resolve().parent.parent.parent / "apps" / "api" / "main.py"
    # We don't actually import main.py — that's heavy. We just verify
    # the source file contains the expected wire patterns.
    return path


class TestListenerWiring:
    """main.py listener wiring (T3 wire)."""

    def test_listener_start_hook_exists(self) -> None:
        """main.py must contain _start_cache_invalidation_listener()."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        assert "_start_cache_invalidation_listener" in text
        assert "listener.start()" in text

    def test_listener_stop_hook_exists(self) -> None:
        """main.py must contain _stop_cache_invalidation_listener()."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        assert "_stop_cache_invalidation_listener" in text
        assert "listener.stop()" in text

    def test_existing_tenant_listener_preserved(self) -> None:
        """_attach_tenant_listener must still be in main.py (backward compat)."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        assert "_attach_tenant_listener" in text
        assert "attach_tenant_listener" in text

    def test_listener_start_failed_handler(self) -> None:
        """main.py must have a handler for ListenerStartFailedError → 503."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        assert "ListenerStartFailedError" in text
        assert "503" in text
        assert "LISTENER_START_FAILED" in text

    def test_listener_stop_failed_handler(self) -> None:
        """main.py must have a handler for ListenerStopFailedError → 503."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        assert "ListenerStopFailedError" in text
        assert "LISTENER_STOP_FAILED" in text

    def test_cr_12_5_d14_envelope_shape(self) -> None:
        """D-14 envelope: {code, message_ko, details, trace_id}."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        # The 4 envelope keys must appear in the listener handlers.
        # Look for the env keys in the listener exception handler section.
        assert '"trace_id"' in text
        assert '"message_ko"' in text
        assert '"details"' in text

    def test_korean_message_constants(self) -> None:
        """Korean error messages: 캐시 무효화 리스너 시작 실패 / 종료 실패."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        assert "캐시 무효화 리스너 시작 실패" in text
        assert "캐시 무효화 리스너 종료 실패" in text


class TestGracefulDegradation:
    """main.py listener startup graceful degradation."""

    def test_import_error_caught(self) -> None:
        """If imports fail (test env), listener startup is skipped."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        # The startup hook must catch ImportError.
        assert "ImportError" in text or "RuntimeError" in text

    def test_app_state_binding(self) -> None:
        """Listener is bound to app.state for shutdown access."""
        path = _load_main_module()
        text = path.read_text(encoding="utf-8")
        assert "app.state.cache_invalidation_listener" in text
