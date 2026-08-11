# Account Security Operations — M12 (2FA) — Story 12.1 + 12.4

PRD §F12.1 + §M12-a — Operational runbook for the 2FA / M2 entry-gate
subsystem. Audience: on-call engineers, SRE, and support staff.

**Scope**: 8 routes + 1 M2 entry-gate route under `/api/v1/account/2fa/*`
and `/api/v1/m2-entry-gate`, backed by `packages/services/m12_account/`
pure kernel + `apps/api/modules/m12_account/` service + HTTP layer.

---

## §1. 2FA policy summary

| Item | Value |
|---|---|
| Standard | RFC 6238 TOTP (HMAC-SHA1, 30s step, 6 digits, ±1 window) |
| Algorithm | base32 encoded shared secret per enrollment |
| Enrollment | `POST /api/v1/account/2fa/setup` → returns base32 secret + `otpauth://` URI + 8 recovery codes |
| Activation | First successful TOTP code via `POST /api/v1/account/2fa/verify` flips `users.totp_enabled_at` |
| Industry-agnostic | 2FA is security baseline (CR 12-1 L4) — applies to all 4 canonical industries regardless of manufacturing footprint |
| Capability gate | **None** (intentional). Authorization is AD-10 role gate only. |
| Recovery codes | 8 codes × 10 chars (Crockford base32), single-use, PBKDF2-HMAC-SHA256 (200k iters) |
| Lockout | 5 consecutive failed TOTP/recovery attempts → 15-min lockout (LOCKOUT_DURATION_SECONDS=900) |
| 2FA disable | Owner-only mutation: current_code (6 digits) OR admin override (reason ≥ 20 chars + owner role) |

---

## §2. Recovery codes

### §2.1 Generation

- 8 codes generated server-side at enrollment time
- 10-character Crockford base32 alphabet (excludes I, L, O, U to avoid visual confusion)
- PBKDF2-HMAC-SHA256 hashed with per-code salt; only hash + salt stored in `users.totp_recovery_codes_hash JSONB`
- Plaintext codes returned to user ONCE during `POST /api/v1/account/2fa/setup` response — never re-shown, never logged

### §2.2 Consumption

- `POST /api/v1/account/2fa/recovery` accepts `{code: "<10-char-base32>"}`
- Service iterates `recovery_codes_hash[]`, attempts `pbkdf2.verify(code, hash)`
- First match → mark code as consumed (re-hash in DB) + reset `totp_failed_attempts = 0`
- No match → increment `totp_failed_attempts`; on 5th failure trigger lockout
- Exhausted list (`recovery_codes_remaining == 0`) → `TwoFactorRecoveryExhaustedError` → 410 Gone
  - Resolution: user must contact owner/admin to disable + re-enroll 2FA

### §2.3 Re-enrollment

- Owner calls `POST /api/v1/account/2fa/disable` (code OR admin override)
- User re-enrolls via `POST /api/v1/account/2fa/setup` → fresh 8 codes generated

---

## §3. Lockout

### §3.1 State machine

```
TOTP_OK → totp_failed_attempts = 0, lockout_until = NULL
TOTP_FAIL → totp_failed_attempts += 1
on (totp_failed_attempts >= 5) → totp_lockout_until = now() + 900 (15 min)
on (now() < totp_lockout_until) → 429 with Retry-After header
```

### §3.2 Recovery during lockout

- **No backdoor**. User MUST wait until `totp_lockout_until` expires.
- Admin override (`POST /api/v1/account/2fa/disable` with admin reason + owner role) does NOT bypass lockout — it disables 2FA entirely, which requires owner role.
- On-call staff MUST NOT manually edit `users.totp_lockout_until` in prod DB — defeats the purpose of the lockout. Escalate to security team if abuse suspected.

### §3.3 Monitoring alerts

- PagerDuty alert on `totp_lockout_total` Prometheus counter > 50/hour across all tenants → possible credential stuffing
- Grafana panel: per-tenant `totp_lockout_count_24h` — investigate tenants with > 10 lockouts/day

---

## §4. NFR6 — AES-256-GCM column-level encryption

### §4.1 What is encrypted

- `users.totp_secret BYTEA` — base32 TOTP secret, plaintext NEVER appears in:
  - logs (any log line that includes the secret triggers AD-15 §11 SSOT grep gate)
  - responses (`POST /setup` returns secret ONCE then service encrypts + persists; subsequent `GET /status` omits it)
  - audit payloads (audit_logs stores user_id + action_class + trace_id, NOT secret)

### §4.2 Crypto envelope

- Algorithm: AES-256-GCM (96-bit nonce, 128-bit auth tag)
- AAD: `b"totp_secret"` (binds ciphertext to column — a blob lifted from another column cannot be decrypted here)
- Key ID: `"v1"` — current key generation
- Key material: KMS-managed (Supabase Vault); service uses key-id → DEK resolution via `apps/api/core/crypto.py::resolve_key`

### §4.3 Failure modes

| Exception | HTTP | Resolution |
|---|---|---|
| `TwoFactorEncryptionError` | 400 | Most likely service-side bug. Check KMS reachability + AAD binding. |
| `TwoFactorCryptoKeyMissingError` | 500 | Critical: KMS cannot resolve `v1` key. Page on-call. Halt enrollments until resolved. |

### §4.4 Key rotation

- Out of scope for Story 12.4. When key rotation ships (Epic 14+):
  - Add `key_id` column to `users.totp_secret` payload (envelope prefix)
  - Dual-read window: read with `key_id="v1"`, on miss try `"v2"`
  - Backfill migration re-encrypts all rows under `"v2"`
  - Drop `"v1"` reader after 90-day soak

---

## §5. Audit trail

### §5.1 ActionClass values (6 typed)

From `apps/api/core/audit_action.py:584-602`:

| ActionClass | Triggered by |
|---|---|
| `two_factor_setup_initiated` | `POST /setup` (initial) |
| `two_factor_setup_completed` | `POST /verify` success |
| `two_factor_challenge_passed` | `POST /challenge` success |
| `two_factor_challenge_failed` | `POST /challenge` failure (any reason) |
| `two_factor_recovery_consumed` | `POST /recovery` success |
| `two_factor_disabled` | `POST /disable` (self or owner reset) |
| `two_factor_lockout_triggered` | 5th consecutive failure |

### §5.2 audit_logs intentionally CHECK-less

`users.audit_logs.action` is plain `TEXT NOT NULL` — no CHECK constraint.
This is a deliberate **invariant**, pinned by
`tests/integration/test_audit_logs_no_action_check_constraint.py`:

- `0001_tenants_users_memberships_settings.py` defines `audit_logs.action TEXT NOT NULL`
- No `0023_*` migration adds a CHECK constraint
- A5 drift detector (`packages/services/_drift_detector/audit_action_drift.py`)
  explicitly excludes `audit_logs` from CHECK gate because the 20-action
  registry is enforced at the service boundary, not the DB boundary

### §5.3 Audit emission order

Per CR 1.1 audit-first: every 2FA mutation (`disable`, `verify`) emits the
audit row in the SAME transaction as the state change. If audit insert
fails, the entire transaction rolls back (no partial state).

`TwoFactorAuditEmitError` → 503 with Retry-After header.

---

## §6. AD-10 4-role gate

### §6.1 Role allowlist

| Role | M2 entry (PRD §M12-a) | 2FA mutation (setup/verify/disable) |
|---|---|---|
| owner | ✅ ALLOWED | ✅ ALLOWED (require_role("owner")) |
| member | ✅ ALLOWED | ❌ DENIED (handler-level role check) |
| viewer | ❌ DENIED | ❌ DENIED |
| consultant_proxy | ❌ DENIED | ❌ DENIED |

Pure kernel enforcement: `packages/services/m12_account/two_factor_gate.py::enforce_role_gate`.

### §6.2 M2 entry gate route

`GET /api/v1/m2-entry-gate` — reads session, returns:
```json
{
  "allowed": true,
  "requires_two_factor": true,
  "requires_challenge": false,
  "role_allowed": true,
  "locked_out": false,
  "lockout_until": null,
  "message_ko": "2FA 인증 필요"
}
```

Frontend `apps/web/lib/m12-two-factor-gate.ts::buildM2EntryGateState`
mirrors the logic for client-side pre-render decisions (avoids flash of
"locked out" state on page load).

### §6.3 Tenant scoping

- M2 entry gate operates within `app.tenant_id` GUC
- Cross-tenant 2FA mutations: not supported (each user enrolls 2FA within their own tenant scope)
- consultant_proxy role DOES grant cross-tenant SELECT on `users.totp_*`
  per RLS policy `users_totp_select_consultant_proxy` — for proxy reports
  only, never for mutations

---

## §7. M2 entry gate flow

```
User navigates to /m2-input/period/[periodKey]
  ↓
Server Component: <TwoFactorGuard role={session.role}
                              totp_enabled={user.totp_enabled}
                              locked_out={user.locked_out}
                              lockout_until={user.lockout_until}>
  ↓
If state.allowed === true:
  Render <MonthlyInputTabs /> (existing M2 input UI)
  ↓
If state.allowed === false:
  Render yellow-bordered panel:
    - "2FA 잠금 — {lockout_until_kst} 이후 재시도" if locked_out
    - "owner/member role만 M2 입력 가능" if !role_allowed
    - "2FA 인증 필요" if !totp_enabled
  ↓
User clicks "인증 진행" → opens TwoFactorChallengeDialog (DEFERRED to 12.5)
  → POST /api/v1/account/2fa/challenge
  → on success: refetch /m2-entry-gate state, render M2 input UI
```

---

## §8. honestly DEFERRED items (Story 12.4)

See `docs/deferred-work.md## Deferred from: 12-4` for the 7 items
honestly DEFERred to a future Story 12.5:

1. TwoFactorSetupForm component (3-step wizard UX)
2. TwoFactorChallengeDialog component (challenge UI + retry timer)
3. TwoFactorDisableForm component (admin override reason field)
4. TwoFactorStatusBadge component (server-side fetch wiring)
5. `/account/security` NEW page (route + nav entry)
6. QR image rendering (`qrcode.react` not installed; HALT-for-new-deps)
7. Playwright E2E specs (16 cases; infra-dependent)

---

## §9. Cross-references

- `docs/conventions.md## §11 TOTP / 2FA` — layering, NFR6, lockout, AD-10, routes, exceptions, Korean SSOT
- `docs/capability-matrix.md## v1.13` — TWO_FACTOR_AUTH capability (industry-agnostic)
- `apps/api/alembic/versions/0022_users_totp_columns.py` — 5 columns + 2 partial indexes + CHECK
- `supabase/policies/0013_users_totp_columns_rls.sql` — 5 RLS policies on users.totp_*
- `tests/integration/test_audit_logs_no_action_check_constraint.py` — invariant regression
- `tests/api/m12_account/test_handlers_route_shape.py` — 12 route shape tests
- `tests/api/m12_account/test_exception_handlers_registered.py` — 14 exception handler tests
- `tests/api/test_alembic_0022_users_totp_columns.py` — 12 migration tests
