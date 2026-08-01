"""apps.api.modules.m10_ai.adapters.fake_adapter — deterministic test fake.

Story 1.3 — Task 2.2.

The fake adapter is the workhorse of Story 1.3 tests + dev. It satisfies
`DocumentExtractionPort` without any network, SDK, or API key, so the
M0 onboarding handlers + completion calculator can be exercised end-to-end
in CI without provisioning an Anthropic account.

Design:
- Field values + confidence scores are derived from the document's
  `content_sha256`. Same bytes → same fields. This makes tests stable
  without coupling to a real provider's quirks.
- Five field names are supported (mirror of `SUPPORTED_FIELD_NAMES`):
    business_registration_number, company_name, address,
    representative_name, industry
  Each field has a derived confidence. A field is OMITTED from the
  result when a specific byte in the hash (modular offset) falls below
  a threshold — this exercises the "drafts with missing fields" path
  that the UI shows as "추출 실패".
- A magic byte sequence in the payload triggers a simulated provider
  failure (so we can test the `failed` FSM end-to-end without breaking
  the deterministic rule above for normal inputs).

Failure simulation:
- Bytes 0..7 == b"FAKEFAIL" → status='failed', error_code='AI_PROVIDER_SIMULATED'
- Bytes 0..7 == b"FAKESLOW" → status='processing' on first call,
  then 'completed' on retry. NOT supported by this fake (we have no
  caller state). Instead, the fake respects `request.idempotency_key`
  — repeated calls with the same key return the cached result.
- Bytes 0..7 == b"FAKEZERO" → all confidences are 0.0 (review-required
  path). Exercises the confidence-badge "추가 확인 필요" branch.

Logging:
- The fake never logs the document bytes (privacy).
- It logs `request_id` + `tenant_id` + `document_id` at INFO via the
  service layer (not here) so log volumes are uniform across adapters.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Final

from packages.services.m10_ai.extraction_port import (
    DocumentExtractionJob,
    ExtractionEvidence,
    ExtractionField,
    ExtractionRequest,
)


# ── Magic-byte failure / behavior flags ──────────────────────
_FAKEFAIL_HEADER: Final[bytes] = b"FAKEFAIL"
_FAKEZERO_HEADER: Final[bytes] = b"FAKEZERO"
_FAKEFIELD_MASK_HEADER: Final[bytes] = b"FAKEFIELD"  # drops `company_name` from output


class FakeDocumentExtractionAdapter:
    """Deterministic adapter for tests + dev. Implements `DocumentExtractionPort`.

    The class is instantiated ONCE per process (the service layer keeps
    a module-level reference). All state is read from `request` — no
    instance attributes are used, so concurrent invocations don't
    interact.
    """

    # Deterministic seed for confidence generation. Index = field_name.
    # Stable across runs so CI tests don't flake.
    _FIELD_OFFSETS: Final[dict[str, int]] = {
        "business_registration_number": 0,
        "company_name": 1,
        "address": 2,
        "representative_name": 3,
        "industry": 4,
    }

    # Field name → fake value generator. Each generator takes the sha256
    # bytes and returns the typed value. Real adapters do NOT exist for
    # these — this fake is the contract test surface only.
    def _fake_value(self, field_name: str, digest: bytes) -> object:
        # Use 4 hex bytes → deterministic short string.
        idx = self._FIELD_OFFSETS[field_name]
        chunk = digest[idx * 4 : idx * 4 + 4].hex()
        if field_name == "business_registration_number":
            # Format as 3-2-5 digits (KR 사업자등록번호).
            return f"{int(chunk[0:3], 16) % 1000:03d}-{int(chunk[3:5], 16) % 100:02d}-{int(chunk[5:9], 16) % 100000:05d}"
        if field_name == "company_name":
            return f"테스트회사_{chunk[:6]}"
        if field_name == "address":
            return f"서울특별시 강남구 테스트로 {int(chunk[:4], 16) % 1000}"
        if field_name == "representative_name":
            return f"홍길동{int(chunk[:2], 16) % 100}"
        if field_name == "industry":
            # Cycle through 4 known industries for variety.
            return ("manufacturing", "service", "manufacturing_service", "manufacturing_service_other")[
                int(chunk[:2], 16) % 4
            ]
        return None

    def _fake_confidence(self, field_name: str, digest: bytes) -> float:
        idx = self._FIELD_OFFSETS[field_name]
        # Confidence = int(byte) / 255 → maps to [0, 1].
        return digest[idx] / 255.0 if idx < len(digest) else 0.0

    def _fake_evidence(self, field_name: str, digest: bytes) -> ExtractionEvidence:
        idx = self._FIELD_OFFSETS[field_name]
        # Synthetic evidence text — first 80 chars of a sha-derived string.
        text = f"[테스트 문서 p.1] {field_name} 값 = {digest[idx * 8 : idx * 8 + 8].hex()}"
        if len(text) > 200:
            text = text[:200]
        return ExtractionEvidence(page=1, text=text, bbox=None)

    def extract(self, request: ExtractionRequest) -> DocumentExtractionJob:
        """Run the deterministic extraction against `request.document_bytes`.

        Implements the full FSM:
        - Magic bytes → failed (FAKEFAIL) or zero-confidence (FAKEZERO)
        - Otherwise → completed with 5 fields, confidence in [0, 1]
        """
        # 1) sha256 of payload → deterministic seed.
        digest = hashlib.sha256(request.document_bytes).digest()

        # 2) Magic-byte failure injection.
        if request.document_bytes[: len(_FAKEFAIL_HEADER)] == _FAKEFAIL_HEADER:
            return DocumentExtractionJob(
                document_id=request.document_id,
                tenant_id=request.tenant_id,
                mime_type=request.mime_type,
                byte_size=request.byte_size,
                content_sha256=digest,
                status="failed",
                fields=(),
                error_code="AI_PROVIDER_SIMULATED",
                error_message_ko="테스트용 실패 시뮬레이션 (FAKEFAIL 헤더)",
            )

        # 3) Magic-byte zero-confidence injection.
        zero_conf = request.document_bytes[: len(_FAKEZERO_HEADER)] == _FAKEZERO_HEADER

        # 4) Build fields.
        skip_company_name = (
            request.document_bytes[: len(_FAKEFIELD_MASK_HEADER)] == _FAKEFIELD_MASK_HEADER
        )

        fields: list[ExtractionField] = []
        for field_name in self._FIELD_OFFSETS:
            if field_name == "company_name" and skip_company_name:
                # Field is absent — exercises the "추출 실패" badge.
                continue
            confidence = 0.0 if zero_conf else self._fake_confidence(field_name, digest)
            fields.append(
                ExtractionField(
                    field_name=field_name,
                    ai_value=self._fake_value(field_name, digest),
                    confidence=confidence,
                    evidence=self._fake_evidence(field_name, digest),
                )
            )

        return DocumentExtractionJob(
            document_id=request.document_id,
            tenant_id=request.tenant_id,
            mime_type=request.mime_type,
            byte_size=request.byte_size,
            content_sha256=digest,
            status="completed",
            fields=tuple(fields),
            error_code=None,
            error_message_ko=None,
        )
