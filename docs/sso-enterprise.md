# SSO Enterprise SAML — Integration Guide

> **Epic 15 (cj-style 60번째 epic 연속 정직 회복 wire)** — AD-28 territory.
>
> Master PRD §F17.3 verbatim wire scope.
>
> Last updated: 2026-08-22 (KST).

## 1. Purpose

This document describes how to integrate **enterprise SAML 2.0 SSO** into the
costmgr platform. It is the canonical reference for tenant IdP configuration,
the JIT provisioning flow, the audit-first guarantee, and the multi-tenant
isolation contract (CR 0-2 RLS lesson).

The wire is implemented by:

- `apps/api/modules/auth/sso/saml_validator.py` — SAML response validation.
- `apps/api/modules/auth/sso/saml_routes.py` — 4 SP endpoints.
- `apps/api/modules/auth/sso/jit_provisioning.py` — 5-step atomic flow.
- `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` — DB schema.
- `apps/web/app/api/auth/sso/callback/route.ts` — Frontend ACS callback.

## 2. Architecture

```
┌────────────┐          ┌─────────────────────────┐         ┌──────────────┐
│  Browser   │ ──/login→│ /api/v1/auth/sso/login  │         │   IdP        │
│ (costmgr)  │←─302────│ (AuthnRequest generation)│────────→│ (Okta/AzureAD│
│            │          │                          │         │  GWS/Custom) │
└────────────┘          └──────────────────────────┘         └──────┬───────┘
       ▲                          ▲                                │
       │                          │ SAMLResponse                   │
       │                          └─────────────────────┐          │
       │                                                 │          │
       │  ┌──────────────────────────────────┐           │          │
       │  │ /api/v1/auth/sso/acs             │←──────────┘          │
       │  │ • validate signature             │                      │
       │  │ • validate timestamps            │                      │
       │  │ • validate Audience/Destination  │                      │
       │  │ • validate InResponseTo          │                      │
       │  │ • decode RelayState              │                      │
       │  │ • JIT provisioning (5-step)      │                      │
       │  │ • audit-first INSERT             │                      │
       │  │ • session cookie set             │                      │
       └──│ session ──────── /api/v1/auth/sso/sls                  │
          │                                  │                      │
          │ /api/auth/sso/callback (web)     │                      │
          └──────────────────────────────────┘                      │
                                                                  │
```

**AD-14 stack pin**: `python3-saml==1.16.0`.

**Multi-tenant isolation**: every row in `external_identities` is gated by the
RLS policy `tenant_id = current_setting('app.tenant_id')` (CR 0-2 RLS lesson).

## 3. Prerequisites

| Service | Why | Cost (baseline) |
|---------|-----|-----------------|
| Supabase (auth) | Custom session cookie + RLS | included |
| Railway (api) | SAML callback endpoint | $5/mo |
| IdP (Okta/AzureAD/GWS) | IdP-side signing | enterprise contract |
| Sentry | ACS failures | $0 (free tier) |

## 4. Step-by-Step Integration

### 4.1 Tenant-side onboarding

1. Create a new tenant in costmgr: `INSERT INTO tenants (slug, name, ...)`.
2. Capture IdP metadata XML from the tenant admin.
3. Configure `tenant_idps` (TODO Epic 16) with:
   - `idp_entity_id`
   - `idp_sso_url`
   - `idp_x509_cert` (PEM)
   - `acs_url` (must match the costmgr SP endpoint)
4. The tenant admin shares their tenant slug (e.g., `acme`) with end users.

### 4.2 SP metadata publication

`GET /api/v1/auth/sso/metadata?tenant=<slug>` returns the costmgr SP
metadata XML (EntityDescriptor). The tenant admin uploads this to their IdP.

### 4.3 End-user login

1. User visits `https://app.costmgr.example.com/sso/acme/login`.
2. costmgr generates an `AuthnRequest` with a fresh `request_id` and
   `RelayState` (URL-safe base64 of the post-login destination).
3. Browser is 302-redirected to the IdP SSO URL.
4. IdP authenticates the user and POSTs `SAMLResponse` + `RelayState` to
   `/api/v1/auth/sso/acs?tenant=acme`.
5. costmgr validates the response (see §5).
6. costmgr runs JIT provisioning (see §6).
7. costmgr sets the session cookie and redirects to `/auth-callback`.

### 4.4 Logout (Single Logout Service)

`GET /api/v1/auth/sso/sls?tenant=<slug>` clears the local session and
(optionally) initiates an IdP-side logout via `LogoutRequest`.

## 5. SAML Response Validation

The validator (`saml_validator.py`) enforces the following invariants in order:

| # | Check | Failure class |
|---|-------|---------------|
| 1 | Base64 decode succeeds | `SAMLInvalidResponseError` |
| 2 | XML parses | `SAMLInvalidResponseError` |
| 3 | `ds:Signature` element present | `SAMLSignatureFailedError` |
| 4 | XML signature verifies against IdP cert | `SAMLSignatureFailedError` |
| 5 | `Conditions/@NotBefore` ≤ now | `SAMLExpiredError` |
| 6 | `Conditions/@NotOnOrAfter` ≥ now | `SAMLExpiredError` |
| 7 | `AudienceRestriction/Audience` matches `costmgr-sp` | `SAMLAudienceMismatchError` |
| 8 | `Destination` matches ACS URL | `SAMLDestinationMismatchError` |
| 9 | `InResponseTo` matches the request_id we stored | `SAMLInResponseToMissingError` |
| 10 | RelayState decodes as URL-safe base64 | `SAMLRelayStateDecodeError` |

**Dual-mode validator**: When `python3-saml==1.16.0` is installed, the
production code path is used. When it is not installed (e.g., CI),
the structural validator (pure-Python XML parsing) still enforces checks
#1, #2, #3, #5, #6, #7, #8, #9, #10 — this is what enables the
`tests/api/core/test_epic_15_sso_validator.py` suite to run.

## 6. JIT Provisioning

`jit_provisioning.py` mirrors the Phase 3-0 atomic `tenant_signup_completed`
pattern with a 5-step flow:

1. **Tenant lookup** (`SELECT id FROM tenants WHERE slug = ?`).
   - On miss → `JITTenantNotFoundError` (typed exception, no info leak).
2. **User upsert** (`INSERT ... ON CONFLICT (email) DO UPDATE ...`).
3. **Tenant membership upsert** (`INSERT ... ON CONFLICT (user_id, tenant_id) DO UPDATE ...`).
4. **External identity insert** (`INSERT INTO external_identities ...`).
5. **Audit-first INSERT** (CR 1-1) — `INSERT INTO audit_logs ...` with
   `action = 'sso_identity_linked'`.

If any step fails, the `session.rollback()` is implicit (no commits happen
between steps). The audit-first INSERT runs **last** so that the audit row
only exists for successful provisioning — this is the CR 1-1 invariant.

### 6.1 Audit envelope (CR 12-5 D-14)

```json
{
  "action": "sso_identity_linked",
  "action_class": "auth",
  "tenant_id": "uuid",
  "actor_user_id": "uuid",
  "details": {
    "provider": "saml_okta",
    "provider_user_id": "fp:sha256:...",
    "tenant_slug": "acme",
    "idp_entity_id": "https://idp.example.com"
  },
  "ip": "...",
  "user_agent": "...",
  "created_at": "2026-08-22T..."
}
```

The `provider_user_id` is fingerprinted (SHA-256 with a per-tenant salt) so
that the raw SAML NameID is not stored in the audit log (NFR4 PII minimization).

## 7. RLS Multi-Tenant Isolation (CR 0-2)

The `external_identities` table enforces:

```sql
ALTER TABLE external_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_identities FORCE ROW LEVEL SECURITY;

CREATE POLICY external_identities_tenant_isolation ON external_identities
  FOR ALL TO authenticated
  USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY external_identities_service_role_bypass ON external_identities
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY external_identities_anon_block ON external_identities
  FOR ALL TO anon USING (false);
```

**Tested** by `tests/api/core/test_epic_15_alembic_0037_external_identities.py`.

## 8. AAL Branching — Epic 12 2FA Gate (D-GATE-01 Inversion)

When the SAML assertion contains `authn_context_class_ref = 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport'`,
the resulting session has `aal = 'aal1'`. The 2FA gate then redirects the user
to the existing Epic 12 TOTP challenge before M2 is unlocked.

If the IdP provides `urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract`
or equivalent, the resulting session has `aal = 'aal2'` and M2 unlocks immediately.

This preserves the Epic 12 2FA gate (D-GATE-01 inversion).

## 9. Capability Matrix v1.26 EXTENSION

5 NEW rows added (CR 12-1 L4 precedent — industry-agnostic):

| Capability | manufacturing | service | mfg+service | mfg+service+other |
|------------|:-------------:|:-------:|:-----------:|:-----------------:|
| `MAGIC_LINK` | ✅ | ✅ | ✅ | ✅ |
| `SOCIAL_OAUTH_GOOGLE` | ✅ | ✅ | ✅ | ✅ |
| `SOCIAL_OAUTH_NAVER` | ✅ | ✅ | ✅ | ✅ |
| `SOCIAL_OAUTH_KAKAO` | ✅ | ✅ | ✅ | ✅ |
| `SSO_ENTERPRISE` | ✅ | ✅ | ✅ | ✅ |

Drift detector: `tests/integration/test_capability_matrix_v1_26_drift.py`.

## 10. Cross-References

- Master PRD §F17.3 (SSO enterprise SAML)
- AD-28 (Magic link + Social OAuth + SSO enterprise SAML territory)
- CR 0-2 RLS lesson (multi-tenant isolation)
- CR 1-1 audit-first INSERT invariant
- CR 12-1 L4 precedent (industry-agnostic capability grants)
- CR 12-5 D-14 (typed exception envelope)
- CR 12-5 D-PARITY-01 inversion (Supabase + Next.js + SAML OAuth parity)
- CR 12-5 D-GATE-01 inversion (Epic 12 2FA gate preserved)
- A19 cohesion pattern 9 surface EXTENSION PASS
- D-1-1-DEFER-3 ✅ RESOLVED (cj-style 58~60번째 epic 연속 정직 회복)

## 11. Test Coverage Summary

| File | Cases | Status |
|------|------:|--------|
| `tests/web/test_epic_15_magic_link_parity.py` | 15 | ✅ PASS |
| `tests/web/test_epic_15_social_oauth_parity.py` | 15 | ✅ PASS |
| `tests/api/core/test_epic_15_sso_validator.py` | 15 | ✅ PASS |
| `tests/api/core/test_epic_15_sso_jit_provisioning.py` | 10 | ✅ PASS |
| `tests/api/core/test_epic_15_sso_routes.py` | 15 | ✅ PASS |
| `tests/api/core/test_epic_15_alembic_0037_external_identities.py` | 10 | ✅ PASS |
| `tests/integration/test_capability_matrix_v1_26_drift.py` | 38 | ✅ PASS |
| **Total** | **118 NEW cases** | ✅ 3중 게이트 FINAL CLEAN |