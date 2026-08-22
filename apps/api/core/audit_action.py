"""apps.api.core.audit_action — single source of truth for audit log actions.

Story 4.3 (A5 spike Phase 1) — Epic 1·2·3·4 CR 1.1 lesson, 4-epic
recurrence pattern. Action values were typed as free-form `str` literals
scattered across 17+ call sites. This module centralizes:

1. `ActionClass` — the audit target class (which table / aggregate)
2. `AuditAction` — the typed verb-subject-context union per ActionClass
3. `AuditLogType` — the destination ledger discriminator
4. `emit_audit_typed()` — typed wrapper that validates (ActionClass, action)
   and routes to the correct destination table.

Per AD-11: this module is in `apps/api/core/` (infra layer). It does NOT
import `packages.cost_engine` directly.

Per AD-22: append-only-leaning preserved. Triggers in migration 0001 still
block UPDATE/DELETE on audit_logs.

Phase 1 (this commit): introduce `audit_action.py` + migrate audit_logs
call sites (17) + CalcLog (3) + `verification_log` (via existing
`_write_verification_log` in `calc_orchestrator.py`). DB schema unchanged
for audit_logs; verification_log gets a CHECK constraint in Alembic 0013.

Phase 2 (Epic 5+): inventory_ledger / reversal_log registry slots pre-fill.
Phase 3 (production data 누적 후): audit_logs / calc_log CHECK additions.
Phase 4 (Epic 5 spec 진입 시): Convention §10 lint + drift detector.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession


# ────────────────────────────────────────────────────────────
# 1. ActionClass — the target class (which table / aggregate)
# ────────────────────────────────────────────────────────────
class ActionClass(str, __import__("enum").Enum):
    """Audit target class. One enum value per logical target.

    Order = introduction order. Do NOT renumber — append-only.
    """

    TENANT_SETTINGS = "tenant_settings"
    SERVICE_ROLE = "service_role"
    UPLOADED_DOCUMENT = "uploaded_document"
    INPUT_DRAFT = "input_draft"
    PRODUCT = "product"
    BOM_LINE = "bom_line"
    MONTHLY_INPUT_ROW = "monthly_input_row"
    MONTHLY_INPUT_PERIOD = "monthly_input_period"
    CALC_LOG = "calc_log"
    VERIFICATION_LOG = "verification_log"  # Story 4.3 (NEW)
    INVENTORY_LEDGER = "inventory_ledger"  # Epic 5 (NEW — slot pre-fill)
    REVERSAL_LOG = "reversal_log"  # Epic 11 (NEW — slot pre-fill)
    CLOSING_GUARD = "closing_guard"  # Story 5.3 (NEW — closing ≥ 0 invariant audit)
    VERIFICATION = "verification"  # Story 5.3 (NEW — V3 closing invariant verification)
    CLOSING_PERIOD = "closing_period"  # Story 6.1 (NEW — closing period service audit-first)
    MONTHLY_CLOSING = "monthly_closing"  # Story 11.2 (NEW — 4-stage close sequence lock audit)
    MONTHLY_CLOSING_REPORT = "monthly_closing_report"  # Story 6.2 (NEW — monthly closing report read-only audit)
    SNAPSHOT_PERSISTENCE = "snapshot_persistence"  # Story 11.3 (NEW — AD-20 state machine 영구화 audit)
    REOPEN_OPERATOR = "reopen_operator"  # Story 11.3 (NEW — W2 reopen flow audit)
    TWO_FACTOR_AUTH = "two_factor_auth"  # Story 12.1 (NEW — 2FA mandatory gate audit)
    ACCOUNT_BACKUP = "account_backup"  # Story 12.2 (NEW — daily auto-backup + JSON self-download audit)
    ACCOUNT_DELETION = "account_deletion"  # Story 12.3 (NEW — destructive endpoint + consent envelope audit)
    AI_EXTRACTION_EXECUTED = "ai_extraction_executed"  # Story 10.1 (NEW — monthly input extraction audit-first)
    AI_INSIGHT_CACHE_ACCESSED = "ai_insight_cache_accessed"  # Story 10.2
    TENANT = "tenant"  # Phase 3-0 (NEW — tenant signup completion audit-first)
    AUTH = "auth"  # Epic 15 (NEW — magic_link + social_oauth + sso audit-first INSERT)
    INFRA = "infra"  # Phase 5 (NEW — cross-region backup + failover + DR drill audit-first INSERT)
    AUDIT = "audit"  # Epic 17 (NEW — audit log viewer export audit-first INSERT)


# ────────────────────────────────────────────────────────────
# 2. AuditLogType — destination ledger discriminator
# ────────────────────────────────────────────────────────────
AuditLogType = Literal[
    "audit_logs",
    "calc_log",
    "verification_log",
    "inventory_ledger",
    "reversal_log",
]


# ────────────────────────────────────────────────────────────
# 3. AuditAction — typed literal per ActionClass
# ────────────────────────────────────────────────────────────
# tenant_settings actions (m0_onboarding + m10_ai company_subblock)
TenantSettingsAction = Literal[
    "industry_selected",  # AC #1 first-time
    "industry_change_initial",  # AC #4 within-grace
    "onboarding_field_saved",  # Story 1.2 fiscal_year_start / currency / language
    "allocation_criterion_saved",  # Story 1.2 allocation_criteria JSONB
    "company_subblock_promoted",  # Story 1.3 confirmed drafts → tenant_settings JSONB
]

# tenant actions (Phase 3-0 — signup completion)
# Distinct from TenantSettingsAction because the target aggregate is
# the `tenants` row itself (creation), not the `tenant_settings` JSONB.
TenantAction = Literal[
    "tenant_signup_completed",  # Phase 3-0 — atomic tenants + users + tenant_memberships + tenant_settings
]

# service_role action
ServiceRoleAction = Literal[
    "service_role_bypass",  # AD-2 audit-first guard
]

# uploaded_document actions (m10_ai)
UploadedDocumentAction = Literal[
    "document_uploaded",
    "document_reprocess_requested",
    "document_retention_soft_deleted",
]

# input_draft actions (m10_ai)
# Story 10.4 (Epic 10) — `input_draft_promoted` EXTENSION for
# InputPromoter.promote() audit-first INSERT Row 1 (AD-17 verbatim
# "records actor plus draft hash in audit_logs"). The 2 existing
# values (`input_draft_confirm` / `input_draft_reject`) cover the
# review-state transitions; the new value covers the
# state-machine terminal `state='promoted'` transition.
# Drift detector: tests/integration/test_audit_action_consistency.py
# enforces ActionClass registry ↔ DB CHECK ↔ call sites parity.
InputDraftAction = Literal[
    "input_draft_confirm",
    "input_draft_reject",
    "input_draft_promoted",  # 10-4 AD-17 audit-first INSERT Row 1
]

# product actions (m1_baseline)
ProductAction = Literal[
    "product_created",
    "product_updated",  # mixed PATCH
    "product_type_changed",  # type-only PATCH
    "product_soft_deleted",
    "product_reactivated",
]

# bom_line actions (m1_baseline)
BOMLineAction = Literal[
    "bom_set",  # bulk replace
    "bom_cleared",
]

# monthly_input_row actions (m2_input)
MonthlyInputRowAction = Literal[
    "monthly_input_row_created",
    "monthly_input_row_updated",  # both save_row update + update_row PATCH
    "monthly_input_row_deleted",
]

# monthly_input_period actions (m2_input)
MonthlyInputPeriodAction = Literal[
    "monthly_input_mode_changed",
    # Story 5.1 (Epic 5) — opening carry chain audit-first events.
    # Audit routes to audit_logs (NOT inventory_ledger — that's 5-2).
    "monthly_input_period_opening_carried",  # auto/manual carry applied
    "monthly_input_period_opening_locked",  # first-row lock marker added
    # Story 11.1 (Epic 11) — opening inventory unlocked on reversal sequence.
    # Audit emit when M11 reversal sequence crosses periods and the
    # target event's period had been previously locked (the lock marker
    # must be cleared before the reversal INSERT completes).
    "monthly_input_period_opening_unlocked",  # Story 11.1 (M11 unlock marker)
]

# calc_log actions (m3_calculate) — DB CHECK constraint applied (0012)
CalcLogAction = Literal[
    "compute",
    "idempotent_skip",
    "rollback",
]

# verification_log actions (Story 4.3 NEW + Story 4.4 forward-lock)
VerificationLogAction = Literal[
    "verification_passed",
    "verification_failed",
    "verification_skipped",
    "verify_v8_golden_match",  # Story 4.4 (V8 골든 mismatch audit-first)
]

# inventory_ledger actions (Story 5.2 — AC #4 + OQ5 cj-style default).
# Epic 5 ships 3 actions (event append, append-only violation, reversal
# request). Epic 11 forward-fills 2 actions (reversal logged / rejected
# — M11 authority approve/deny). Epic 6 close-out forward-fills 1
# action (reprojection trigger — periodic close maintenance).
# Drift detector: registry ↔ DB CHECK ↔ call sites (3-way gate).
InventoryLedgerAction = Literal[
    # Story 5.2 immediate (this commit)
    "inventory_ledger_event_appended",  # primary INSERT path (5-2 T3)
    "inventory_ledger_event_rejected",  # append-only violation (DB trigger)
    "inventory_ledger_reversal_requested",  # M4 entrypoint (5-2 T6 forward-fill)
    # Epic 11 forward-fill stubs (M11 authority approve/deny sequence)
    "inventory_ledger_reversal_logged",  # M11 reversal approved + INSERTed
    "inventory_ledger_reversal_rejected",  # M11 reversal denied
    # Epic 6 close-out forward-fill stub (periodic close maintenance)
    "inventory_ledger_reprojection_triggered",  # M6 closing_snapshot materialized
]

# reversal_log actions (Epic 11 — Story 11.1 fill).
# AD-22 reversal sequence + AD-25 cache invalidation publisher audits.
# 5 values fill:
# - `reversal_negating_inserted` — sign-negating row INSERTED (AD-22 seq step 1)
# - `reversal_corrected_inserted` — corrected row INSERTED (AD-22 seq step 2)
# - `reversal_rejected` — authorize_reversal denied (403/422 envelope)
# - `reversal_unauthorized` — caller actor/role mismatch (403 envelope)
# - `m11_reversal_handler_invoked` — M11 module entrypoint invoked (audit-first)
# DB CHECK constraint mirror: reversal_log CHECK constraint includes these
# 5 values (Alembic 0019_m11_reversal_ledger forward-fill).
# Drift detector: tests/integration/test_audit_action_consistency.py enforces
# registry ↔ DB CHECK ↔ call sites parity (3-way gate).
ReversalLogAction = Literal[
    "reversal_negating_inserted",
    "reversal_corrected_inserted",
    "reversal_rejected",
    "reversal_unauthorized",
    "m11_reversal_handler_invoked",
]

# closing_guard actions (Story 5.3 NEW — AC #2 + AC #5).
# Closing ≥ 0 invariant (PRD §F4.2 + §V3) audit-first events:
# - `closing_guard_violated` — invariant.code=NEGATIVE_CLOSING detected
#   (manual close attempt rejected)
# - `closing_guard_passed` — invariant.code=CLOSING_OK after verify
#   (close-time hook 200 OK response)
# - `v3_closing_invariant_verified` — V3 verdict emitted (PASS/FAIL/SKIP)
ClosingGuardAction = Literal[
    "closing_guard_violated",
    "closing_guard_passed",
    "v3_closing_invariant_verified",
]

# verification actions (Story 5.3 NEW — V3 closing invariant verifier).
# Distinct from VERIFICATION_LOG: VERIFICATION_LOG tracks per-rule
# verdicts (PASS/FAIL/SKIP + V8 golden match); VERIFICATION tracks
# cross-rule invariants (V3 closing ≥ 0 + future Epic 11 reversal
# verification + Epic 12 close-out verification + Story 6.1 V4
# closing snapshot 일관성 verification).
VerificationAction = Literal[
    "verify_v3_closing_invariant",  # Story 5.3 V3 rule audit (PASS/FAIL/SKIP)
    "verify_v4_closing_period_consistency",  # Story 6.1 V4 rule audit
]

# closing_period actions (Story 6.1 NEW — closing period service audit-first).
# PRD §F4.3 + AD-6 fiscal-period close lock. Audit routes to audit_logs
# (ActionClass.CLOSING_PERIOD). 3 values:
# - `closing_period_confirmed` — confirm_closing_period succeeded
#   (closing_snapshot ledger events INSERTed + monthly_input_periods
#   UPDATEd to 'closed' status).
# - `closing_period_blocked` — confirm_closing_period raised
#   ClosingPeriodBlockedError (negative closing invariant violation).
# - `closing_period_snapshot_inconsistency` — V4 verifier detected
#   inconsistency (V4 status='failed'). Audit-first V4 dispatch
#   (CR 1.1 lesson) — emitted BEFORE raising the typed exception.
ClosingPeriodAction = Literal[
    "closing_period_confirmed",
    "closing_period_blocked",
    "closing_period_snapshot_inconsistency",
]

# monthly_closing actions (Story 11.2 NEW — 4-stage close sequence lock).
# PRD §F11.1 + §8.M11(a) + AD-6 close lock. Audit routes to
# `audit_logs` (ActionClass.MONTHLY_CLOSING). 4 values:
# - `closing_sequence_initiated` — initiate_close_sequence succeeded
#   (fiscal_periods INSERT + close_sequence_state='divisions').
# - `closing_sequence_step_completed` — step_complete dispatch
#   (divisions / manufacturing / abc / common).
# - `closing_sequence_blocked` — partial_close_guard rejected
#   (4단계 미완료 → 409 PARTIAL_CLOSE_BLOCKED). Audit-first emit
#   BEFORE raising the typed exception.
# - `closing_sequence_confirmed` — confirm_close_sequence succeeded
#   (fiscal_periods.status='closed' + close_sequence_state='confirmed').
MonthlyClosingAction = Literal[
    "closing_sequence_initiated",
    "closing_sequence_step_completed",
    "closing_sequence_blocked",
    "closing_sequence_confirmed",
]

# monthly_closing_report actions (Story 6.2 NEW — read-only report 자체 audit).
# PRD §F5 + §F5.2 + §V4. Audit routes to audit_logs
# (ActionClass.MONTHLY_CLOSING_REPORT). 2 values:
# - `monthly_closing_report_viewed` — read-only report 조회 audit log
#   INSERT (closing report의 조회 trace). CR 1.1 idempotent re-view
#   skip은 service-layer에서 1 view = 1 audit 발동.
# - `closing_pdf_export_viewed` — Story 6.3 PDF export audit log INSERT
#   (PDF/A4 byte stream export trace). 6-2 wire의 `monthly_closing_report_viewed`
#   와 별도 액션으로 분리 — 동일 ActionClass 내 row 타입 식별 가능.
MonthlyClosingReportAction = Literal[
    "monthly_closing_report_viewed",
    "closing_pdf_export_viewed",
]

# snapshot_persistence actions (Story 11.3 NEW — AD-20 state machine
# 영구화 audit). PRD §F11.2 + AD-20 + AD-22. Audit routes to
# `audit_logs` (ActionClass.SNAPSHOT_PERSISTENCE). 4 values:
# - `snapshot_persistence_committed` — AD-20 verified → committed
#   transition succeeded (T3 wire).
# - `snapshot_persistence_reversed` — AD-22 영구화 committed → reversed
#   transition succeeded (T4 wire).
# - `snapshot_persistence_blocked` — 3-tier guard rejected
#   (state != 'committed' or fiscal_periods.status != 'closed').
# - `snapshot_persistence_reopened` — W2 reopen flow succeeded
#   (fiscal_periods.status='closed' → 'open' transition).
SnapshotPersistenceAction = Literal[
    "snapshot_persistence_committed",
    "snapshot_persistence_reversed",
    "snapshot_persistence_blocked",
    "snapshot_persistence_reopened",
]

# reopen_operator actions (Story 11.3 NEW — W2 reopen flow audit).
# PRD §F11.4 + AD-10 owner-only + AD-15 audit-justification. Audit routes
# to `audit_logs` (ActionClass.REOPEN_OPERATOR). 2 values:
# - `reopen_authorized` — execute_reopen kernel authorization succeeded
#   (pre-UPDATE emit).
# - `reopen_completed` — execute_reopen succeeded
#   (fiscal_periods.status='closed' → 'open' + AD-25 4 channels publish).
ReopenOperatorAction = Literal[
    "reopen_authorized",
    "reopen_completed",
]


# two_factor_auth actions (Story 12.1 NEW — 2FA mandatory gate audit).
# PRD §F12.1 + §M12-a + AD-22 audit-first + NFR6 AES-256-GCM at-rest.
# Audit routes to `audit_logs` (ActionClass.TWO_FACTOR_AUTH). 6 values:
# - `two_factor_setup_initiated` — setup_totp succeeded (CR 1.1 audit-first
#   for `users.totp_secret` ciphertext + `users.totp_recovery_codes_hash` JSONB
#   mutation). Idempotent no-op: re-setup does NOT re-emit (CR 1.1 lesson).
# - `two_factor_setup_completed` — verify_and_enable_totp succeeded (first
#   successful TOTP code entry flips `users.twofa_enabled` true).
# - `two_factor_challenge_passed` — verify_totp_challenge succeeded (M2
#   entry gate 통과, JWT 2FA claim set).
# - `two_factor_challenge_failed` — verify_totp_challenge rejected (TOTP
#   invalid + failed_attempts increment). Audit emit BEFORE raising
#   TotpInvalidCodeError / TotpLockoutError (A5 forward-lock).
# - `two_factor_recovery_consumed` — verify_recovery_code succeeded
#   (one-time recovery code consumed — entry used_at marker flipped).
# - `two_factor_disabled` — disable_totp succeeded (owner-initiated
#   disable — requires current valid TOTP code + reason captured).
# DB CHECK constraint mirror: audit_logs CHECK includes the 6 values
# (Alembic 0022_m12_two_factor_auth wire). Drift detector enforces
# ActionClass registry ↔ DB CHECK ↔ call sites parity (3-way gate).
TwoFactorAuthAction = Literal[
    "two_factor_setup_initiated",
    "two_factor_setup_completed",
    "two_factor_challenge_passed",
    "two_factor_challenge_failed",
    "two_factor_recovery_consumed",
    "two_factor_disabled",
]


# account_backup actions (Story 12.2 NEW — daily auto-backup + JSON self-download).
# PRD §F12.2 + NFR4 backup + AD-9 Seoul + AD-15 §4 envelope. Audit routes
# to `audit_logs` (ActionClass.ACCOUNT_BACKUP). 5 values:
# - `backup_created` — successful backup row INSERT
#   (run_backup / trigger_backup audit-first emit BEFORE row commit).
# - `backup_failed` — try/except guard fires BEFORE raise
#   (BackupExportServiceError surfaces to cron runner; audit captures
#   failure context).
# - `backup_retention_purged` — 30-day soft-delete UPDATE succeeded
#   (purged_at timestamp set; row remains for audit).
# - `backup_downloaded` — owner self-download audit (per-row download
#   trace — forensic chain for "who downloaded what when").
# - `backup_triggered` — manual owner trigger via POST /backups/trigger
#   (manual run triggered — same action_class as backup_created but
#   distinct audit entry for forensic separation).
# Drift detector: tests/integration/test_audit_action_consistency.py
# enforces ActionClass registry ↔ DB CHECK (no-op for audit_logs) ↔
# call sites parity (3-way gate).
AccountBackupAction = Literal[
    "backup_created",
    "backup_failed",
    "backup_retention_purged",
    "backup_downloaded",
    "backup_triggered",
]

# Story 12.3 — account deletion + retention consent (epics.md §F12.3).
# 8 NEW actions per AC #4 — destructive endpoint 3-layer TOTP defense
# (CR 12-5 L3) requires audit trace for all code paths (success + failure).
AccountDeletionAction = Literal[
    "deletion_requested",  # AC #4 row 1 — AFTER successful state transition
    "deletion_consent_given",  # AC #4 row 2 — consent text encrypted + persisted
    "deletion_cancelled",  # cancel_deletion route
    "deletion_anonymized",  # cron anonymization step
    "tenant_hard_deleted",  # AC #3 — cron hard-delete 30일 후
    "deletion_failed",  # cron hard-delete failure / general failure
    "deletion_2fa_failed",  # CR 12-5 L3 Layer 3 — handler audit-first BEFORE raise
    "two_factor_verified",  # CR 12-5 L3 Layer 3 — handler audit-first BEFORE challenge_token mint
]

# Story 10.1 (Epic 10) — ai_extraction_executed (PRD §8.1 M10 (c)).
# AD-7 verbatim: AI output → input_drafts (NOT confirmed_inputs).
# monthly_extraction_executed is the live audit-first INSERT value
# used in apps/api/modules/m10_ai/service.py:944 (#d56959c).
# The other 2 values are forward-fill for 10-1 follow-up sprint
# (D-10-1-DEFER-3 frontend RED 배지 후속) + 10-4 (AD-7 strict
# invariant promote-denied counter).
#
# Story 10.4 (Epic 10) — `monthly_extraction_promote_executed`
# EXTENSION for InputPromoter.promote() audit-first INSERT Row 2
# (CR 1.1 verbatim 2-row append pattern). Mirrors AD-17 verbatim
# "writes the canonical confirmed-input shape" — the action
# captures the M2 service role executing the canonical INSERT into
# `monthly_input_rows` (NOT directly into `confirmed_inputs` —
# AD-7 strict invariant preserved).
AIExtractionAction = Literal[
    "monthly_extraction_executed",              # 10.1 service audit-first INSERT
    "monthly_extraction_low_confidence_warning",  # 10-1 frontend RED 배지 후속
    "monthly_extraction_promote_denied",        # 10-4 AD-7 strict invariant guard
    "monthly_extraction_promote_executed",      # 10-4 AD-17 audit-first INSERT Row 2
]


# Story 10.2 (Epic 10) — ai_insight_cache_accessed (PRD §F10.1).
# AD-25 verbatim 3-tuple cache key + audit-first INSERT (CR 1.1 verbatim).
# 4 values: ai_insight_cache_hit (3 insights returned from cache),
# ai_insight_cache_miss (cache miss → cold compute → INSERT 3 default insights),
# ai_insight_cache_cold_compute (cold compute fell within NFR11 P95 ≤ 30s SLO),
# ai_insight_cache_invalidation (AD-25 publisher cache invalidation log consume).
#
# Story 10.3 EXTENSION (Epic 10, PRD §F10.2 (b)(c) + master PRD §SM-3a):
# 2 NEW values (총 6 values) for the SM-3a counter trail —
# ai_insight_cache_invalid_source_kind (F10.2-(b) source_kind 미매칭 strict reject),
# ai_insight_cache_auto_analysis_modify_denied (F10.2-(c) auto_analysis 수정 시도 deny).
# 카운터는 별도 table 없이 이 두 action 의 audit_logs row count 로 derive 한다.
AIInsightCacheAction = Literal[
    "ai_insight_cache_hit",          # 10.2 cache hit (AC #2)
    "ai_insight_cache_miss",         # 10.2 cache miss → cold compute (AC #3)
    "ai_insight_cache_cold_compute",  # 10.2 cold compute within NFR11 SLO
    "ai_insight_cache_invalidation",  # 10.2 F10.1-(c) cache invalidation log consume
    "ai_insight_cache_invalid_source_kind",  # 10.3 F10.2-(b) strict reject + counter
    "ai_insight_cache_auto_analysis_modify_denied",  # 10.3 F10.2-(c) deny + counter
]


# Phase 5 — INFRA actions (multi-region backup + failover + DR drill).
# PRD §F20.1 + §F20.2 + §F20.3 verbatim + AD-31 (a)~(f) sub-decisions.
# Audit routes to `audit_logs` (ActionClass.INFRA — system-only table
# mutation + audit-first INSERT pattern, CR 1-1 verbatim). 4 values:
# - `replica_status_changed` — phase_5_replication_lag row INSERT
#   (every 5-second health probe captures status transition).
# - `failover_initiated` — failover_orchestrator.trigger_failover()
#   audit-first INSERT Row 1 (BEFORE secondary promotion).
# - `failover_completed` — failover_orchestrator.trigger_failover()
#   audit-first INSERT Row 2 (AFTER secondary promotion + DNS update).
# - `dr_drill_completed` — dr_drill cron quarterly drill result
#   audit-first INSERT (6 drill steps + RPO/RTO measurement).
# Drift detector: tests/integration/test_audit_action_consistency.py
# enforces ActionClass registry ↔ DB CHECK ↔ call sites parity.
InfraAction = Literal[
    "replica_status_changed",  # §F20.1 replication_lag row audit-first
    "failover_initiated",      # §F20.2 failover Row 1 audit-first
    "failover_completed",      # §F20.2 failover Row 2 audit-first
    "dr_drill_completed",      # §F20.3 quarterly DR drill result audit-first
]


# Epic 17 (cj-style 82번째 epic 연속 정직 회복 wire) — AUDIT actions
# (audit log viewer CSV export audit-first INSERT, AD-32 (f) verbatim).
# PRD §F21.5 + AC #5.5 — audit-first INSERT `audit_log_exported` BEFORE
# the CSV byte stream flush (CR 1-1 verbatim + ActionClass.AUDIT).
# Routes to `audit_logs` (NOT to a separate ledger — audit log viewer
# export events are tenant-scoped platform-event trail only, mirroring
# AUTH (Epic 15) / INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) pattern).
# 1 NEW value: `audit_log_exported` (CSV export wire).
# Drift detector: tests/integration/test_audit_action_consistency.py
# enforces ActionClass registry ↔ DB CHECK ↔ call sites parity.
# Phase 6 (cj-style 87번째 wire) — AUDIT 5 NEW values
# (audit log retention policy + purge job + archive + GDPR Article 17
# erasure + cold-archive + personal-data-erased audit-first INSERT,
# AD-33 (e) verbatim). PRD §F22.5 + AC #5.1~#5.8 — audit-first INSERT
# for each new destructive operation BEFORE the destructive event
# (CR 1-1 verbatim). Each new audit action emits BEFORE the
# destructive operation (purge / archive / mask / cold-archive /
# personal-data-erased). Routes to `audit_logs`.
# Drift detector: tests/api/core/test_epic_17_audit_action.py
# (Epic 17 cj-style 82번째 wire backend, EXTENSION in Phase 6)
# enforces ActionClass registry ↔ DB CHECK ↔ call sites parity.
AuditAction = Literal[
    "audit_log_exported",  # §F21.5 CSV export Row audit-first INSERT
    # Phase 6 (cj-style 87번째 wire) — 5 NEW values
    "audit_log_purged",  # §F22.5 + AC #5.1 — purge job BEFORE DELETE
    "audit_log_archived",  # §F22.5 + AC #5.2 — purge job BEFORE archive snapshot
    "audit_log_pii_masked",  # §F22.5 + AC #5.3 — erasure BEFORE PII mask UPDATE
    "audit_log_cold_archived",  # §F22.5 + AC #5.4 — manual cold-archive BEFORE S3 copy
    "audit_log_personal_data_erased",  # §F22.5 + AC #5.5 — GDPR Article 17 BEFORE erasure
]


# Union type for type checking
AuditAction = (
    TenantSettingsAction
    | ServiceRoleAction
    | UploadedDocumentAction
    | InputDraftAction
    | ProductAction
    | BOMLineAction
    | MonthlyInputRowAction
    | MonthlyInputPeriodAction
    | CalcLogAction
    | VerificationLogAction
    | InventoryLedgerAction
    | ReversalLogAction
    | ClosingGuardAction
    | VerificationAction
    | ClosingPeriodAction
    | MonthlyClosingAction
    | MonthlyClosingReportAction
    | SnapshotPersistenceAction
    | ReopenOperatorAction
    | TwoFactorAuthAction
    | AccountBackupAction
    | AccountDeletionAction
    | AIExtractionAction  # NEW — Story 10.1 (Epic 10)
    | AIInsightCacheAction  # NEW — Story 10.2 (Epic 10)
    | TenantAction  # NEW — Phase 3-0 (Epic 1 carry-over = auth contract)
    | InfraAction  # NEW — Phase 5 (multi-region backup + failover + DR drill)
    | AuditAction  # NEW — Epic 17 (audit log viewer CSV export) + Phase 6 EXTENSION (5 NEW values)
)


# ────────────────────────────────────────────────────────────
# 4. Mapping table — ActionClass → AuditLogType + accepted actions
# ────────────────────────────────────────────────────────────
class _ActionRegistry:
    """Internal registry — (ActionClass, AuditAction) → AuditLogType.

    Used by `emit_audit_typed()` to validate action against ActionClass
    and route to the correct destination table.
    """

    _REGISTRY: dict[ActionClass, tuple[AuditLogType, frozenset[str]]] = {
        ActionClass.TENANT_SETTINGS: (
            "audit_logs",
            frozenset(
                {
                    "industry_selected",
                    "industry_change_initial",
                    "onboarding_field_saved",
                    "allocation_criterion_saved",
                    "company_subblock_promoted",
                }
            ),
        ),
        ActionClass.TENANT: (
            "audit_logs",
            frozenset({"tenant_signup_completed"}),
        ),
        # Epic 15 — AUTH 3 values (magic link + social OAuth + SSO enterprise
        # SAML audit-first INSERT per CR 1-1 verbatim). AD-2 audit_logs
        # INSERT-only preserved; no DB CHECK constraint on action
        # (matches TWO_FACTOR_AUTH / ACCOUNT_BACKUP / ACCOUNT_DELETION
        # pattern). Drift detector enforces ActionClass registry ↔ DB
        # CHECK (no-op for audit_logs) ↔ call sites parity (3-way gate).
        # Routes to audit_logs (NOT to a separate ledger — auth events
        # are tenant-scoped platform-event trail only, mirroring
        # TWO_FACTOR_AUTH pattern).
        ActionClass.AUTH: (
            "audit_logs",
            frozenset(
                {
                    "magic_link_sent",
                    "social_oauth_initiated",
                    "sso_identity_linked",
                    # Story Epic 16 (cj-style 69번째 epic 연속 정직
                    # 회복 wire) — 4 NEW audit-first INSERT actions for
                    # tenant_idps CRUD operations (CR 1-1 verbatim):
                    # `tenant_idp_created` (POST /api/v1/admin/tenant/
                    # {slug}/idp success), `tenant_idp_updated` (PUT
                    # success), `tenant_idp_deleted` (DELETE soft delete
                    # via enabled=FALSE), `tenant_idp_tested` (POST /test
                    # validation dry-run). Mirrors the SSO identity
                    # linked envelope (Epic 15 wire `5f9e37f` carry-over
                    # pattern verbatim). Routes to audit_logs (NOT to a
                    # separate ledger — auth events are tenant-scoped
                    # platform-event trail only).
                    "tenant_idp_created",
                    "tenant_idp_updated",
                    "tenant_idp_deleted",
                    "tenant_idp_tested",
                }
            ),
        ),
        ActionClass.SERVICE_ROLE: ("audit_logs", frozenset({"service_role_bypass"})),
        ActionClass.UPLOADED_DOCUMENT: (
            "audit_logs",
            frozenset(
                {
                    "document_uploaded",
                    "document_reprocess_requested",
                    "document_retention_soft_deleted",
                }
            ),
        ),
        ActionClass.INPUT_DRAFT: (
            "audit_logs",
            frozenset(
                {
                    "input_draft_confirm",
                    "input_draft_reject",
                    # 10-4 EXTENSION — AD-17 audit-first INSERT Row 1
                    "input_draft_promoted",
                }
            ),
        ),
        ActionClass.PRODUCT: (
            "audit_logs",
            frozenset(
                {
                    "product_created",
                    "product_updated",
                    "product_type_changed",
                    "product_soft_deleted",
                    "product_reactivated",
                }
            ),
        ),
        ActionClass.BOM_LINE: ("audit_logs", frozenset({"bom_set", "bom_cleared"})),
        ActionClass.MONTHLY_INPUT_ROW: (
            "audit_logs",
            frozenset(
                {
                    "monthly_input_row_created",
                    "monthly_input_row_updated",
                    "monthly_input_row_deleted",
                }
            ),
        ),
        ActionClass.MONTHLY_INPUT_PERIOD: (
            "audit_logs",
            frozenset(
                {
                    "monthly_input_mode_changed",
                    # Story 5.1 — opening carry chain
                    "monthly_input_period_opening_carried",
                    "monthly_input_period_opening_locked",
                    # Story 11.1 — opening inventory unlocked on M11 reversal sequence
                    "monthly_input_period_opening_unlocked",
                }
            ),
        ),
        ActionClass.CALC_LOG: (
            "calc_log",
            frozenset({"compute", "idempotent_skip", "rollback"}),
        ),
        ActionClass.VERIFICATION_LOG: (
            "verification_log",
            frozenset(
                {
                    "verification_passed",
                    "verification_failed",
                    "verification_skipped",
                    "verify_v8_golden_match",  # Story 4.4 (V8 골든 mismatch audit-first)
                }
            ),
        ),
        # Story 5.2 — INVENTORY_LEDGER 6 values fill (D1 deferral 해결).
        # Epic 5 ships 3 + Epic 11 forward-fills 2 + Epic 6 close-out 1.
        # DB CHECK constraint mirror is Alembic 0015_inventory_ledger.
        # Drift detector: tests/integration/test_audit_action_consistency.py
        # `test_registry_matches_db_check_constraints` (3-way gate).
        ActionClass.INVENTORY_LEDGER: (
            "inventory_ledger",
            frozenset(
                {
                    "inventory_ledger_event_appended",
                    "inventory_ledger_event_rejected",
                    "inventory_ledger_reversal_requested",
                    # Epic 11 forward-fill
                    "inventory_ledger_reversal_logged",
                    "inventory_ledger_reversal_rejected",
                    # Epic 6 close-out forward-fill
                    "inventory_ledger_reprojection_triggered",
                }
            ),
        ),
        # Story 11.1 — REVERSAL_LOG 5 values fill (Epic 11 wire).
        # AD-22 reversal sequence + AD-25 cache invalidation publisher.
        # DB CHECK constraint mirror: reversal_log CHECK includes the 5 values.
        # Drift detector: tests/integration/test_audit_action_consistency.py
        # enforces registry ↔ DB CHECK ↔ call sites parity (3-way gate).
        ActionClass.REVERSAL_LOG: (
            "reversal_log",
            frozenset(
                {
                    "reversal_negating_inserted",
                    "reversal_corrected_inserted",
                    "reversal_rejected",
                    "reversal_unauthorized",
                    "m11_reversal_handler_invoked",
                }
            ),
        ),
        # Story 5.3 — closing_guard 3 values (AC #2 + AC #5 + AC #6).
        # DB CHECK constraint mirror: audit_logs CHECK includes
        # closing_guard_violated, closing_guard_passed,
        # v3_closing_invariant_verified (drift detector enforces parity).
        ActionClass.CLOSING_GUARD: (
            "audit_logs",
            frozenset(
                {
                    "closing_guard_violated",
                    "closing_guard_passed",
                    "v3_closing_invariant_verified",
                }
            ),
        ),
        # Story 5.3 — verification 1 value (V3 closing invariant verifier).
        # Routes to verification_log destination (shared with
        # VERIFICATION_LOG — distinct action_class but same destination).
        ActionClass.VERIFICATION: (
            "verification_log",
            frozenset(
                {
                    "verify_v3_closing_invariant",
                    # Story 6.1 — V4 closing snapshot 일관성 verifier.
                    "verify_v4_closing_period_consistency",
                }
            ),
        ),
        # Story 6.1 — closing_period 3 values (closing period service).
        # DB CHECK constraint mirror: audit_logs CHECK includes
        # closing_period_confirmed, closing_period_blocked,
        # closing_period_snapshot_inconsistency (drift detector enforces
        # parity between ActionClass registry, DB CHECK constraint, and
        # call sites).
        ActionClass.CLOSING_PERIOD: (
            "audit_logs",
            frozenset(
                {
                    "closing_period_confirmed",
                    "closing_period_blocked",
                    "closing_period_snapshot_inconsistency",
                }
            ),
        ),
        # Story 11.2 — monthly_closing 4 values (4-stage close sequence
        # lock). DB CHECK constraint mirror: audit_logs CHECK includes
        # closing_sequence_initiated/step_completed/blocked/confirmed
        # (drift detector enforces parity between ActionClass registry,
        # DB CHECK constraint, and call sites).
        ActionClass.MONTHLY_CLOSING: (
            "audit_logs",
            frozenset(
                {
                    "closing_sequence_initiated",
                    "closing_sequence_step_completed",
                    "closing_sequence_blocked",
                    "closing_sequence_confirmed",
                }
            ),
        ),
        # Story 6.2 — monthly_closing_report 1 value (read-only report 자체 audit).
        # DB CHECK constraint mirror: audit_logs CHECK includes
        # monthly_closing_report_viewed (drift detector enforces parity
        # between ActionClass registry, DB CHECK constraint, and call sites).
        ActionClass.MONTHLY_CLOSING_REPORT: (
            "audit_logs",
            frozenset(
                {
                    "monthly_closing_report_viewed",
                    # Walking Skeleton (2026-08-16): Story 6.3 wire
                    # call site (closing_pdf_export_viewed) was added
                    # to the Literal type but missing from the
                    # registry frozenset. Without this row, the v6.3
                    # audit emit raises ValueError via
                    # `_ActionRegistry.validate` and the entire PDF
                    # export endpoint 500s with
                    # CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR.
                    "closing_pdf_export_viewed",
                }
            ),
        ),
        # Story 11.3 — snapshot_persistence 4 values (AD-20 영구화 + AD-22 역분개).
        # DB CHECK constraint mirror: audit_logs CHECK includes
        # snapshot_persistence_committed / snapshot_persistence_reversed /
        # snapshot_persistence_blocked / snapshot_persistence_reopened
        # (drift detector enforces parity).
        ActionClass.SNAPSHOT_PERSISTENCE: (
            "audit_logs",
            frozenset(
                {
                    "snapshot_persistence_committed",
                    "snapshot_persistence_reversed",
                    "snapshot_persistence_blocked",
                    "snapshot_persistence_reopened",
                }
            ),
        ),
        # Story 11.3 — reopen_operator 2 values (W2 reopen flow).
        # DB CHECK constraint mirror: audit_logs CHECK includes
        # reopen_authorized / reopen_completed.
        ActionClass.REOPEN_OPERATOR: (
            "audit_logs",
            frozenset(
                {
                    "reopen_authorized",
                    "reopen_completed",
                }
            ),
        ),
        # Story 12.1 — two_factor_auth 6 values (2FA mandatory gate).
        # DB CHECK constraint mirror: audit_logs CHECK includes the 6
        # values (Alembic 0022_m12_two_factor_auth wire). Drift detector
        # enforces ActionClass registry ↔ DB CHECK ↔ call sites parity
        # (3-way gate). Routes to audit_logs (NOT to a separate ledger —
        # 2FA events are tenant-scoped platform-event trail only).
        ActionClass.TWO_FACTOR_AUTH: (
            "audit_logs",
            frozenset(
                {
                    "two_factor_setup_initiated",
                    "two_factor_setup_completed",
                    "two_factor_challenge_passed",
                    "two_factor_challenge_failed",
                    "two_factor_recovery_consumed",
                    "two_factor_disabled",
                }
            ),
        ),
        # Story 12.2 — account_backup 5 values (daily auto-backup + JSON
        # self-download). DB CHECK-less per AD-2 invariant (audit_logs has
        # NO action CHECK constraint per conventions.md §10.1 + docs
        # 907-910). Drift detector enforces ActionClass registry ↔ DB
        # CHECK (no-op for audit_logs) ↔ call sites parity (3-way gate).
        # Routes to audit_logs (NOT to a separate ledger — backup events
        # are tenant-scoped platform-event trail only, mirroring
        # TWO_FACTOR_AUTH pattern).
        ActionClass.ACCOUNT_BACKUP: (
            "audit_logs",
            frozenset(
                {
                    "backup_created",
                    "backup_failed",
                    "backup_retention_purged",
                    "backup_downloaded",
                    "backup_triggered",
                }
            ),
        ),
        # Story 12.3 — account deletion + retention consent (8 NEW actions).
        # AD-2 audit_logs INSERT-only preserved (no DB CHECK constraint
        # on action; routing to audit_logs + RLS policy enforcement).
        ActionClass.ACCOUNT_DELETION: (
            "audit_logs",
            frozenset(
                {
                    "deletion_requested",
                    "deletion_consent_given",
                    "deletion_cancelled",
                    "deletion_anonymized",
                    "tenant_hard_deleted",
                    "deletion_failed",
                    "deletion_2fa_failed",
                    "two_factor_verified",
                }
            ),
        ),
        # Story 10.1 (Epic 10) — AI monthly input extraction (PRD §8.1 M10 (c)).
        # AD-2 audit_logs INSERT-only preserved; AD-7 strict invariant enforced
        # via service-layer target_table='monthly_inputs' discriminator (NEVER
        # 'confirmed_inputs'). 3 NEW actions: monthly_extraction_executed (live
        # in service.py:944 #d56959c), monthly_extraction_low_confidence_warning
        # (10-1 frontend RED 배지 후속), monthly_extraction_promote_denied
        # (10-4 AD-7 strict invariant promote-denied counter).
        ActionClass.AI_EXTRACTION_EXECUTED: (
            "audit_logs",
            frozenset(
                {
                    "monthly_extraction_executed",
                    "monthly_extraction_low_confidence_warning",
                    "monthly_extraction_promote_denied",
                    # 10-4 EXTENSION — AD-17 audit-first INSERT Row 2
                    "monthly_extraction_promote_executed",
                }
            ),
        ),
        # Story 10.2 (Epic 10) — three-insight cache access (PRD §F10.1).
        # AD-25 verbatim 3-tuple cache key + audit-first INSERT (CR 1.1 verbatim).
        # 4 NEW actions: hit / miss / cold_compute / invalidation log consume.
        # Routes to audit_logs (NOT to a separate ledger — cache events are
        # tenant-scoped platform-event trail only).
        ActionClass.AI_INSIGHT_CACHE_ACCESSED: (
            "audit_logs",
            frozenset(
                {
                    "ai_insight_cache_hit",
                    "ai_insight_cache_miss",
                    "ai_insight_cache_cold_compute",
                    "ai_insight_cache_invalidation",
                    # Story 10.3 EXTENSION (F10.2-(b)(c) SM-3a counter trail)
                    "ai_insight_cache_invalid_source_kind",
                    "ai_insight_cache_auto_analysis_modify_denied",
                }
            ),
        ),
        # Epic 17 (cj-style 82번째 wire) — AUDIT 1 value (audit log
        # viewer CSV export audit-first INSERT, AD-32 (f) verbatim).
        # Routes to audit_logs (NOT to a separate ledger — audit log
        # viewer events are tenant-scoped platform-event trail only,
        # mirroring AUTH (Epic 15) / INFRA (Phase 5) / TWO_FACTOR_AUTH
        # (Epic 12) pattern). Drift detector enforces ActionClass
        # registry ↔ DB CHECK ↔ call sites parity (3-way gate).
        # Phase 6 (cj-style 87번째 wire) — AUDIT EXTENSION 5 NEW values
        # (audit log retention + purge + archive + GDPR Article 17
        # erasure + cold-archive audit-first INSERT, AD-33 (e) verbatim).
        # PRD §F22.5 — each destructive operation emits audit log BEFORE
        # the destructive event (CR 1-1 verbatim). Drift detector
        # enforces ActionClass registry ↔ DB CHECK ↔ call sites parity.
        ActionClass.AUDIT: (
            "audit_logs",
            frozenset(
                {
                    "audit_log_exported",  # §F21.5 CSV export Row audit-first
                    # Phase 6 (cj-style 87번째 wire) — 5 NEW values (AD-33 (e))
                    "audit_log_purged",  # §F22.5 + AC #5.1 — purge job BEFORE DELETE
                    "audit_log_archived",  # §F22.5 + AC #5.2 — purge job BEFORE archive snapshot
                    "audit_log_pii_masked",  # §F22.5 + AC #5.3 — erasure BEFORE PII mask UPDATE
                    "audit_log_cold_archived",  # §F22.5 + AC #5.4 — manual cold-archive BEFORE S3 copy
                    "audit_log_personal_data_erased",  # §F22.5 + AC #5.5 — GDPR Article 17 BEFORE erasure
                }
            ),
        ),
    }

    @classmethod
    def validate(cls, *, action_class: ActionClass, action: str) -> AuditLogType:
        """Return destination ledger for (action_class, action). Raise if invalid."""
        if action_class not in cls._REGISTRY:
            raise ValueError(
                f"audit_action: unknown ActionClass {action_class!r}. "
                f"Add to _REGISTRY in apps/api/core/audit_action.py"
            )
        log_type, accepted = cls._REGISTRY[action_class]
        if action not in accepted:
            raise ValueError(
                f"audit_action: action {action!r} is not in ActionClass "
                f"{action_class.value!r}. Accepted: {sorted(accepted)}. "
                f"This is the CR 1.1 lesson — free-form string drift is forbidden."
            )
        return log_type


# ────────────────────────────────────────────────────────────
# 5. Helper — typed emit_audit wrapper
# ────────────────────────────────────────────────────────────
async def emit_audit_typed(
    session: AsyncSession,
    *,
    action_class: ActionClass,
    action: AuditAction,
    actor_id: uuid.UUID | None,
    target_id: uuid.UUID | None = None,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
    tenant_id: uuid.UUID | None = None,
    flush: bool = True,
) -> None:
    """Typed emit_audit wrapper. Routes to correct destination ledger.

    Args:
        action_class: Which target class (CR 1.1 single source of truth).
        action: Typed action literal. Must match action_class's accepted set.
        actor_id, target_id, reason, payload, tenant_id, flush:
            Same semantics as emit_audit (apps/api/core/audit.py).

    Raises:
        ValueError: If action not in action_class's accepted set.
        NotImplementedError: If action_class routes to a destination
            (calc_log, verification_log, inventory_ledger, reversal_log)
            that is not yet wired through `emit_audit_typed()`. Call sites
            for those classes must use the service-layer writer
            (e.g. `CalcOrchestrator._write_calc_log`).

    Example:
        await emit_audit_typed(
            session,
            action_class=ActionClass.TENANT_SETTINGS,
            action="industry_selected",
            actor_id=actor_id,
            target_id=tenant_id,
            payload={"..."},
            tenant_id=tenant_id,
        )
    """
    log_type = _ActionRegistry.validate(action_class=action_class, action=action)

    if log_type == "audit_logs":
        # delegate to existing emit_audit (apps/api/core/audit.py)
        from apps.api.core.audit import emit_audit

        await emit_audit(
            session,
            actor_id=actor_id,
            action=action,
            target_table=action_class.value,
            target_id=target_id,
            reason=reason,
            payload=payload or {},
            tenant_id=tenant_id,
            flush=flush,
        )
    elif log_type == "calc_log":
        # CalcLog is written via CalcOrchestrator._write_calc_log
        # (m3_calculate/services/calc_orchestrator.py).
        # The service-layer writer owns the typed writer because it
        # requires the orchestrator's session/trace_id context.
        raise NotImplementedError(
            "audit_action: calc_log destination is wired through "
            "CalcOrchestrator._write_calc_log — call site is "
            "apps/api/modules/m3_calculate/services/calc_orchestrator.py"
        )
    elif log_type in ("verification_log", "inventory_ledger", "reversal_log"):
        # verification_log → CalcOrchestrator._write_verification_log (Story 4.3)
        # inventory_ledger → m4_inventory service (Epic 5)
        # reversal_log → m11_reversal service (Epic 11)
        # Each is wired through its domain service, not via emit_audit_typed.
        raise NotImplementedError(
            f"audit_action: {log_type!r} destination is wired through its "
            f"domain service writer — see story spec for wire contract."
        )


__all__ = [
    "ActionClass",
    "AuditAction",
    "AuditLogType",
    "TenantSettingsAction",
    "ServiceRoleAction",
    "UploadedDocumentAction",
    "InputDraftAction",
    "ProductAction",
    "BOMLineAction",
    "MonthlyInputRowAction",
    "MonthlyInputPeriodAction",
    "CalcLogAction",
    "VerificationLogAction",
    "InventoryLedgerAction",
    "ReversalLogAction",
    "ClosingGuardAction",
    "VerificationAction",
    "ClosingPeriodAction",
    "MonthlyClosingAction",
    "MonthlyClosingReportAction",
    "SnapshotPersistenceAction",
    "ReopenOperatorAction",
    "TwoFactorAuthAction",
    "AccountBackupAction",
    "AIExtractionAction",  # NEW — Story 10.1 (Epic 10)
    "AIInsightCacheAction",  # NEW — Story 10.2 (Epic 10)
    "InfraAction",  # NEW — Phase 5 (multi-region backup + failover + DR drill)
    "AuditAction",  # NEW — Epic 17 (audit log viewer CSV export)
    "emit_audit_typed",
]
