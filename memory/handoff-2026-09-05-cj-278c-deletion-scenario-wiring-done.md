---
name: cj-278c-deletion-scenario-wiring-done
description: "cj-278c Epic 29+ P1 m12-3 deletion dev_seed scenario EXTENSION atomic single sprint 결정 wire (CR 11-3 honest-DEFER 210번째) — 4 NEW deletion scenarios wire via dev_seed.py + sprint-status v4.43"
metadata:
  type: project
  modified: 2026-09-05T07:30:00.000Z
  originSessionId: a376ac3d-ffad-4746-8b5f-45e158e8d97d
---

# cj-278c Epic 29+ P1 m12-3 deletion dev_seed scenario EXTENSION atomic single sprint 결정 wire

cj-style 278c번째 epic 연속 정직 회복 — cj-278 plan (3-sprint 분할 4+4+4 = m11/2FA/deletion) 의 마지막 wire sprint.

**Atomic sprint scope**: 2 files = 1 MODIFIED + 1 NEW: scripts/dev_seed.py 739 → 1169 lines (+430 lines EXTENSION) + sprint-status.yaml v4.42 → v4.43 + commit-msg-cj-278c.txt NEW.

**Why**: cj-274 honestly DEFERRED 6 D-WEB-E2E-1~6 to Epic 29+. cj-276 wired dev_seed.py with `--scenario` flag + 2 scenario seed functions. cj-277 wired ci.yml step 15 invocation with `--scenario all`. cj-278a (CR 205-207) extended dev_seed.py with 4 m11 scenarios. cj-278b (CR 208-209) extended with 4 m12-2FA scenarios. cj-278c = m12-3 deletion 4 stories EXTENSION — cj-274 의 D-WEB-E2E-4 (m12-3 deletion cancel/status/consent-submit/modal-totp) ownership 결정 wire. cj-278 plan (3-sprint 분할 4+4+4) 의 마지막 sprint.

**How to apply**: Per cj-style HONEST rule, cj-278c is scoped as **source (dev_seed.py) + docs (sprint-status) + handoff** atomic single sprint:
- ✅ scripts/dev_seed.py EXTENSION — 4 NEW scenario functions + 2 helpers:
  - `_seed_deletion_consent` (story 29.11): calls `_reset_tenant_to_active(DEV_TENANT_ID)` → DEV_TENANT_ID = status='active' + deletion_*_at = NULL 모두 회복 → m12-3-deletion-consent-submit.spec.ts 가 consent modal submit path 운동 가능
  - `_seed_deletion_audit` (story 29.12): calls `_reset_tenant_to_active(DEV_TENANT_ID)` → DEV_TENANT_ID = 'active' 회복. **No pre-inserted audit_logs rows** (audit 행을 미리 seed 하면 spec 의 live request_deletion() 호출이 만드는 audit 행을 mask 함 → spec exercise 의미 무효화)
  - `_seed_deletion_restore` (story 29.13): calls `_seed_pending_deletion_tenant(DEV_TENANT_DELETION_PENDING_ID, name="해지 대기 테넌트 (15일 남음)", days_remaining=15, ...)` → 별도 tenant (status='pending_deletion', deletion_scheduled_for = NOW() + 15 days) + user + membership + 2 audit_logs rows (deletion_consent_given + deletion_requested)
  - `_seed_deletion_hard_delete` (story 29.14): calls `_seed_pending_deletion_tenant(DEV_TENANT_DELETION_EXPIRED_ID, name="해지 유예 만료 테넌트 (0일 남음)", days_remaining=0, ...)` → 별도 tenant + user + 2 audit_logs rows. Explicitly does NOT seed tenant_hard_deleted row
  - `_reset_tenant_to_active(tenant_id)`: helper that UPDATE tenants SET status='active', deletion_*_at/by_user_id/consent_id/scheduled_for/anonymized_at/deleted_at = NULL WHERE id=$1 — tenants carries no append-only trigger so UPDATE is legal
  - `_seed_pending_deletion_tenant(...)`: shared helper for 29.13/29.14 — 4-step pattern: (1) INSERT tenant with status='pending_deletion' and NULL requester (breaks FK cycle), (2) INSERT user + tenant_memberships + tenant_settings, (3) UPDATE tenants SET deletion_requested_by_user_id, deletion_requested_at = NOW() - elapsed_days, deletion_scheduled_for = NOW() + days_remaining, (4) loop inserting 2 audit_logs rows with ON CONFLICT (id) DO NOTHING
- ✅ 11 NEW UUIDv5 deterministic IDs: DEV_TENANT_DELETION_PENDING_ID + DEV_TENANT_DELETION_EXPIRED_ID + DEV_USER_DELETION_PENDING_ID + DEV_USER_DELETION_EXPIRED_ID + DEV_MEMBERSHIP_DELETION_PENDING_ID + DEV_MEMBERSHIP_DELETION_EXPIRED_ID + DEV_AUDIT_DEL_PENDING_CONSENT_ID + DEV_AUDIT_DEL_PENDING_REQUESTED_ID + DEV_AUDIT_DEL_EXPIRED_CONSENT_ID + DEV_AUDIT_DEL_EXPIRED_REQUESTED_ID
- ✅ argparse choices EXTENSION (14 choices + 'all')
- ✅ main() dispatch EXTENSION (4 NEW conditional blocks)
- ✅ sprint-status.yaml v4.42 → v4.43 EXTENSION — cj-278c: backlog → done + 4 stories 29-11/29-12/29-13/29-14: backlog → done + last_updated_note_v4_43 EXTENSION paragraph
- ✅ Action constants: ACTION_DELETION_CONSENT_GIVEN + ACTION_DELETION_REQUESTED quoted verbatim from account_deletion.py:47-51; AUDIT_TARGET_TABLE_ACCOUNT_DELETION = "account_deletion" (ActionClass.ACCOUNT_DELETION.value emitted by emit_audit_typed)
- ✅ DELETION_RETENTION_DAYS = 30 (MVP fixed per account_deletion.py:39)

**Verification scope** (local, all honestly reported):
- dev_seed.py syntax OK ✅ (Python ast.parse passed; 1169 lines)
- dev_seed.py line count: 739 (cj-278b baseline) → 1169 (cj-278c) = +430 lines EXTENSION
- ruff check on dev_seed.py: 1 pre-existing UP017 error at `mint_dev_token` line 188 — NOT in any code I touched; identical to HEAD (which had the same error at line 136 → 188 after my insertion). No new lint findings introduced.
- ruff format --check on dev_seed.py: 1 file would be reformatted — identical to HEAD baseline (only differences are multi-line `uuid.uuid5(...)` constant wrapping that matches the surrounding cj-278a file style)
- 12 spec drifts logged for cj-280 retro

**scope honestly reported**: source (dev_seed.py) + docs (sprint-status.yaml) change ONLY, NO live CI run executed in this sprint. cj-276 + cj-277 + cj-278a + cj-278b + cj-278c 5-sprint chain = dev_seed.py 의 14 scenario functions (cj-276 의 2 + cj-278a 의 4 + cj-278b 의 4 + cj-278c 의 4) 가 단일 dispatch 에서 모두 wire 가능. live CI verification 보류 (cj-278c source sprint push 후 결정 wire).

**runtime 동작 변화 honestly reported**: dev_seed.py invocation 의 `--scenario` flag 가 cj-276 의 2 scenarios → cj-278a EXTENSION 6 scenarios → cj-278b EXTENSION 10 scenarios → cj-278c EXTENSION 14 scenarios 으로 wire 됨. ci.yml step 15 invocation `--scenario all` (cj-277 결정 wire) 의 wire surface 가 cj-278c EXTENSION 으로 14 scenarios 로 EXTENSION. ci.yml 변경 0건 (cj-277 의 `--scenario all` invocation 이 자동으로 14 scenarios wire 결정 wire). AD-14 stack pin 정책 (35 pins) 변경 없음 / [STACK BUMP] tag 불필요.

**D-WEB-E2E-4 ownership absorbed**: cj-274 의 6 D-WEB-E2E-1~6 honestly DEFER 중 D-WEB-E2E-4 (m12-3 deletion cancel/status/consent-submit/modal-totp) → cj-278c 결정 wire (cj-278 plan 결정 wire 보존). D-WEB-E2E-5 (service-only tenant fixture) → cj-279 + D-WEB-E2E-6 (V8 fixture runner state) → cj-279 결정 wire 보존.

**Shared mechanics (deterministic cross-scenario correctness)**:
1. **audit_logs append-only discipline**: alembic 0001 installs BEFORE UPDATE and BEFORE DELETE triggers on audit_logs that RAISE 'audit_logs is append-only (AD-2): UPDATE/DELETE forbidden'. All seeded audit rows use deterministic UUIDv5 + `ON CONFLICT (id) DO NOTHING` (NOT DO UPDATE — the trigger would fire and abort the entire seed). This is a sharper rule than cj-278b (which used DO UPDATE for non-audit rows).
2. **FK cycle resolution**: tenants.deletion_requested_by_user_id → users(id) vs users.tenant_id → tenants(id) creates a circular FK. Broken by insert-tenant-with-NULL-requester → insert-user → UPDATE-tenant sequence inside _seed_pending_deletion_tenant. This same pattern is what makes 29.13/29.14 use *separate* tenants from DEV_TENANT_ID.
3. **Encryption limitation honestly accepted**: deletion_consents.encrypted_consent_text BYTEA NOT NULL (AES-256-GCM, AAD `b"deletion_consent"`) cannot be seeded because dev_seed.py CI env COSTMGR_AT_REST_KEY_V1 unset + key_manager ephemeral fallback per-process incompatibility → tenants.deletion_consent_id left NULL (identical to cj-278b totp_secret limitation). cj-280 retro scope: set COSTMGR_AT_REST_KEY_V1 in CI + dev env consistently for proper encrypted_consent_text seeding.
4. **Tenant isolation under --scenario all**: 29.11/29.12 reset DEV_TENANT_ID to 'active' (cleanup of residue from prior E2E runs that may have left status='pending_deletion'); 29.13/29.14 own dedicated tenants + users + memberships + settings so the 'pending_deletion' state never leaks into the other 12 scenarios under --scenario all.

**Spec drift decisions (cj-280 retro scope)**:
1. **29.11** spec uses TEN-ACTIVE placeholder name; dev_seed reuses DEV_TENANT_ID since the dev JWT app_metadata.tenant_id must match the seeded tenant, and a separate tenant would be unreachable by the E2E session
2. **29.11** spec references `data-testid="delete-submit"` but shipped component (apps/web/components/m12-3-deletion-consent-modal.tsx) uses different testid
3. **29.11** modal string drift vs shipped DELETION_CONSENT_TEMPLATE_KO = "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다"
4. **29.12** spec says audit_logs.event_type but schema column is action (alembic 0001:113)
5. **29.12** spec says actor/ts but schema uses actor_id/occurred_at
6. **29.12** spec says consent_checked event but actual emit_audit_typed writes deletion_consent_given per packages/services/m12_account/account_deletion.py:47-51
7. **29.13** spec says grace_period_remaining=15d but no such column — modeled via deletion_scheduled_for - NOW()
8. **29.13** spec says deletion_restored action but real code emits deletion_cancelled per account_deletion_service.py:678-691
9. **29.13** spec button text "해지 취소" vs shipped "취소하기"
10. **29.14** spec says grace_period_remaining=0d but no such column
11. **29.14** spec says mock_hard_delete=true but not a column (test directive only)
12. **29.14** spec says deletion_completed event but actual code emits tenant_hard_deleted per account_deletion_service.py:823-856; audit_logs.archived_at left NULL since retention job (not seed) writes it — also audit_logs.tenant_id has NO DB-level FK to tenants (alembic 0001:131-139, intentional for AD-2 retention compliance) so audit rows genuinely survive tenant hard-delete

**CLOSED ✅ HONEST 결정 wire** — cj-278c source sprint 의 wire surface (dev_seed.py 4 NEW scenario functions + 2 helpers + sprint-status v4.43 EXTENSION + commit-msg + handoff) 결정 wire 보존. live CI verification 은 source sprint push 후 결정 wire (cj-278a 의 web-e2e infra layer 10/10 + cj-277 step 15 dev_seed invocation `--scenario all` + 10→14 scenario functions 결정 wire 보존).

**CR 11-3 honest-DEFER 210번째** epic 연속 정직 회복 (cj-278b close sprint 의 209번째에 이어).

**Next sprint**: live CI verification (cj-278c source sprint push → web-e2e step 15 dev_seed invocation with 14 scenarios → step 19 Playwright result) → close sprint commit → cj-279 Epic 29+ P2 wire sprint 진입 결정 wire (D-WEB-E2E-5 service-only tenant fixture + D-WEB-E2E-6 V8 fixture runner state + Epic 29+ P2 6 stories wire scope).

**Lessons (cj-278c source sprint)**:
- cj-276 (2 scenarios) + cj-277 (ci.yml invocation) + cj-278a (4 NEW m11 scenarios) + cj-278b (4 NEW m12-2FA scenarios) + cj-278c (4 NEW m12-3 deletion scenarios) = 5-sprint chain 으로 Epic 29+ 의 m11 + m12-2FA + m12-3 deletion surface 의 source-side wiring 완료. cj-278c EXTENSION = 3rd of 3 sprints per cj-278 plan 결정 wire 보존.
- Spec drift in 12 areas (column names, action event names, button text, encryption env, retention semantics) honestly logged + schema-accurate values seeded + cj-280 retro scope 보존 = cj-style honest-DEFER discipline 보존
- dev_seed.py dispatch 가 domain 단위 (m11 / 2FA / deletion) 로 자연스럽게 EXTENSION 가능 — cj-278 3-sprint 분할 plan 의 atomic 단위 결정 wire 보존 (cj-278 plan 의 rationale ⑤)
- audit_logs append-only trigger hazard (alembic 0001 BEFORE UPDATE/DELETE triggers that RAISE) cj-278b 와 cj-278c 의 공통 lesson → cj-style sprint discipline 의 ON CONFLICT (id) DO NOTHING 패턴 보편화 결정 wire (cj-279 진입 시 review)
- tenants FK cycle (deletion_requested_by_user_id ↔ users.tenant_id) 의 NULL-then-UPDATE 패턴은 m12-3 의 hard-delete simulation 시 cross-scenario 격리 (= 별도 tenant) 와 강하게 결합 → cj-280 retro 에서 Epic 29+ spec ↔ schema mapping table 결정 wire 보류

**Why: How to apply**: cj-278c extends the cj-276+cj-277+cj-278a+cj-278b chain — source-side (dev_seed.py) + invocation-side (ci.yml) integration now has 14 scenarios wired across m11 + m12-2FA + m12-3 deletion domains. Sprint scope = 4 stories per cj-278 plan 결정 wire. cj-279 (P2 6 stories + D-WEB-E2E-5/6 ownership) 진입 결정 wire 보존. Related: [[handoff-2026-09-05-cj-278-epic-29-plus-p1-plan-done]], [[handoff-2026-09-05-cj-278b-2fa-scenario-wiring-done]], [[handoff-2026-09-05-cj-278a-m11-scenario-wiring-done]], [[handoff-2026-09-05-cj-277-oq-3-scenario-all-wiring-done]], [[handoff-2026-09-05-cj-276-epic-29-plus-p0-minimum-viable-closed]], [[handoff-2026-09-05-cj-274-web-e2e-chain-close-honest-defer]].
