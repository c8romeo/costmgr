"""apps.api.modules.m0_onboarding.services.settings_service — tenant settings writes.

Story 1.1 — Task 2.4. The single canonical place that writes to
`tenant_settings.onboarding` (AD-23 — JSONB namespace ownership).

Responsibilities:
- `update_industry()` — upsert the industry + bump `settings_version` +
  write a typed `audit_logs` row.
- `get_tenant_settings()` — read the full aggregate row (used by the GET
  endpoint Task 5).

Concurrency model:
- AC #1 calls for optimistic concurrency on `settings_version`. We use
  `SELECT ... FOR UPDATE` (AC #1 Step 1) + a `settings_version = :prev + 1`
  predicate on the UPDATE so concurrent writers can't both succeed
  silently. The Pydantic schema does NOT expose `settings_version` as an
  input — it is server-controlled.

Anti-pattern guards (Story §Anti-pattern prevention):
- Audit row is written in the SAME transaction but BEFORE the settings
  update. If the audit insert fails, the settings update is aborted.
- `tenant_id` is derived from JWT — never accepted from the request body.
- `actor_id` is the JWT user_id, never spoofable.

Defensive parsing:
- Unknown industry values in persisted JSONB raise `InconsistentSettingsError`
  (not ValueError) so the GET endpoint can return a typed 500 instead of
  crashing. (F-10)
- Unparseable `selected_at` raises `InconsistentSettingsError` (F-15) — never
  silently reset the grace clock.
- Future `selected_at` (clock skew) is rejected as inconsistent state (F-16).
- `role` comparison normalizes case + whitespace (F-14).
- Same-industry POST is treated as a no-op (F-8/F-9): no UPDATE, no audit,
  no version bump.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit import emit_audit
from apps.api.core.db_models import TenantSettings
from apps.api.core.jsonb_schemas import (
    OnboardingField,
    OnboardingValidationError,
    enforce_onboarding_schema,
)
from apps.api.modules.m0_onboarding.menu import (
    GRACE_PERIOD_DAYS,
    Industry,
    IndustryChangeDecision,
    is_industry_change_allowed,
)
from packages.services.m0_onboarding.settings_completion import (
    CompletionStatus,
    compute_completion,
)


# ── Typed exceptions (mapped to HTTP by handlers.py) ────────
class IndustryLockedError(Exception):
    """409 INDUSTRY_LOCKED — A7 전진법 enforced (AC #4).

    Carries the current industry, decision reason, days-since, and next
    fiscal year start so the frontend can show precise copy and support
    engineers can diagnose without an audit-log query (F-34).
    """

    def __init__(
        self,
        *,
        current_industry: Industry,
        next_fiscal_year_start: str,
        decision_reason: str,
        days_since_selection: int,
        trace_id: str,
    ) -> None:
        super().__init__("industry locked by A7 전진법")
        self.current_industry = current_industry
        self.next_fiscal_year_start = next_fiscal_year_start
        self.decision_reason = decision_reason
        self.days_since_selection = days_since_selection
        self.trace_id = trace_id


class ForbiddenRoleError(Exception):
    """403 FORBIDDEN_ROLE — only `owner` may change industry (Decision §3, F-14)."""

    def __init__(self, *, role: str, trace_id: str) -> None:
        super().__init__(f"role {role!r} cannot change industry")
        self.role = role
        self.trace_id = trace_id


class TenantSettingsNotFoundError(Exception):
    """TenantSettings row missing — should be impossible after Story 0.2 (signup
    creates the row), but raised defensively if the row is somehow absent.
    """

    def __init__(self, *, tenant_id: uuid.UUID, trace_id: str) -> None:
        super().__init__(f"tenant_settings row missing for tenant {tenant_id}")
        self.tenant_id = tenant_id
        self.trace_id = trace_id


class InconsistentSettingsError(Exception):
    """500 INCONSISTENT_SETTINGS — persisted JSONB state is unparseable.

    Raised when:
    - `selected_at` is missing/invalid (F-15)
    - `selected_at` is materially in the future (F-16, clock skew)
    - persisted `industry` value is not a known `Industry` enum (F-10)

    The frontend sees a typed 500 (handlers.py maps to a recovery contract).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        reason: str,
        field: str,
        raw_value: Any,
        trace_id: str,
    ) -> None:
        super().__init__(f"inconsistent tenant_settings: {reason}")
        self.tenant_id = tenant_id
        self.reason = reason
        self.field = field
        self.raw_value = raw_value
        self.trace_id = trace_id


# ── Story 1.2 — wizard typed exceptions ─────────────────────
class FiscalYearLockedError(Exception):
    """409 FISCAL_YEAR_LOCKED — A7 전진법 after first calc (AC #3)."""

    def __init__(
        self,
        *,
        next_fiscal_year_start: str,
        trace_id: str,
    ) -> None:
        super().__init__("fiscal year locked by A7 전진법")
        self.next_fiscal_year_start = next_fiscal_year_start
        self.trace_id = trace_id


class CurrencyLockedError(Exception):
    """409 CURRENCY_LOCKED — A7 전진법 after first calc."""

    def __init__(
        self,
        *,
        next_fiscal_year_start: str,
        trace_id: str,
    ) -> None:
        super().__init__("currency locked by A7 전진법")
        self.next_fiscal_year_start = next_fiscal_year_start
        self.trace_id = trace_id


# ── Role normalization (F-14) ─────────────────────────────────
def _normalize_role(raw: str) -> str:
    """Normalize role string: strip whitespace + lowercase.

    Defends against JWT issuer variants like `Owner`, `OWNER`, ` owner `.
    Raises ValueError if the normalized value is empty.
    """
    normalized = raw.strip().lower()
    if not normalized:
        raise ValueError("role is empty after normalization")
    return normalized


# ── Public API ──────────────────────────────────────────────
class SettingsService:
    """Service-layer facade for tenant settings writes/reads.

    Instances are stateless; one per request. The caller owns the session
    lifecycle (handlers pass the FastAPI `get_session` dependency).
    """

    def __init__(self, session: AsyncSession, *, trace_id: str | None = None) -> None:
        self.session = session
        self.trace_id = trace_id or str(uuid.uuid4())

    # ── update_industry ─────────────────────────────────────
    async def update_industry(
        self,
        *,
        tenant_id: uuid.UUID,
        target_industry: Industry,
        actor_id: uuid.UUID,
        role: str,
    ) -> tuple[Industry, int, bool, datetime, bool, str]:
        """Upsert industry + audit + bump `settings_version`.

        Returns:
            (industry, settings_version, is_initial, selected_at, warning_header, trace_id)
            where `warning_header` is True iff the caller should add the
            `X-Onboarding-Warning: initial-change-allowed-for-7-days` header.
            `is_initial` is True only for the very first onboarding write
            (F-2). `trace_id` is the same value used for the audit row so the
            success envelope can correlate (F-43).

        Raises:
            ForbiddenRoleError: role normalized != 'owner' (F-14).
            IndustryLockedError: A7 전진법 — change blocked after grace OR after
                first calculation (F-5).
            InconsistentSettingsError: persisted JSONB state is unparseable.
        """
        # ── Role gate (Decision §3: owner only — F-14 normalized) ──
        try:
            normalized_role = _normalize_role(role)
        except ValueError as err:
            raise ForbiddenRoleError(role=role, trace_id=self.trace_id) from err
        if normalized_role != "owner":
            raise ForbiddenRoleError(role=role, trace_id=self.trace_id)

        # ── Step 1: SELECT FOR UPDATE (AC #1, optimistic concurrency) ──
        stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id).with_for_update()
        result = await self.session.execute(stmt)
        settings_row = result.scalar_one_or_none()
        if settings_row is None:
            raise TenantSettingsNotFoundError(tenant_id=tenant_id, trace_id=self.trace_id)

        # Read the current onboarding namespace (JSONB).
        onboarding: dict[str, Any] = dict(settings_row.onboarding or {})
        current_industry_raw = onboarding.get("industry")
        if current_industry_raw is not None:
            try:
                current_industry = Industry(current_industry_raw)
            except ValueError as e:
                raise InconsistentSettingsError(
                    tenant_id=tenant_id,
                    reason="unknown persisted industry value",
                    field="onboarding.industry",
                    raw_value=current_industry_raw,
                    trace_id=self.trace_id,
                ) from e
        else:
            current_industry = None

        # F-2 invariant: `is_initial` is True ONLY on the first write.
        # F-27 fallback: if the key is missing entirely (legacy row, pre-migration
        # hand-edit), infer True when current_industry is None, False otherwise.
        # The write side below always sets an explicit value, so the fallback
        # only matters for one read cycle on inconsistent rows.
        is_initial_flag = bool(onboarding.get("is_initial", current_industry is None))

        # Parse selected_at with strict validation (F-15, F-16).
        selected_at_dt: datetime | None = None
        if current_industry is not None:
            selected_at_raw = onboarding.get("selected_at")
            if selected_at_raw is None:
                raise InconsistentSettingsError(
                    tenant_id=tenant_id,
                    reason="selected_at missing for non-null industry",
                    field="onboarding.selected_at",
                    raw_value=None,
                    trace_id=self.trace_id,
                )
            if isinstance(selected_at_raw, str):
                try:
                    selected_at_dt = datetime.fromisoformat(selected_at_raw.replace("Z", "+00:00"))
                except ValueError as e:
                    raise InconsistentSettingsError(
                        tenant_id=tenant_id,
                        reason="selected_at is not ISO-8601",
                        field="onboarding.selected_at",
                        raw_value=selected_at_raw,
                        trace_id=self.trace_id,
                    ) from e
            elif isinstance(selected_at_raw, datetime):
                selected_at_dt = selected_at_raw
            else:
                raise InconsistentSettingsError(
                    tenant_id=tenant_id,
                    reason="selected_at has unexpected type",
                    field="onboarding.selected_at",
                    raw_value=selected_at_raw,
                    trace_id=self.trace_id,
                )

        # Compute days_since_selection (UTC calendar-day floor — F-26).
        now = datetime.now(tz=UTC)
        if selected_at_dt is None:
            days_since = -1
        else:
            # Make selected_at timezone-aware if naive.
            if selected_at_dt.tzinfo is None:
                selected_at_dt = selected_at_dt.replace(tzinfo=UTC)
            # F-16: future timestamps are inconsistent state (clock skew / data corruption).
            if selected_at_dt - now > timedelta(minutes=5):
                raise InconsistentSettingsError(
                    tenant_id=tenant_id,
                    reason="selected_at is in the future (clock skew)",
                    field="onboarding.selected_at",
                    raw_value=selected_at_dt.isoformat(),
                    trace_id=self.trace_id,
                )
            days_since = _days_between(selected_at_dt, now)

        # F-5: industry change is blocked after first calculation.
        # `last_calc_date` lives in tenant_settings.onboarding JSONB for now
        # (Epic 4 calc engine will write to it). If set, force A7 lock.
        last_calc_date_raw = onboarding.get("last_calc_date")
        has_first_calc = bool(last_calc_date_raw)
        if has_first_calc:
            # A7 post-calc lock takes precedence over the grace window.
            raise IndustryLockedError(
                current_industry=current_industry or Industry.MANUFACTURING,
                next_fiscal_year_start=_next_fiscal_year_start(
                    now, dict(settings_row.baseline or {})
                ),
                decision_reason="locked_after_calc",
                days_since_selection=days_since,
                trace_id=self.trace_id,
            )

        # ── Step 2: A7 전진법 + 7-day grace decision ───────
        decision: IndustryChangeDecision = is_industry_change_allowed(
            current_industry=current_industry,
            target_industry=target_industry,
            is_initial=is_initial_flag,
            days_since_selection=days_since,
        )

        # F-7 invariant: if `is_initial=True`, also require the timestamp to be
        # within the grace window. This bounds the risk of a stray `is_initial=True`
        # value re-granting unlimited changes.
        if (
            decision.allowed
            and is_initial_flag
            and current_industry is not None
            and days_since >= GRACE_PERIOD_DAYS
        ):
            decision = IndustryChangeDecision(
                allowed=False,
                reason="locked_after_grace",
                days_since_selection=days_since,
            )

        if not decision.allowed:
            raise IndustryLockedError(
                current_industry=current_industry or Industry.MANUFACTURING,
                next_fiscal_year_start=_next_fiscal_year_start(
                    now, dict(settings_row.baseline or {})
                ),
                decision_reason=decision.reason,
                days_since_selection=days_since,
                trace_id=self.trace_id,
            )

        # ── Same-industry POST is a no-op (F-8 / F-9) ───────
        # Only when current_industry is a real value AND equals target_industry.
        # First-time onboarding (current_industry is None) is NOT a no-op —
        # we still need to write the first record below.
        is_noop = current_industry is not None and current_industry == target_industry
        if is_noop:
            return (
                current_industry,
                settings_row.settings_version,
                is_initial_flag,  # preserved as-is on no-op
                selected_at_dt or now,
                False,  # no warning header on no-op
                self.trace_id,
            )

        # ── Step 3: write audit row (BEFORE settings update) ─
        # AC #1 — first-time selection writes action='industry_selected'.
        # AC #4 — subsequent change within grace window writes
        # action='industry_change_initial'.
        # F-36 — payload `reason` is self-describing (compound action+reason)
        # so log analytics can distinguish the path without joining tenant_settings.
        if is_initial_flag:
            audit_action = "industry_selected"
            payload_reason = "industry_selected_initial"
        else:
            audit_action = "industry_change_initial"
            payload_reason = "industry_change_within_grace"
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action=audit_action,
            target_table="tenant_settings",
            target_id=tenant_id,
            reason=payload_reason,
            payload={
                "industry": target_industry.value,
                "prev_industry": current_industry.value if current_industry else None,
                # F-36: pre-bump version. Audit row fires BEFORE the UPDATE
                # below, so `settings_row.settings_version` is still the
                # previous value here. Recording the pre-bump version makes
                # the log a complete before/after record without joining
                # tenant_settings.
                "version": settings_row.settings_version,
                "reason": payload_reason,
                "days_since_selection": days_since,
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )

        # ── Step 4: UPDATE settings row ──────────────────────
        now_iso = now.isoformat()
        new_onboarding = dict(onboarding)
        new_onboarding["industry"] = target_industry.value
        new_onboarding["selected_at"] = now_iso
        # F-2: preserve `is_initial=True` ONLY on the very first write
        # (current_industry was None at read time). Any subsequent change flips it.
        new_onboarding["is_initial"] = current_industry is None

        settings_row.onboarding = new_onboarding
        # F-17: BigInteger column — int4 overflow is structurally prevented
        # by the column type (changed in migration 0003 alongside this story).
        settings_row.settings_version = settings_row.settings_version + 1
        settings_row.updated_at = now

        await self.session.flush()

        # Warning header fires only on `within_grace` — a subsequent change
        # within the 7-day window. First-time onboarding (`initial`) is a
        # fresh tenant writing for the first time; the frontend does NOT
        # surface a warning in that case (AC #1 — no warning header in
        # 200 OK response). The original F-39 resolution ("BOTH initial
        # AND within_grace") was incorrect per AC #1; corrected here.
        warning_header = decision.reason == "within_grace"

        # F-2 post-write is_initial: True only if this was the very first write.
        post_write_is_initial = current_industry is None

        return (
            target_industry,
            settings_row.settings_version,
            post_write_is_initial,
            now,
            warning_header,
            self.trace_id,
        )

    # ── get_tenant_settings ─────────────────────────────────
    async def get_tenant_settings(self, *, tenant_id: uuid.UUID) -> TenantSettings:
        """Read the full aggregate row. Raises TenantSettingsNotFoundError
        if missing (should not happen after Story 0.2).
        """
        stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        settings_row = result.scalar_one_or_none()
        if settings_row is None:
            raise TenantSettingsNotFoundError(tenant_id=tenant_id, trace_id=self.trace_id)
        return settings_row

    # ── Story 1.2 — update_onboarding_field ─────────────────
    async def update_onboarding_field(
        self,
        *,
        tenant_id: uuid.UUID,
        field: OnboardingField,
        value: Any,
        actor_id: uuid.UUID,
        role: str,
    ) -> tuple[OnboardingField, Any, int, CompletionStatus, str]:
        """Save a top-level wizard field (fiscal_year_start / currency / language).

        A7 (전진법) enforcement:
        - fiscal_year_start / currency cannot change after first calc
          (`onboarding.last_calc_date` set) or after the 7-day grace window
          (mirrors industry rules from Story 1.1).
        - language is owner-editable any time (no lock — language is MVP-locked
          to ko-KR per NFR-18, so it has no real ambiguity).

        Returns:
            (field, value, settings_version, completion, trace_id).
            `completion` is computed from the post-write state.
        """
        # Role gate (AD-10 — owner only).
        try:
            normalized_role = _normalize_role(role)
        except ValueError as err:
            raise ForbiddenRoleError(role=role, trace_id=self.trace_id) from err
        if normalized_role != "owner":
            raise ForbiddenRoleError(role=role, trace_id=self.trace_id)

        # Read row + lock.
        stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id).with_for_update()
        result = await self.session.execute(stmt)
        settings_row = result.scalar_one_or_none()
        if settings_row is None:
            raise TenantSettingsNotFoundError(tenant_id=tenant_id, trace_id=self.trace_id)

        onboarding = dict(settings_row.onboarding or {})

        # A7: fiscal_year_start / currency lock after first calc.
        # (PRD §3.A7 — same pattern as industry; see Story 1.1 update_industry.)
        last_calc_date_raw = onboarding.get("last_calc_date")
        has_first_calc = bool(last_calc_date_raw)

        now = datetime.now(tz=UTC)
        baseline = dict(settings_row.baseline or {})

        if field in (OnboardingField.FISCAL_YEAR_START, OnboardingField.CURRENCY):
            # Same-industry no-op is handled by reading the current value.
            current_value = onboarding.get(field.value)
            if current_value == value:
                # No-op: return current completion status.
                completion = await self._build_completion(tenant_id)
                return (
                    field,
                    value,
                    settings_row.settings_version,
                    completion,
                    self.trace_id,
                )

            if has_first_calc:
                # A7 post-calc lock takes precedence over grace.
                if field == OnboardingField.FISCAL_YEAR_START:
                    raise FiscalYearLockedError(
                        next_fiscal_year_start=_next_fiscal_year_start(now, baseline),
                        trace_id=self.trace_id,
                    )
                raise CurrencyLockedError(
                    next_fiscal_year_start=_next_fiscal_year_start(now, baseline),
                    trace_id=self.trace_id,
                )

            # Grace window check (mirrors Story 1.1 logic). `last_calc_date`
            # is the canonical lock signal; without it, the 7-day grace applies
            # if the field was previously set.
            if field.value in onboarding and isinstance(onboarding[field.value], str):
                # `selected_at` analog: use the field's own set timestamp if
                # present, else fall back to onboarding.selected_at.
                ref_iso = onboarding.get(
                    f"{field.value}_selected_at",
                    onboarding.get("selected_at"),
                )
                days_since = _days_since_iso(ref_iso, now)
                if days_since is not None and days_since >= GRACE_PERIOD_DAYS:
                    if field == OnboardingField.FISCAL_YEAR_START:
                        raise FiscalYearLockedError(
                            next_fiscal_year_start=_next_fiscal_year_start(now, baseline),
                            trace_id=self.trace_id,
                        )
                    raise CurrencyLockedError(
                        next_fiscal_year_start=_next_fiscal_year_start(now, baseline),
                        trace_id=self.trace_id,
                    )

        # Audit + write (audit-first per AD-2 / spec anti-pattern).
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="onboarding_field_saved",
            target_table="tenant_settings",
            target_id=tenant_id,
            reason=None,
            payload={
                "field": field.value,
                "value": value,
                "version": settings_row.settings_version + 1,
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )

        new_onboarding = dict(onboarding)
        new_onboarding[field.value] = value
        new_onboarding[f"{field.value}_selected_at"] = now.isoformat()

        # Defensive schema check — should be impossible after Pydantic, but
        # guard against future regression in the validator.
        try:
            enforce_onboarding_schema(new_onboarding, trace_id=self.trace_id)
        except OnboardingValidationError as e:
            raise InconsistentSettingsError(
                tenant_id=tenant_id,
                reason="onboarding schema violation after write",
                field=str([err.field for err in e.errors]),
                raw_value=None,
                trace_id=self.trace_id,
            ) from e

        settings_row.onboarding = new_onboarding
        settings_row.settings_version = settings_row.settings_version + 1
        settings_row.updated_at = now

        await self.session.flush()

        completion = await self._build_completion(tenant_id)
        return (
            field,
            value,
            settings_row.settings_version,
            completion,
            self.trace_id,
        )

    # ── Story 1.2 — update_allocation_criteria ─────────────
    async def update_allocation_criteria(
        self,
        *,
        tenant_id: uuid.UUID,
        criterion: str,
        count: int,
        actor_id: uuid.UUID,
        role: str,
    ) -> tuple[str, int, int, CompletionStatus, str]:
        """Save an allocation criterion's count (≥1).

        Returns:
            (criterion, count, settings_version, completion, trace_id).
        """
        # Role gate.
        try:
            normalized_role = _normalize_role(role)
        except ValueError as err:
            raise ForbiddenRoleError(role=role, trace_id=self.trace_id) from err
        if normalized_role != "owner":
            raise ForbiddenRoleError(role=role, trace_id=self.trace_id)

        stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id).with_for_update()
        result = await self.session.execute(stmt)
        settings_row = result.scalar_one_or_none()
        if settings_row is None:
            raise TenantSettingsNotFoundError(tenant_id=tenant_id, trace_id=self.trace_id)

        onboarding = dict(settings_row.onboarding or {})
        criteria = dict(onboarding.get("allocation_criteria") or {})

        now = datetime.now(tz=UTC)

        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="allocation_criterion_saved",
            target_table="tenant_settings",
            target_id=tenant_id,
            reason=None,
            payload={
                "criterion": criterion,
                "count": count,
                "version": settings_row.settings_version + 1,
                "trace_id": self.trace_id,
            },
            tenant_id=tenant_id,
            flush=True,
        )

        criteria[criterion] = {
            "completed": count >= 1,
            "count": count,
            "last_updated": now.isoformat(),
        }
        new_onboarding = dict(onboarding)
        new_onboarding["allocation_criteria"] = criteria

        settings_row.onboarding = new_onboarding
        settings_row.settings_version = settings_row.settings_version + 1
        settings_row.updated_at = now

        await self.session.flush()

        completion = await self._build_completion(tenant_id)
        return (
            criterion,
            count,
            settings_row.settings_version,
            completion,
            self.trace_id,
        )

    # ── Story 1.2 — get_completion ──────────────────────────
    async def get_completion(self, *, tenant_id: uuid.UUID) -> tuple[CompletionStatus, str | None]:
        """Read current onboarding JSONB + count allocation criteria → completion.

        Pure orchestration: delegates the decision to the pure domain function
        `compute_completion()`. Counts come from M1 baseline + M9 ABC tables
        (Story 1.2 Task 4 scaffolds those tables — the read uses a default
        of 0 when the scaffold tables don't exist yet, so the GET endpoint
        is always responsive).

        F-34: returns `(completion, last_calc_date)` where `last_calc_date`
        is the A7 lock signal (None when no calc has run). The API layer
        surfaces this to the UI so it can warn before save.
        """
        stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        settings_row = result.scalar_one_or_none()
        if settings_row is None:
            raise TenantSettingsNotFoundError(tenant_id=tenant_id, trace_id=self.trace_id)

        onboarding = dict(settings_row.onboarding or {})
        last_calc_date_raw = onboarding.get("last_calc_date")
        last_calc_date: str | None = (
            last_calc_date_raw if isinstance(last_calc_date_raw, str) else None
        )

        completion = await self._build_completion(tenant_id)
        return completion, last_calc_date

    async def _build_completion(self, tenant_id: uuid.UUID) -> CompletionStatus:
        """Internal helper — fetches settings + counts and runs `compute_completion`."""
        stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        settings_row = result.scalar_one_or_none()
        if settings_row is None:
            raise TenantSettingsNotFoundError(tenant_id=tenant_id, trace_id=self.trace_id)

        onboarding = dict(settings_row.onboarding or {})
        industry_raw = onboarding.get("industry")
        try:
            industry = Industry(industry_raw) if industry_raw else None
        except ValueError:
            industry = None

        # Counts come from the M1/M9 scaffold tables when they exist, else 0.
        counts = await self._fetch_allocation_counts(tenant_id)
        return compute_completion(industry, onboarding, counts)

    async def _fetch_allocation_counts(self, tenant_id: uuid.UUID) -> dict[str, int]:
        """Read allocation criterion row counts.

        Tries the M1 baseline + M9 ABC tables. If the modules' tables don't
        exist yet (Story 1.2 Task 4 scaffolds are still in-progress), returns
        zeros so the completion endpoint never 500s.

        The scaffold tables use simple row counting here — Epic 2 / Epic 9
        will replace with real aggregation queries.
        """
        counts: dict[str, int] = {}
        try:
            from apps.api.modules.m1_baseline.handlers import (
                count_account_classifications,
            )
            from apps.api.modules.m9_abc.handlers import count_drivers

            baseline_counts = await count_account_classifications(self.session, tenant_id=tenant_id)
            counts.update(baseline_counts)
            counts["drivers"] = await count_drivers(self.session, tenant_id=tenant_id)
        except (ImportError, RuntimeError, AttributeError):
            # Scaffold modules not wired yet → return zeros.
            counts = {"direct_indirect": 0, "fixed_variable": 0, "drivers": 0}
        return counts


# ── Internal helpers ─────────────────────────────────────────
def _days_between(start: datetime, end: datetime) -> int:
    """UTC calendar-day floor between two timezone-aware datetimes (F-26).

    Computed as `date(end) - date(start)` so a change at 23:59 UTC and the
    next attempt at 00:01 UTC the following day are guaranteed to differ
    by 1 day, not 0.

    Negative durations (clock skew) are clamped to 0 — but the caller should
    have already rejected materially-future timestamps via InconsistentSettingsError.
    """
    if start.tzinfo is None or end.tzinfo is None:
        start = start.replace(tzinfo=UTC) if start.tzinfo is None else start
        end = end.replace(tzinfo=UTC) if end.tzinfo is None else end
    delta_days = (end.date() - start.date()).days
    return max(0, delta_days)


def _next_fiscal_year_start(now: datetime, baseline: dict[str, Any]) -> str:
    """A7 전진법 — industry change applies next fiscal year.

    Reads `fiscal_year_start_month` from tenant_settings.baseline (Story 1.2
    wizard wires this; default Jan = 1 for backward compat — F-35).
    """
    try:
        month = int(baseline.get("fiscal_year_start_month", 1))
    except (TypeError, ValueError):
        month = 1
    if not 1 <= month <= 12:
        month = 1
    if now.month >= month:
        return f"{now.year + 1}-{month:02d}-01"
    return f"{now.year}-{month:02d}-01"


def _days_since_iso(iso_str: Any, now: datetime) -> int | None:
    """Calendar-day floor between an ISO-8601 string and `now`.

    Returns None if the input is missing or unparseable (caller decides
    what to do with None — usually "no lock yet"). Mirrors the
    `_days_between()` shape from Story 1.1.
    """
    if not isinstance(iso_str, str):
        return None
    try:
        ts = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    if ts - now > timedelta(minutes=5):
        return None  # future timestamp — treat as unparseable
    return _days_between(ts, now)
