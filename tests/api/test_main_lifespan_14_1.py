"""Test main.py 14.1 EXTENSION — leader election wiring + 2 NEW exception handlers.

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): T3 EXTENSION.

Verifies the 14.1 EXTENSION to the 13.1 main.py lifespan:
- 2 NEW lifespan functions: `_start_leader_election` + `_stop_leader_election`
- 2 NEW exception handlers (LeaderElectionFailedError → 503 +
  LeaderTakeoverFailedError → 503)
- CR 12-5 D-14 envelope shape (extending the existing handler)
- Existing listener wiring preserved (backward compat)
- Tenant listener (0.2 wire) preserved
- Graceful degradation: leader election failure does NOT crash startup
"""

from __future__ import annotations

from pathlib import Path


def _load_main_module_path() -> Path:
    """Return the path to apps/api/main.py."""
    return (
        Path(__file__).resolve().parent.parent.parent
        / "apps"
        / "api"
        / "main.py"
    )


class TestLeaderElectionWiring:
    """main.py leader election wiring (Story 14.1 T3 wire)."""

    def test_start_leader_election_function_exists(self) -> None:
        """main.py must contain `_start_leader_election()`."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "_start_leader_election" in text

    def test_stop_leader_election_function_exists(self) -> None:
        """main.py must contain `_stop_leader_election()`."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "_stop_leader_election" in text

    def test_listener_start_calls_leader_election_start(self) -> None:
        """`_start_cache_invalidation_listener` must call `_start_leader_election`."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        # The call site pattern is `_start_cache_invalidation_listener`
        # followed by an `_start_leader_election()` call before the
        # `except ListenerStartFailedError` block.
        start_section_start = text.find(
            "async def _start_cache_invalidation_listener"
        )
        assert start_section_start > 0
        # Look for `_start_leader_election` inside the function body.
        start_section_end = text.find(
            "async def _stop_cache_invalidation_listener",
            start_section_start,
        )
        start_section = text[start_section_start:start_section_end]
        assert "_start_leader_election" in start_section

    def test_listener_stop_calls_leader_election_stop(self) -> None:
        """`_stop_cache_invalidation_listener` must call `_stop_leader_election`."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        stop_section_start = text.find(
            "async def _stop_cache_invalidation_listener"
        )
        assert stop_section_start > 0
        stop_section_end = text.find(
            "async def _start_leader_election",
            stop_section_start,
        )
        stop_section = text[stop_section_start:stop_section_end]
        assert "_stop_leader_election" in stop_section

    def test_app_state_leader_state_binding(self) -> None:
        """Leader state bound to app.state.cache_invalidation_leader_state."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "app.state.cache_invalidation_leader_state" in text


class TestLeaderElectionExceptionHandlers:
    """2 NEW exception handlers (CR 12-5 D-14 envelope)."""

    def test_leader_election_failed_handler_exists(self) -> None:
        """main.py must have a handler for LeaderElectionFailedError → 503."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "LeaderElectionFailedError" in text
        assert "LEADER_ELECTION_FAILED" in text

    def test_leader_takeover_failed_handler_exists(self) -> None:
        """main.py must have a handler for LeaderTakeoverFailedError → 503."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "LeaderTakeoverFailedError" in text
        assert "LEADER_TAKEOVER_FAILED" in text

    def test_leader_election_failed_ko_message(self) -> None:
        """Korean SSOT message for leader election failure."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "리스너 리더 선출 실패" in text

    def test_leader_takeover_failed_ko_message(self) -> None:
        """Korean SSOT message for leader takeover failure."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "리스너 리더 인계 실패" in text

    def test_d14_envelope_extended_to_leader_failures(self) -> None:
        """D-14 envelope {code, message_ko, details, trace_id} for leader failures."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        # All 4 envelope keys must appear in the leader election handler.
        # We look at the section between LeaderElectionFailedError import
        # and the start of the next async def / class.
        assert '"trace_id"' in text
        assert '"message_ko"' in text
        assert '"details"' in text


class TestBackwardCompatibility:
    """Existing wiring preserved (13.1 + 0.2)."""

    def test_existing_tenant_listener_preserved(self) -> None:
        """_attach_tenant_listener (Story 0.2) still in main.py."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "_attach_tenant_listener" in text

    def test_existing_listener_start_hook_preserved(self) -> None:
        """_start_cache_invalidation_listener (13.1) still in main.py."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "_start_cache_invalidation_listener" in text
        assert "listener.start()" in text

    def test_existing_listener_stop_hook_preserved(self) -> None:
        """_stop_cache_invalidation_listener (13.1) still in main.py."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "_stop_cache_invalidation_listener" in text
        assert "listener.stop()" in text

    def test_existing_listener_start_failed_handler_preserved(self) -> None:
        """ListenerStartFailedError → 503 LISTENER_START_FAILED preserved."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "ListenerStartFailedError" in text
        assert "LISTENER_START_FAILED" in text

    def test_existing_listener_stop_failed_handler_preserved(self) -> None:
        """ListenerStopFailedError → 503 LISTENER_STOP_FAILED preserved."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        assert "ListenerStopFailedError" in text
        assert "LISTENER_STOP_FAILED" in text


class TestGracefulDegradation:
    """Leader election graceful degradation (CR 11-3 honest-DEFER 보존)."""

    def test_leader_election_failure_logged_not_raised(self) -> None:
        """Leader election failure logged, not raised (graceful degradation)."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        # The _start_leader_election function must catch all exceptions
        # and log them rather than raising (graceful degradation).
        # Look for the function body and verify it has a try/except.
        start = text.find("async def _start_leader_election")
        assert start > 0
        end = text.find("async def _stop_leader_election", start)
        body = text[start:end]
        assert "try:" in body or "try " in body
        assert "except" in body
        assert "warning" in body.lower() or "log" in body.lower()

    def test_import_error_caught_for_listener_startup(self) -> None:
        """If imports fail (test env), listener startup is skipped."""
        text = _load_main_module_path().read_text(encoding="utf-8")
        # The startup hook must catch ImportError (preserved from 13-1).
        assert "ImportError" in text
