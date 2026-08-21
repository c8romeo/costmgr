/**
 * apps/web/lib/auth/logout.ts — Backend audit log on logout.
 *
 * Phase 3-1 — T5.3 (AC #4.3) — CR 1-1 audit-first INSERT.
 * Calls `POST /api/v1/auth/logout` with the access token so the backend
 * can write `audit_logs` row with `action_name='user_logged_out'`.
 *
 * The backend route is expected to call `emit_audit_typed` with:
 *   payload = {
 *     session_duration_seconds: number,
 *     logout_method: 'manual' | 'session_expired',
 *   }
 *
 * This wrapper is best-effort: failures are propagated to the caller
 * for logging but do NOT block the local cookie clear.
 */
export interface LogoutWithAuditArgs {
  accessToken: string;
  actorUserId: string;
  tenantId: string | null;
  sessionStartedAt: string | null;
}

export async function logoutWithAudit(args: LogoutWithAuditArgs): Promise<void> {
  const sessionDurationSeconds =
    args.sessionStartedAt
      ? Math.max(0, Math.floor((Date.now() - Date.parse(args.sessionStartedAt)) / 1000))
      : 0;

  const response = await fetch("/api/v1/auth/logout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${args.accessToken}`,
    },
    body: JSON.stringify({
      actor_user_id: args.actorUserId,
      tenant_id: args.tenantId,
      session_duration_seconds: sessionDurationSeconds,
      logout_method: "manual",
    }),
  });

  if (!response.ok) {
    // Surface the error for the route handler to log + ignore.
    throw new Error(`audit_logout_failed: ${response.status}`);
  }
}
