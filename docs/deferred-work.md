# Deferred Work — costmgr project

Items honestly DEFERred from completed sprints per CR 11-3 honest-DEFER
discipline (8번째 epic 연속 적용). Each entry records: source story,
reason for deferral, scope of deferred work, pickup plan.

## Deferred from: 12-3 (Account Deletion + Retention Consent)

Story 12.3 atomic wire completed 2026-08-15. 5 items honestly-DEFERred
per CR 11-3 discipline (8번째 epic 연속 — Epic 4·5·6·11·12 + carry-over 3번째):

### D-12-3-DEFER-1 — Quarterly 5-year audit aggregate
- Source: `apps/api/modules/m12_account/services/account_deletion_service.py`
  (registry placeholder for `deletion_audit_archived` action)
- Reason: NFR4 2절 requires quarterly aggregation of audit_logs into
  5-year cold storage. Sprint-scale (would require new ETL pipeline +
  cold-storage backend); spec wire 0건.
- Scope: future Story (12-3.5 or 13-N). Solution candidates: scheduled
  worker that copies `audit_logs` rows older than 5 years to cold storage
  + removes the in-DB copy.
- CR 11-3 honest-DEFER (structural sprint-scale).

### D-12-3-DEFER-2 — Configurable `retention_days`
- Source: `packages/services/m12_account/account_deletion.py::RETENTION_DAYS`
- Reason: MVP fixed `RETENTION_DAYS = 30` (epics.md AC verbatim). Spec did
  not allow per-tenant configurability.
- Scope: future Story when AD-23 settings aggregate extension adds
  `account_settings.retention_days` per-tenant override. Pure-kernel
  function `compute_deletion_scheduled_for` already accepts caller-controlled
  `requested_at` (CR 12-1 L1); extension would add `tenant_settings` lookup.
- CR 11-3 honest-DEFER (low priority, no immediate customer demand).

### D-12-3-DEFER-3 — NFR7 2FA 진입 gate (other account mutations)
- Source: `apps/api/modules/m12_account/handlers.py` (destructive endpoint
  3-layer TOTP defense — only on `POST /api/v1/account/deletion/request`)
- Reason: NFR7 requires 2FA on destructive endpoints. 12-3 implements this
  for the destructive deletion endpoint only. Other account mutations
  (email change, password reset) are honestly DEFERRED.
- Scope: future Story 12-3.6 or 13-N. Solution: extend 3-layer TOTP defense
  pattern to all `require_role("owner")` mutation routes.
- CR 11-3 honest-DEFER (medium priority — security baseline extension).

### D-12-3-DEFER-4 — Playwright E2E for account deletion flow
- Source: `apps/web/app/[locale]/(dashboard)/account/settings/page.tsx`
  (RSC + embedded AccountDeletionModal)
- Reason: Vitest component tests (27 NEW cases) cover the modal + status
  panel + parity. Playwright E2E for the full owner flow (login → settings
  → totp verify → consent type → submit → pending state → cancel) was
  deferred following the 12-5 T6 pattern (sprint-scale).
- Scope: future Story 12-3.7 (mirror 12-5 T6). Solution: 4 NEW Playwright
  spec files (m12-deletion-totp + m12-deletion-consent + m12-deletion-cancel
  + m12-deletion-status) with `page.route()` interception pattern.
- CR 11-3 honest-DEFER (HIGH priority — runtime E2E verification).

### D-12-3-DEFER-5 — Cross-region replication
- Source: `apps/api/alembic/versions/0025_tenants_deletion_status.py`
  (`deletion_consents` table stored in Supabase Postgres Seoul region)
- Reason: AD-9 Seoul region requirement disables cross-region replication.
  `deletion_consents` rows must stay in Seoul for data-residency compliance.
- Scope: BLOCKED by AD-9 (architectural decision, not a sprint deferral).
- CR 11-3 honest-DEFER (BLOCKED — architectural).

### Pickup plan (5 deferred items)

- **HIGH priority**: D-12-3-DEFER-4 (Playwright E2E) — follow-up sprint
  mirroring 12-5 T6 pattern. Estimated 4 spec files / +600 lines / 16
  scenarios.
- **MEDIUM priority**: D-12-3-DEFER-3 (NFR7 2FA gate on other mutations)
  — sprint-scale security baseline extension.
- **LOW priority**: D-12-3-DEFER-1 (5-year audit aggregation) — future
  cold-storage ETL pipeline.
- **LOW priority**: D-12-3-DEFER-2 (configurable retention_days) — only if
  customer demand materializes (no immediate driver).
- **BLOCKED**: D-12-3-DEFER-5 (cross-region replication) — AD-9 architectural
  decision.

## Deferred from: 12-4 (Epic 12 carry-over sprint)

Story 12.4 sprint-up'd 4 items honestly-DEFERred from Story 12.1 (T3 + T4 +
T8 + T10). The carry-over sprint completed the backend wire (8 routes + 1
M2 entry gate route, 14 typed exception handlers, 12 T2 migration tests,
4 RLS policies, audit_logs-no-CHECK invariant regression test) and a
minimum-viable frontend wire (3 TS mirrors + 1 TwoFactorGuard component +
m2-input page mount + 23 vitest parity tests + ko-KR.json extensions).

### Honestly DEFERRED items (pickup: future Story 12.5 or Epic 13)

#### 1. TwoFactorSetupForm component

- Source: Story 12.4 T3 spec (component list, item 1 of 5)
- Reason: form UX requires careful wizard design (3-step flow: scan QR →
  enter code → save recovery codes). Wire-up depends on QR rendering
  strategy which is blocked by dependency rule.
- Scope: `apps/web/components/m12-account/TwoFactorSetupForm.tsx` with
  step1 (display secret + otpauth URI), step2 (verify 6-digit code),
  step3 (display 8 recovery codes with copy-to-clipboard). Calls
  POST /api/v1/account/2fa/setup then POST /api/v1/account/2fa/verify.

#### 2. TwoFactorChallengeDialog component

- Source: Story 12.4 T3 spec (component list, item 2 of 5)
- Reason: dialog UX needs M2 entry integration story (replaces the
  default M2 entry render with the challenge dialog when 2FA required).
  State machine needs `useTwoFactorGuard` hook for retry/lockout UX.
- Scope: `apps/web/components/m12-account/TwoFactorChallengeDialog.tsx`
  with 6-digit input + "use recovery code" toggle. Calls POST
  /api/v1/account/2fa/challenge, on lockout (429) shows retry timer.

#### 3. TwoFactorDisableForm component

- Source: Story 12.4 T3 spec (component list, item 3 of 5)
- Reason: disable UX requires owner-only mutation gate UX (admin override
  reason field needs text-area, validation, etc.). Wire-up needs
  separate "disable 2FA" settings page.
- Scope: `apps/web/components/m12-account/TwoFactorDisableForm.tsx`
  with code-input OR admin-override reason input (≥ 20 chars). Calls
  POST /api/v1/account/2fa/disable.

#### 4. TwoFactorStatusBadge component

- Source: Story 12.4 T3 spec (component list, item 4 of 5)
- Reason: status badge needs GET /api/v1/account/2fa/status server-side
  fetch wiring in page-level Server Component. Trivial but requires
  tenant_context resolution (out of scope for sprint).
- Scope: `apps/web/components/m12-account/TwoFactorStatusBadge.tsx`
  showing enabled/disabled/locked badge + recovery_codes_remaining count.

#### 5. `/account/security` NEW page

- Source: Story 12.4 T3 spec (1 NEW page)
- Reason: page composition (route group placement + Server Component +
  client form composition) is a 0.5 plumbing step that requires the
  4 above components to be wired first. Owner of M12-Account
  navigation entry.
- Scope: `apps/web/app/[locale]/(dashboard)/account/security/page.tsx`
  with role check, capability-free 2FA section, link to disable flow.
  Route: `/[locale]/(dashboard)/account/security`.

#### 6. QR image rendering

- Source: Story 12.4 T3 spec (TwoFactorSetupForm step1)
- Reason: `qrcode.react` is not installed in `apps/web/package.json`.
  Adding a new npm dependency triggers the BMAD workflow's
  HALT-for-new-dependencies rule plus CR 0-3 lockfile-drift risk.
- Scope: install `qrcode.react` + verify lockfile + add import in
  TwoFactorSetupForm.tsx.
- Workaround applied: TwoFactorGuard.tsx renders the `otpauth://` URI
  as a clickable link (manual-entry fallback supported by all major
  authenticator apps).

#### 7. Playwright E2E specs

- Source: Story 12.4 T3 spec (16 NEW E2E cases)
- Reason: Playwright tests require running FastAPI app + Supabase DB
  + test JWT issuance. Out of scope for the backend-sprint carry-over;
  belongs to a frontend-flow sprint with running infrastructure.
- Scope: `apps/web/e2e/m12-account/` with setup/challenge/recovery/
  disable flows. Pattern mirrors Story 11.4 E2E specs.

### CR 11-4 lessons applied to deferred items

- D-001 (must actually mount components in page.tsx): for the
  minimum-viable wire, `<TwoFactorGuard>` IS mounted in
  `m2-input/period/[periodKey]/page.tsx`. Future stories must apply
  the same discipline to the 4 deferred components.
- D-002 (ko-KR.json SSOT = `apps/web/messages/ko-KR.json` ONLY): all
  minimum-viable strings added directly to ko-KR.json. Future stories
  must NOT introduce new i18n files.
- D-005 (TS mirror unknown state must reject, not fall through to
  authorized): all 3 TS mirrors explicitly return
  `authorized=false` + reject_reason_ko for unknown / malformed input.

### Pickup plan

- Story 12.5 (proposed): "2FA Form Components + QR + Playwright E2E"
  — sprint up the 7 deferred items in 1 story (~1,800 LOC + 16 E2E).
- Alternative: split into Story 12.5a (4 components + status badge +
  account/security page) and Story 12.5b (QR + Playwright E2E).

## Deferred from: code review of 12-4-epic-12-carry-over-sprint (2026-08-11)

bmad-code-review 1st sweep surfaced 4 pre-existing issues that are out of
scope for the 12.4 wire (would expand scope beyond carry-over sprint
budget). These are documented honestly per CR 11-3 discipline:

### Pre-existing deferred items

#### D-01 — Spec text typo "AD-3 (RLS) column-level encryption"
- Source: `_bmad-output/implementation-artifacts/12-4-epic-12-carry-over-sprint.md:404`
- Reason: RLS is row-level (AD-3), column-level encryption is via NFR6
  AES-256-GCM. Confusing two security layers. Inherited from 12-1 spec.
- Scope: Spec text clarification (1 paragraph).

#### D-02 — Spec AC #11 says "5 components" but only TwoFactorGuard mounted
- Source: `12-4-epic-12-carry-over-sprint.md:354-359`
- Reason: 4 components honestly DEFERred to Story 12.5 (TwoFactorSetupForm +
  TwoFactorChallengeDialog + TwoFactorDisableForm + TwoFactorStatusBadge).
  CR 11-3 honest-DEFER discipline (5번째 epic 연속). Spec AC text was
  inherited from 12-1 carry-over scope description.
- Scope: AC #11 bullet 1 amendment (document deviation).

#### D-03 — Audit_logs CHECK EXTENSION 0023 NOT WIRED
- Source: `12-4-epic-12-carry-over-sprint.md` §AC #10 bullet 2
- Reason: `audit_logs.action` has NO CHECK constraint in current schema
  (per A5 drift detector design). Dev wire correctly pinned this with
  4 invariant regression tests in `test_audit_logs_no_action_check_constraint.py`.
  Pre-existing schema state from 0001 migration.
- Scope: AC #10 bullet 2 amendment (document absence of CHECK).

#### D-04 — Loose test assertion in test_handlers_route_shape
- Source: `tests/api/m12_account/test_handlers_route_shape.py:4693-4703`
- Reason: `r.path.startswith("/api/v1/m2-entry-gate")` is order-sensitive
  subset check. Acceptable for current 9-route surface but loose if future
  routes are added without scope discipline.
- Scope: Replace with strict `==` set comparison (LOW effort, 1 line).

### Pickup plan (4 deferred items)

- Story 12.4.1 carry-over sprint (proposed, parallel to 12.5 form
  components sprint-up): wire 16 HIGH + 16 MEDIUM patches surfaced by
  this review (separate sprint per CR 11-3 honest-DEFER discipline — too
  many PATCH items for in-place patching during 3rd sweep).
- Pickup target: 12.4.1 T1 (HIGH patches) + T2 (MEDIUM patches) OR
  amend Story 12.5 scope to include these patches alongside the 7 form
  components.
- Items D-01~D-04 may stay in this file as documentation drift cleanup
  for future retro.

## Deferred from: code review of 12-2-daily-auto-backup-json-self-download (2026-08-14)

bmad-code-review 3rd sweep chunk 1 (backend, 12 files) surfaced 1
pre-existing scalability concern that is out of scope for the 12-2
wire (would expand scope beyond daily auto-backup + JSON self-download
sprint budget). Documented honestly per CR 11-3 discipline:

### Pre-existing deferred items

#### D-12-2-DEFER-1 — backup_daily cron sequential per-tenant iteration
- Source: `apps/api/jobs/backup_daily.py:507-541`
- Reason: cron iterates all tenants sequentially in a single session.
  For fleet > 50 tenants, the 1-hour KST window (02:00-03:00) may be
  exceeded, causing overlap with `backup_retention` cron at KST 03:00.
  Spec did not specify concurrent batching strategy.
- Scope: future Story (12-2.5 or 13-N). Solution candidates: batch
  tenants into groups of 50 with `asyncio.gather()`, OR move to
  Railway cron with worker-queue.
- CR 11-3 honest-DEFER (structural W-class — pre-existing scalability,
  not a critical correctness invariant).
