/**
 * apps/web/lib/closing-guard-toast.ts — Story 5.3 T9 sonner integration.
 *
 * Wires the `ApiError` thrown by `requestClosingGuardAttempt` on 409
 * NEGATIVE_CLOSING_INVENTORY into a Korean sonner toast. Pure-TS
 * helper — no React component, no I/O.
 *
 * Usage:
 * ```ts
 * import { toast } from "sonner";
 * try {
 *   await requestClosingGuardAttempt(periodKey);
 * } catch (err) {
 *   if (isClosingGuardNegativeError(err)) {
 *     showClosingGuardNegativeToast(err);
 *     return;
 *   }
 *   throw err;
 * }
 * ```
 *
 * AD-15 §11 parity: Korean message from `payload.message_ko` (server
 * SSOT) is preferred over a hardcoded client fallback.
 */

import { toast } from "sonner";

import type { ApiError } from "@/lib/api-client";
import { NEGATIVE_CLOSING_INVENTORY_KO } from "@/lib/l2-input-inventory-ledger";

/**
 * Returns true iff the given `ApiError` is a 409 NEGATIVE_CLOSING_INVENTORY.
 *
 * Discriminated by:
 * 1. `err.status === 409`
 * 2. `err.payload.code === "NEGATIVE_CLOSING_INVENTORY"`
 */
export function isClosingGuardNegativeError(
  err: unknown,
): err is ApiError {
  if (!err || typeof err !== "object") {
    return false;
  }
  const e = err as { status?: number; payload?: { code?: string } };
  return (
    e.status === 409 &&
    e.payload?.code === "NEGATIVE_CLOSING_INVENTORY"
  );
}

/**
 * Show a sonner error toast for a 409 NEGATIVE_CLOSING_INVENTORY.
 *
 * Korean message preference:
 * - `err.payload.message_ko` (server SSOT, AD-15 §11 parity)
 * - fallback to `NEGATIVE_CLOSING_INVENTORY_KO` constant (TS SSOT)
 *
 * Toast duration: 6000ms (long enough for the user to read the banner).
 */
export function showClosingGuardNegativeToast(err: ApiError): void {
  // P29 (patch): Use NEGATIVE_CLOSING_INVENTORY_KO SSOT from
  // `apps/web/lib/l2-input-inventory-ledger.ts` instead of hardcoded
  // literal — single source of truth per AD-15 §11.
  const message =
    err.payload.message_ko || NEGATIVE_CLOSING_INVENTORY_KO;
  toast.error(message, {
    duration: 6000,
    description: err.payload.details
      ? JSON.stringify(err.payload.details, null, 2)
      : undefined,
  });
}