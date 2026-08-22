# Tenant IdP Admin Management

> Epic 16 — Tenant IdP admin management territory. Owner/admin of a tenant
> can register, update, test, and disable their SAML 2.0 IdP through the
> `/api/v1/admin/tenant/{tenant_slug}/idp` endpoints.

## Overview

Tenant IdP admin management is the second half of the SAML enterprise SSO
territory. Epic 15 (`5f9e37f`) wired the SAML response consumption side
(login → IdP redirect → ACS → JIT provisioning) using a **hardcoded
placeholder** for the IdP X509 cert and SSO URL. Epic 16 replaces those
placeholders with a per-tenant row in `public.tenant_idps`, allowing each
tenant to point at their own corporate IdP.

The `tenant_idps` table is the canonical source of truth for:

- **IdP entity ID** (`idp_entity_id`) — SAML `EntityDescriptor/@entityID`
- **SingleSSO Service URL** (`idp_sso_url`) — SAML `<SingleSignOnService>`
- **Single Logout Service URL** (`idp_slo_url`) — optional
- **X509 cert PEM** (`idp_x509_cert`) — `<X509Certificate>` base64 decoded
- **NameID format** (`name_id_format`) — usually `emailAddress`
- **ACS URL** (`acs_url`) — where the IdP POSTs the SAML response
- **enabled** flag — soft delete + global kill switch

## Schema (alembic 0038)

```
public.tenant_idps
  id              uuid PK
  tenant_id       uuid FK public.tenants(id) UNIQUE per (tenant_id, idp_entity_id)
  idp_entity_id   text NOT NULL  (>0 chars, CHECK)
  idp_sso_url     text NOT NULL  (https://, CHECK)
  idp_slo_url     text NULL
  idp_x509_cert   text NOT NULL  (PEM wrapped, CHECK)
  acs_url         text NULL
  name_id_format  text NULL
  enabled         bool NOT NULL DEFAULT TRUE
  created_at      timestamptz NOT NULL DEFAULT now()
  updated_at      timestamptz  (auto-updated via trigger)
  created_by      uuid FK auth.users(id)
  updated_by      uuid FK auth.users(id)
```

3 RLS policies (`tenant_id = current_setting('app.tenant_id')`) — verbatim
Epic 15 external_identities pattern.

The migration also seeds the `acme` tenant row with Epic 15 placeholder
values so dev environments without an explicit IdP registration can
still attempt SSO without crashing hard.

## Validation pipeline (8 steps)

`apps/api/modules/auth/sso/idp_metadata_validator.py` runs each POST/PUT
payload through 8 validation steps (PRD §F19.2 verbatim):

1. **XML well-formedness** — stdlib `xml.etree.ElementTree.parse()`
2. **Root element = `EntityDescriptor`** — must match SAML 2.0 metadata
3. **`entityID` extraction** — must be present, must be a URI
4. **`IDPSSODescriptor` presence** — SAML 2.0 IdP role
5. **X509Certificate PEM wrap** — base64 decode + RFC 7468 64-char line wrap
6. **SSO URL https://** — defense against plaintext SSO redirects
7. **SLO URL optional + https** — if provided
8. **Tenant slug host match** — `entityID` host must contain tenant slug

Each failure raises a typed exception (`IDPMetadataError` base +
4 subclasses) carrying the CR 12-5 D-14 envelope
`{code, message_ko, details, trace_id}`.

## API surface (5 routes)

All routes mounted at `/api/v1/admin/tenant/{tenant_slug}/idp`:

| Method | Path | Roles | Description |
|---|---|---|---|
| `GET` | `/{tenant_slug}/idp` | owner / admin | List current tenant's IdP config (0 or 1 row) |
| `POST` | `/{tenant_slug}/idp` | owner / admin | Create new IdP config (metadata_xml OR 4 direct fields) |
| `PUT` | `/{tenant_slug}/idp` | owner / admin | Full-replace update |
| `DELETE` | `/{tenant_slug}/idp` | **owner only** | Soft-delete (enabled=FALSE) |
| `POST` | `/{tenant_slug}/idp/test` | owner / admin | Validate metadata XML without writing to DB |

All 5 routes are gated by `TENANT_IDP_MANAGEMENT` capability
(capability matrix v1.28 EXTENSION — industry-agnostic per CR 12-1 L4
precedent). The DELETE route is additionally restricted to `owner` only
(per AD-22 destructive-op RBAC).

## Audit-first INSERT (CR 1-1 verbatim)

Every successful mutation emits an `audit_logs` row **before** the
`tenant_idps` row is touched. 4 NEW ActionClass.AUTH actions:

- `tenant_idp_created` — POST success
- `tenant_idp_updated` — PUT success
- `tenant_idp_deleted` — DELETE soft-delete (enabled=FALSE)
- `tenant_idp_tested` — POST /test validation dry-run

The audit row carries the cert's SHA-256 fingerprint (NFR4 PII
minimization) — never the raw cert body — plus entity_id, sso_url,
and acs_url.

## Per-tenant routing EXTENSION

`apps/api/modules/auth/sso/saml_routes.py` (Epic 15) now loads the
tenant's IdP cert dynamically via `load_tenant_idp()` instead of the
hardcoded placeholder. Two call sites updated:

1. **GET `/api/v1/auth/sso/login`** — uses `idp_sso_url` for the 302 redirect
2. **POST `/api/v1/auth/sso/acs`** — uses `idp_x509_cert_pem` for SAML
   signature validation

Defense-in-depth: both routes fall back to the Epic 15 placeholder if
the tenant has no row, but `enabled=FALSE` triggers a typed 403
envelope.

## Capability matrix (v1.28 EXTENSION)

```
| TENANT_IDP_MANAGEMENT | Epic 16 | ✅ | ✅ | ✅ | ✅ |
```

All 4 industries (manufacturing / service / 겸영 / 겸영+기타) get the
capability. Capability gate is enforced per-tenant via
`require_tenant_idp_management` (apps/api/dependencies/capability.py).

## Tests

- `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py` — 35 pytest cases
- `tests/api/core/test_epic_16_idp_metadata_validator.py` — 15 pytest cases
- `tests/api/core/test_epic_16_idp_admin_routes.py` — 19 pytest cases
- `tests/api/core/test_epic_16_tenant_idp_lookup.py` — 15 pytest cases
- `tests/api/core/test_epic_16_audit_log_verification.py` — 14 pytest cases
- `tests/integration/test_capability_matrix_v1_28_drift.py` — 7 pytest cases

Total: ~105 NEW pytest cases (CR 1-1 + CR 0-2 + CR 12-5 + CR 12-1 L4
verification).

## Cross-references

- Epic 15 spec: `_bmad-output/implementation-artifacts/epic-15-sso-magic-oauth-wire.md`
- Epic 16 spec: `_bmad-output/implementation-artifacts/epic-16-tenant-idp-admin-wire.md`
- Master PRD v3.4 §F19 verbatim
- AD-30 Tenant IdP admin management 신규
- Capability matrix v1.28
- Alembic 0038 migration
- SAML 2.0 metadata spec: https://docs.oasis-open.org/security/saml/v2.0/saml-metadata-2.0-os.pdf