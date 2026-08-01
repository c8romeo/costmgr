"""tests.services.test_extraction_port_contract — port + fake adapter tests.

Story 1.3 — Task 5 (port contract) + Task 2.2 (fake adapter).

Two guarantees tested:
1. SUPPORTED_FIELD_NAMES is the canonical set; field names outside it
   are dropped silently (the adapter MUST not persist unknown fields).
2. The fake adapter is DETERMINISTIC — same bytes → same fields. This
   keeps integration tests stable without coupling to a real provider.
3. The fake adapter's magic bytes (FAKEFAIL / FAKEZERO / FAKEFIELD)
   exercise the failure / zero-confidence / partial-field paths.
"""

from __future__ import annotations

import hashlib
import uuid

import pytest

from apps.api.modules.m10_ai.adapters.fake_adapter import FakeDocumentExtractionAdapter
from packages.services.m10_ai.extraction_port import (
    SUPPORTED_FIELD_NAMES,
    ExtractionEvidence,
    ExtractionField,
    ExtractionRequest,
    FieldName,
)


# ── Canonical field set ────────────────────────────────────
def test_supported_field_names_is_frozen() -> None:
    """Adding a new field requires updating SUPPORTED_FIELD_NAMES + TS mirror."""
    expected = {
        "business_registration_number",
        "company_name",
        "address",
        "representative_name",
        "industry",
    }
    assert SUPPORTED_FIELD_NAMES == frozenset(expected)
    assert isinstance(SUPPORTED_FIELD_NAMES, frozenset)


def test_field_name_enum_mirrors_supported_set() -> None:
    """FieldName enum is a 1:1 mirror of SUPPORTED_FIELD_NAMES."""
    enum_values = {member.value for member in FieldName}
    assert enum_values == SUPPORTED_FIELD_NAMES


# ── Fake adapter determinism ───────────────────────────────
def _make_request(*, payload: bytes, mime: str = "application/pdf") -> ExtractionRequest:
    return ExtractionRequest(
        tenant_id=uuid.uuid4(),
        uploaded_by=uuid.uuid4(),
        document_id=uuid.uuid4(),
        mime_type=mime,
        byte_size=len(payload),
        document_bytes=payload,
        idempotency_key=str(uuid.uuid4()),
        request_id="test-trace",
    )


def test_fake_adapter_is_deterministic_for_same_bytes() -> None:
    """Same bytes → identical field set + confidence values."""
    adapter = FakeDocumentExtractionAdapter()
    payload = b"hello deterministic world"
    a = adapter.extract(_make_request(payload=payload))
    b = adapter.extract(_make_request(payload=payload))
    assert a.status == "completed"
    assert b.status == "completed"
    assert len(a.fields) == len(b.fields) == 5
    for fa, fb in zip(a.fields, b.fields):
        assert fa.field_name == fb.field_name
        assert fa.ai_value == fb.ai_value
        assert fa.confidence == fb.confidence


def test_fake_adapter_emits_all_five_canonical_fields() -> None:
    adapter = FakeDocumentExtractionAdapter()
    payload = b"normal payload"
    job = adapter.extract(_make_request(payload=payload))
    assert job.status == "completed"
    emitted = {f.field_name for f in job.fields}
    assert emitted == SUPPORTED_FIELD_NAMES


def test_fake_adapter_fakefail_returns_failed_status() -> None:
    """Magic header → status='failed' + error_code typed."""
    adapter = FakeDocumentExtractionAdapter()
    payload = b"FAKEFAIL" + b"some content"
    job = adapter.extract(_make_request(payload=payload))
    assert job.status == "failed"
    assert job.error_code == "AI_PROVIDER_SIMULATED"
    assert job.fields == ()


def test_fake_adapter_fakezero_emits_zero_confidence() -> None:
    """Magic header → all confidence = 0.0 (review-required badge path)."""
    adapter = FakeDocumentExtractionAdapter()
    payload = b"FAKEZERO" + b"some content"
    job = adapter.extract(_make_request(payload=payload))
    assert job.status == "completed"
    assert all(f.confidence == 0.0 for f in job.fields)


def test_fake_adapter_fakefield_drops_company_name() -> None:
    """Magic header → `company_name` is OMITTED from the field set."""
    adapter = FakeDocumentExtractionAdapter()
    payload = b"FAKEFIELD" + b"some content"
    job = adapter.extract(_make_request(payload=payload))
    assert job.status == "completed"
    emitted = {f.field_name for f in job.fields}
    assert "company_name" not in emitted
    assert len(emitted) == 4


def test_fake_adapter_persists_content_sha256() -> None:
    adapter = FakeDocumentExtractionAdapter()
    payload = b"sha check"
    job = adapter.extract(_make_request(payload=payload))
    assert job.content_sha256 == hashlib.sha256(payload).digest()


# ── Frozen dataclass invariants ────────────────────────────
def test_extraction_field_is_frozen() -> None:
    field = ExtractionField(
        field_name="company_name",
        ai_value="Test Co",
        confidence=0.85,
        evidence=ExtractionEvidence(page=1, text="Test Co", bbox=None),
    )
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        field.field_name = "tampered"  # type: ignore[misc]


def test_extraction_evidence_bbox_tuple_is_jsonable() -> None:
    """bbox is `tuple[float, float, float, float] | None` — service layer
    converts to list for JSONB. The port keeps the tuple invariant."""
    ev = ExtractionEvidence(page=1, text="x", bbox=(0.1, 0.2, 0.3, 0.4))
    assert ev.bbox is not None
    assert len(ev.bbox) == 4
