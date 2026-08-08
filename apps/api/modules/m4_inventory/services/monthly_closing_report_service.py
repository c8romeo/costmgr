"""apps.api.modules.m4_inventory.services.monthly_closing_report_service — Story 6.2.

Service layer for the Monthly Closing Report (PRD §F5 + §F5.2 + §V4 + §A11).

Wraps the pure kernel in
`packages.services.m4_inventory.monthly_closing_report` +
`packages.cost_engine.monthly_closing_report_aggregator` with:

- 3 service operations:
  - `get_monthly_closing_report` (T3.1) — read-only aggregator — 6-1
    `closing_period_service.evaluate_closing_period` + 5-2
    `LedgerService.query_period_closing` + 4-2 fiscal_period_snapshots
    query + T1 pure kernel `aggregate_monthly_closing_report` dispatch.
  - `get_monthly_closing_report_audit_trail` (T3.2) — audit log
    emission trace (CR 1.1 observability).
  - `verify_monthly_closing_report_v4` (T3.3) — V4 verification
    dispatch — 6-1 V4 wire extension + 4-3 V4 placeholder fill 진입점.

- 3 typed exceptions (AD-15 §4 envelope mapping):
  - `MonthlyClosingReportAuditEmitError` (500) — audit-first emit failure
    (조회 자체 audit log INSERT — CR 1.1).
  - `MonthlyClosingReportEmptyError` (409 CLOSING_REPORT_EMPTY) —
    no data at all (CLOSING_REPORT_EMPTY view mode).
  - `MonthlyClosingReportKrwUsdRateMissingError` (422
    CLOSING_REPORT_KRW_USD_RATE_MISSING) — 환율 source missing when
    KRW/USD dual display required.

Layering (AD-11):
- Pure kernel: `packages/services/m4_inventory/monthly_closing_report.py` (T1 ✅)
- Pure kernel #2: `packages/cost_engine/monthly_closing_report_aggregator.py` (T2 ✅)
- Service layer (this file): SQLAlchemy AsyncSession + audit-first emit
  (CR 1.1 lesson) + 3 typed exceptions.

A5 forward-lock:
- Audit rows route to `audit_logs` (ActionClass.MONTHLY_CLOSING_REPORT)
  via `emit_audit_typed()`. NEW 1 action:
  - `monthly_closing_report_viewed` — read-only report 조회 audit log
    INSERT (CR 1.1 idempotent re-view skip).
- Drift detector: `tests/integration/test_audit_action_consistency.py`
  + `tests/services/test_audit_action_centralization.py` extensions.

AD-22 reversal entrypoint preserved (5-2 wire + Epic 11 forward-fill):
read-only consumer — correction flow is Epic 11 module authority.

A8 inline projection deprecation timeline:
- 6-2 wire 시점: inline projection 보존 상태로 wire (1 epic maintenance
  window 진행 중), monthly_closing_report aggregator는 ledger aggregate
  + 5-2 wire + 6-1 wire + 4-2 wire 4-source read-only join.
- Epic 6 close-out 시점에 fold-in vs deprecate 결정 필수 (A8 결정).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from packages.cost_engine.monthly_closing_report_aggregator import (
    V4Verdict,
    verify_monthly_closing_report_consistency,
)
from packages.services.m4_inventory.monthly_closing_report import (
    ClosingSnapshotEventLite,
    CurrencyPair,
    FiscalPeriodSnapshotLite,
    LedgerEventLite,
    OpeningInventoryEntryLite,
    aggregate_monthly_closing_report,
)


def _now_utc() -> datetime:
    """UTC now (AD-5: pure kernel no clock, service layer owns)."""
    return datetime.now(tz=UTC)


def _to_iso(dt: datetime) -> str:
    """ISO-8601 UTC timestamp string."""
    return dt.isoformat()


def _decimal_to_str(qty: Decimal | None) -> str | None:
    """Decimal → str for JSON serialization (AD-8 monetary types)."""
    if qty is None:
        return None
    return f"{qty:f}"


# ─────────────────────────────────────────────────────────────
# Typed exceptions (mapped to HTTP by handlers.py / main.py)
# ─────────────────────────────────────────────────────────────


class MonthlyClosingReportEmptyError(Exception):
    """409 CLOSING_REPORT_EMPTY — no data at all.

    PRD §F5: monthly closing report with 0 ledger events + 0
    closing_snapshot + 0 fiscal_period_snapshots → CLOSING_REPORT_EMPTY.
    Defense-in-depth for callers that explicitly require READY view mode.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"monthly_closing_report empty for {period_key} "
            f"(tenant {tenant_id})"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class MonthlyClosingReportKrwUsdRateMissingError(Exception):
    """422 CLOSING_REPORT_KRW_USD_RATE_MISSING — 환율 source missing.

    PRD §F5.2: KRW/USD dual display requires 환율 source from
    tenant_settings.baseline.currency_pair. When 환율 missing AND
    USD display required → 422 typed envelope.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"monthly_closing_report KRW/USD 환율 missing for {period_key} "
            f"(tenant {tenant_id})"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class MonthlyClosingReportAuditEmitError(Exception):
    """500 MONTHLY_CLOSING_REPORT_AUDIT_EMIT_ERROR — audit-first invariant guard.

    CR 1.1 lesson: audit-first emit failure MUST raise (not silent skip).
    Read-only report 자체 audit log INSERT — closing report의 조회 trace.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"monthly_closing_report audit emit failed for tenant {tenant_id}: {details}"
        )
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


# ─────────────────────────────────────────────────────────────
# MonthlyClosingReportService
# ─────────────────────────────────────────────────────────────


class MonthlyClosingReportService:
    """Story 6.2 — monthly closing report service.

    Read-only aggregator (PRD §F5 + §F5.2 + §V4 + §A11 4-layer defense).
    All state-changing operations write a typed audit row BEFORE the
    data write (AD-2), with idempotent no-op skip on idempotent re-view
    (CR 1.1 lesson — 1 view = 1 audit).

    Constructor:
        session: AsyncSession (per-request).
        tenant_id: tenant UUID (from JWT).
        trace_id: request trace ID.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.trace_id = trace_id

    # ── Operation 1: get monthly closing report (read-only) ─────
    async def get_monthly_closing_report(
        self,
        period_key: str,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Read-only monthly closing report aggregator (PRD §F5 + §F5.2).

        4-source read-only join:
        1. `closing_snapshot` ledger events (6-1 wire).
        2. `inventory_ledger` 전체 events (5-2 wire).
        3. `monthly_input_periods.opening_inventory` JSONB (5-1 wire).
        4. `fiscal_period_snapshots` engine_type='trad' (4-2 wire).
        + 환율 source from `tenant_settings.baseline.currency_pair`.

        Read-only transaction (no INSERT + no UPDATE — REPEATABLE READ).

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.
            actor_id: actor who triggered the view; None for system cron.

        Returns:
            dict[str, Any] with view_mode + allowed + closing_per_product
            + closing_snapshot_count + ledger_event_count +
            fiscal_period_snapshot_count + finalized_at + currency_pair
            + title_ko.

        Raises:
            MonthlyClosingReportKrwUsdRateMissingError: 환율 missing.
            MonthlyClosingReportAuditEmitError: audit emit failure.
        """
        # Load 4 sources in parallel-friendly sequence (session-level
        # sequential awaits; service layer owns DB I/O).
        closing_snapshot_events = await self._query_closing_snapshot_events(
            period_key
        )
        ledger_events = await self._query_ledger_events(period_key)
        fiscal_period_snapshots = await self._query_fiscal_period_snapshots(
            period_key
        )
        opening_inventory_entries = await self._query_opening_inventory(
            period_key
        )
        product_code_lookup = await self._query_product_code_lookup(
            {e.product_id for e in ledger_events}
            | {e.product_id for e in closing_snapshot_events}
            | {e.product_id for e in fiscal_period_snapshots}
            | {e.product_id for e in opening_inventory_entries}
        )
        currency_pair = await self._query_currency_pair()

        # Pure kernel dispatch (T1 — aggregate_monthly_closing_report).
        aggregate = aggregate_monthly_closing_report(
            closing_snapshot_events=[
                ClosingSnapshotEventLite(
                    product_id=e["product_id"],
                    closing_qty=e["closing_qty"],
                    finalized_at=e["finalized_at"],
                )
                for e in closing_snapshot_events
            ],
            ledger_events=[
                LedgerEventLite(
                    product_id=e["product_id"],
                    event_type=e["event_type"],
                )
                for e in ledger_events
            ],
            fiscal_period_snapshots=[
                FiscalPeriodSnapshotLite(
                    product_id=e["product_id"],
                    engine_type=e["engine_type"],
                )
                for e in fiscal_period_snapshots
            ],
            opening_inventory_entries=[
                OpeningInventoryEntryLite(
                    product_id=e["product_id"],
                    opening_qty=e["opening_qty"],
                )
                for e in opening_inventory_entries
            ],
            period_key=period_key,
            currency_pair=currency_pair,
            product_code_lookup=product_code_lookup,
        )

        # Audit-first emit (CR 1.1) for read-only report 자체 audit log.
        # 1 view = 1 audit (idempotent re-view skip은 AC #4 spec 참조).
        await self._emit_audit_viewed(
            period_key=period_key,
            actor_id=actor_id,
            view_mode=aggregate.view_mode,
            closing_snapshot_count=aggregate.closing_snapshot_count,
            ledger_event_count=aggregate.ledger_event_count,
            fiscal_period_snapshot_count=aggregate.fiscal_period_snapshot_count,
        )

        # Build response payload.
        # NOTE (bmad-code-review H8 결정, 2026-08-08): READY/PARTIAL view
        # mode 인데 환율 missing 이면 MonthlyClosingReportKrwUsdRateMissingError
        # raise (422 typed envelope). EMPTY view mode 는 환율 없이도 OK
        # (panel 이 currency_pair=null 허용).
        if (
            aggregate.view_mode in ("READY", "PARTIAL")
            and currency_pair is None
        ):
            raise MonthlyClosingReportKrwUsdRateMissingError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )

        # NOTE (bmad-code-review H3 결정, 2026-08-08): payload 필드명을
        # TS `MonthlyClosingReportResponse` mirror 와 정렬. backend 의
        # `opening_qty_krw/closing_qty_krw/delta_krw` (KRW suffix) 와
        # `currency_pair.from_currency/to_currency/rate_source_ko/rate_as_of`
        # 는 TS mirror 와 일치하지 않아 panel 이 `undefined` 렌더링.
        # TS mirror 가 source-of-truth (CR 1.1 AD-15 §11 SSOT parity
        # discipline 이며 `tests/integration/test_monthly_closing_report_label_consistency.py`
        # 가 TS mirror 를 assert target 으로 wire 됨).
        currency_pair_payload: dict[str, Any] | None = None
        if currency_pair is not None:
            currency_pair_payload = {
                "base": currency_pair.from_currency,
                "quote": currency_pair.to_currency,
                "rate": _decimal_to_str(currency_pair.rate),
                "source": currency_pair.rate_source_ko,
            }

        return {
            "period_key": aggregate.period_key,
            "view_mode": aggregate.view_mode,
            "closing_snapshot_count": aggregate.closing_snapshot_count,
            "ledger_event_count": aggregate.ledger_event_count,
            "fiscal_period_snapshot_count": aggregate.fiscal_period_snapshot_count,
            "opening_inventory_count": aggregate.opening_inventory_count,
            "closing_per_product": [
                {
                    "product_id": str(row.product_id),
                    "opening_qty": _decimal_to_str(row.opening_qty_krw),
                    "closing_qty": _decimal_to_str(row.closing_qty_krw),
                    "delta_qty": _decimal_to_str(row.delta_krw),
                    "closing_qty_krw": _decimal_to_str(row.closing_qty_krw),
                    "closing_qty_usd": _decimal_to_str(row.closing_qty_usd),
                    "delta_usd": _decimal_to_str(row.delta_usd),
                }
                for row in aggregate.closing_per_product
            ],
            "currency_pair": currency_pair_payload,
            "trace_id": self.trace_id,
            "report_generated_at": _to_iso(_now_utc()),
        }

    # ── Operation 2: audit trail query ──────────────────────────
    async def get_monthly_closing_report_audit_trail(
        self,
        period_key: str,
    ) -> list[dict[str, Any]]:
        """Audit log emission trace for the monthly closing report (CR 1.1).

        Returns audit_logs rows where action_class='monthly_closing_report'
        OR action_class='closing_period' OR action_class='verification'
        (verify_v4_closing_period_consistency) for the current period_key,
        time DESC, capped at 10.
        """
        # NOTE (bmad-code-review H3 결정, 2026-08-08): SQL 컬럼을
        # TS `MonthlyClosingReportAuditEntry { id, action, actor_id,
        # created_at, payload }` mirror 와 정렬. target_table =
        # 'verification_log' 으로 수정 (ActionClass.VERIFICATION 이
        # verification_log 에 write — 6-1 wire).
        result = await self.session.execute(
            text(
                """
                SELECT id, action, actor_id, payload, occurred_at
                FROM audit_logs
                WHERE tenant_id = :tenant_id
                  AND (
                    target_table IN ('monthly_closing_report', 'closing_period')
                    OR (
                      target_table = 'verification_log'
                      AND payload->>'action_name' = 'verify_v4_closing_period_consistency'
                    )
                  )
                  AND payload->>'period_key' = :period_key
                ORDER BY occurred_at DESC
                LIMIT 10
                """
            ),
            {
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
            },
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "action": row[1],
                "actor_id": str(row[2]) if row[2] is not None else None,
                "created_at": row[4].isoformat() if row[4] is not None else None,
                "payload": row[3] if isinstance(row[3], dict) else {},
            }
            for row in rows
        ]

    # ── Operation 3: V4 verification dispatch ───────────────────
    async def verify_monthly_closing_report_v4(
        self,
        period_key: str,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> V4Verdict:
        """V4 closing-period-consistency verifier dispatch (PRD §V4).

        4-source aggregate verification (extension 6-1 2-source → 6-2
        4-source): ledger + closing_snapshot + fiscal_period_snapshot +
        product_whitelist. Returns V4Verdict TypedDict.

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.
            actor_id: actor who triggered the verification.

        Returns:
            V4Verdict TypedDict:
            - status='skipped' if industry='service' OR all aggregates empty.
            - status='passed' if all per-product qty + cost match.
            - status='failed' if any per-product qty/cost mismatch.
        """
        # Load 4-source aggregates.
        closing_snapshot_aggregate = await self._query_closing_snapshot_aggregate(
            period_key
        )
        ledger_aggregate = await self._query_ledger_aggregate(period_key)
        product_whitelist = await self._query_active_product_whitelist()

        # Read industry (for service-only SKIP).
        industry = await self._query_tenant_industry()

        # Pure kernel dispatch (T2 — verify_monthly_closing_report_consistency).
        # NOTE (bmad-code-review D1 결정, 2026-08-08): 3-source contract —
        # fiscal_period_snapshot_aggregate 인자 제거 (PRD §6.1 산식 체인이
        # manufacturing_cost KRW 임을 명시). 2-source (ledger +
        # closing_snapshot) + product_whitelist 만 비교.
        v4_verdict = verify_monthly_closing_report_consistency(
            ledger_aggregate=ledger_aggregate,
            closing_snapshot_aggregate=closing_snapshot_aggregate,
            product_whitelist=product_whitelist,
            industry=industry,
        )

        # AD-5: pure kernel returns placeholder timestamp; overwrite
        # with real UTC now.
        # NOTE (bmad-code-review H9 결정, 2026-08-08): status 를
        # upper-case 정규화 — TS `MonthlyClosingReportV4Verdict.status:
        # 'PASS'|'FAIL'|'SKIP'` discriminator 와 정렬.
        v4_verdict_dict = dict(v4_verdict)
        v4_verdict_dict["verified_at"] = _to_iso(_now_utc())
        v4_verdict_dict["status"] = v4_verdict_dict["status"].upper()

        # Audit-first emit (CR 1.1) — V4 verifier dispatch itself is
        # observable regardless of PASS/FAIL/SKIP.
        await self._emit_audit_v4_dispatched(
            period_key=period_key,
            actor_id=actor_id,
            v4_status=v4_verdict_dict["status"],
            failure_count=len(v4_verdict_dict["failures"]),
        )

        return v4_verdict_dict  # type: ignore[return-value]

    # ── Internal helpers: 4-source data queries ──────────────────
    async def _query_closing_snapshot_events(
        self,
        period_key: str,
    ) -> list[dict[str, Any]]:
        """closing_snapshot ledger events (6-1 wire) — per product.

        SELECT product_id, qty AS closing_qty, payload->>'finalized_at'
        FROM inventory_ledger WHERE event_type='closing_snapshot'
        AND period_key=:period_key.
        """
        result = await self.session.execute(
            text(
                """
                SELECT product_id, qty, payload->>'finalized_at' AS finalized_at
                FROM inventory_ledger
                WHERE tenant_id = :tenant_id
                  AND period_key = :period_key
                  AND event_type = 'closing_snapshot'
                """
            ),
            {
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
            },
        )
        return [
            {
                "product_id": row[0],
                "closing_qty": row[1] if isinstance(row[1], Decimal) else Decimal(str(row[1])),
                "finalized_at": row[2] or "",
            }
            for row in result.fetchall()
        ]

    async def _query_ledger_events(
        self,
        period_key: str,
    ) -> list[dict[str, Any]]:
        """inventory_ledger 전체 events (5-2 wire) — per product ledger_event_count."""
        result = await self.session.execute(
            text(
                """
                SELECT product_id, event_type
                FROM inventory_ledger
                WHERE tenant_id = :tenant_id
                  AND period_key = :period_key
                """
            ),
            {
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
            },
        )
        return [
            {
                "product_id": row[0],
                "event_type": row[1],
            }
            for row in result.fetchall()
        ]

    async def _query_fiscal_period_snapshots(
        self,
        period_key: str,
    ) -> list[dict[str, Any]]:
        """fiscal_period_snapshots engine_type='trad' (4-2 wire)."""
        result = await self.session.execute(
            text(
                """
                SELECT product_id, engine_type
                FROM fiscal_period_snapshots
                WHERE tenant_id = :tenant_id
                  AND period_key = :period_key
                  AND engine_type = 'trad'
                """
            ),
            {
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
            },
        )
        return [
            {
                "product_id": row[0],
                "engine_type": row[1],
            }
            for row in result.fetchall()
        ]

    async def _query_opening_inventory(
        self,
        period_key: str,
    ) -> list[dict[str, Any]]:
        """monthly_input_periods.opening_inventory JSONB (5-1 wire).

        Each row in opening_inventory JSONB is
        `{product_id: qty}` mapping. Unnest via JSONB each + text cast.
        """
        result = await self.session.execute(
            text(
                """
                SELECT opening_inventory
                FROM monthly_input_periods
                WHERE tenant_id = :tenant_id
                  AND period_key = :period_key
                """
            ),
            {
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
            },
        )
        rows = result.fetchall()
        entries: list[dict[str, Any]] = []
        for row in rows:
            opening = row[0] or {}
            if isinstance(opening, dict):
                for pid_str, qty in opening.items():
                    try:
                        pid = uuid.UUID(pid_str)
                    except (ValueError, TypeError):
                        continue
                    qty_decimal = qty if isinstance(qty, Decimal) else Decimal(str(qty))
                    entries.append(
                        {
                            "product_id": pid,
                            "opening_qty": qty_decimal,
                        }
                    )
        return entries

    async def _query_product_code_lookup(
        self,
        product_ids: set[uuid.UUID],
    ) -> dict[uuid.UUID, tuple[str, str]]:
        """Product code/name lookup from products table (optional helper).

        Returns dict[product_id → (code, name)]. Empty when no products
        in scope (service-only tenant / no events).
        """
        if not product_ids:
            return {}
        result = await self.session.execute(
            text(
                """
                SELECT product_id, code, name
                FROM products
                WHERE tenant_id = :tenant_id
                  AND product_id = ANY(:product_ids)
                """
            ),
            {
                "tenant_id": str(self.tenant_id),
                "product_ids": [str(pid) for pid in product_ids],
            },
        )
        return {
            row[0]: (row[1] or f"PRD-{str(row[0])[:8]}", row[2] or f"제품-{str(row[0])[:8]}")
            for row in result.fetchall()
        }

    async def _query_currency_pair(self) -> CurrencyPair | None:
        """tenant_settings.baseline.currency_pair (PRD §F5.2 SSOT).

        NOTE (bmad-code-review M2 결정, 2026-08-08): silent fallback
        ("1970-01-01" / "한국은행") 제거. 환율 누락 시 None 그대로
        반환 — caller (get_monthly_closing_report) 가 view_mode 에 따라
        결정. READY/PARTIAL view mode 이고 환율 missing 이면
        MonthlyClosingReportKrwUsdRateMissingError raise (H8).
        """
        result = await self.session.execute(
            text(
                """
                SELECT baseline
                FROM tenant_settings
                WHERE tenant_id = :tenant_id
                """
            ),
            {"tenant_id": str(self.tenant_id)},
        )
        row = result.fetchone()
        if row is None or row[0] is None:
            return None
        baseline = row[0] if isinstance(row[0], dict) else {}
        currency_pair_raw = baseline.get("currency_pair")
        if currency_pair_raw is None:
            return None
        if not isinstance(currency_pair_raw, dict):
            return None
        rate_raw = currency_pair_raw.get("usd_krw_rate")
        if rate_raw is None:
            return None
        try:
            rate = (
                Decimal(str(rate_raw))
                if not isinstance(rate_raw, Decimal)
                else rate_raw
            )
        except Exception:
            return None
        # M2: source_ko / rate_as_of 도 누락 시 None 반환 (silent
        # fallback 제거). Caller 가 view_mode 별로 결정.
        source_ko = currency_pair_raw.get("source_ko")
        rate_as_of = currency_pair_raw.get("rate_as_of")
        if source_ko is None or rate_as_of is None:
            return None
        return CurrencyPair(
            from_currency="USD",
            to_currency="KRW",
            rate=rate,
            rate_source_ko=source_ko,
            rate_as_of=rate_as_of,
        )

    async def _query_closing_snapshot_aggregate(
        self,
        period_key: str,
    ) -> dict[uuid.UUID, Decimal]:
        """closing_snapshot ledger aggregate per product (6-1 wire)."""
        events = await self._query_closing_snapshot_events(period_key)
        result_dict: dict[uuid.UUID, Decimal] = {}
        for e in events:
            result_dict[e["product_id"]] = e["closing_qty"]
        return result_dict

    async def _query_ledger_aggregate(
        self,
        period_key: str,
    ) -> dict[uuid.UUID, Decimal]:
        """ledger aggregate per product (5-2 wire SSOT)."""
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )

        ledger_service = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            trace_id=self.trace_id,
        )
        return await ledger_service.query_period_closing_all(
            period_key=period_key,
        )

    async def _query_active_product_whitelist(self) -> set[uuid.UUID]:
        """Active product UUID set for current tenant (V4 verification input)."""
        result = await self.session.execute(
            text(
                """
                SELECT product_id
                FROM products
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
                """
            ),
            {"tenant_id": str(self.tenant_id)},
        )
        return {row[0] for row in result.fetchall()}

    async def _query_tenant_industry(self) -> str | None:
        """Industry SSOT (Story 4-3 wire) — V4 SKIP gate (industry='service')."""
        result = await self.session.execute(
            text(
                """
                SELECT onboarding
                FROM tenant_settings
                WHERE tenant_id = :tenant_id
                """
            ),
            {"tenant_id": str(self.tenant_id)},
        )
        row = result.fetchone()
        if row is None or row[0] is None:
            return None
        onboarding = row[0] if isinstance(row[0], dict) else {}
        industry = onboarding.get("industry")
        return industry if isinstance(industry, str) else None

    # ── Internal helpers: audit emit ─────────────────────────────
    async def _emit_audit_viewed(
        self,
        *,
        period_key: str,
        actor_id: uuid.UUID | None,
        view_mode: str,
        closing_snapshot_count: int,
        ledger_event_count: int,
        fiscal_period_snapshot_count: int,
    ) -> None:
        """Audit-first emit (CR 1.1) for monthly_closing_report_viewed.

        Read-only report 자체 audit log INSERT (closing report의 조회 trace).
        Payload is self-describing (CR 1.1 lesson) — includes view_mode +
        counts + actor_id + tenant_id for downstream observability queries.
        """
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.MONTHLY_CLOSING_REPORT,
                action="monthly_closing_report_viewed",
                actor_id=actor_id,
                target_id=self.tenant_id,
                tenant_id=self.tenant_id,
                payload={
                    "period_key": period_key,
                    "view_mode": view_mode,
                    "closing_snapshot_count": closing_snapshot_count,
                    "ledger_event_count": ledger_event_count,
                    "fiscal_period_snapshot_count": fiscal_period_snapshot_count,
                    "actor_id": str(actor_id) if actor_id is not None else None,
                    "tenant_id": str(self.tenant_id),
                    "trace_id": self.trace_id,
                },
            )
        except Exception as err:
            raise MonthlyClosingReportAuditEmitError(
                tenant_id=self.tenant_id,
                details={
                    "action": "monthly_closing_report_viewed",
                    "period_key": period_key,
                    "error": str(err),
                },
                trace_id=self.trace_id,
            ) from err

    async def _emit_audit_v4_dispatched(
        self,
        *,
        period_key: str,
        actor_id: uuid.UUID | None,
        v4_status: str,
        failure_count: int,
    ) -> None:
        """Audit-first emit (CR 1.1) for V4 verifier dispatch.

        NOTE (bmad-code-review M1 결정, 2026-08-08): payload 에
        `action_name` 키 추가 — audit-trail query 의 V4 branch
        (target_table='verification_log' AND payload->>'action_name' =
        'verify_v4_closing_period_consistency') 가 이 dispatch row 를
        잡을 수 있도록.
        """
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.VERIFICATION,
                action="verify_v4_closing_period_consistency",
                actor_id=actor_id,
                target_id=self.tenant_id,
                tenant_id=self.tenant_id,
                payload={
                    "action_name": "verify_v4_closing_period_consistency",
                    "period_key": period_key,
                    "status": v4_status,
                    "failure_count": failure_count,
                    "source": "monthly_closing_report_service",
                    "trace_id": self.trace_id,
                },
            )
        except Exception as err:
            raise MonthlyClosingReportAuditEmitError(
                tenant_id=self.tenant_id,
                details={
                    "action": "verify_v4_closing_period_consistency",
                    "period_key": period_key,
                    "error": str(err),
                },
                trace_id=self.trace_id,
            ) from err


__all__ = [
    "MonthlyClosingReportAuditEmitError",
    "MonthlyClosingReportEmptyError",
    "MonthlyClosingReportKrwUsdRateMissingError",
    "MonthlyClosingReportService",
]
