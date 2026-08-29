// apps/web/lib/l2-input-opening-carry.ts — Story 5.1 M14 + Story 5.3 wire
// TS mirror helper for opening carry chain (PRD §6.1 + §V3)
//
// AD-23: one enum per module. Mirrors Python helpers in
// `packages/services/m2_input/opening_carry.py`. Drift caught by
// `tests/integration/test_m2_input_label_consistency.py`.
//
// PURE TYPESCRIPT — no React, no DOM, no I/O. Consumed by:
// - [기초재고] tab form (auto-fill from prior period closing)
// - m2-input Tabs lock badge (locked = manual edit rejected)

import { Decimal } from "decimal.js";

/**
 * Carry-chain decision enum (mirrors Python `CarryChainDecision`).
 *
 * - `auto_carry`: opening = previous period's closing (auto).
 * - `manual_lock`: operator pinned this period's opening (no chain).
 * - `chain_recompute`: chain recomputed after upstream change.
 * - `manual_edit_rejected`: invariant violation blocked manual edit.
 */
export type CarryChainDecision =
  | "auto_carry"
  | "manual_lock"
  | "chain_recompute"
  | "manual_edit_rejected";

/**
 * Per-period opening carry state.
 *
 * `opening_inventory`: product_id → qty Decimal mapping for the period.
 * `opening_inventory_locked`: True if auto carry chain is active
 *   (manual edits are rejected by gate).
 * `opening_inventory_lock_reason_ko`: Korean reason string (AD-15 §11
 *   parity). `null` when not locked.
 */
export interface OpeningCarryState {
  opening_inventory: Record<string, Decimal>;
  opening_inventory_locked: boolean;
  opening_inventory_lock_reason_ko: string | null;
}

/**
 * Returns true iff the opening inventory is currently locked by the
 * auto carry chain.
 */
export function isOpeningLocked(state: OpeningCarryState): boolean {
  return state.opening_inventory_locked;
}

/**
 * Returns true iff manual edits are allowed for the opening inventory.
 * Inverse of `isOpeningLocked`.
 */
export function canEditOpening(state: OpeningCarryState): boolean {
  return !state.opening_inventory_locked;
}

/**
 * Format the Korean lock reason for display. Falls back to a stable
 * SSOT constant when the state has no explicit reason.
 */
// eslint-disable-next-line camelcase
export function formatCarryChainReason(reason_ko: string | null): string {
  // eslint-disable-next-line camelcase
  return reason_ko ?? "기초재고 이월 체인 비활성";
}

/**
 * Default lock reason SSOT (AD-15 §11).
 * Mirrors Python `OPENING_CARRY_LOCK_REASON_KO`.
 */
export const OPENING_CARRY_LOCK_REASON_KO = "기초재고 이월 체인 활성";

/**
 * Period chain limit SSOT (PRD §F4.1 + OQ4 cj-style default).
 * Mirrors Python `INVENTORY_PERIOD_CHAIN_LIMIT`.
 */
export const OPENING_CARRY_CHAIN_LIMIT = 12;

/**
 * Locked-period Korean helper string for UX toast (PRD §F4.1).
 * Mirrors Python `_lock_reason_ko` default returned by
 * `lock_opening_after_first_row(state)`.
 */
export const OPENING_CARRY_LOCKED_REASON_KO = "전월 기말 자동 이월";