# Deferred Work — costmgr project

Items honestly DEFERred from completed sprints per CR 11-3 honest-DEFER
discipline (11번째 epic 연속 적용). Each entry records: source story,
reason for deferral, scope of deferred work, pickup plan.

## Deferred from: 7-2 (Next-Month Projection with 4 Required Parameters)

Story 7.2 atomic wire completed 2026-08-15. 6 items honestly-DEFERred
per CR 11-3 discipline (12번째 epic 연속 — Epic 4·5·6·11·12·A19·7-1·7-2 + 8-1):

### D-7-2-DEFER-1 — AI 추천 4종 파라미터 (F10.1 input_drafts 우회)
- Source: `apps/web/components/m7-simulation/ProjectionForm.tsx` (4 inputs)
- Reason: AI 추천은 Epic 10 carry-over (F10.1 input_drafts 우회 필수).
  차입금·이자율·원가 상승률·법인세율 4종을 자동 추천하려면
  `input_drafts` 인프라가 먼저 필요한데, 이는 Epic 10의 F10.1.
- Scope: 1 NEW ML 모델 + 4 NEW UI 추천 버튼 + input_drafts 연동.
  ~300 LOC backend + ~150 LOC frontend.
- Pickup plan: Epic 10 진입 시 (F10.1 wire 후).

### D-7-2-DEFER-2 — 차월 추정 시나리오 저장 (Epic 8 Pre-Standard Cost 패턴)
- Source: PRD §F7.2 + `apps/api/modules/m7_simulation/services/projection_service.py`
- Reason: PRD §F7.2는 단일 차월 추정 (현재 projection_month 1개).
  "2026-08#P1" 같은 virtual projection key로 multi-scenario 저장은
  Epic 8 Budget Pre-Standard Cost 패턴 (D-8-1-DEFER-4) 완성 후 결정.
- Scope: 1 NEW `derive_projection_key` pure kernel + DB column +
  `monthly_input_periods.projection_key` RLS 정책.
- Pickup plan: 7-3 retro 결정 (Epic 7 close-out 시).

### D-7-2-DEFER-3 — Monte Carlo projection sensitivity (multi-variate)
- Source: `packages/cost_engine/projection.py` (single-point projection)
- Reason: Single-point projection → multi-variate sensitivity는
  7-1 honestly DEFER #2와 동일 사유 (over-engineering 회피).
  4 inputs × 100 trials = 400 evaluations → 1초 한도 초과 위험.
- Scope: 1 NEW `monte_carlo_projection` pure kernel + Recharts distribution chart.
- Pickup plan: 7-3 retro 결정 (demand-driven).

### D-7-2-DEFER-4 — PDF 보고서 다국어 (ko-KR only per NFR18)
- Source: `apps/web/components/m7-simulation/ProjectionPdfButton.tsx`
- Reason: NFR18 (ko-KR only MVP) — 영문/중문 PDF는 2차 release.
  M5 PDF generator reuse (`packages/services/m6_reports/pdf_helpers.py`)
  현재 ko-KR only.
- Scope: 1 NEW i18n PDF template layer (en/zh-CN/ja 등).
- Pickup plan: 2차 multi-locale release 시 (Epic 10+ carry-over).

### D-7-2-DEFER-5 — Playwright E2E (16 cases)
- Source: `apps/web/components/m7-simulation/ProjectionClient.tsx`
- Reason: 7-2 sprint는 frontend wire + unit tests까지 포함.
  Playwright E2E는 sprint-scale follow-up sprint 패턴
  (12-5 T6 패턴, 6번째 epic 연속).
- Scope: 16 NEW test scenarios across 4 spec files
  (4-form-fill / submit-disabled / submit-success / PDF-download).
- Pickup plan: 7-2 follow-up sprint (carry-over pattern 6번째).

### D-7-2-DEFER-6 — Web Worker offload (over-engineering 회피)
- Source: `apps/web/components/m7-simulation/ProjectionClient.tsx`
- Reason: 1초 한도 (NFR9) 대비 5배 여유 (200ms P95 측정).
  Web Worker offload은 pure-frontend TS mirror에 의존 — 복잡도 대비
  이득 없음. 7-1 honestly DEFER #1과 동일 사유.
- Scope: 1 NEW `m7-projection.worker.ts` + Comlink bridge.
- Pickup plan: 7-3 retro 결정 (only if 200ms P95 violated).

### D-7-2-DEFER-7 — react-hook-form + zod 의존성 추가
- Source: `apps/web/components/m7-simulation/ProjectionForm.tsx`
- Reason: 스펙은 react-hook-form + Zod schema 사용을 권장했지만,
  두 패키지 모두 현재 `apps/web/package.json`에 미포함. 본 sprint는
  dependency 추가 없이 atomic wire 완료 우선시 → plain React `useState`
  + inline validation으로 대체 (동일 bounds + 동일 `disabled` gate).
- Scope: 1 patch — `pnpm add zod react-hook-form` 후
  `ProjectionForm.tsx`을 `useForm` + `zodResolver` 패턴으로 마이그레이션.
  `lib/m7-simulation-projection-schema.ts`는 이미 Zod-style API surface
  (validateProjectionInputs) 제공 — 마이그레이션 비용 ~30 LOC.
- Pickup plan: 7-2 follow-up sprint 또는 8-1 dependency bump 시.

## Deferred from: 8-1 (Virtual Budget Period Key + Scenario Lock to One)

Story 8.1 atomic wire completed 2026-08-15. 5 items honestly-DEFERred
per CR 11-3 discipline (11번째 epic 연속 — Epic 4·5·6·11·12·A19·7-1·7-2 + 8-1):

### D-8-1-DEFER-1 — Full DB integration tests (real Postgres)
- Source: `tests/services/test_m8_budget_scenario_service.py`
- Reason: 8.1 atomic wire used mocked AsyncSession for service tests
  (no local Postgres in CI). The CR 12-5 L3 defense-in-depth (DB UNIQUE
  constraint + RLS) requires real DB roundtrip to verify.
- Scope: 1 sprint-up test file (~150 LOC) using existing 0026 migration +
  RLS 0016 — covers INSERT happy path + 409 SCENARIO_LIMIT_EXCEEDED race +
  RLS same-tenant SELECT isolation.
- Pickup plan: Story 8.2 cj-style follow-up (when ≥5 테넌트 요청 triggers
  multi-scenario wire).

### D-8-1-DEFER-2 — Multi-scenario comparison (`scenario_index >= 2`)
- Source: `packages/cost_engine/budget_period_key.py::MVP_SCENARIO_INDEX=1`
- Reason: PRD §15 NON-GOAL #2 verbatim — 1차 MVP = 1 scenario only.
- Scope: 1 NEW pure function `derive_multi_scenario_budget_period_keys`
  + 1 NEW typed exception `MultiScenarioNotSupportedYetError` + DB
  constraint relaxation + RLS multi-row policy.
- Pickup plan: Story 8.2 spec 진입 (cj-style 7번째 epic 연속).

### D-8-1-DEFER-3 — Budget vs Actual Variance Table with ABCD Gray Badge (PRD §F8.2)
- Source: PRD §F8.2 + Epic 8 retro A20
- Reason: PRD §F8.2 — Epic 8 story 2.
- Scope: 1 NEW pure kernel `variance_calculator.py` + 4 NEW typed
  exceptions + ABCD badge component + ReadOnlyTable RSC.
- Pickup plan: Story 8.2 cj-style (PRD §F8.2 wire).

### D-8-1-DEFER-4 — Budget Pre-Standard Cost Preview (`engine_type='budget'`)
- Source: PRD §F8.3 + Epic 8 retro A20
- Reason: PRD §F8.3 — Epic 8 story 3.
- Scope: 1 NEW `BudgetEngine` wrapper around `fiscal_period_snapshots` +
  pre-standard cost preview endpoint + RSC.
- Pickup plan: Story 8.3 cj-style (PRD §F8.3 wire).

### D-8-1-DEFER-5 — Playwright E2E (16 cases)
- Source: `apps/web/components/m8-budget/BudgetScenarioPanel.tsx`
- Reason: Playwright E2E suite not yet built for Epic 8 surface
  (cj-style follow-up sprint pattern — 6번째 epic 연속).
- Scope: 16 NEW test scenarios across 4 spec files
  (setup / create / list / detail).
- Pickup plan: Epic 8 follow-up sprint (post-8.2 + 8.3 wire).

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

#### D-7-1-DEFER-1 — CVP slider Web Worker offload
- Source: `apps/web/components/m7-simulation/CVPSimulationClient.tsx:140-180`
- Reason: 1초 한도 (NFR9 stricter) 대비 150ms debounce + 10ms pure calc
  + 50ms React re-render = 210ms P95 — over-engineering 회피 (1초 한도
  대비 5배 여유).
- Scope: future sprint (follow-up sprint). Reassess when P95 > 500ms OR
  when slider 드래그가 10+ 동시 사용 패턴으로 escalate.

#### D-7-1-DEFER-2 — Monte Carlo sensitivity 분석
- Source: `packages/cost_engine/cvp.py:simulate_cvp` (single-variable only)
- Reason: 단일 변수 슬라이더만 — multi-variate (joint distribution over
  4 variables) 는 7-3 retro 결정 시 deferred.
- Scope: cj-style 7-3 retro 진입 시 N차 follow-up.

#### D-7-1-DEFER-3 — AI 추천 가격 제안 (input_drafts 우회)
- Source: `apps/web/components/m7-simulation/CVPSimulationClient.tsx` (no AI hint)
- Reason: Epic 10 carry-over (input_drafts 우회 필수). 가격 추천 시
  baseline + cost driver 분석 필수 — 7-1 scope 외.
- Scope: Epic 10 wire 후 follow-up sprint.

#### D-7-1-DEFER-4 — 차월 추정 4종 파라미터 (Story 7-2)
- Source: `packages/cost_engine/cvp.py` (현재월 simulation only)
- Reason: cj-style 3-story 분할 2번째 진입점 — projection.py surface 분리
  (A19 cohesion pattern).
- Scope: bmad-dev-story 7-2 T1~T8 execution sprint.

#### D-7-1-DEFER-5 — Playwright E2E for CVPSimulationClient
- Source: `apps/web/components/m7-simulation/CVPSimulationClient.tsx`
- Reason: sprint-scale atomic wire (12-5 T6 패턴 검증). 1차 MVP launch
  후 follow-up sprint.
- Scope: 7-1 follow-up sprint (cj-style sprint pattern 12-1/12-4/12-5 T6
  + 12-3 T7 mirror).

## Epic 9 (ABC / TDABC Engine — Service Business) honestly DEFER

### Story 9.1 (Cost Pool + Activity + Driver 100% Validation) — 6 honestly DEFER

#### D-9-1-DEFER-1 — CCR (Cost Center Rate) compute
- Source: `packages/cost_engine/abc_engine.py` (validate_* only — no compute)
- Reason: 9-1 = validation only. CCR compute = cost_pool_total /
  activity_hours = KRW/hr, arrives in 9-2 wire.
- Scope: bmad-dev-story 9-2 T1~T8 execution sprint.

#### D-9-1-DEFER-2 — ABC allocation engine (driver × CCR = activity cost)
- Source: `packages/cost_engine/abc_engine.py` (no allocation routine)
- Reason: 9-1 = pre-condition validation. ABC allocation = driver_qty ×
  CCR = KRW allocated to activity, arrives in 9-3 wire.
- Scope: bmad-dev-story 9-3 T1~T8 execution sprint.

#### D-9-1-DEFER-3 — M3 endpoint dispatch (AD-19 service-only routing)
- Source: `apps/api/core/capability.py::require_capability`
- Reason: 9-1 = validation only — service-only tenants still 403 on
  COST_CALCULATION. AD-19 extension target = 9-3 wire.
- Scope: bmad-dev-story 9-3 T1~T8 execution sprint.

#### D-9-1-DEFER-4 — Cost Object Breakdown
- Source: `packages/cost_engine/abc_engine.py` (no cost_object output)
- Reason: 9-1 = layer-sum guard only. Cost Object Breakdown = per-product
  KRW allocation summary, arrives in 9-2 wire.
- Scope: bmad-dev-story 9-2 T1~T8 execution sprint.

#### D-9-1-DEFER-5 — Multi-industry ABC (§14.B Non-Goal #1)
- Source: PRD §14.B Non-Goal #1
- Reason: Mixed-industry tenants (manufacturing_service /
  manufacturing_service_other) currently use COST_CALCULATION; multi-ABC
  routing for them is 2차 non-goal (explicit PRD exclusion).
- Scope: (none — explicit PRD non-goal).

#### D-9-1-DEFER-6 — Playwright E2E (16 cases)
- Source: `apps/web/components/m9-abc/AbcValidationPanel.tsx`
- Reason: sprint-scale atomic wire (cj-style 11-3 D-2 ALLOWED_SERVICE_SUBMODULES
  즉시 sweep pattern). 1차 MVP launch 후 follow-up sprint.
- Scope: 9-1 follow-up sprint (cj-style sprint pattern 12-1/12-4/12-5 T6
  + 12-3 T7 mirror).

### Story 9.2 (ABC Allocation Engine — Single CCR, 1-Won Precision) — 5 honestly DEFER

#### D-9-2-DEFER-1 — `fiscal_period_snapshots.engine_type='abc'` COMMIT
- Source: `packages/cost_engine/abc_engine.py` (compute only — no persistence)
- Reason: 9-2 = in-memory compute only (AD-18 + AD-19). M3 dispatch →
  fiscal_period_snapshots write = 9-3 wire (A29 forward-lock 결정 후).
- Scope: bmad-dev-story 9-3 T1~T8 execution sprint.

#### D-9-2-DEFER-2 — Public endpoint exposure for ABC allocation
- Source: `apps/api/modules/m9_abc/__init__.py` (no router)
- Reason: 9-2 = service-layer orchestrator ONLY. Public endpoint wire
  requires AD-19 dual-route dispatch (service-only tenants →
  m9_abc router). Arrives in 9-3 wire.
- Scope: bmad-dev-story 9-3 T1~T8 execution sprint.

#### D-9-2-DEFER-3 — Cost Object Breakdown backend persistence (4컬럼)
- Source: `packages/cost_engine/abc_engine.py` (in-memory CostObjectRow only)
- Reason: 9-2 = frontend TanStack Table only. Backend cost_object_breakdown
  schema + INSERT = 9-3 wire (fiscal_period_snapshots JSONB subdocument).
- Scope: bmad-dev-story 9-3 T1~T8 execution sprint.

#### D-9-2-DEFER-4 — Unused capacity full breakdown by department
- Source: `apps/web/components/m9-abc/UnusedCapacityRow.tsx` (gray badge + accordion)
- Reason: MVP scope = single-row 별도 행 gray badge. Full breakdown by
  department (PRD §A9 long-form) = 9-4 wire (Report #21 PDF generator reuse).
- Scope: bmad-dev-story 9-4 T1~T8 execution sprint.

#### D-9-2-DEFER-5 — Audit trail write for CCR compute
- Source: `apps/api/modules/m9_abc/services/abc_allocation_service.py` (no audit)
- Reason: 9-2 = compute only (AD-22 ledger append-only invariant preserved).
  Audit trail entry = 9-3 wire (after AD-22 capability wire).
- Scope: bmad-dev-story 9-3 T1~T8 execution sprint.

#### D-9-2-DEFER-6 — ruff N806 pre-existing in `test_api_calls_only_ports.py`
- Source: `tests/architecture/test_api_calls_only_ports.py` lines 64 / 134 / 283
  (3 uppercase module-level frozenset constants: `CORE_IMPORT_ALLOWLIST`,
  `ALLOWED_SERVICE_SUBMODULES`, `RUNTIME_CORE_IMPORT_ALLOWLIST`).
- Reason: Pre-existing baseline (Walking Skeleton MVP `1e034c4` = 9-2
  `baseline_commit`). 9-2 wire did NOT introduce these N806 warnings — they
  have been present since `fc7759f` (Story 6.3 ALLOWED_SERVICE_SUBMODULES
  original) and propagated through every story that touched the file
  (12-1, 12-3, 8-1, 8-2, 8-3, Walking Skeleton MVP). Module-level
  frozenset convention is intentional (mirrors 8-3 `LINT_ALLOWLIST_CONSTANTS`
  decision). Renaming to lowercase would conflict with the architectural
  test ALLOWED list semantic and require coordinated rename across all
  call sites + ruff `# noqa` policy update. 9-2 3중 게이트 scope = 9-2
  files only, NOT pre-existing baseline cleanup.
- Scope: Walking Skeleton MVP follow-up sprint (A22 candidate — pre-existing
  infra debt cleanup of 6 ruff + 9 test isolation + 69 format files).
  Could also be addressed in 9-3 sprint if ALLOWED_SERVICE_SUBMODULES sweep
  requires touching this file again.

#### D-9-3-DEFER-1 — Report #21 PDF export for ABC dispatch
- Source: `apps/web/components/m9-abc/AbcDispatchPanel.tsx` (no PDF button).
- Reason: 9-3 wire focuses on the discriminated union envelope + V7 verdict
  + dual-route gate. PDF export of the dispatch result (Report #21)
  requires separate backend wiring (`POST /api/v1/reports/abc-allocation/pdf`)
  with `ABC_CALCULATION` capability + report orchestrator integration.
  Mirrors 8-3 `D-8-3-DEFER-1` pattern.
- Scope: bmad-dev-story 9-4 T1~T8 execution sprint.

#### D-9-3-DEFER-2 — Activity standard hour 자동 추출 Epic 9 close-out follow-up
- Source: `packages/cost_engine/abc_engine.py` `compute_multi_dept_ccr`
  (manual `practical_capacity_hours` input).
- Reason: 9-3 wire reuses the 9-1+9-2 activity manual hour input contract.
  Auto-extraction from `monthly_input_periods` ledger events + activity
  registry is deferred to Epic 9 close-out follow-up (mirrors 9-1
  D-9-1-DEFER-2 which was resolved at 9-3 wire for per-dept CCR, but the
  activity hour 자동 추출 is a separate concern).
- Scope: Epic 9 close-out retro follow-up sprint.

#### D-9-3-DEFER-3 — Unused capacity full breakdown (PRD §A9 verbatim)
- Source: `packages/cost_engine/abc_engine.py` `UnusedCapacitySubRow` (per-dept only).
- Reason: 9-3 wire covers per-department unused capacity breakdown.
  Full breakdown (per activity × per driver × per product) for the
  미사용능력 row is deferred — requires additional 4-column × 3-row
  breakdown serialization + backend report template updates. Mirrors
  D-9-2-DEFER-4 pattern.
- Scope: bmad-dev-story 9-4 T1~T8 execution sprint.

#### D-9-3-DEFER-4 — Playwright E2E for ABC dispatch dual-route UI
- Source: `apps/web/app/[locale]/(dashboard)/budget/abc-calculation/page.tsx`
  (no Playwright E2E coverage yet).
- Reason: 9-3 wire covers the discriminated union envelope + V7 verdict +
  dual-route gate UI but does NOT include Playwright E2E scenarios.
  Mirrors D-9-1-DEFER-6 pattern. E2E coverage requires:
  - 1 scenario: service industry → ABC path (engine_type='abc' badge + V7 verdict + breakdown table)
  - 1 scenario: manufacturing industry → trad path (engine_type='trad' badge + material/labor/overhead)
  - 1 scenario: 422 ABC_EMPTY_DEPARTMENTS error toast
  - 1 scenario: 422 ABC_TOO_MANY_DEPARTMENTS error toast
  Total: 4 scenarios minimum (or 16 for full Epic 9 close-out pattern).
- Scope: Epic 9 close-out retro follow-up sprint.

#### D-9-4-DEFER-1 — epics.md "원가대상별 원가 집계표" vs PRD §9 #21 "부문귀속명세서" 정합

- **Description**: The PRD §9 #21 report is named "원가대상별 원가 집계표"
  (Cost Object Breakdown) but is also referenced as "부문귀속명세서" in
  epics.md. The PDF label + UX 표기 decision requires Product Owner sign-off.
- **Source**: `docs/abc-report-21.md` (PDF title label) +
  `apps/web/messages/ko-KR.json` (`report21.page_title` = "원가대상별 원가 집계표") +
  `packages/services/m5_reports/pdf_generator.py` (`REPORT21_PDF_TITLE_KO`).
- **Reason**: 9-4 본 진입점 scope-out. PRD §9 #21 wording is consistent
  with "원가대상별 원가 집계표" but epics.md alternate name "부문귀속명세서"
  may require UX cross-reference. Decision deferred to Epic 9 close-out
  follow-up to align UX + PDF label + PRD wording.
- **Scope**: Epic 9 close-out follow-up sprint.

#### D-9-4-DEFER-2 — Report #15 wire (활동원가 내역서) — A30 SHARED factory 재사용 entry

- **Description**: Report #15 (활동원가 내역서, Activity Cost Detail) is
  documented in PRD §9 but is NOT yet wired. A30 forward-lock 결정 wire
  reserves `_compose_report15_pdf` placeholder in
  `packages/services/m5_reports/pdf_generator.py` Discriminated union
  factory pattern (`report_id: Literal[15, 16, 17, 18, 19, 20, 21]`).
- **Source**: `packages/services/m5_reports/pdf_generator.py`
  (`_compose_report15_pdf` placeholder branch).
- **Reason**: 9-4 본 진입점 scope-out. Report #15 wire requires A31+
  forward-lock 결정 일정 to wire the corresponding ABC backend surface
  + capability matrix extension. A30 SHARED factory enables Report #15
  to REUSE the generator without duplicating PDF byte composition.
- **Scope**: 후속 story (A31+ 결정 후).

#### D-9-4-DEFER-3 — AI 자동 분석의견 (PRD §9 #16 + §A11 + §10)

- **Description**: AI-driven auto-analysis 의견 (narrative commentary)
  for Report #21 (and other ABC reports) — PRD §9 #16 + §A11 + §10
  mandate AI-generated insight text on cost object breakdowns.
- **Source**: `docs/abc-report-21.md` (AI commentary section placeholder)
  + PRD §A11 AI cross-cutting feature.
- **Reason**: 9-4 본 진입점 scope-out. AI 자동 분석의견 requires:
  - LLM provider wiring (PRD §A11 §10)
  - Report #21 prompt template + cost-engine context injection
  - TS mirror + ko-KR.json SSOT (CR 11-4 D-002)
  - 1 NEW capability matrix row OR AI_EXTRACT reuse decision
- **Scope**: 9-4 follow-up story.

#### D-9-4-DEFER-4 — Playwright E2E for Report #21 (Cost Object Breakdown)

- **Description**: End-to-end Playwright coverage for Report #21 flow:
  period_key input → fetch breakdown → render 4-column table + unused
  accordion → PDF download trigger → file save.
- **Source**: `apps/web/app/[locale]/(dashboard)/reports/21/page.tsx`
  (no Playwright E2E coverage yet).
- **Reason**: 9-4 wire covers the Report21 panel + 4 sub-components +
  PDF button but does NOT include Playwright E2E scenarios. Mirrors
  D-9-1-DEFER-6 + D-9-3-DEFER-4 pattern. E2E coverage requires:
  - 1 scenario: GET /api/v1/reports/21 → breakdown table + V7 verdict
  - 1 scenario: unused capacity accordion toggle per department
  - 1 scenario: POST /api/v1/reports/21/pdf → base64 → Blob → download
  - 1 scenario: 422 REPORT21_NO_COST_OBJECT_BREAKDOWN envelope
  - 1 scenario: 422 REPORT21_PERIOD_NOT_COMMITTED envelope
  - 1 scenario: 404 REPORT21_BREAKDOWN_NOT_FOUND envelope
  Total: 6 scenarios minimum (or 16 for full Epic 9 close-out pattern).
- **Scope**: Epic 9 close-out follow-up sprint (cj-style 결정 A27).

## Deferred from: 10-1 (AI Document Extraction to Input Drafts)

Story 10.1 partial wire completed 2026-08-17 (atomic commit `43d32ac`).
6 items honestly-DEFERred per A34 4-category framework
((a) docs 정합 / (b) retro input / (c) separate epic / (d) dedicated sprint).
T1 (backend pure kernel) + T4 (capability matrix drift detector) DONE —
40 tests pass (26 kernel + 14 drift detector).

### D-10-1-DEFER-1 — T2 service layer + 4 envelope handlers (a: docs 정합)

- **Source**: `apps/api/modules/m10_ai/{service,schemas,handlers,exceptions}.py` + `apps/api/main.py` + 2 NEW test files (`test_extraction_service.py` ~20 cases + `test_extraction_endpoint.py` ~12 cases).
- **Reason**: T1 backend pure kernel (`packages/services/m10_ai/`) DONE — service layer는 T1 kernel을 import하여 wire 진입 필요. service module 진입 시점에 audit-first INSERT (CR 1.1 verbatim) + AD-7 RBAC gate + PIPA consent check + discriminated union envelope wire 필수.
- **Scope**: 5 MODIFIED + 2 NEW files = 7 files. POST /api/v1/ai/extract-monthly endpoint + 3 NEW typed exceptions (AiPipaConsentMissingError + InvalidMonthlyFieldValueError + MonthlyExtractionError) + 3 NEW envelope handlers (403 AI_PIPA_CONSENT_MISSING + 422 INVALID_MONTHLY_FIELD_VALUE + 500 MONTHLY_EXTRACTION_ERROR).
- **Pickup plan**: 10-1 follow-up sprint (cj-style 27번째 epic 연속 = 본 handoff 진입 후) → 10-1 done 진입.

### D-10-1-DEFER-2 — T3 alembic migration + tests (a: docs 정합)

- **Source**: `alembic/versions/0029_input_drafts_monthly_extension.py` NEW + `tests/api/test_alembic_0029_input_drafts_monthly.py` NEW ~10 cases.
- **Reason**: `input_drafts` table EXTENSION 필요 (Story 1.3 baseline = `onboarding_inputs` 5 fields, Story 10.1 = `monthly_inputs` 6 fields). 5 NEW column (`target_table` VARCHAR(32) NOT NULL DEFAULT 'onboarding_inputs' + `extraction_confidence` NUMERIC(4,3) + `extracted_at` TIMESTAMPTZ NOT NULL DEFAULT NOW() + `period_key` VARCHAR(32) + `idx_input_drafts_target_table_period`) + 1 NEW check constraint `ck_input_drafts_confidence_range` (0.000~1.000) + AD-2 INSERT-only trigger EXTENSION.
- **Scope**: 1 NEW migration + 1 NEW test = 2 files. Migration up/down × 3 cases + column existence × 3 + check constraint boundary × 2 + index existence × 2.
- **Pickup plan**: 10-1 follow-up sprint (T2 service layer wire 진입 후 의존성 — alembic 먼저 wire 후 service layer wire 권장).

### D-10-1-DEFER-3 — T5 frontend 5 components + TS mirror + 3 vitest files (d: dedicated sprint)

- **Source**: `apps/web/components/ai-extract/{AiDraftCard,ConfidenceBadge,AiExtractModal}.tsx` NEW (~350 LOC) + `apps/web/messages/ko-KR.json` EXTENSION (ai_extract namespace ~25 strings) + `apps/web/components/ai-extract/__tests__/{AiDraftCard,ConfidenceBadge}.test.tsx` NEW + `apps/web/lib/ai-extract.ts` NEW (TS mirror parity) + `apps/web/__tests__/lib/ai-extract-parity.test.ts` NEW.
- **Reason**: A35 frontend test debt honestly DEFER (9-7 wire DONE 후 frontend 5 components 8 vitest cases 진입 완료). 본 Story 10.1 frontend 진입 시점 = 9-7 wire 패턴 미러 + 8 NEW files (3 components + 2 vitest + 1 ko-KR + 1 TS mirror + 1 parity test) + 120 case 부채 해소 (9-7 sprint precedent).
- **Scope**: 8 NEW files = ~600 LOC frontend + ~120 NEW vitest cases.
- **Pickup plan**: 10-1 follow-up sprint 후 별도 dedicated sprint (T2/T3 wire done 진입 후) — frontend work는 backend wire done 진입 후 권장 (D-9-7 follow-up precedent).

### D-10-1-DEFER-4 — T7 master PRD v2.0 본체 edit (a: docs 정합)

- **Source**: `_bmad-output/planning-artifacts/prd.md` §F10.1·§F10.2·§8.1 M10·부록 A 추가 (Epic 10 close-out retro 진입 시점에 본체 edit).
- **Reason**: Epic 10 PRD entry는 workspace canonical `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-08-17/prd.md` 만 wire. master PRD 본체 §F10.1·§F10.2·§8.1 M10·부록 A 추가는 Epic 10 close-out retro 진입 시점에 별도 atomic wire (cj-style standard pattern).
- **Scope**: 1 MODIFIED file (master PRD v2.0 본체). 부록 A A23~A36 + §8.1 M10 4-story AC extension.
- **Pickup plan**: Epic 10 close-out retro 진입 시점 (10-1~10-4 done 진입 후).

### D-10-1-DEFER-5 — T8.1 docs/deferred-work.md EXTENSION — **partial wire DONE**

- **Source**: 본 handoff 진입 (10-1 follow-up sprint = cj-style 27번째 epic 연속 = 본 handoff 진입 후).
- **Reason**: T8.1 본 항목 = 본 follow-up sprint 진입 시점에 wire. 6 honestly DEFER categories preserved 명시 (D-10-1-DEFER-1~6).
- **Scope**: 0 NEW files (EXTENSION only) — 본 항목 완료.
- **Pickup plan**: DONE (cj-style 27번째 epic 연속 진입 시점에 wire).

### D-10-1-DEFER-6 — T8.2 sprint-status.yaml final done (a: docs 정합)

- **Source**: `_bmad-output/implementation-artifacts/sprint-status.yaml` `10-1-ai-document-extraction-input-drafts: review → done` (follow-up sprint 후 진입).
- **Reason**: 10-1 follow-up sprint DONE 후 진입. T2/T3/T5/T7/T8 honestly DEFER 6 categories 해소 후 sprint-status: `review → done` 정합.
- **Scope**: 1 MODIFIED file (sprint-status.yaml).
- **Pickup plan**: 10-1 follow-up sprint DONE 후 진입.
