"""apps.api.modules.m10_ai.adapters — concrete `DocumentExtractionPort` impls.

Story 1.3 — Task 2.2.

Adapters:
- `fake_adapter.py` — deterministic, sha256-of-bytes-driven test fake.
  Used by unit tests + dev environments without `ANTHROPIC_API_KEY`.
  Status is `completed` with confidence values derived from byte
  content; failures are simulated by specific magic bytes (see
  FAULT_INJECTION_HEADER below).
- `claude_vision.py` — production stub. The full Anthropic SDK call is
  gated by the [STACK BUMP] workflow (Story 0.3 lesson). Until that
  bump ships, this module raises `AIProviderNotConfiguredError` so the
  service layer can fail fast instead of returning a half-formed job.

Selection rule (in `service.py`):
- If `AI_PROVIDER_ENABLED` is True AND the env has `ANTHROPIC_API_KEY`,
  use `ClaudeVisionAdapter`.
- Else use `FakeDocumentExtractionAdapter`.

Cross-language parity test:
- `tests/integration/test_extraction_parity.py` (Task 5) asserts the
  fake's output shape matches the TS types in
  `apps/web/lib/extraction-types.ts`.
"""
