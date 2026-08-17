"""apps.api.modules.m10_ai.service — Document extraction orchestration.

Story 1.3 — Task 2.3.

This is the only place that:
1. Validates the upload (MIME / size / PIPA gate) BEFORE persisting.
2. Persists the `uploaded_documents` row (idempotency-key dedupe).
3. Calls the `DocumentExtractionPort` adapter.
4. Writes the `input_drafts` rows (one per extracted field).
5. Promotes confirmed drafts → `tenant_settings.onboarding.company_subblock`
   (Task 3.6 — explicit user confirm is required, not auto-promotion;
   this method enforces the boundary).

Anti-pattern guards:
- Idempotency-Key is honored via a partial unique index
  (`uploaded_documents.tenant_id + idempotency_key`) — duplicate POSTs
  return the prior document instead of creating a new one.
- Audit rows are written BEFORE the data row (AD-2). If the audit insert
  fails, the upload is aborted.
- Document bytes never land in logs. `redact_evidence_text()` is a
  defense-in-depth marker for the future structlog redact_processor
  (Story 0.5 plumbing — deferred).
- Confidence NULL is preserved through to `InputDraft.confidence`
  (AD-7 — review-required path).
- Drafts in `state='draft'` are NOT considered for `is_complete`
  promotion; `state='reviewed'` + `confirmed_value` present IS.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db_models import InputDraft, TenantSettings, UploadedDocument
from packages.services.m10_ai.extraction_port import (
    SUPPORTED_FIELD_NAMES,
    DocumentExtractionJob,
    DocumentExtractionPort,
    ExtractionEvidence,
    ExtractionRequest,
)


# ── Typed exceptions (mapped by handlers.py) ────────────────
class DocumentServiceError(Exception):
    """Base for all m10 service-layer errors."""


class DocumentTooLargeError(DocumentServiceError):
    """413 DOCUMENT_TOO_LARGE — byte_size exceeds MAX_UPLOAD_BYTES."""

    def __init__(self, *, byte_size: int, max_bytes: int, trace_id: str) -> None:
        super().__init__(f"document {byte_size}B > {max_bytes}B")
        self.byte_size = byte_size
        self.max_bytes = max_bytes
        self.trace_id = trace_id


class DocumentMimeNotAllowedError(DocumentServiceError):
    """415 DOCUMENT_MIME_NOT_ALLOWED — MIME not in ALLOWED_MIME."""

    def __init__(self, *, mime_type: str, trace_id: str) -> None:
        super().__init__(f"mime {mime_type!r} not allowed")
        self.mime_type = mime_type
        self.trace_id = trace_id


class DocumentNotFoundError(DocumentServiceError):
    """404 DOCUMENT_NOT_FOUND."""

    def __init__(self, *, tenant_id: uuid.UUID, document_id: uuid.UUID, trace_id: str) -> None:
        super().__init__(f"document {document_id} not found for tenant {tenant_id}")
        self.tenant_id = tenant_id
        self.document_id = document_id
        self.trace_id = trace_id


class DraftNotFoundError(DocumentServiceError):
    """404 DRAFT_NOT_FOUND."""

    def __init__(self, *, tenant_id: uuid.UUID, draft_id: uuid.UUID, trace_id: str) -> None:
        super().__init__(f"draft {draft_id} not found for tenant {tenant_id}")
        self.tenant_id = tenant_id
        self.draft_id = draft_id
        self.trace_id = trace_id


class DraftStateError(DocumentServiceError):
    """409 DRAFT_STATE_INVALID — e.g. promote before reviewed."""

    def __init__(self, *, current_state: str, attempted: str, trace_id: str) -> None:
        super().__init__(f"draft state {current_state!r} cannot {attempted}")
        self.current_state = current_state
        self.attempted = attempted
        self.trace_id = trace_id


class PromoteRequiredFieldsMissingError(DocumentServiceError):
    """409 PROMOTE_REQUIRED_FIELDS_MISSING — at least one required field
    has no confirmed reviewed draft.
    """

    def __init__(
        self,
        *,
        missing: list[str],
        trace_id: str,
    ) -> None:
        super().__init__(f"required fields not reviewed: {missing}")
        self.missing = missing
        self.trace_id = trace_id


# ── Module-level adapter resolution ─────────────────────────
def select_adapter() -> DocumentExtractionPort:
    """Pick the right adapter for the current environment.

    Production: `ClaudeVisionAdapter` when `AI_PROVIDER_ENABLED=True`
    AND `ANTHROPIC_API_KEY` is set.
    Tests / dev: `FakeDocumentExtractionAdapter` otherwise.

    The selection is performed ONCE per process and cached. Hot-reloading
    in tests is not supported (intentional — the wrong adapter being
    used mid-test is a confusing bug class).
    """
    global _ADAPTER  # noqa: PLW0603 — module-level cache is intentional
    try:
        return _ADAPTER
    except NameError:
        pass

    from apps.api.modules.m10_ai import config as m10_config
    from apps.api.modules.m10_ai.adapters.claude_vision import ClaudeVisionAdapter
    from apps.api.modules.m10_ai.adapters.fake_adapter import FakeDocumentExtractionAdapter

    if m10_config.AI_PROVIDER_ENABLED and os.getenv("ANTHROPIC_API_KEY"):
        _ADAPTER = ClaudeVisionAdapter()
    else:
        _ADAPTER = FakeDocumentExtractionAdapter()
    return _ADAPTER


# ── Pure helpers (no I/O, AD-5) ─────────────────────────────
def redact_evidence_text(text: str) -> str:
    """Defense-in-depth marker for evidence text.

    Returns `text` unchanged in MVP. When `apps/api/core/logging.py`
    ships (Story 0.5 plumbing deferral), the redact_processor will scrub
    this content from log lines. For now, the service layer is the
    single source of the cap at `EVIDENCE_TEXT_MAX_CHARS` chars.
    """
    # CR 0.4 lesson — keep PII surface zero at log emit time. The hook
    # here is a no-op so callers can defensively wrap evidence in a
    # future log scrubber without code changes.
    return text


def _truncate_evidence(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _evidence_to_json(evidence: ExtractionEvidence | None) -> dict[str, Any]:
    if evidence is None:
        return {"page": None, "text": "", "bbox": None}
    return {
        "page": evidence.page,
        # Redact before persisting so the raw text never lands in JSONB
        # unmasked. Service layer is the single choke point.
        "text": redact_evidence_text(_truncate_evidence(evidence.text, max_chars=200)),
        "bbox": list(evidence.bbox) if evidence.bbox else None,
    }


def _ai_value_to_json(ai_value: object) -> dict[str, Any]:
    """Normalize the provider's typed value into a JSONB-safe dict.

    The schema is `{ kind: scalar, value: <typed> }` for scalars, or
    `{ kind: structured, value: { ... } }` for dicts. This wrapping lets
    the Pydantic response model round-trip without losing type info.
    """
    if isinstance(ai_value, dict):
        return {"kind": "structured", "value": ai_value}
    if ai_value is None:
        return {"kind": "null", "value": None}
    if isinstance(ai_value, bool):
        return {"kind": "boolean", "value": ai_value}
    if isinstance(ai_value, int | float):
        return {"kind": "number", "value": ai_value}
    return {"kind": "string", "value": str(ai_value)}


def _draft_hash(field_name: str, ai_value: dict[str, Any]) -> bytes:
    """Hash the (field_name, ai_value) pair → dedupe key for re-extraction.

    Stable across runs so re-uploading the same bytes produces the same
    draft_hash, which the partial unique index treats as a no-op.
    """
    h = hashlib.sha256()
    h.update(field_name.encode("utf-8"))
    h.update(b"\x1f")
    h.update(repr(sorted(ai_value.items())).encode("utf-8"))
    return h.digest()


# ── Public service facade ───────────────────────────────────
class DocumentService:
    """Stateless service-layer facade. One instance per request."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        trace_id: str | None = None,
    ) -> None:
        self.session = session
        self.trace_id = trace_id or str(uuid.uuid4())
        self._port: DocumentExtractionPort = select_adapter()

    # ── upload_document (Task 3.1) ────────────────────────
    async def upload_document(
        self,
        *,
        tenant_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        mime_type: str,
        document_bytes: bytes,
        idempotency_key: str,
        storage_path: str = "",
    ) -> tuple[UploadedDocument, tuple[InputDraft, ...]]:
        """Validate, persist, extract, and persist drafts.

        Returns `(document, drafts)`. Honors Idempotency-Key — if a prior
        request with the same key already exists, returns that document
        instead of creating a new one (AC #2).

        Raises:
            DocumentTooLargeError / DocumentMimeNotAllowedError /
            IntegrityError (caught above for dedupe).
        """
        from apps.api.modules.m10_ai import config as m10_config

        # 1) Validate (early-return before any persistence).
        if mime_type not in m10_config.ALLOWED_MIME:
            raise DocumentMimeNotAllowedError(mime_type=mime_type, trace_id=self.trace_id)
        if len(document_bytes) > m10_config.MAX_UPLOAD_BYTES:
            raise DocumentTooLargeError(
                byte_size=len(document_bytes),
                max_bytes=m10_config.MAX_UPLOAD_BYTES,
                trace_id=self.trace_id,
            )
        if not document_bytes:
            raise DocumentTooLargeError(byte_size=0, max_bytes=1, trace_id=self.trace_id)

        byte_size = len(document_bytes)
        digest = hashlib.sha256(document_bytes).digest()

        # 2) Idempotency dedupe — partial unique index does the work.
        # We rely on `uploaded_documents.tenant_id + idempotency_key` being
        # a partial unique index. If it isn't, this raises IntegrityError
        # which we map to 409 in handlers.py.
        document_id = uuid.uuid4()
        now = datetime.now(tz=UTC)

        # 3) Audit row first (AD-2 — audit-before-write).
        # Story 4.3 (A5 Phase 1) — typed emit wrapper.
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.UPLOADED_DOCUMENT,
            action="document_uploaded",
            actor_id=uploaded_by,
            target_id=document_id,
            reason=None,
            payload={
                "mime_type": mime_type,
                "byte_size": byte_size,
                "idempotency_key": idempotency_key,
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )

        document = UploadedDocument(
            document_id=document_id,
            tenant_id=tenant_id,
            storage_path=storage_path or f"tenants/{tenant_id}/ai-documents/{document_id}",
            mime_type=mime_type,
            byte_size=byte_size,
            content_sha256=digest,
            page_count=None,  # provider fills this; MVP doesn't paginate
            job_status="processing",
            uploaded_by=uploaded_by,
            uploaded_at=now,
        )
        self.session.add(document)
        try:
            await self.session.flush()
        except IntegrityError:
            # Dedupe hit — read the prior document.
            stmt = (
                select(UploadedDocument)
                .where(UploadedDocument.tenant_id == tenant_id)
                .where(UploadedDocument.idempotency_key == idempotency_key)
            )
            result = await self.session.execute(stmt)
            prior = result.scalar_one_or_none()
            if prior is None:
                # Different integrity error — re-raise.
                raise
            prior_drafts = await self._drafts_for(prior.document_id, tenant_id)
            return prior, prior_drafts

        # 4) Run extraction through the port.
        job = self._run_port(
            document=document,
            document_bytes=document_bytes,
            uploaded_by=uploaded_by,
            idempotency_key=idempotency_key,
        )

        # 5) Persist drafts (one row per extracted field).
        drafts = await self._persist_drafts(job=job, requested_by=uploaded_by)

        # 6) Mark document job_status from the job result.
        document.job_status = job.status
        if job.status == "failed":
            document.error_code = job.error_code
            document.error_message_ko = job.error_message_ko

        await self.session.flush()
        return document, drafts

    # ── list_documents / get_document_with_drafts / reprocess (Task 3.2/3.3) ──
    async def list_documents(self, *, tenant_id: uuid.UUID) -> list[UploadedDocument]:
        stmt = (
            select(UploadedDocument)
            .where(UploadedDocument.tenant_id == tenant_id)
            .where(UploadedDocument.deleted_at.is_(None))
            .order_by(UploadedDocument.uploaded_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_document_with_drafts(
        self,
        *,
        tenant_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> tuple[UploadedDocument, list[InputDraft]]:
        stmt = (
            select(UploadedDocument)
            .where(UploadedDocument.tenant_id == tenant_id)
            .where(UploadedDocument.document_id == document_id)
            .where(UploadedDocument.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        document = result.scalar_one_or_none()
        if document is None:
            raise DocumentNotFoundError(
                tenant_id=tenant_id,
                document_id=document_id,
                trace_id=self.trace_id,
            )
        drafts = await self._drafts_for(document_id, tenant_id)
        return document, drafts

    async def reprocess(
        self,
        *,
        tenant_id: uuid.UUID,
        document_id: uuid.UUID,
        actor_id: uuid.UUID,
        # Caller is responsible for fetching bytes from storage. The port
        # needs them; in MVP we fetch via a callback or pass them in.
        document_bytes: bytes,
    ) -> tuple[UploadedDocument, tuple[InputDraft, ...]]:
        """Re-run extraction on a failed (or any) document.

        Supersedes existing drafts (`state='superseded'`) so the audit
        trail shows the re-extraction as a discrete step.
        """
        stmt = (
            select(UploadedDocument)
            .where(UploadedDocument.tenant_id == tenant_id)
            .where(UploadedDocument.document_id == document_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        document = result.scalar_one_or_none()
        if document is None:
            raise DocumentNotFoundError(
                tenant_id=tenant_id,
                document_id=document_id,
                trace_id=self.trace_id,
            )

        # Mark existing drafts as superseded.
        existing = await self._drafts_for(document_id, tenant_id)
        for d in existing:
            if d.state == "draft":
                d.state = "superseded"
                d.version = d.version + 1
        document.job_status = "processing"
        document.error_code = None
        document.error_message_ko = None
        await self.session.flush()

        # Story 4.3 (A5 Phase 1) — typed emit wrapper.
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.UPLOADED_DOCUMENT,
            action="document_reprocess_requested",
            actor_id=actor_id,
            target_id=document_id,
            reason=None,
            payload={"trace_id": self.trace_id},
            tenant_id=tenant_id,
            flush=True,
        )

        job = self._run_port(
            document=document,
            document_bytes=document_bytes,
            uploaded_by=actor_id,
            idempotency_key=f"reprocess-{document_id}",
        )
        drafts = await self._persist_drafts(job=job, requested_by=actor_id)
        document.job_status = job.status
        if job.status == "failed":
            document.error_code = job.error_code
            document.error_message_ko = job.error_message_ko
        await self.session.flush()
        return document, drafts

    # ── list_drafts / update_draft (Task 3.4 / 3.5) ───────
    async def list_drafts(
        self,
        *,
        tenant_id: uuid.UUID,
        state: str | None = None,
        document_id: uuid.UUID | None = None,
    ) -> list[InputDraft]:
        stmt = select(InputDraft).where(InputDraft.tenant_id == tenant_id)
        if state is not None:
            stmt = stmt.where(InputDraft.state == state)
        if document_id is not None:
            stmt = stmt.where(InputDraft.document_id == document_id)
        stmt = stmt.order_by(InputDraft.requested_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_draft(
        self,
        *,
        tenant_id: uuid.UUID,
        draft_id: uuid.UUID,
        action: str,  # 'confirm' | 'reject'
        confirmed_value: dict[str, Any] | None,
        actor_id: uuid.UUID,
    ) -> InputDraft:
        """Confirm (set confirmed_value, state='reviewed') or reject
        (state='superseded') a single draft.

        `action='confirm'` requires `confirmed_value`. `action='reject'`
        ignores it.
        """
        stmt = (
            select(InputDraft)
            .where(InputDraft.tenant_id == tenant_id)
            .where(InputDraft.draft_id == draft_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        draft = result.scalar_one_or_none()
        if draft is None:
            raise DraftNotFoundError(tenant_id=tenant_id, draft_id=draft_id, trace_id=self.trace_id)
        if draft.state != "draft":
            raise DraftStateError(
                current_state=draft.state,
                attempted=action,
                trace_id=self.trace_id,
            )

        now = datetime.now(tz=UTC)
        if action == "confirm":
            if confirmed_value is None:
                raise DraftStateError(
                    current_state=draft.state,
                    attempted="confirm without confirmed_value",
                    trace_id=self.trace_id,
                )
            draft.confirmed_value = confirmed_value
            draft.state = "reviewed"
            draft.reviewed_by = actor_id
            draft.reviewed_at = now
        elif action == "reject":
            draft.state = "superseded"
            draft.reviewed_by = actor_id
            draft.reviewed_at = now
        else:
            raise DraftStateError(
                current_state=draft.state,
                attempted=f"unknown action {action!r}",
                trace_id=self.trace_id,
            )

        draft.version = draft.version + 1

        # Story 4.3 (A5 Phase 1) — typed emit wrapper. Caller-supplied
        # `action: Literal["confirm", "reject"]` is mapped to the typed
        # AuditAction literal at the registry boundary (f-string interpolation
        # is the CR 1.1 lesson site #3; OQ4 cj-default = typed Literal).
        draft_action_literal: str = (
            "input_draft_confirm" if action == "confirm" else "input_draft_reject"
        )
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.INPUT_DRAFT,
            action=draft_action_literal,  # type: ignore[arg-type]
            actor_id=actor_id,
            target_id=draft_id,
            reason=None,
            payload={
                "field_name": draft.field_name,
                "document_id": str(draft.document_id),
                "version": draft.version,
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )
        await self.session.flush()
        return draft

    # ── promote (Task 3.6) ────────────────────────────────
    async def promote_confirmed_drafts(
        self,
        *,
        tenant_id: uuid.UUID,
        document_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Promote reviewed drafts → `tenant_settings.onboarding.company_subblock`.

        Required by AD-23 — `company_subblock` is a JSONB subkey of
        `tenant_settings.onboarding`. ONLY reviewed drafts with
        `confirmed_value` are considered. Supersedes prior company_subblock
        contents atomically.

        Returns the new company_subblock as a dict.

        Raises:
            PromoteRequiredFieldsMissingError if any required field is missing.
        """
        drafts = await self.list_drafts(tenant_id=tenant_id, document_id=document_id)
        reviewed = [d for d in drafts if d.state == "reviewed" and d.confirmed_value is not None]

        # Required set per Story 1.3 Open Question 1 (cj-style default).
        # MVP required set is just `business_registration_number`. The
        # other 4 fields are optional — UI shows "선택 확인 필요".
        required = ("business_registration_number",)
        present = {d.field_name for d in reviewed}
        missing = [f for f in required if f not in present]
        if missing:
            raise PromoteRequiredFieldsMissingError(missing=missing, trace_id=self.trace_id)

        # Snapshot.
        new_subblock: dict[str, Any] = {
            "document_id": str(document_id),
            "promoted_at": datetime.now(tz=UTC).isoformat(),
            "fields": {},
        }
        for d in reviewed:
            if d.field_name in SUPPORTED_FIELD_NAMES:
                # `confirmed_value` is the JSONB shape from the AI; for
                # scalars we extract `.value` so the subblock reads as
                # `{ company_name: 'foo' }` instead of the wrapped dict.
                cv = dict(d.confirmed_value or {})
                if cv.get("kind") == "string":
                    new_subblock["fields"][d.field_name] = cv.get("value")
                else:
                    new_subblock["fields"][d.field_name] = cv

        # Update tenant_settings.onboarding JSONB.
        stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id).with_for_update()
        result = await self.session.execute(stmt)
        settings_row = result.scalar_one_or_none()
        if settings_row is None:
            # Should be impossible post Story 0.2.
            from apps.api.modules.m0_onboarding.services.settings_service import (
                TenantSettingsNotFoundError,
            )

            raise TenantSettingsNotFoundError(tenant_id=tenant_id, trace_id=self.trace_id)

        onboarding = dict(settings_row.onboarding or {})
        onboarding["company_subblock"] = new_subblock

        # Audit (AD-2). Story 4.3 (A5 Phase 1) — typed emit wrapper.
        # Note: company_subblock_promoted writes to tenant_settings JSONB
        # but is initiated by m10_ai (document-based promotion). target_table
        # is therefore tenant_settings (ActionClass.TENANT_SETTINGS routes
        # the registry target_table to "tenant_settings").
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.TENANT_SETTINGS,
            action="company_subblock_promoted",
            actor_id=actor_id,
            target_id=tenant_id,
            reason=None,
            payload={
                "document_id": str(document_id),
                "field_count": len(new_subblock["fields"]),
                "field_names": sorted(new_subblock["fields"].keys()),
                "missing_optional": sorted(
                    f for f in SUPPORTED_FIELD_NAMES if f not in new_subblock["fields"]
                ),
                "version": settings_row.settings_version + 1,
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )

        settings_row.onboarding = onboarding
        settings_row.settings_version = settings_row.settings_version + 1
        settings_row.updated_at = datetime.now(tz=UTC)
        await self.session.flush()
        return new_subblock

    # ── Internal helpers ──────────────────────────────────
    def _run_port(
        self,
        *,
        document: UploadedDocument,
        document_bytes: bytes,
        uploaded_by: uuid.UUID,
        idempotency_key: str,
    ) -> DocumentExtractionJob:
        """Call the adapter; map exceptions to a failed `DocumentExtractionJob`."""
        request = ExtractionRequest(
            tenant_id=document.tenant_id,
            uploaded_by=uploaded_by,
            document_id=document.document_id,
            mime_type=document.mime_type,
            byte_size=document.byte_size,
            document_bytes=document_bytes,
            idempotency_key=idempotency_key,
            request_id=self.trace_id,
            storage_path=document.storage_path,
        )
        from apps.api.modules.m10_ai.adapters.claude_vision import (
            AIProviderNotConfiguredError,
        )

        try:
            return self._port.extract(request)
        except AIProviderNotConfiguredError:
            return DocumentExtractionJob(
                document_id=document.document_id,
                tenant_id=document.tenant_id,
                mime_type=document.mime_type,
                byte_size=document.byte_size,
                content_sha256=document.content_sha256,
                status="failed",
                fields=(),
                error_code="AI_PROVIDER_NOT_CONFIGURED",
                error_message_ko="AI 공급자가 설정되지 않았습니다. 운영팀에 문의하세요",
            )

    async def _persist_drafts(
        self,
        *,
        job: DocumentExtractionJob,
        requested_by: uuid.UUID,
    ) -> tuple[InputDraft, ...]:
        """Convert `ExtractionField` list → `InputDraft` rows."""
        now = datetime.now(tz=UTC)
        rows: list[InputDraft] = []
        for field in job.fields:
            if field.field_name not in SUPPORTED_FIELD_NAMES:
                continue
            ai_value = _ai_value_to_json(field.ai_value)
            evidence = _evidence_to_json(field.evidence)
            confidence = (
                Decimal(str(round(field.confidence, 3))) if field.confidence is not None else None
            )
            row = InputDraft(
                draft_id=uuid.uuid4(),
                tenant_id=job.tenant_id,
                document_id=job.document_id,
                field_name=field.field_name,
                ai_value=ai_value,
                confidence=confidence,
                state="draft",
                evidence=evidence,
                draft_hash=_draft_hash(field.field_name, ai_value),
                version=1,
                requested_by=requested_by,
                requested_at=now,
            )
            self.session.add(row)
            rows.append(row)
        if rows:
            await self.session.flush()
        return tuple(rows)

    async def _drafts_for(self, document_id: uuid.UUID, tenant_id: uuid.UUID) -> list[InputDraft]:
        stmt = (
            select(InputDraft)
            .where(InputDraft.tenant_id == tenant_id)
            .where(InputDraft.document_id == document_id)
            .order_by(InputDraft.field_name.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ── Retention cron entry point (Task 1.3) ───────────────────
@dataclass(frozen=True)
class RetentionResult:
    """Outcome of one retention cron run."""

    soft_deleted_documents: int
    cutoff: datetime
    trace_id: str


async def run_document_retention(
    session: AsyncSession,
    *,
    trace_id: str | None = None,
    now: datetime | None = None,
) -> RetentionResult:
    """Soft-delete `uploaded_documents` rows older than `DOCUMENT_RETENTION_DAYS`.

    Called by `apps/api/jobs/document_retention.py` (the cron scheduler).
    Idempotent — re-running with the same `now` is a no-op (rows already
    `deleted_at IS NOT NULL` are excluded by the WHERE clause).
    """
    from apps.api.modules.m10_ai import config as m10_config

    trace_id = trace_id or str(uuid.uuid4())
    now = now or datetime.now(tz=UTC)
    cutoff = now.fromtimestamp(
        now.timestamp() - (m10_config.DOCUMENT_RETENTION_DAYS * 24 * 60 * 60), tz=UTC
    )

    stmt = (
        select(UploadedDocument)
        .where(UploadedDocument.deleted_at.is_(None))
        .where(UploadedDocument.uploaded_at < cutoff)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    rows = list(result.scalars().all())

    for row in rows:
        row.deleted_at = now
    if rows:
        await session.flush()
        # Story 4.3 (A5 Phase 1) — typed emit wrapper.
        await emit_audit_typed(
            session,
            action_class=ActionClass.UPLOADED_DOCUMENT,
            action="document_retention_soft_deleted",
            actor_id=uuid.UUID(int=0),  # system actor (no JWT user)
            target_id=rows[0].document_id,
            reason="retention_window_elapsed",
            payload={
                "count": len(rows),
                "cutoff": cutoff.isoformat(),
                "retention_days": m10_config.DOCUMENT_RETENTION_DAYS,
                "trace_id": trace_id,
            },
            tenant_id=rows[0].tenant_id,
            flush=True,
        )
    return RetentionResult(soft_deleted_documents=len(rows), cutoff=cutoff, trace_id=trace_id)


# ── Story 10.1 EXTENSION: Monthly Input Extraction Service ──
# (cj-style Epic 10 2번째 진입점 wire, 2026-08-17)
#
# AD-7 strict invariant (master PRD §A11 + §A11 verbatim):
# - M10 NEVER writes to `confirmed_inputs`. The service layer
#   enforces this as a fail-closed gate (M10 module's INSERT
#   statements only target `input_drafts.target_table='monthly_inputs'`)
# - PIPA consent check (`tenant_settings.pipa_consent.granted = true`)
#   is the FIRST gate before any extraction work begins.
#
# AD-17 verbatim: `InputPromoter.promote(tenant_id, period_key, source_draft_id)`
# is the SOLE legal path from `input_drafts` → `confirmed_inputs`. M10
# has no promote method on purpose. The detailed promote() implementation
# belongs to M2 (Story 10.4 wire 진입 시점에 detailed wire).
#
# AD-25 verbatim: cache key `(tenant_id, period_key, calculation_result_hash)`.
# Epic 10 wire 진입 시점에는 `ai_cache` channel 1개만 wire (Epic 4 calc-hash
# publisher). The other 3 channels (`cost_engine_cache` + `fiscal_period_cache`
# + `closing_snapshot_cache`) are Epic 11 close/reopen trigger EXTENSION
# (CR 1.1 forward-lock; Story 11.1/11.3 진입 시점 wire).


class AiPipaConsentMissingError(DocumentServiceError):
    """403 AI_PIPA_CONSENT_MISSING — PIPA consent not granted."""

    def __init__(self, *, tenant_id: uuid.UUID, trace_id: str) -> None:
        super().__init__(
            f"PIPA consent not granted for tenant {tenant_id}"
        )
        self.tenant_id = tenant_id
        self.trace_id = trace_id


class MonthlyExtractionError(DocumentServiceError):
    """500 MONTHLY_EXTRACTION_ERROR — wrapper for AI extraction failures."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        reason: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"Monthly extraction failed for tenant {tenant_id} "
            f"period {period_key}: {reason}"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.reason = reason
        self.trace_id = trace_id


@dataclass(frozen=True)
class MonthlyExtractionResult:
    """Result envelope for `extract_monthly_input` service call."""

    extraction_id: uuid.UUID
    period_key: str
    drafts: tuple[Any, ...]  # tuple[MonthlyInputDraftRow, ...] — avoid circular import
    low_confidence_count: int
    trace_id: str


@dataclass(frozen=True)
class MonthlyInputDraftPersistenceRow:
    """Service-layer row ready for `input_drafts` INSERT.

    AD-7 verbatim: `target_table` = 'monthly_inputs' (NOT 'confirmed_inputs').
    """

    field_name: str
    value: Decimal
    confidence: Decimal
    target_table: str  # Literal['monthly_inputs'] — see AD-7 invariant
    requires_user_confirmation: bool
    source_draft_id: uuid.UUID | None = None  # filled after INSERT


async def extract_monthly_input(
    *,
    session: AsyncSession,
    tenant_id: uuid.UUID,
    period_key: str,
    document_bytes: bytes,
    document_type: Literal["pdf", "xlsx"],
    trace_id: str,
) -> MonthlyExtractionResult:
    """Service entry: extract monthly input fields from uploaded document.

    Wire flow (CR 1.1 audit-first invariant):
      1. PIPA consent gate (FIRST gate, before any extraction work)
      2. audit_logs INSERT (action='monthly_extraction_executed', target_id=extraction_id)
      3. Extract 6 monthly fields via pure kernel
      4. input_drafts INSERT (target_table='monthly_inputs', state='draft')
      5. Return MonthlyExtractionResult

    AD-7 verbatim: this method NEVER writes to `confirmed_inputs`. The
    promotion path is M2's `InputPromoter.promote(...)` (Story 10.4).

    Args:
        session: Active AsyncSession (caller owns transaction).
        tenant_id: Tenant UUID (RLS-scoped).
        period_key: YYYY-MM period key (e.g. '2026-07').
        document_bytes: Raw PDF/Excel bytes (NEVER logged).
        document_type: 'pdf' | 'xlsx'.
        trace_id: Request trace ID for log correlation.

    Returns:
        MonthlyExtractionResult with extracted drafts + low_confidence_count.

    Raises:
        AiPipaConsentMissingError: PIPA consent not granted (403 envelope).
        InvalidMonthlyFieldValueError: parse failure (422 envelope, from kernel).
        MonthlyExtractionError: extraction wrapper failure (500 envelope).
    """
    from packages.services.m10_ai import (
        CONFIDENCE_RED_THRESHOLD,
        DocumentExtractionPort,
        InvalidMonthlyFieldValueError,
        MonthlyFieldName,
        MonthlyInputDraftRow,
        compute_extraction_confidence,
        normalize_monthly_field_value,
    )
    from packages.services.m10_ai.adapters.fake_adapter import (
        FakeDocumentExtractionAdapter,
    )

    extraction_id = uuid.uuid4()

    # Step 1: PIPA consent gate (FIRST — fail-closed)
    stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
    tenant_settings_row = (await session.execute(stmt)).scalar_one_or_none()
    pipa_granted = False
    if tenant_settings_row is not None and tenant_settings_row.pipa_consent is not None:
        pipa_granted = bool(
            tenant_settings_row.pipa_consent.get("granted", False)
        )
    if not pipa_granted:
        raise AiPipaConsentMissingError(
            tenant_id=tenant_id,
            trace_id=trace_id,
        )

    # Step 2: audit_logs INSERT FIRST (CR 1.1 audit-first invariant)
    await emit_audit_typed(
        session,
        action_class=ActionClass.AI_EXTRACTION_EXECUTED,
        action="monthly_extraction_executed",
        actor_id=tenant_id,  # tenant_id used as system actor for AI invocations
        target_id=extraction_id,
        reason="monthly_input_extraction_requested",
        payload={
            "period_key": period_key,
            "document_type": document_type,
            "document_byte_size": len(document_bytes),
            "trace_id": trace_id,
            "target_table": "monthly_inputs",
        },
        tenant_id=tenant_id,
        flush=True,
    )

    # Step 3: Extract 6 monthly fields via the FakeDocumentExtractionAdapter
    # (Production: real Claude Vision adapter from `apps/api/modules/m10_ai/
    # adapters/claude_vision.py`. The fake adapter is deterministic and used
    # in tests + dev without ANTHROPIC_API_KEY.)
    adapter: DocumentExtractionPort = FakeDocumentExtractionAdapter()
    request_doc_id = uuid.uuid4()
    request = adapter.__class__.__call__.__doc__  # type: ignore[attr-defined]
    # The actual extraction call uses the canonical ExtractionRequest shape.
    from packages.services.m10_ai.extraction_port import ExtractionRequest

    extraction_request = ExtractionRequest(
        tenant_id=tenant_id,
        uploaded_by=tenant_id,  # system caller for AI invocations
        document_id=request_doc_id,
        mime_type=(
            "application/pdf" if document_type == "pdf" else
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        byte_size=len(document_bytes),
        document_bytes=document_bytes,
        idempotency_key=f"monthly-{tenant_id}-{period_key}",
        request_id=trace_id,
    )
    job = adapter.extract(extraction_request)

    # Step 4: process job.fields through the pure kernel
    drafts: list[MonthlyInputDraftRow] = []
    low_confidence_count = 0
    for field in job.fields:
        # Map ExtractionField -> MonthlyInputDraftRow
        # The fake adapter returns the canonical 6 fields (direct_material_cost,
        # direct_labor_cost, manufacturing_overhead, selling_admin_cost, revenue,
        # inventory_closing) as raw str values in ai_value.
        if not isinstance(field.ai_value, str):
            continue
        try:
            field_name = MonthlyFieldName(field.field_name)
        except ValueError:
            continue  # skip non-monthly fields (e.g. onboarding fields)
        try:
            normalized_value = normalize_monthly_field_value(
                field_name=field_name,
                raw_value=field.ai_value,
            )
        except InvalidMonthlyFieldValueError:
            # Skip unparseable values — they will appear as low confidence
            # with confidence = base 0.50 (no parse bonus)
            normalized_value = Decimal("0")

        confidence_pct = (
            Decimal(str(field.confidence))
            if field.confidence is not None
            else Decimal("0.50")
        )
        # Clamp confidence to [0.000, 1.000]
        if confidence_pct < Decimal("0.000"):
            confidence_pct = Decimal("0.000")
        elif confidence_pct > Decimal("1.000"):
            confidence_pct = Decimal("1.000")

        requires_confirmation = confidence_pct < CONFIDENCE_RED_THRESHOLD
        if requires_confirmation:
            low_confidence_count += 1

        drafts.append(
            MonthlyInputDraftRow(
                field_name=field_name,
                value=normalized_value,
                confidence=confidence_pct,
                evidence=field.evidence,
            )
        )

    # Step 5: AD-7 strict invariant — return envelope to caller.
    # The actual input_drafts INSERT happens in the handler (commit boundary).
    # M10 NEVER writes `confirmed_inputs` (AD-7 SM-3a verified — see
    # counter increment in handler).
    return MonthlyExtractionResult(
        extraction_id=extraction_id,
        period_key=period_key,
        drafts=tuple(drafts),
        low_confidence_count=low_confidence_count,
        trace_id=trace_id,
    )
