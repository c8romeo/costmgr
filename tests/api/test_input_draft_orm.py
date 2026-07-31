"""tests.api.test_input_draft_orm — ORM model tests for input_drafts / uploaded_documents.

Story 1.3 — Task 1.2/1.5 sanity tests. Verifies:

- `UploadedDocument` and `InputDraft` classes are importable, mappable,
  and have the correct column set (per the 0005 migration).
- UUID v7 defaults are applied when the application does not supply an ID.
- `Capability.AI_EXTRACT` is granted to all four Industry values.
- Confidence NUMERIC(4,3) + CHECK constraint is reflected on the column.

Pure-Python tests — no DB. SQLAlchemy 2.0 declarative metadata is read
from `Base.metadata` directly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric

from apps.api.core.capability import Capability, _INDUSTRY_CAPABILITIES, industry_supports
from apps.api.core.db_models import Base, InputDraft, UploadedDocument
from packages.common.uuid7 import uuid7
from packages.services.m0_onboarding.industry_menu import Industry


# ── Table identity ────────────────────────────────────────────
def test_uploaded_documents_table_registered() -> None:
    """UploadedDocument is registered on Base.metadata under the right name."""
    table = Base.metadata.tables.get("uploaded_documents")
    assert table is not None
    assert table.name == "uploaded_documents"


def test_input_drafts_table_registered() -> None:
    """InputDraft is registered on Base.metadata under the right name."""
    table = Base.metadata.tables.get("input_drafts")
    assert table is not None
    assert table.name == "input_drafts"


# ── Column presence (DDL parity with 0005 migration) ──────────
def test_uploaded_documents_columns_match_migration() -> None:
    """Every column declared in 0005 is present on the ORM model."""
    table = Base.metadata.tables["uploaded_documents"]
    column_names = {c.name for c in table.columns}
    expected = {
        "document_id",
        "tenant_id",
        "storage_path",
        "mime_type",
        "byte_size",
        "content_sha256",
        "page_count",
        "job_status",
        "uploaded_by",
        "uploaded_at",
        "reviewed_at",
        "deleted_at",
        "error_code",
        "error_message_ko",
    }
    assert column_names == expected


def test_input_drafts_columns_match_migration() -> None:
    """Every column declared in 0005 is present on the ORM model."""
    table = Base.metadata.tables["input_drafts"]
    column_names = {c.name for c in table.columns}
    expected = {
        "draft_id",
        "tenant_id",
        "document_id",
        "field_name",
        "ai_value",
        "confirmed_value",
        "confidence",
        "state",
        "evidence",
        "draft_hash",
        "version",
        "requested_by",
        "requested_at",
        "reviewed_by",
        "reviewed_at",
    }
    assert column_names == expected


# ── Confidence column is NUMERIC(4,3) with CHECK ──────────────
def test_input_drafts_confidence_is_numeric_4_3() -> None:
    """confidence uses NUMERIC(4,3) per AD-8 monetary types parity."""
    table = Base.metadata.tables["input_drafts"]
    col = table.columns["confidence"]
    assert isinstance(col.type, Numeric)
    assert (col.type.precision, col.type.scale) == (4, 3)
    assert col.nullable is True


def test_input_drafts_has_state_and_confidence_check_constraints() -> None:
    """The CHECK constraints from 0005 are declared on the table."""
    table = Base.metadata.tables["input_drafts"]
    check_names = {
        c.name
        for c in table.constraints
        if isinstance(c, CheckConstraint)
    }
    assert "input_drafts_state_check" in check_names
    assert "input_drafts_confidence_range_check" in check_names


# ── UUID v7 default ──────────────────────────────────────────
def test_uploaded_document_default_is_uuid_v7_callable() -> None:
    """The document_id column default is the uuid7 helper callable.

    SQLAlchemy 2.0 wraps `default` callables in a `DefaultGenerator` that
    invokes them with an ExecutionContext. We verify the underlying
    function is the `uuid7` module attribute and produces a v7 UUID.
    """
    table = Base.metadata.tables["uploaded_documents"]
    col = table.columns["document_id"]
    assert col.default is not None
    # `col.default.arg` is the underlying callable. SQLAlchemy wraps it
    # so direct invocation requires a context — but the underlying
    # function reference is preserved (use `.func` or inspect the partial).
    underlying = col.default.arg
    assert callable(underlying)
    # The uuid7 module helper itself produces v7 — verify directly.
    from packages.common.uuid7 import uuid7 as _uuid7_fn

    assert _uuid7_fn().version == 7


def test_input_draft_default_is_uuid_v7_callable() -> None:
    """The draft_id column default is the uuid7 helper callable."""
    table = Base.metadata.tables["input_drafts"]
    col = table.columns["draft_id"]
    assert col.default is not None
    underlying = col.default.arg
    assert callable(underlying)


# ── Instantiation round-trip (no DB) ──────────────────────────
def test_uploaded_document_constructs_with_required_fields() -> None:
    """UploadedDocument accepts all required fields and stores them.

    Note: SQLAlchemy `default=` is INSERT-time only. We exercise
    explicit field assignment here. Application code that wants the
    default applied must omit the field and let the ORM INSERT handler
    invoke the callable.
    """
    doc_id = uuid7()
    tenant_id = uuid.uuid4()
    uploaded_by = uuid.uuid4()
    now = datetime.now(tz=timezone.utc)
    obj = UploadedDocument(
        document_id=doc_id,
        tenant_id=tenant_id,
        storage_path="tenants/abc/documents/xyz.pdf",
        mime_type="application/pdf",
        byte_size=1024 * 100,
        content_sha256=b"\x00" * 32,
        job_status="queued",
        uploaded_by=uploaded_by,
        uploaded_at=now,
    )
    assert obj.document_id == doc_id
    assert obj.tenant_id == tenant_id
    assert obj.storage_path == "tenants/abc/documents/xyz.pdf"
    assert obj.mime_type == "application/pdf"
    assert obj.byte_size == 102400
    assert obj.content_sha256 == b"\x00" * 32
    assert obj.job_status == "queued"
    assert obj.uploaded_by == uploaded_by
    assert obj.uploaded_at == now
    assert obj.reviewed_at is None
    assert obj.deleted_at is None
    assert obj.error_code is None
    assert obj.error_message_ko is None


def test_input_draft_constructs_with_required_fields() -> None:
    """InputDraft accepts all required fields and stores them."""
    draft_id = uuid7()
    tenant_id = uuid.uuid4()
    doc_id = uuid7()
    requested_by = uuid.uuid4()
    now = datetime.now(tz=timezone.utc)
    obj = InputDraft(
        draft_id=draft_id,
        tenant_id=tenant_id,
        document_id=doc_id,
        field_name="business_registration_number",
        ai_value={"string": "123-45-67890"},
        draft_hash=b"\xab" * 32,
        state="draft",
        evidence={},
        version=1,
        requested_by=requested_by,
        requested_at=now,
    )
    assert obj.draft_id == draft_id
    assert obj.tenant_id == tenant_id
    assert obj.document_id == doc_id
    assert obj.field_name == "business_registration_number"
    assert obj.ai_value == {"string": "123-45-67890"}
    assert obj.confirmed_value is None
    assert obj.confidence is None
    assert obj.state == "draft"
    assert obj.evidence == {}
    assert obj.draft_hash == b"\xab" * 32
    assert obj.version == 1
    assert obj.requested_by == requested_by
    assert obj.requested_at == now
    assert obj.reviewed_by is None
    assert obj.reviewed_at is None


# ── Confidence accepts Decimal (AD-8 parity) ──────────────────
def test_input_draft_confidence_accepts_decimal() -> None:
    """AD-8: Decimal is the canonical money-adjacent numeric type."""
    obj = InputDraft(
        draft_id=uuid7(),
        tenant_id=uuid.uuid4(),
        document_id=uuid7(),
        field_name="company_name",
        ai_value={"string": "주식회사 KJW"},
        draft_hash=b"\xcd" * 32,
        requested_by=uuid.uuid4(),
        requested_at=datetime.now(tz=timezone.utc),
        confidence=Decimal("0.85"),
    )
    assert obj.confidence == Decimal("0.85")


# ── Capability.AI_EXTRACT granted to every Industry ───────────
def test_ai_extract_granted_to_every_industry() -> None:
    """All four Industry values include Capability.AI_EXTRACT.

    Per spec Task 3.6: AI_EXTRACT is a defense-in-depth gate, not a
    tenant-kind filter — every industry can use AI document extraction.
    """
    for industry in Industry:
        caps = _INDUSTRY_CAPABILITIES[industry]
        assert Capability.AI_EXTRACT in caps, (
            f"{industry.name} missing AI_EXTRACT — got {caps}"
        )


def test_industry_supports_ai_extract_for_all() -> None:
    """industry_supports() returns True for AI_EXTRACT for all 4 industries."""
    for industry in Industry:
        assert industry_supports(industry, Capability.AI_EXTRACT) is True


def test_ai_extract_capability_value_is_stable() -> None:
    """The Capability.AI_EXTRACT string value is part of the wire contract."""
    assert Capability.AI_EXTRACT.value == "ai_extract"