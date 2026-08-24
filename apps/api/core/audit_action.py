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
    OBSERVABILITY = "observability"  # Phase 7 (NEW — observability stack alert + sampling audit-first INSERT)
    PERFORMANCE_TEST = "performance_test"  # Phase 8 (NEW — k6 load test + SLO/SLI + latency regression + perf regression gate + cost-engine benchmark audit-first INSERT)
    CHAOS_ENGINEERING = "chaos_engineering"  # Phase 9 (NEW — chaos experiment + game day + continuous chaos + auto-rollback audit-first INSERT)
    SLO_ENGINEERING = "slo_engineering"  # Phase 10 (NEW — SLO definition + error budget + multi-region aggregation + governance review + auto-rollback SLO breach trigger audit-first INSERT)
    FINOPS = "finops"  # Phase 11 (NEW — FinOps showback generation + department mapping update + chargeback calculation + chargeback export audit-first INSERT)
    FINOPS_ANOMALY = "finops_anomaly"  # Phase 12 (NEW — Cost anomaly detection + budget alerting audit-first INSERT, AD-39)
    FINOPS_BUDGET = "finops_budget"  # Phase 12 (NEW — Budget definition + budget alert routing audit-first INSERT, AD-39)
    FINOPS_FORECAST = "finops_forecast"  # Phase 13 (NEW — Forecast definition + forecast generation + capacity headroom + budget burn-rate + forecast accuracy + model retraining + dry-run audit-first INSERT, AD-39)
    FINOPS_OPTIMIZATION = "finops_optimization"  # Phase 14 (NEW — Optimization definition + rightsizing + idle detection + commitment + accuracy tracking + dry-run audit-first INSERT, AD-41)
    FINOPS_TAG_GOVERNANCE = "finops_tag_governance"  # Phase 15 (cj-style 123번째 wire — NEW — Tag policy + untagged resource detector + allocation rules engine + compliance + chargeback allocation reconciliation audit-first INSERT, AD-42)


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


# Phase 7 (cj-style 91번째 wire) — OBSERVABILITY actions
# (alert firing + trace sampling decision audit-first INSERT, AD-34 (e)
# verbatim). PRD §F23.5 + AC #5.9 — alert firing emits audit log BEFORE
# Slack/PagerDuty notification dispatch (CR 1-1 verbatim + ActionClass.
# OBSERVABILITY). Routes to `audit_logs` (NOT to a separate ledger —
# observability events are tenant-scoped platform-event trail only,
# mirroring AUTH (Epic 15) / INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12)
# / AUDIT (Epic 17 / Phase 6) pattern). 2 NEW values:
# - `alert_fired` — Prometheus AlertManager webhook ingress + Slack
#   notification dispatch + PagerDuty owner-only manual trigger audit
#   trace (severity + alert_name + tenant_id + trace_id payload).
# - `trace_sampled` — OpenTelemetry trace_id sampling decision audit
#   trace (decision + tenant_id + sampling_ratio + trace_id payload).
#   Per-request sampling audit ensures head_based sampler ratio (1.0 dev
#   / 0.1 prod) is observable + Sentry `tracesSampleRate=0.1` carry-over
#   alignment + tenant_id dimension observability (CR 0-2 RLS-preserved).
# Drift detector: tests/api/core/test_phase_7_observability_audit_action.py
# (Phase 7 cj-style 91번째 wire backend) enforces ActionClass registry ↔
# DB CHECK (no-op for audit_logs per AD-2) ↔ call sites parity (3-way
# gate). Phase 6 cj-style 87번째 wire `test_phase_6_retention_audit_action.py`
# pattern verbatim applied.
ObservabilityAction = Literal[
    "alert_fired",  # §F23.5 + AC #5.9 — alert BEFORE Slack/PagerDuty dispatch
    "trace_sampled",  # §F23.5 + AC #5.10 — sampling decision audit trace
]


# Phase 8 (cj-style 95번째 wire) — PERFORMANCE_TEST actions
# (k6 load test + SLO/SLI modifications + latency regression detection +
# performance regression gate + cost-engine benchmark V8 invalidation
# audit-first INSERT, AD-35 (c)(d)(e)(f) verbatim). PRD §F24.1~§F24.6 +
# AC §F24.1-10 + §F24.2-8 + §F24.3-8 + §F24.4-5 + §F24.5-6 + §F24.6-6 —
# audit-first INSERT for each new destructive / observation event BEFORE
# the actual operation (CR 1-1 verbatim + ActionClass.PERFORMANCE_TEST).
# Routes to `audit_logs` (NOT to a separate ledger — performance/load
# testing events are tenant-scoped platform-event trail only, mirroring
# AUTH (Epic 15) / INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) / AUDIT
# (Epic 17 / Phase 6) / OBSERVABILITY (Phase 7) pattern).
# 4 NEW values:
# - `performance_test_started` — k6 load test run started (manual
#   trigger or nightly schedule; scenario + VU + tenant_id + trace_id
#   payload; owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존).
# - `performance_test_completed` — k6 load test run completed (summary
#   metrics p95/p99 latency + RPS + error rate + tenant-scoped result_hash
#   payload).
# - `p99_regression_detected` — latency regression detector golden_diff
#   exceeded threshold 20% (baseline + current + delta + tenant_id
#   payload; CR 1-1 verbatim).
# - `cost_engine_benchmark_invalidated` — cost-engine benchmark V8
#   golden diff exceeded threshold 5% (V8 snapshot + current + delta +
#   tenant_id + invalidation reason payload; AD-22 owner-only RBAC).
# Drift detector: tests/api/core/test_phase_8_performance_audit_action.py
# (Phase 8 cj-style 95번째 wire backend) enforces ActionClass registry ↔
# DB CHECK (no-op for audit_logs per AD-2) ↔ call sites parity (3-way
# gate). Phase 7 cj-style 91번째 wire `test_phase_7_observability_audit_action.py`
# pattern verbatim applied.
PerformanceTestAction = Literal[
    "performance_test_started",  # §F24.1-10 — k6 load test run start
    "performance_test_completed",  # §F24.1-10 — k6 load test run completion
    "p99_regression_detected",  # §F24.4-5 — latency regression detection
    "cost_engine_benchmark_invalidated",  # §F24.6-6 — V8 golden invalidate
]


# Phase 9 (cj-style 99번째 wire) — CHAOS_ENGINEERING actions
# (chaos experiment start/complete + manual abort + auto-rollback
# audit-first INSERT, AD-36 (c)(d)(e) verbatim). PRD §F25.1~§F25.7 +
# AC §F25.1-7 + §F25.3-8 + §F25.6-4 + §F25.6-6 — audit-first INSERT
# for each new destructive / observation event BEFORE the actual
# operation (CR 1-1 verbatim + ActionClass.CHAOS_ENGINEERING). Routes
# to `audit_logs` (NOT to a separate ledger — chaos engineering events
# are tenant-scoped platform-event trail only, mirroring AUTH (Epic 15)
# / INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) / AUDIT (Epic 17 / Phase
# 6) / OBSERVABILITY (Phase 7) / PERFORMANCE_TEST (Phase 8) pattern).
# 4 NEW values:
# - `chaos_experiment_started` — chaos experiment run started (manual
#   trigger or quarterly game day or continuous chaos L1 single_request;
#   experiment_name + blast_radius + intensity + tenant_id + trace_id
#   payload; owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존).
# - `chaos_experiment_completed` — chaos experiment run completed
#   (blast radius assessment + observed metrics + auto-rollback
#   performance summary payload; AD-22 owner-only RBAC).
# - `chaos_experiment_aborted` — manual abort via POST /api/v1/admin/
#   chaos/{experiment_id}/abort (owner-only RBAC AD-22 + Epic 12 2FA
#   챌린지 보존 + abort conditions 4 rules trigger payload; CR 1-1
#   verbatim).
# - `chaos_rollback_triggered` — auto-rollback strategy executed
#   (automatic / manual / hybrid / scheduled abort strategy payload;
#   AD-22 owner-only RBAC; steady state recovery verification payload).
# Drift detector: tests/api/core/test_phase_9_audit_action.py
# (Phase 9 cj-style 99번째 wire backend) enforces ActionClass registry
# ↔ DB CHECK (no-op for audit_logs per AD-2) ↔ call sites parity
# (3-way gate). Phase 8 cj-style 95번째 wire
# `test_phase_8_performance_audit_action.py` pattern verbatim applied.
ChaosEngineeringAction = Literal[
    "chaos_experiment_started",  # §F25.1-7 — chaos experiment run start
    "chaos_experiment_completed",  # §F25.3-8 — chaos experiment completion
    "chaos_experiment_aborted",  # §F25.3-8 + §F25.1-5 — manual/abort trigger
    "chaos_rollback_triggered",  # §F25.6-6 — auto-rollback strategy execution
]


# Phase 10 (cj-style 103번째 wire) — SLO_ENGINEERING actions
# (SLO target change + error budget exhaustion + SLO violation detection
# audit-first INSERT, AD-37 (b)(d)(e) verbatim). PRD §F26.1~§F26.7 +
# AC §F26.1-7 + §F26.3-6 + §F26.5-5 — audit-first INSERT for each new
# destructive / observation event BEFORE/AFTER the actual operation
# (CR 1-1 verbatim + ActionClass.SLO_ENGINEERING). Routes to
# `audit_logs` (NOT to a separate ledger — SLO engineering events are
# tenant-scoped platform-event trail only, mirroring AUTH (Epic 15) /
# INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) / AUDIT (Epic 17 /
# Phase 6) / OBSERVABILITY (Phase 7) / PERFORMANCE_TEST (Phase 8) /
# CHAOS_ENGINEERING (Phase 9) pattern). 3 NEW values:
# - `slo_target_updated` — SLO definition target / state changed
#   (manual create/update/delete + lifecycle state transition; slo_id +
#   new_state + tenant_id + trace_id payload; owner-only RBAC AD-22 +
#   Epic 12 2FA 챌린지 보존 when governance_required=True; CR 1-1
#   verbatim audit-first INSERT BEFORE target 변경).
# - `slo_budget_exhausted` — error budget exhaustion event
#   (budget_remaining_minutes < 0 + freeze_triggered + tenant_id +
#   trace_id payload; AD-22 owner-only RBAC; CR 1-1 verbatim
#   audit-first INSERT AFTER budget exhaustion 알람 + freeze trigger).
# - `slo_violation_detected` — multi-window burn-rate composite alert
#   fired (slo_id + window + burn_rate + threshold + composite_severity
#   + tenant_id + trace_id payload; AD-22 owner-only RBAC; CR 1-1
#   verbatim audit-first INSERT AFTER composite alert dispatch).
# Drift detector: tests/api/core/test_phase_10_slo_audit_action.py
# (Phase 10 cj-style 103번째 wire backend) enforces ActionClass
# registry ↔ DB CHECK (no-op for audit_logs per AD-2) ↔ call sites
# parity (3-way gate). Phase 9 cj-style 99번째 wire
# `test_phase_9_audit_action.py` pattern verbatim applied.
SloEngineeringAction = Literal[
    "slo_target_updated",  # §F26.1-7 — SLO target change + state transition
    "slo_budget_exhausted",  # §F26.3-6 — error budget exhaustion + freeze
    "slo_violation_detected",  # §F26.5-5 — multi-window composite alert
]


# Phase 11 (cj-style 107번째 wire) — FINOPS actions
# (showback generation + department mapping update + chargeback
# calculation + chargeback export audit-first INSERT, AD-38 (b)(c)(e)
# verbatim). PRD §F27.1~§F27.7 + AC §F27.1-7 + §F27.3-3 +
# §F27.4-4 + §F27.5-8 — audit-first INSERT for each new destructive
# / observation event BEFORE/AFTER the actual operation (CR 1-1
# verbatim + ActionClass.FINOPS). Routes to `audit_logs` (NOT to a
# separate ledger — FinOps events are tenant-scoped platform-event
# trail only, mirroring AUTH (Epic 15) / INFRA (Phase 5) /
# TWO_FACTOR_AUTH (Epic 12) / AUDIT (Epic 17 / Phase 6) /
# OBSERVABILITY (Phase 7) / PERFORMANCE_TEST (Phase 8) /
# CHAOS_ENGINEERING (Phase 9) / SLO_ENGINEERING (Phase 10) pattern).
# 4 NEW values:
# - `showback_generated` — showback report generation succeeded
#   (group_by + period_mode + comparison_period + tenant_id + trace_id
#   payload; AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존 when
#   governance_required=True; CR 1-1 verbatim audit-first INSERT
#   AFTER showback snapshot persisted).
# - `department_mapping_updated` — department → cost_center mapping
#   change (manual create/update or auto-create on first calculation;
#   department_id + cost_center_id + auto_created + tenant_id + trace_id
#   payload; AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT
#   BEFORE/UPDATE mapping row).
# - `chargeback_calculated` — chargeback calculation succeeded
#   (chargeback_id + rule_type + total_amount + period_key + tenant_id
#   + trace_id payload; AD-22 owner-only RBAC; CR 1-1 verbatim
#   audit-first INSERT AFTER chargeback row computed).
# - `chargeback_exported` — CSV/PDF export succeeded
#   (chargeback_id + export_format + row_count + file_size_bytes +
#   tenant_id + trace_id payload; AD-22 owner-only RBAC + owner-only
#   export rate limit 1/minute; CR 1-1 verbatim audit-first INSERT
#   BEFORE export byte stream flushed).
# Drift detector: tests/api/core/test_phase_11_audit_action.py
# (Phase 11 cj-style 107번째 wire backend) enforces ActionClass
# registry ↔ DB CHECK (no-op for audit_logs per AD-2) ↔ call sites
# parity (3-way gate). Phase 10 cj-style 103번째 wire
# `test_phase_10_audit_action.py` pattern verbatim applied.
FinopsAction = Literal[
    "showback_generated",  # §F27.1-7 — showback report generation
    "department_mapping_updated",  # §F27.3-3 + §F27.3-10 — mapping change + cache invalidation
    "chargeback_calculated",  # §F27.4-4 — chargeback calculation
    "chargeback_exported",  # §F27.5-8 — CSV/PDF export
]


# Phase 12 (cj-style 111번째 wire) — FINOPS_ANOMALY actions
# (anomaly detection + forecast accuracy tracking audit-first INSERT,
# AD-39 (b)(d)(e)(f) verbatim). PRD §F28.1 + §F28.5 + §F28.6 +
# AC §F28.1-12 + §F28.5-7 + §F28.6-12 — audit-first INSERT for each new
# detection / observation event BEFORE/AFTER the actual operation
# (CR 1-1 verbatim + ActionClass.FINOPS_ANOMALY). Routes to
# `audit_logs` (NOT to a separate ledger — FinOps anomaly events are
# tenant-scoped platform-event trail only, mirroring FINOPS Phase 11
# wire + AUTH (Epic 15) / INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) /
# AUDIT (Epic 17 / Phase 6) / OBSERVABILITY (Phase 7) /
# PERFORMANCE_TEST (Phase 8) / CHAOS_ENGINEERING (Phase 9) /
# SLO_ENGINEERING (Phase 10) pattern). 4 NEW values:
# - `anomaly_detected` — multi-method voting consensus confirmed
#   anomaly (3 of 4 methods agree + severity assigned; result_id +
#   dimension + dimension_value + observed_cost + baseline_cost +
#   deviation_pct + severity + methods_voted + tenant_id + trace_id
#   payload; AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존 when
#   governance_required=True; CR 1-1 verbatim audit-first INSERT
#   AFTER detection confirmed).
# - `forecast_deviation` — forecast accuracy tracking observed
#   deviation > threshold (forecast + actual + mae + mape + rmse +
#   status + retraining_recommended + tenant_id + trace_id payload;
#   AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT
#   AFTER forecast evaluation completes).
# - `model_retraining_triggered` — MAPE > 20% triggers model retrain
#   (model_name + current_mape + retrain_reason + tenant_id + trace_id
#   payload; AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT
#   AFTER retrain flag set).
# - `anomaly_baseline_updated` — baseline window update (last_30d /
#   last_90d / YTD aggregation refreshed + tenant_id + trace_id
#   payload; AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT
#   AFTER baseline partition refresh).
FinopsAnomalyAction = Literal[
    "anomaly_detected",  # §F28.1-12 — multi-method voting consensus confirmed
    "forecast_deviation",  # §F28.5-7 — forecast accuracy deviation observed
    "model_retraining_triggered",  # §F28.5-7 — MAPE > 20% retrain trigger
    "anomaly_baseline_updated",  # §F28.3-12 — baseline window update
]


# Phase 12 (cj-style 111번째 wire) — FINOPS_BUDGET actions
# (budget definition + budget alert routing audit-first INSERT,
# AD-39 (c)(e)(g) verbatim). PRD §F28.2 + §F28.4 + AC §F28.2-12 +
# §F28.4-12 — audit-first INSERT for each new budget operation
# BEFORE/AFTER the actual operation (CR 1-1 verbatim +
# ActionClass.FINOPS_BUDGET). Routes to `audit_logs` (NOT to a separate
# ledger — FinOps budget events are tenant-scoped platform-event trail
# only, mirroring FINOPS_ANOMALY Phase 12 wire + FINOPS Phase 11 wire
# + AUTH (Epic 15) / INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) /
# AUDIT (Epic 17 / Phase 6) / OBSERVABILITY (Phase 7) /
# PERFORMANCE_TEST (Phase 8) / CHAOS_ENGINEERING (Phase 9) /
# SLO_ENGINEERING (Phase 10) pattern). 3 NEW values:
# - `budget_definition_updated` — budget created/updated/paused/expired
#   (budget_id + scope + scope_id + amount + alert_thresholds +
#   tenant_id + trace_id payload; AD-22 owner-only RBAC + Epic 12 2FA
#   챌린지 보존 when governance_required=True; CR 1-1 verbatim
#   audit-first INSERT AFTER budget row committed).
# - `budget_threshold_exceeded` — consumption crossed warning/critical/
#   exceeded threshold (alert_level + consumption_pct + budget_amount +
#   channels + tenant_id + trace_id payload; AD-22 owner-only RBAC;
#   CR 1-1 verbatim audit-first INSERT AFTER threshold crossed).
# - `budget_alert_sent` — alert successfully dispatched to channels
#   (alert_id + alert_level + channels + recipients + status +
#   tenant_id + trace_id payload; AD-22 owner-only RBAC; CR 1-1
#   verbatim audit-first INSERT AFTER alert dispatched).
FinopsBudgetAction = Literal[
    "budget_definition_updated",  # §F28.2-12 — budget created/updated
    "budget_threshold_exceeded",  # §F28.4-12 — threshold crossed
    "budget_alert_sent",  # §F28.4-12 — alert dispatched to channels
]


# Phase 13 (cj-style 115번째 wire) — FINOPS_FORECAST actions
# (forecast definition + forecast generation + capacity headroom +
# budget burn-rate + forecast accuracy + model retraining + dry-run
# audit-first INSERT, AD-39 verbatim). PRD §F29.1 + §F29.2 + §F29.3 +
# §F29.4 + §F29.5 + AC §F29.1-12 + §F29.2-12 — audit-first INSERT for
# each new forecast operation BEFORE/AFTER the actual operation (CR 1-1
# verbatim + ActionClass.FINOPS_FORECAST). Routes to `audit_logs` (NOT
# to a separate ledger — FinOps forecast events are tenant-scoped
# platform-event trail only, mirroring FINOPS_BUDGET + FINOPS_ANOMALY
# Phase 12 wire + FINOPS Phase 11 wire + AUTH (Epic 15) / INFRA
# (Phase 5) / TWO_FACTOR_AUTH (Epic 12) / AUDIT (Epic 17 / Phase 6) /
# OBSERVABILITY (Phase 7) / PERFORMANCE_TEST (Phase 8) /
# CHAOS_ENGINEERING (Phase 9) / SLO_ENGINEERING (Phase 10) pattern).
# 7 NEW values:
# - `forecast_definition_updated` — forecast definition created/updated/
#   paused/expired (forecast_id + target_metric + dimension_value +
#   horizon_months + model_type + confidence_level + retraining_cron +
#   status + tenant_id + trace_id payload; AD-22 owner-only RBAC + Epic
#   12 2FA 챌린지 보존 when governance_required=True; CR 1-1 verbatim
#   audit-first INSERT AFTER forecast definition row committed).
# - `forecast_generated` — forecast prediction completed (4-method
#   parallel run + ensemble voting consensus reached; forecast_id +
#   horizon_months + model_type + predicted_values + confidence_lower +
#   confidence_upper + tenant_id + trace_id payload; AD-22 owner-only
#   RBAC; CR 1-1 verbatim audit-first INSERT AFTER forecast result
#   committed).
# - `capacity_headroom_analyzed` — capacity headroom analysis completed
#   (compute / storage / network saturation + saturation_level +
#   primary_model + lookahead_days + recommendation + tenant_id +
#   trace_id payload; AD-22 owner-only RBAC; CR 1-1 verbatim
#   audit-first INSERT AFTER capacity headroom report committed).
# - `budget_burn_rate_projected` — budget burn-rate projection completed
#   (4-input formula + 3-level severity routing + predicted_end_period_
#   spend + ARIMA prediction + tenant_id + trace_id payload; AD-22
#   owner-only RBAC; CR 1-1 verbatim audit-first INSERT AFTER projection
#   committed).
# - `forecast_accuracy_degraded` — MAPE > 20% detected for 3 consecutive
#   periods (3-tuple tenant_id + target_metric + model_type + mape_value
#   + consecutive_periods + industry + tenant_id + trace_id payload;
#   AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT AFTER
#   accuracy record committed).
# - `model_retraining_triggered` — retraining dispatch triggered
#   (MAPE_CONSECUTIVE_PERIODS_THRESHOLD = 3 reached; trigger_id +
#   retraining_cron `'0 3 * * 0'` KST Sunday 03:00 UTC 18:00 + model_type
#   + tenant_id + trace_id payload; AD-22 owner-only RBAC; CR 1-1
#   verbatim audit-first INSERT AFTER retraining trigger committed).
# - `forecast_dry_run_executed` — dry-run preview completed (no actual
#   forecast generation; forecast_id + horizon + tenant_id + trace_id
#   payload; AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT
#   AFTER dry-run preview committed).
FinopsForecastAction = Literal[
    "forecast_definition_updated",  # §F29.1-12 — forecast definition row update
    "forecast_generated",  # §F29.2-12 — forecast prediction completed
    "capacity_headroom_analyzed",  # §F29.3-12 — capacity headroom analysis
    "budget_burn_rate_projected",  # §F29.4-12 — burn-rate projection
    "forecast_accuracy_degraded",  # §F29.5-12 — MAPE > 20% detected
    "model_retraining_triggered",  # §F29.5-12 — retrain dispatch triggered
    "forecast_dry_run_executed",  # §F29.1-5 — dry-run preview
]


# Phase 14 (cj-style 119번째 wire) — AD-41 (a)~(g) verbatim +
# §F30.1 + §F30.2 + §F30.3 + §F30.4 + §F30.5. 8 NEW audit actions
# (CR 1-1 verbatim applied + ActionClass.FINOPS_OPTIMIZATION):
# - `optimization_definition_updated` — optimization definition row update
#   (PRD §F30.1-10 verbatim; AD-22 owner-only RBAC; CR 1-1 verbatim
#   audit-first INSERT BEFORE optimization definition commit).
# - `recommendation_generated` — rightsizing recommendation generated
#   (PRD §F30.2-11 verbatim; 5 resource types parallel run; CR 1-1
#   verbatim audit-first INSERT BEFORE recommendation generation).
# - `idle_resource_detected` — idle resource detected via z-score < -2.0
#   (PRD §F30.3-11 verbatim; Phase 12 anomaly_detection EXTENSION; CR 1-1
#   verbatim audit-first INSERT AFTER idle resource detection).
# - `commitment_recommended` — RI/SP commitment recommendation
#   (PRD §F30.4-11 verbatim; 6 commitment_type options + 1y/3y
#   simulation; CR 1-1 verbatim audit-first INSERT AFTER commitment
#   recommendation).
# - `optimization_recommended_action` — optimization recommended action
#   apply (PRD §F30.5-10 verbatim; 5.5 EXTENSION; CR 1-1 verbatim
#   audit-first INSERT BEFORE recommended action apply).
# - `optimization_dry_run_executed` — dry-run preview completed (no
#   actual optimization; tenant_id + resource_type + trace_id payload;
#   AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT AFTER
#   dry-run preview committed).
# - `optimization_accuracy_degraded` — accuracy_score < 70% for 3
#   consecutive months detected (PRD §F30.5-9 verbatim; Phase 13
#   forecast_accuracy EXTENSION; CR 1-1 verbatim audit-first INSERT
#   BEFORE model retraining trigger).
# - `optimization_retraining_triggered` — retrain dispatch triggered
#   (PRD §F30.5-9 verbatim; `0 3 * * 0` KST Sunday 03:00; CR 1-1
#   verbatim audit-first INSERT AFTER retraining trigger).
FinopsOptimizationAction = Literal[
    "optimization_definition_updated",  # §F30.1-10 — optimization definition row update
    "recommendation_generated",  # §F30.2-11 — rightsizing recommendation generated
    "idle_resource_detected",  # §F30.3-11 — idle resource detected (z-score < -2.0)
    "commitment_recommended",  # §F30.4-11 — RI/SP commitment recommendation
    "optimization_recommended_action",  # §F30.5-10 — recommended action apply
    "optimization_dry_run_executed",  # §F30.8-1 — dry-run preview
    "optimization_accuracy_degraded",  # §F30.5-9 — accuracy_score < 70% detected
    "optimization_retraining_triggered",  # §F30.5-9 — retrain dispatch triggered
]


# Phase 15 (cj-style 123번째 wire) — AD-42 (a)~(g) verbatim + §F31.1
# + §F31.2 + §F31.3 + §F31.4 + §F31.5. 12 NEW audit actions (10 NEW = 7 d
# + 5 e EXTENSION + 1 dry_run tag_governance_dry_run_executed) (CR 1-1
# verbatim applied + ActionClass.FINOPS_TAG_GOVERNANCE):
# - `tag_policy_updated` — tag policy DSL create/update/paused/expired
#   (PRD §F31.1-10 verbatim; 6 resource_types + 4 enforcement_levels + tag
#   key validation; AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존 when
#   governance_required=True; CR 1-1 verbatim audit-first INSERT BEFORE
#   tag policy commit).
# - `untagged_resource_detected` — untagged resource detected (PRD §F31.2-11
#   verbatim; 6 resource_types (ec2/rds/s3/lambda/eks/vpc) + Phase 14
#   idle_resource_detector EXTENSION; CR 1-1 verbatim audit-first INSERT
#   AFTER untagged resource detection).
# - `allocation_rule_evaluated` — allocation rule evaluated (PRD §F31.3-11
#   verbatim; 5 rule_types parallel run (tag_match/percentage_split/
#   weighted/conditional/fallback); CR 1-1 verbatim audit-first INSERT
#   AFTER allocation rule evaluation).
# - `allocation_rule_updated` — allocation rule create/update (PRD §F31.3-11
#   verbatim; 5 rule_types + priority + tag_key + tag_value_pattern; CR 1-1
#   verbatim audit-first INSERT BEFORE/AFTER allocation rule update).
# - `compliance_report_generated` — compliance report generation (PRD
#   §F31.4-11 verbatim; ComplianceReport TypedDict + report format PDF +
#   CSV + JSON + monthly cadence; AD-22 owner-only RBAC + Epic 12 2FA
#   챌린지 보존; CR 1-1 verbatim audit-first INSERT AFTER report generation).
# - `compliance_alert_sent` — compliance alert dispatched (PRD §F31.4-11
#   verbatim; Slack #bizup-compliance-alerts + PagerDuty pd_compliance_
#   critical + Email owner-only; CR 1-1 verbatim audit-first INSERT AFTER
#   alert dispatched).
# - `compliance_remediation_initiated` — compliance remediation workflow
#   initiated (PRD §F31.4-11 verbatim; 5 steps (1. owner notifier 발송
#   + 2. tag_value 자동 추천 Phase 14 resource_pattern 기반 + 3. owner의
#   7일 SLA 내 tag 추가 + 4. 만료 시 escalate to admin + 5. audit log
#   기록); AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT
#   BEFORE remediation workflow).
# - `reconciliation_initiated` — reconciliation initiated (PRD §F31.5-11
#   verbatim; 4 reconciliation steps (1. chargeback cost aggregate + 2.
#   tag allocation cost aggregate + 3. variance 계산 + 4. investigation_
#   trigger); AD-22 owner-only RBAC; CR 1-1 verbatim audit-first INSERT
#   BEFORE reconciliation).
# - `reconciliation_report_generated` — reconciliation report generation
#   (PRD §F31.5-11 verbatim; ReconciliationReport TypedDict 13 fields +
#   variance calculation + 3 reconciliation strategy; CR 1-1 verbatim
#   audit-first INSERT AFTER reconciliation report generation).
# - `reconciliation_investigation_triggered` — reconciliation investigation
#   triggered (PRD §F31.5-11 verbatim; variance_pct > threshold →
#   Slack + Email + Jira ticket auto-create optional + 14일 SLA 내
#   resolution; CR 1-1 verbatim audit-first INSERT AFTER investigation).
# - `reconciliation_approved` — reconciliation approved (PRD §F31.5-11
#   verbatim; owner 승인 mandatory + approval pending 시 chargeback
#   status = pending_reconciliation; AD-22 owner-only RBAC; CR 1-1
#   verbatim audit-first INSERT BEFORE approval).
# - `reconciliation_resolved` — reconciliation resolved (PRD §F31.5-11
#   verbatim; reconciliation 완료 + chargeback 확정; CR 1-1 verbatim
#   audit-first INSERT AFTER resolution).
# - `tag_governance_dry_run_executed` — dry-run preview completed (PRD
#   §F31.8-1 verbatim; 5 dry-run modes (--finops-tag-policy-dry-run +
#   --finops-untagged-resource-dry-run + --finops-allocation-rule-dry-run
#   + --finops-compliance-report-dry-run + --finops-chargeback-
#   reconciliation-dry-run); AD-22 owner-only RBAC; CR 1-1 verbatim
#   audit-first INSERT AFTER dry-run preview committed).
FinopsTagGovernanceAction = Literal[
    "tag_policy_updated",  # §F31.1-10 — tag policy row update
    "untagged_resource_detected",  # §F31.2-11 — untagged resource detected
    "allocation_rule_evaluated",  # §F31.3-11 — allocation rule evaluated
    "allocation_rule_updated",  # §F31.3-11 — allocation rule row update
    "compliance_report_generated",  # §F31.4-11 — compliance report generation
    "compliance_alert_sent",  # §F31.4-11 — compliance alert dispatched
    "compliance_remediation_initiated",  # §F31.4-11 — remediation workflow
    "reconciliation_initiated",  # §F31.5-11 — reconciliation initiated
    "reconciliation_report_generated",  # §F31.5-11 — reconciliation report generation
    "reconciliation_investigation_triggered",  # §F31.5-11 — investigation triggered
    "reconciliation_approved",  # §F31.5-11 — reconciliation approved
    "reconciliation_resolved",  # §F31.5-11 — reconciliation resolved
    "tag_governance_dry_run_executed",  # §F31.8-1 — dry-run preview
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
    | ObservabilityAction  # NEW — Phase 7 (observability alert + sampling audit-first INSERT)
    | PerformanceTestAction  # NEW — Phase 8 (k6 load test + SLO + latency regression + perf regression gate + cost-engine benchmark audit-first INSERT)
    | ChaosEngineeringAction  # NEW — Phase 9 (chaos experiment + game day + continuous chaos + auto-rollback audit-first INSERT)
    | SloEngineeringAction  # NEW — Phase 10 (SLO target change + error budget + multi-region aggregation + governance review + auto-rollback SLO breach trigger audit-first INSERT)
    | FinopsAction  # NEW — Phase 11 (FinOps showback generation + department mapping update + chargeback calculation + chargeback export audit-first INSERT)
    | FinopsAnomalyAction  # NEW — Phase 12 (Cost anomaly detection + forecast accuracy + model retraining + baseline window update audit-first INSERT)
    | FinopsBudgetAction  # NEW — Phase 12 (Budget definition + threshold exceeded + alert dispatched audit-first INSERT)
    | FinopsForecastAction  # NEW — Phase 13 (Forecast definition + forecast generation + capacity headroom + budget burn-rate + forecast accuracy + model retraining + dry-run audit-first INSERT)
    | FinopsOptimizationAction  # NEW — Phase 14 (Optimization definition + rightsizing + idle detection + commitment + accuracy tracking + dry-run audit-first INSERT, AD-41)
    | FinopsTagGovernanceAction  # NEW — Phase 15 (Tag policy + untagged resource detector + allocation rules engine + compliance + chargeback allocation reconciliation + dry-run audit-first INSERT, AD-42)
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
        # Phase 7 (cj-style 91번째 wire) — OBSERVABILITY 2 values
        # (alert + trace sampling audit-first INSERT, AD-34 (e) verbatim).
        # Routes to audit_logs (NOT to a separate ledger — observability
        # events are tenant-scoped platform-event trail only, mirroring
        # AUTH (Epic 15) / INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) /
        # AUDIT (Epic 17 / Phase 6) pattern). Drift detector enforces
        # ActionClass registry ↔ DB CHECK (no-op for audit_logs per AD-2)
        # ↔ call sites parity (3-way gate). target_table=`observability`
        # aligns with ActionClass.OBSERVABILITY value (audit_log target_table
        # column populated verbatim — RLS preserved).
        ActionClass.OBSERVABILITY: (
            "audit_logs",
            frozenset(
                {
                    "alert_fired",  # §F23.5 + AC #5.9 — alert BEFORE Slack/PagerDuty dispatch
                    "trace_sampled",  # §F23.5 + AC #5.10 — sampling decision audit trace
                }
            ),
        ),
        # Phase 8 (cj-style 95번째 wire) — PERFORMANCE_TEST 4 values
        # (k6 load test start/complete + latency regression detection +
        # cost-engine benchmark invalidation audit-first INSERT, AD-35
        # (c)(d)(e)(f) verbatim). Routes to audit_logs (NOT to a separate
        # ledger — performance/load testing events are tenant-scoped
        # platform-event trail only, mirroring AUTH (Epic 15) / INFRA
        # (Phase 5) / TWO_FACTOR_AUTH (Epic 12) / AUDIT (Epic 17 / Phase
        # 6) / OBSERVABILITY (Phase 7) pattern). target_table=
        # `performance_test` aligns with ActionClass.PERFORMANCE_TEST value
        # (audit_log target_table column populated verbatim — RLS
        # preserved). Drift detector enforces ActionClass registry ↔ DB
        # CHECK (no-op for audit_logs per AD-2) ↔ call sites parity.
        ActionClass.PERFORMANCE_TEST: (
            "audit_logs",
            frozenset(
                {
                    "performance_test_started",  # §F24.1-10 — k6 load test start
                    "performance_test_completed",  # §F24.1-10 — k6 load test completion
                    "p99_regression_detected",  # §F24.4-5 — latency regression detection
                    "cost_engine_benchmark_invalidated",  # §F24.6-6 — V8 golden invalidate
                }
            ),
        ),
        # Phase 9 (cj-style 99번째 wire) — CHAOS_ENGINEERING 4 values
        # (chaos experiment start/complete + manual abort + auto-rollback
        # audit-first INSERT, AD-36 (c)(d)(e) verbatim). Routes to
        # audit_logs (NOT to a separate ledger — chaos engineering events
        # are tenant-scoped platform-event trail only, mirroring AUTH
        # (Epic 15) / INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) / AUDIT
        # (Epic 17 / Phase 6) / OBSERVABILITY (Phase 7) / PERFORMANCE_TEST
        # (Phase 8) pattern). target_table=`chaos_engineering` aligns with
        # ActionClass.CHAOS_ENGINEERING value (audit_log target_table
        # column populated verbatim — RLS preserved). Drift detector
        # enforces ActionClass registry ↔ DB CHECK (no-op for audit_logs
        # per AD-2) ↔ call sites parity.
        ActionClass.CHAOS_ENGINEERING: (
            "audit_logs",
            frozenset(
                {
                    "chaos_experiment_started",  # §F25.1-7 — chaos experiment run start
                    "chaos_experiment_completed",  # §F25.3-8 — chaos experiment completion
                    "chaos_experiment_aborted",  # §F25.3-8 + §F25.1-5 — manual/abort trigger
                    "chaos_rollback_triggered",  # §F25.6-6 — auto-rollback strategy execution
                }
            ),
        ),
        # Phase 10 (cj-style 103번째 wire) — SLO_ENGINEERING 3 values
        # (SLO target change + error budget exhaustion + multi-window
        # burn-rate composite alert audit-first INSERT, AD-37 (b)(d)(e)
        # verbatim). Routes to audit_logs (NOT to a separate ledger —
        # SLO engineering events are tenant-scoped platform-event trail
        # only, mirroring AUTH (Epic 15) / INFRA (Phase 5) /
        # TWO_FACTOR_AUTH (Epic 12) / AUDIT (Epic 17 / Phase 6) /
        # OBSERVABILITY (Phase 7) / PERFORMANCE_TEST (Phase 8) /
        # CHAOS_ENGINEERING (Phase 9) pattern). target_table=
        # `slo_engineering` aligns with ActionClass.SLO_ENGINEERING value
        # (audit_log target_table column populated verbatim — RLS
        # preserved). Drift detector enforces ActionClass registry ↔ DB
        # CHECK (no-op for audit_logs per AD-2) ↔ call sites parity
        # (3-way gate). Phase 9 cj-style 99번째 wire `test_phase_9_audit_action.py`
        # pattern verbatim applied.
        ActionClass.SLO_ENGINEERING: (
            "audit_logs",
            frozenset(
                {
                    "slo_target_updated",  # §F26.1-7 — SLO target / state change
                    "slo_budget_exhausted",  # §F26.3-6 — error budget exhaustion + freeze
                    "slo_violation_detected",  # §F26.5-5 — multi-window composite alert
                }
            ),
        ),
        # Phase 11 (cj-style 107번째 wire) — FINOPS 4 values
        # (showback generation + department mapping update + chargeback
        # calculation + chargeback export audit-first INSERT, AD-38
        # (b)(c)(e) verbatim). Routes to audit_logs (NOT to a separate
        # ledger — FinOps events are tenant-scoped platform-event trail
        # only, mirroring AUTH (Epic 15) / INFRA (Phase 5) /
        # TWO_FACTOR_AUTH (Epic 12) / AUDIT (Epic 17 / Phase 6) /
        # OBSERVABILITY (Phase 7) / PERFORMANCE_TEST (Phase 8) /
        # CHAOS_ENGINEERING (Phase 9) / SLO_ENGINEERING (Phase 10)
        # pattern). target_table=`finops` aligns with ActionClass.FINOPS
        # value (audit_log target_table column populated verbatim — RLS
        # preserved). Drift detector enforces ActionClass registry ↔ DB
        # CHECK (no-op for audit_logs per AD-2) ↔ call sites parity
        # (3-way gate). Phase 10 cj-style 103번째 wire `test_phase_10_audit_action.py`
        # pattern verbatim applied.
        ActionClass.FINOPS: (
            "audit_logs",
            frozenset(
                {
                    "showback_generated",  # §F27.1-7 — showback report generation
                    "department_mapping_updated",  # §F27.3-3 — department mapping change
                    "chargeback_calculated",  # §F27.4-4 — chargeback calculation
                    "chargeback_exported",  # §F27.5-8 — CSV/PDF export
                }
            ),
        ),
        # Phase 12 (cj-style 111번째 wire) — FINOPS_ANOMALY 4 values
        # (anomaly detection + forecast accuracy + model retraining +
        # baseline window update audit-first INSERT, AD-39
        # (b)(d)(e)(f) verbatim). Routes to audit_logs (NOT to a separate
        # ledger — FinOps anomaly events are tenant-scoped platform-event
        # trail only, mirroring FINOPS Phase 11 wire + AUTH (Epic 15) /
        # INFRA (Phase 5) / TWO_FACTOR_AUTH (Epic 12) / AUDIT (Epic 17 /
        # Phase 6) / OBSERVABILITY (Phase 7) / PERFORMANCE_TEST (Phase
        # 8) / CHAOS_ENGINEERING (Phase 9) / SLO_ENGINEERING (Phase 10)
        # pattern). target_table=`finops_anomaly` aligns with
        # ActionClass.FINOPS_ANOMALY value (audit_log target_table
        # column populated verbatim — RLS preserved). Drift detector
        # enforces ActionClass registry ↔ DB CHECK (no-op for
        # audit_logs per AD-2) ↔ call sites parity (3-way gate).
        # Phase 11 cj-style 107번째 wire `test_phase_11_audit_action.py`
        # pattern verbatim applied.
        ActionClass.FINOPS_ANOMALY: (
            "audit_logs",
            frozenset(
                {
                    "anomaly_detected",  # §F28.1-12 — multi-method voting consensus
                    "forecast_deviation",  # §F28.5-7 — forecast accuracy deviation
                    "model_retraining_triggered",  # §F28.5-7 — MAPE > 20% retrain
                    "anomaly_baseline_updated",  # §F28.3-12 — baseline window update
                }
            ),
        ),
        # Phase 12 (cj-style 111번째 wire) — FINOPS_BUDGET 3 values
        # (budget definition + threshold exceeded + alert dispatched
        # audit-first INSERT, AD-39 (c)(e)(g) verbatim). Routes to
        # audit_logs (NOT to a separate ledger — FinOps budget events
        # are tenant-scoped platform-event trail only, mirroring
        # FINOPS_ANOMALY + FINOPS Phase 11 wire pattern). target_table=
        # `finops_budget` aligns with ActionClass.FINOPS_BUDGET value
        # (audit_log target_table column populated verbatim — RLS
        # preserved). Drift detector enforces ActionClass registry ↔
        # DB CHECK (no-op for audit_logs per AD-2) ↔ call sites parity
        # (3-way gate).
        ActionClass.FINOPS_BUDGET: (
            "audit_logs",
            frozenset(
                {
                    "budget_definition_updated",  # §F28.2-12 — budget row update
                    "budget_threshold_exceeded",  # §F28.4-12 — threshold crossed
                    "budget_alert_sent",  # §F28.4-12 — alert dispatched
                }
            ),
        ),
        # Phase 13 (cj-style 115번째 wire) — FINOPS_FORECAST 7 values
        # (forecast definition + forecast generation + capacity headroom +
        # budget burn-rate + forecast accuracy + model retraining + dry-run
        # audit-first INSERT, AD-39 verbatim). Routes to audit_logs (NOT
        # to a separate ledger — FinOps forecast events are tenant-scoped
        # platform-event trail only, mirroring FINOPS_BUDGET +
        # FINOPS_ANOMALY Phase 12 wire + FINOPS Phase 11 wire pattern).
        # target_table=`finops_forecast` aligns with
        # ActionClass.FINOPS_FORECAST value (audit_log target_table column
        # populated verbatim — RLS preserved). Drift detector enforces
        # ActionClass registry ↔ DB CHECK (no-op for audit_logs per AD-2)
        # ↔ call sites parity (3-way gate).
        ActionClass.FINOPS_FORECAST: (
            "audit_logs",
            frozenset(
                {
                    "forecast_definition_updated",  # §F29.1-12 — forecast definition row update
                    "forecast_generated",  # §F29.2-12 — forecast prediction completed
                    "capacity_headroom_analyzed",  # §F29.3-12 — capacity headroom analysis
                    "budget_burn_rate_projected",  # §F29.4-12 — burn-rate projection
                    "forecast_accuracy_degraded",  # §F29.5-12 — MAPE > 20% detected
                    "model_retraining_triggered",  # §F29.5-12 — retrain dispatch triggered
                    "forecast_dry_run_executed",  # §F29.1-5 — dry-run preview
                }
            ),
        ),
        # Phase 14 (cj-style 119번째 wire) — FINOPS_OPTIMIZATION 8 values
        # (optimization definition + rightsizing + idle detection +
        # commitment + accuracy tracking + dry-run audit-first INSERT,
        # AD-41 verbatim). Routes to audit_logs (NOT to a separate
        # ledger — FinOps optimization events are tenant-scoped
        # platform-event trail only, mirroring FINOPS_FORECAST +
        # FINOPS_BUDGET + FINOPS_ANOMALY Phase 12 wire + FINOPS Phase 11
        # wire pattern). target_table=`finops_optimization` aligns with
        # ActionClass.FINOPS_OPTIMIZATION value (audit_log target_table
        # column populated verbatim — RLS preserved). Drift detector
        # enforces ActionClass registry ↔ DB CHECK (no-op for
        # audit_logs per AD-2) ↔ call sites parity (3-way gate).
        ActionClass.FINOPS_OPTIMIZATION: (
            "audit_logs",
            frozenset(
                {
                    "optimization_definition_updated",  # §F30.1-10 — optimization definition row update
                    "recommendation_generated",  # §F30.2-11 — rightsizing recommendation generated
                    "idle_resource_detected",  # §F30.3-11 — idle resource detected (z-score < -2.0)
                    "commitment_recommended",  # §F30.4-11 — RI/SP commitment recommendation
                    "optimization_recommended_action",  # §F30.5-10 — recommended action apply
                    "optimization_dry_run_executed",  # §F30.8-1 — dry-run preview
                    "optimization_accuracy_degraded",  # §F30.5-9 — accuracy_score < 70% detected
                    "optimization_retraining_triggered",  # §F30.5-9 — retrain dispatch triggered
                }
            ),
        ),
        # Phase 15 (cj-style 123번째 wire) — FINOPS_TAG_GOVERNANCE 13
        # values (tag policy + untagged resource detector + allocation
        # rules engine + compliance + reconciliation + dry-run audit-
        # first INSERT, AD-42 verbatim). Routes to audit_logs (NOT to a
        # separate ledger — FinOps tag governance events are tenant-
        # scoped platform-event trail only, mirroring FINOPS_OPTIMIZATION
        # + FINOPS_FORECAST + FINOPS_BUDGET + FINOPS_ANOMALY Phase 12 wire
        # + FINOPS Phase 11 wire pattern). target_table=
        # `finops_tag_governance` aligns with ActionClass.FINOPS_TAG_GOVERNANCE
        # value (audit_log target_table column populated verbatim — RLS
        # preserved). Drift detector enforces ActionClass registry ↔ DB
        # CHECK (no-op for audit_logs per AD-2) ↔ call sites parity
        # (3-way gate). Phase 14 cj-style 119번째 wire FINOPS_OPTIMIZATION
        # registry pattern verbatim applied.
        ActionClass.FINOPS_TAG_GOVERNANCE: (
            "audit_logs",
            frozenset(
                {
                    "tag_policy_updated",  # §F31.1-10 — tag policy row update
                    "untagged_resource_detected",  # §F31.2-11 — untagged resource detected
                    "allocation_rule_evaluated",  # §F31.3-11 — allocation rule evaluated
                    "allocation_rule_updated",  # §F31.3-11 — allocation rule row update
                    "compliance_report_generated",  # §F31.4-11 — compliance report generation
                    "compliance_alert_sent",  # §F31.4-11 — compliance alert dispatched
                    "compliance_remediation_initiated",  # §F31.4-11 — remediation workflow
                    "reconciliation_initiated",  # §F31.5-11 — reconciliation initiated
                    "reconciliation_report_generated",  # §F31.5-11 — reconciliation report generation
                    "reconciliation_investigation_triggered",  # §F31.5-11 — investigation triggered
                    "reconciliation_approved",  # §F31.5-11 — reconciliation approved
                    "reconciliation_resolved",  # §F31.5-11 — reconciliation resolved
                    "tag_governance_dry_run_executed",  # §F31.8-1 — dry-run preview
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
    "ObservabilityAction",  # NEW — Phase 7 (observability alert + sampling audit-first INSERT)
    "PerformanceTestAction",  # NEW — Phase 8 (k6 load test + SLO + latency regression + perf regression gate + cost-engine benchmark audit-first INSERT)
    "ChaosEngineeringAction",  # NEW — Phase 9 (chaos experiment + game day + continuous chaos + auto-rollback audit-first INSERT)
    "SloEngineeringAction",  # NEW — Phase 10 (SLO target change + error budget + multi-region aggregation + governance review + auto-rollback SLO breach trigger audit-first INSERT)
    "FinopsAction",  # NEW — Phase 11 (FinOps showback generation + department mapping update + chargeback calculation + chargeback export audit-first INSERT)
    "FinopsAnomalyAction",  # NEW — Phase 12 (Cost anomaly detection + forecast accuracy + model retraining + baseline window update audit-first INSERT)
    "FinopsBudgetAction",  # NEW — Phase 12 (Budget definition + threshold exceeded + alert dispatched audit-first INSERT)
    "FinopsForecastAction",  # NEW — Phase 13 (Forecast definition + forecast generation + capacity headroom + budget burn-rate + forecast accuracy + model retraining + dry-run audit-first INSERT)
    "FinopsOptimizationAction",  # NEW — Phase 14 (Optimization definition + rightsizing + idle detection + commitment + accuracy tracking + dry-run audit-first INSERT, AD-41)
    "FinopsTagGovernanceAction",  # NEW — Phase 15 (Tag policy + untagged resource detector + allocation rules engine + compliance + chargeback allocation reconciliation + dry-run audit-first INSERT, AD-42)
    "emit_audit_typed",
]
