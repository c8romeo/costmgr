"""apps.api.modules.m10_ai.adapters.claude_vision — production Claude Vision stub.

Story 1.3 — Task 2.2 (DEFERRED).

The real Anthropic SDK call (`@anthropic-ai/sdk`) requires:
- A `[STACK BUMP]` workflow (Story 0.3 lesson: pin values in
  `_bmad/bmm/config.yaml` + regen `apps/api/pyproject.toml` lockfile).
- A new dependency in `pyproject.toml` (not yet added — see deferred
  AD for tracking).
- Operational secrets: `ANTHROPIC_API_KEY` + `AI_PROVIDER_ENABLED=true`.

Until those are wired, this module:
- Satisfies the `DocumentExtractionPort` Protocol.
- Raises `AIProviderNotConfiguredError` at call time so the service
  layer fails fast (mapped to 503 SERVICE_UNAVAILABLE in handlers.py).
- Logs at WARNING with `request_id` so operators can see the gate.

When the SDK lands, replace `extract()` with:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=DOCUMENT_EXTRACTION_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}}
            or {"type": "document", "source": {...}}  # for PDFs
        ]}],
        system=EXTRACTION_SYSTEM_PROMPT,
        tools=[...],  # structured output
    )
    return _normalize_response(response, request, sha256, elapsed)

The `_normalize_response()` helper maps the provider's structured output
to `DocumentExtractionJob`. It MUST:
1. Validate the response against `SUPPORTED_FIELD_NAMES` (drop unknowns).
2. Truncate evidence.text to `EVIDENCE_TEXT_MAX_CHARS` before persisting.
3. Map provider errors to the typed 4-state FSM (see AD-15 §3).
"""

from __future__ import annotations

from packages.services.m10_ai.extraction_port import (
    DocumentExtractionJob,
    ExtractionRequest,
)


class AIProviderNotConfiguredError(Exception):
    """503 AI_PROVIDER_NOT_CONFIGURED — operator has not enabled the real adapter.

    Mapped by the M10 handlers.py exception handler. Raised here so the
    service layer doesn't need to know about provider configuration —
    only the adapter does.
    """

    def __init__(self, *, message: str = "AI provider not configured") -> None:
        super().__init__(message)


class ClaudeVisionAdapter:
    """Production adapter stub. Implements `DocumentExtractionPort`.

    Replace `extract()` body once [STACK BUMP] ships the SDK. Until then,
    every call raises — the fake adapter is the only path that produces
    `DocumentExtractionJob` instances in tests/dev.
    """

    def extract(self, request: ExtractionRequest) -> DocumentExtractionJob:  # noqa: ARG002 — interface compliance
        raise AIProviderNotConfiguredError(
            message=(
                "claude_vision adapter is a stub; "
                "enable AI_PROVIDER_ENABLED=true + wire ANTHROPIC_API_KEY, "
                "or use FakeDocumentExtractionAdapter for tests/dev."
            )
        )
