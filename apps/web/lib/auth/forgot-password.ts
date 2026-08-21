/**
 * apps/web/lib/auth/forgot-password.ts — Password reset request wrapper.
 *
 * Phase 3-1 — T6.5 (AC #5.2, #5.5) — F-15.5.
 * SECURITY: This wrapper ALWAYS returns ok=true regardless of whether
 * the email is registered, so callers cannot leak account existence.
 * The actual `supabase.auth.resetPasswordForEmail` call is wrapped in
 * try/catch so any network error doesn't surface to the user.
 */
"use client";

import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export interface RequestPasswordResetArgs {
  email: string;
  locale: string;
}

export async function requestPasswordReset(
  args: RequestPasswordResetArgs,
): Promise<{ ok: true }> {
  const email = args.email.trim();
  if (!email) return { ok: true };

  try {
    const supabase = createSupabaseBrowserClient();
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${origin}/${args.locale}/reset-password`,
    });
  } catch {
    // Swallow — security invariant: always return success.
  }
  return { ok: true };
}
