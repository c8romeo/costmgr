/**
 * apps/web/lib/supabase/types.ts — Database type definitions.
 *
 * Phase 3-1 — T1.4 (AC #1.5, #1.6) — CR 1-1 audit-first + AD-26 verbatim.
 * The frontend types here are a hand-curated subset of the schema that
 * Phase 3-1 actually reads (auth + tenant + audit). Backend has the
 * full authoritative schema in `alembic/versions/0001_baseline.py`+
 * — this is a typed VIEW-shaped read contract, not a duplicate schema.
 *
 * NOTE: `tenant_memberships` is the canonical table name (corrected
 * from PRD v2.5 `user_tenants` typo — see master PRD v3.0 §F15.2).
 * DO NOT use `user_tenants` anywhere in NEW frontend code.
 *
 * These types are intentionally MINIMAL — they only cover the columns
 * the auth flow reads. Add new table shapes as the auth surface grows.
 */
export interface AppMetadata {
  tenant_id?: string;
  role?: "owner" | "member" | "viewer" | "consultant_proxy";
  industry?: "manufacturing" | "service" | "manufacturing_service" | "manufacturing_service_other";
}

export interface UserMetadata {
  email?: string;
  email_verified?: boolean;
  phone_verified?: boolean;
  sub?: string;
  /** AAL claim from Supabase (2FA state). Epic 12 wire. */
  aal?: "aal1" | "aal2";
}

export interface AuthUser {
  id: string;
  email: string;
  app_metadata: AppMetadata;
  user_metadata: UserMetadata;
  created_at: string;
  updated_at: string;
}

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  /** Epoch (seconds) when the access token expires. */
  expires_at: number;
  /** Supabase assigns this — `aal1` (password only) or `aal2` (2FA verified). */
  aal: "aal1" | "aal2";
  user: AuthUser;
}

export interface Tenant {
  id: string;
  name: string;
  industry: string | null;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TenantMembership {
  id: string;
  tenant_id: string;
  user_id: string;
  role: "owner" | "member" | "viewer" | "consultant_proxy";
  joined_at: string;
}

export interface TenantSettings {
  tenant_id: string;
  settings_version: number;
  onboarding: {
    industry?: string;
    selected_at?: string;
  } | null;
  deleted_at: string | null;
}

export interface AuditLog {
  id: string;
  tenant_id: string | null;
  actor_user_id: string | null;
  action_name: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface Database {
  public: {
    Tables: {
      tenants: { Row: Tenant };
      tenant_memberships: { Row: TenantMembership };
      tenant_settings: { Row: TenantSettings };
      audit_logs: { Row: AuditLog };
    };
  };
}
