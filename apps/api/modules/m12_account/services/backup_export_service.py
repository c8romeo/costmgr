"""apps.api.modules.m12_account.services.backup_export_service — Story 12.2 PRIMARY.

Daily auto-backup + JSON self-download service layer (PRD §F12.2 + NFR4
+ AD-15 §4). Wraps the pure kernel in
`packages.services.m12_account.backup_export` with:

- DB I/O (SQLAlchemy 2.0 AsyncSession) — SELECT 7 tables + INSERT/UPDATE
  on tenant_backups
- A5 audit-first invariant via `emit_audit_typed` (ACCOUNT_BACKUP class)
- AD-2 INSERT-only preservation (UPDATE/DELETE attempts raise
  `append-only violation` via trigger — see migration 0024)
- AD-10 owner-only role gate (caller MUST pre-resolve via
  `enforce_role_gate`; service layer is role-agnostic)
- 30-day retention sweep via `purged_at` soft-delete (NOT DELETE)
- Korean SSOT (AD-15 §11) — error messages reference pure-kernel constants

Service operations (6):
  - `run_backup` — cron-callable entry point: SELECT 7 tables → build
    envelope → serialize → INSERT `tenant_backups` (audit-first
    `backup_created`).
  - `run_retention_sweep` — 30-day rolling soft-delete (UPDATE
    `purged_at = now()`). Audit `backup_retention_purged` per row.
  - `trigger_backup` — manual owner trigger (POST /backups/trigger).
    Audit `backup_triggered` + `backup_created`.
  - `list_recent_backups` — SELECT 7-day window for owner UI.
  - `fetch_backup_payload` — SELECT single row + return payload bytes
    for JSON download.
  - `_record_audit` — internal helper: emit_audit_typed wrapper with
    audit-first error guard (CR 1.1 pattern).

Layering (AD-11):
- Pure kernel: `packages/services/m12_account/backup_export.py`
  (7-table JSON dump + sha256 + envelope)
- Service layer (this file): SQLAlchemy + audit-first + 5 typed
  exceptions (apps/api/modules/m12_account/exceptions.py)

NFR4 contract:
- 30-day rolling sweep (daily cron KST 03:00 / UTC 18:00)
- Quarterly 1-year archive: honestly DEFER (sprint-scale per CR 11-3)
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db_models import (
    AuditLog,
    BOMLine,
    FiscalPeriodSnapshot,
    MonthlyInputPeriod,
    MonthlyInputRow,
    Product,
    TenantBackup,
    TenantSettings,
)
from apps.api.modules.m12_account.exceptions import (
    BackupExportServiceError,
    BackupNotFoundError,
    BackupRetentionCutoffInvalidError,
    BackupServiceAuditEmitError,
)
from packages.services.m12_account.backup_export import (
    AUDIT_LOG_WINDOW_DAYS,
    SCHEMA_VERSION,
    BackupPayloadTooLargeError,
    build_backup_envelope,
    collapse_audit_logs,
    compute_payload_sha256,
    serialize_backup_payload,
)

# ── Constants ────────────────────────────────────────────────
DEFAULT_LIST_DAYS: int = 7  # AC #4: "최근 7일 백업 다운로드"
MAX_LIST_DAYS: int = 30  # PRD safety cap for the `days` query param.


def _resolve_kst_tz() -> ZoneInfo:
    """Lazy KST ZoneInfo with graceful fallback (F-28).

    `tzdata` is OS-dependent (Linux has it built-in via system tzdata,
    Windows does NOT). To avoid a hard STACK_PIN dependency on the
    `tzdata` PyPI package (which would require a BUMP per AD-14), we
    try `ZoneInfo("Asia/Seoul")` lazily and fall back to a fixed
    `UTC+9` `timezone(timedelta(hours=9))` if the system tzdata is
    missing.

    Display-only path: the canonical KST conversion for `backup_date`
    is computed via `now.astimezone(UTC) + timedelta(hours=9)` (F-13)
    — see `run_backup`. The ZoneInfo is only used for richer display
    formatting (e.g. tz-aware timestamps in audit payload) where a
    fixed-offset fallback is semantically equivalent.
    """
    try:
        return ZoneInfo("Asia/Seoul")
    except ZoneInfoNotFoundError:
        # tzdata missing on this OS (Windows without tzdata PyPI).
        # Fall back to fixed-offset UTC+9 — KST has no DST, so the
        # offset is stable year-round.
        from datetime import timezone
        return timezone(timedelta(hours=9), name="KST")


KST_TZ: ZoneInfo = _resolve_kst_tz()  # AD-15 §2 — KST display DST-safe


# ── Typed results ────────────────────────────────────────────
@dataclass
class BackupResult:
    """Result of `run_backup` / `trigger_backup`.

    Returned to cron runner / HTTP handler. Caller is responsible for
    translating into AD-15 §4 envelope response.
    """

    backup_id: uuid.UUID
    tenant_id: uuid.UUID
    backup_date: date
    schema_version: str
    payload_sha256: str
    payload_size_bytes: int
    row_count_total: int
    audit_log_exported_rows: int
    created_at: datetime


@dataclass
class RetainResult:
    """Result of `run_retention_sweep`."""

    purged_count: int
    cutoff: datetime


@dataclass
class BackupMetadata:
    """Lightweight metadata for `list_recent_backups`."""

    backup_id: uuid.UUID
    backup_date: date
    schema_version: str
    payload_sha256: str
    payload_size_bytes: int
    row_count_total: int
    audit_log_exported_rows: int
    created_at: datetime


@dataclass
class BackupPayload:
    """Single-row payload for `fetch_backup_payload`."""

    backup_id: uuid.UUID
    tenant_id: uuid.UUID
    payload: dict[str, Any]
    payload_sha256: str


# ── Service class ─────────────────────────────────────────────
class BackupExportService:
    """Daily auto-backup + JSON self-download service (PRD §F12.2 + NFR4)."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.trace_id = trace_id

    # ── 1. run_backup ────────────────────────────────────────
    async def run_backup(
        self,
        *,
        retention_class: str = "daily",
        triggered_by_user_id: uuid.UUID | None = None,
        now: datetime | None = None,
    ) -> BackupResult:
        """Cron entry point: SELECT 7 tables → INSERT tenant_backups row.

        AD-2 INSERT-only: this method performs INSERT ONLY. The 0024
        alembic trigger prevents UPDATE/DELETE on this table.

        Args:
            retention_class: 'daily' (default) or 'quarterly' (honestly
                DEFER — sprint-scale). Default 'daily' per AC #1.
            triggered_by_user_id: Manual trigger trace (cron path = NULL).
            now: Injected wall-clock time (crontab path uses
                `datetime.now(tz=UTC)`; test path passes a fixed
                datetime for deterministic testability per CR 4-3).

        Returns:
            BackupResult(backup_id, tenant_id, payload_sha256, ...).

        Raises:
            BackupPayloadTooLargeError: 50 MB cap exceeded.
            BackupServiceAuditEmitError: audit-first emit failed.
        """
        now = now or datetime.now(tz=UTC)
        cutoff = now - timedelta(days=AUDIT_LOG_WINDOW_DAYS)
        # KST via ZoneInfo (CR 12-5 L4 + AD-15 §2) — DST-safe.
        kst_now = now.astimezone(KST_TZ)
        backup_date = kst_now.date()

        # 1. SELECT 7 tables
        tables = await self._select_7_tables(cutoff=cutoff, now=now)

        # 2. Build envelope + serialize + sha256
        backup_id = uuid.uuid4()
        envelope = build_backup_envelope(
            backup_id=backup_id,
            tenant_id=self.tenant_id,
            created_at=now,
            backup_date=backup_date,
            tables=tables,
        )
        try:
            payload_bytes = serialize_backup_payload(envelope)
        except BackupPayloadTooLargeError as exc:
            # Surface service-layer exception with trace_id (CR 1.1)
            raise BackupPayloadTooLargeError(
                size_bytes=exc.size_bytes,
                max_bytes=exc.max_bytes,
                trace_id=self.trace_id,
            ) from exc
        payload_sha = compute_payload_sha256(payload_bytes)
        audit_count = len(tables["audit_logs"])

        # 3. Audit-first emit (BEFORE INSERT) — CR 1.1 pattern
        await self._record_audit(
            action="backup_created",
            target_id=backup_id,
            reason="daily auto-backup cron (KST 02:00)",
            payload={
                "backup_date": backup_date.isoformat(),
                "row_count_total": envelope["row_count_total"],
                "audit_log_exported_rows": audit_count,
                "retention_class": retention_class,
            },
        )

        # 4. INSERT tenant_backups row (with audit-first failure handling)
        row = TenantBackup(
            backup_id=backup_id,
            tenant_id=self.tenant_id,
            backup_date=datetime.combine(backup_date, datetime.min.time()),
            created_at=now,
            schema_version=SCHEMA_VERSION,
            payload=envelope,
            payload_sha256=payload_sha,
            row_count_total=envelope["row_count_total"],
            audit_log_exported_rows=audit_count,
            retention_class=retention_class,
            purged_at=None,
            triggered_by_user_id=triggered_by_user_id,
        )
        try:
            self.session.add(row)
            await self.session.flush()
        except IntegrityError as exc:
            # F-18: UNIQUE (tenant_id, backup_date) WHERE purged_at IS NULL
            # collision. Emit backup_failed audit atomic-first, then raise.
            await self.session.rollback()
            with contextlib.suppress(Exception):
                # Audit failure on top of DB failure — best-effort log.
                await self._record_audit(
                    action="backup_failed",
                    target_id=backup_id,
                    reason="UNIQUE constraint violation on (tenant_id, backup_date)",
                    payload={
                        "backup_date": backup_date.isoformat(),
                        "retention_class": retention_class,
                        "triggered_by": (
                            "manual" if triggered_by_user_id else "cron"
                        ),
                    },
                )
            raise BackupRetentionCutoffInvalidError(
                reason=f"UNIQUE violation: {exc!s}",
                trace_id=self.trace_id,
            ) from exc
        except Exception as exc:
            # F-03: generic backup_failed audit emit BEFORE raise (CR 1.1).
            await self.session.rollback()
            with contextlib.suppress(Exception):
                # Audit failure on top of DB failure — best-effort log.
                await self._record_audit(
                    action="backup_failed",
                    target_id=backup_id,
                    reason=f"backup run failed: {type(exc).__name__}",
                    payload={
                        "backup_date": backup_date.isoformat(),
                        "retention_class": retention_class,
                        "triggered_by": (
                            "manual" if triggered_by_user_id else "cron"
                        ),
                    },
                )
            raise BackupExportServiceError(
                message=f"backup_failed: {exc!s}",
                trace_id=self.trace_id,
            ) from exc

        return BackupResult(
            backup_id=backup_id,
            tenant_id=self.tenant_id,
            backup_date=backup_date,
            schema_version=SCHEMA_VERSION,
            payload_sha256=payload_sha,
            payload_size_bytes=len(payload_bytes),
            row_count_total=envelope["row_count_total"],
            audit_log_exported_rows=audit_count,
            created_at=now,
        )

    # ── 2. run_retention_sweep ───────────────────────────────
    async def run_retention_sweep(
        self,
        *,
        cutoff: datetime | None = None,
        now: datetime | None = None,
    ) -> RetainResult:
        """30-day rolling soft-delete (UPDATE purged_at = now()).

        Per AC #3: only `retention_class='daily'` rows are swept. Quarterly
        1-year archive is honestly DEFER (per CR 11-3 — sprint-scale).

        Idempotent: 2회째 실행 → 0 row affected (이미 purged_at 채워짐).

        Args:
            cutoff: Lower bound — rows with `backup_date < cutoff` AND
                `purged_at IS NULL` get soft-deleted. Default = now - 30d.
            now: Reference "now" for soft-delete timestamp. Default UTC now.

        Returns:
            RetainResult(purged_count, cutoff).

        Raises:
            BackupRetentionCutoffInvalidError: cutoff >= now.
            BackupServiceAuditEmitError: audit-first emit failed.
        """
        now = now or datetime.now(tz=UTC)
        cutoff = cutoff or (now - timedelta(days=30))
        if cutoff >= now:
            raise BackupRetentionCutoffInvalidError(
                reason=f"cutoff ({cutoff.isoformat()}) >= now ({now.isoformat()})",
                trace_id=self.trace_id,
            )

        # SELECT rows eligible for purge (read-only — UPDATE happens after)
        eligible = await self.session.execute(
            select(TenantBackup.backup_id).where(
                and_(
                    TenantBackup.tenant_id == self.tenant_id,
                    TenantBackup.retention_class == "daily",
                    TenantBackup.purged_at.is_(None),
                    TenantBackup.backup_date < cutoff,
                )
            )
        )
        eligible_ids = [row[0] for row in eligible.all()]

        # Audit-first: emit BEFORE UPDATE (CR 1.1)
        for bid in eligible_ids:
            await self._record_audit(
                action="backup_retention_purged",
                target_id=bid,
                reason=f"30-day rolling retention cutoff {cutoff.isoformat()}",
                payload={"backup_id": str(bid), "cutoff": cutoff.isoformat()},
            )

        # UPDATE purged_at = now() (NOT DELETE — AD-2 INSERT-only)
        if eligible_ids:
            await self.session.execute(
                update(TenantBackup)
                .where(
                    and_(
                        TenantBackup.tenant_id == self.tenant_id,
                        TenantBackup.retention_class == "daily",
                        TenantBackup.purged_at.is_(None),
                        TenantBackup.backup_date < cutoff,
                        TenantBackup.backup_id.in_(eligible_ids),
                    )
                )
                .values(purged_at=now)
            )
        await self.session.flush()

        return RetainResult(purged_count=len(eligible_ids), cutoff=cutoff)

    # ── 3. trigger_backup ────────────────────────────────────
    async def trigger_backup(self) -> BackupResult:
        """Manual owner trigger (POST /backups/trigger) — same as run_backup
        but with `triggered_by_user_id` set + distinct audit chain.

        Audit-first: emit `backup_triggered` BEFORE the actual run
        (forensic separation from cron-triggered `backup_created`).
        """
        if self.actor_id is None:
            raise BackupExportServiceError(
                message="trigger_backup requires actor_id",
                trace_id=self.trace_id,
            )
        # F-16: target_id must be a uuid (audit_logs.target_id NOT NULL).
        # Generate a 1-shot audit_id linking trigger → backup_created.
        audit_id = uuid.uuid4()
        await self._record_audit(
            action="backup_triggered",
            target_id=audit_id,
            reason="manual owner trigger (POST /backups/trigger)",
            payload={"tenant_id": str(self.tenant_id)},
        )
        return await self.run_backup(
            retention_class="daily",
            triggered_by_user_id=self.actor_id,
        )

    # ── 4. list_recent_backups ───────────────────────────────
    async def list_recent_backups(
        self,
        *,
        days: int = DEFAULT_LIST_DAYS,
    ) -> list[BackupMetadata]:
        """SELECT last N days of backups (default 7) for owner UI.

        AD-2 INSERT-only: this is a SELECT — no UPDATE/DELETE allowed.

        Args:
            days: Window size. Default 7, clamped to [1, MAX_LIST_DAYS=30].
        """
        days = max(1, min(days, MAX_LIST_DAYS))
        cutoff = datetime.now(tz=UTC) - timedelta(days=days)
        # F-09: filter on `backup_date` (KST date) not `created_at` to match
        # the (tenant_id, backup_date DESC) index. F-13: convert UTC cutoff
        # to KST date for consistency with backup_date column.
        cutoff_kst_date = cutoff.astimezone(KST_TZ).date()
        result = await self.session.execute(
            select(TenantBackup)
            .where(
                and_(
                    TenantBackup.tenant_id == self.tenant_id,
                    TenantBackup.purged_at.is_(None),
                    TenantBackup.backup_date >= cutoff_kst_date,
                )
            )
            .order_by(TenantBackup.backup_date.desc())
        )
        rows = result.scalars().all()
        metadata: list[BackupMetadata] = []
        for row in rows:
            payload_size = self._estimate_payload_size(row.payload)
            metadata.append(
                BackupMetadata(
                    backup_id=row.backup_id,
                    backup_date=row.backup_date.date()
                    if isinstance(row.backup_date, datetime)
                    else row.backup_date,
                    schema_version=row.schema_version,
                    payload_sha256=row.payload_sha256,
                    payload_size_bytes=payload_size,
                    row_count_total=row.row_count_total,
                    audit_log_exported_rows=row.audit_log_exported_rows,
                    created_at=row.created_at,
                )
            )
        return metadata

    # ── 5. fetch_backup_payload ──────────────────────────────
    async def fetch_backup_payload(
        self,
        *,
        backup_id: uuid.UUID,
    ) -> BackupPayload:
        """SELECT single row by backup_id + return payload dict.

        RLS already enforces tenant_id isolation at the DB layer; this
        method adds a service-layer double-check (defense-in-depth)
        + computes sha256 from the actual payload bytes to detect
        JSONB corruption (CR 11-1 audit-first + F-05 integrity).

        Raises:
            BackupNotFoundError: backup_id not found OR purged_at != NULL
                OR cross-tenant (defense-in-depth) OR sha256 mismatch.
        """
        import hashlib
        import json as _json

        result = await self.session.execute(
            select(TenantBackup).where(TenantBackup.backup_id == backup_id)
        )
        row = result.scalar_one_or_none()
        # F-12: audit-first — emit BEFORE access checks so failed probes
        # (cross-tenant, purged, missing) are all in the forensic trail.
        await self._record_audit(
            action="backup_downloaded",
            target_id=backup_id,
            reason="owner self-download audit (GET /backups/{id}/download)",
            payload={"backup_id": str(backup_id)},
        )
        if row is None:
            raise BackupNotFoundError(
                backup_id=backup_id,
                tenant_id=self.tenant_id,
                trace_id=self.trace_id,
            )
        if row.tenant_id != self.tenant_id:
            # Defense-in-depth — RLS already blocks this at DB layer.
            raise BackupNotFoundError(
                backup_id=backup_id,
                tenant_id=self.tenant_id,
                trace_id=self.trace_id,
            )
        if row.purged_at is not None:
            raise BackupNotFoundError(
                backup_id=backup_id,
                tenant_id=self.tenant_id,
                trace_id=self.trace_id,
            )
        # F-05: integrity check — recompute sha256 from payload bytes.
        actual_sha = hashlib.sha256(
            _json.dumps(
                row.payload, sort_keys=True, default=str
            ).encode("utf-8")
        ).hexdigest()
        if actual_sha != row.payload_sha256:
            raise BackupRetentionCutoffInvalidError(
                reason=(
                    f"sha256 integrity check failed: stored={row.payload_sha256} "
                    f"actual={actual_sha}"
                ),
                trace_id=self.trace_id,
            )
        return BackupPayload(
            backup_id=row.backup_id,
            tenant_id=row.tenant_id,
            payload=row.payload,
            payload_sha256=row.payload_sha256,
        )

    # ── Internal helpers ─────────────────────────────────────
    async def _select_7_tables(
        self,
        *,
        cutoff: datetime,
        now: datetime,
    ) -> dict[str, list[dict[str, Any]]]:
        """SELECT 7 tenant-scoped tables + collapse audit_logs to 365d window.

        Pure-kernel `collapse_audit_logs` enforces the 365-day sliding
        window per AC #1. Service layer is responsible for the SQL fetch
        + JSONB serialization.
        """
        # 1. tenant_settings (1 row per tenant — singleton)
        ts_result = await self.session.execute(
            select(TenantSettings).where(TenantSettings.tenant_id == self.tenant_id)
        )
        ts_row = ts_result.scalar_one_or_none()
        tenant_settings_rows = (
            [self._orm_to_dict(ts_row)] if ts_row else []
        )

        # 2. products
        prod_result = await self.session.execute(
            select(Product).where(Product.tenant_id == self.tenant_id)
        )
        products_rows = [self._orm_to_dict(r) for r in prod_result.scalars().all()]

        # 3. bom_lines (via product join — bom_lines has no direct tenant_id)
        prod_ids_result = await self.session.execute(
            select(Product.id).where(Product.tenant_id == self.tenant_id)
        )
        product_ids = [row[0] for row in prod_ids_result.all()]
        if product_ids:
            bom_result = await self.session.execute(
                select(BOMLine).where(BOMLine.product_id.in_(product_ids))
            )
            bom_rows = [self._orm_to_dict(r) for r in bom_result.scalars().all()]
        else:
            bom_rows = []

        # 4. monthly_input_periods
        mip_result = await self.session.execute(
            select(MonthlyInputPeriod).where(
                MonthlyInputPeriod.tenant_id == self.tenant_id
            )
        )
        mip_rows = [self._orm_to_dict(r) for r in mip_result.scalars().all()]

        # 5. monthly_input_rows (via period join)
        mip_ids_result = await self.session.execute(
            select(MonthlyInputPeriod.period_id).where(
                MonthlyInputPeriod.tenant_id == self.tenant_id
            )
        )
        mip_ids = [row[0] for row in mip_ids_result.all()]
        if mip_ids:
            mir_result = await self.session.execute(
                select(MonthlyInputRow).where(
                    MonthlyInputRow.period_id.in_(mip_ids)
                )
            )
            mir_rows = [self._orm_to_dict(r) for r in mir_result.scalars().all()]
        else:
            mir_rows = []

        # 6. fiscal_period_snapshots
        fps_result = await self.session.execute(
            select(FiscalPeriodSnapshot).where(
                FiscalPeriodSnapshot.tenant_id == self.tenant_id
            )
        )
        fps_rows = [self._orm_to_dict(r) for r in fps_result.scalars().all()]

        # 7. audit_logs (last 365d)
        audit_result = await self.session.execute(
            select(AuditLog).where(
                and_(
                    AuditLog.tenant_id == self.tenant_id,
                    AuditLog.occurred_at >= cutoff,
                )
            )
        )
        audit_rows_raw = [self._orm_to_dict(r) for r in audit_result.scalars().all()]

        tables: dict[str, list[dict[str, Any]]] = {
            "tenant_settings": tenant_settings_rows,
            "products": products_rows,
            "bom_lines": bom_rows,
            "monthly_input_periods": mip_rows,
            "monthly_input_rows": mir_rows,
            "fiscal_period_snapshots": fps_rows,
            "audit_logs": audit_rows_raw,
        }
        # collapse_audit_logs is idempotent if rows are already filtered
        # but pure kernel defensively filters again on cutoff.
        return collapse_audit_logs(tables, cutoff=cutoff, now=now)

    @staticmethod
    def _orm_to_dict(row: Any) -> dict[str, Any]:
        """Convert ORM row → JSON-serializable dict.

        Handles UUID, datetime, Decimal, bytes via JSON-safe coercion:
        - datetime → ISO-8601 string (UTC if naive)
        - UUID → str
        - Decimal → str (AD-8 monetary precision)
        - bytes → hex str (rare; mostly crypto columns)
        - Pydantic models → dict via model_dump
        """
        if row is None:
            return {}

        def _coerce(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=UTC)
                return value.isoformat()
            if isinstance(value, uuid.UUID):
                return str(value)
            if isinstance(value, bytes | bytearray):
                return value.hex()
            # Pydantic v2 BaseModel
            if hasattr(value, "model_dump") and callable(value.model_dump):
                try:
                    return value.model_dump()
                except Exception:
                    return str(value)
            if hasattr(value, "__dict__") and not isinstance(value, str | int | float | bool):
                # Plain ORM-like objects: fall through to str()
                pass
            return value

        result: dict[str, Any] = {}
        for col in row.__table__.columns:
            value = getattr(row, col.name, None)
            result[col.name] = _coerce(value)
        return result

    @staticmethod
    def _estimate_payload_size(payload: dict[str, Any]) -> int:
        """Estimate JSON-serialized byte size for UI display."""
        import json as _json

        return len(
            _json.dumps(
                payload, default=str, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
        )

    async def _record_audit(
        self,
        *,
        action: str,
        target_id: uuid.UUID | None,
        reason: str | None,
        payload: dict[str, Any] | None,
    ) -> None:
        """Audit-first emit wrapper — CR 1.1 pattern.

        Wraps `emit_audit_typed` and translates infrastructure failures
        into `BackupServiceAuditEmitError` (503 envelope). Pre-emit pattern:
        audit is INSERTed BEFORE the data write so a data-write failure
        still leaves a forensic trace.
        """
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.ACCOUNT_BACKUP,
                action=action,  # type: ignore[arg-type]
                actor_id=self.actor_id,
                target_id=target_id,
                reason=reason,
                payload=payload or {},
                tenant_id=self.tenant_id,
                flush=True,
            )
        except Exception as exc:
            raise BackupServiceAuditEmitError(
                message=f"audit emit failed for {action}: {exc!s}",
                trace_id=self.trace_id,
            ) from exc


__all__ = [
    "DEFAULT_LIST_DAYS",
    "MAX_LIST_DAYS",
    "BackupResult",
    "RetainResult",
    "BackupMetadata",
    "BackupPayload",
    "BackupExportService",
]


# Re-export pure-kernel errors for service callers (12-4 convention)
__all__.extend(
    [
        "BackupPayloadTooLargeError",
        "BackupRetentionCutoffInvalidError",
    ]
)
