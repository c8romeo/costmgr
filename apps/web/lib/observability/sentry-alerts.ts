/**
 * apps/web/lib/observability/sentry-alerts.ts — Sentry alert wiring (frontend).
 *
 * 1st release launch (cj-style 64번째 진입점) — T5.3 (AC #5.3) — F18.5 Production verification.
 * - Sentry alert wiring production 환경 결정 wire.
 * - 5 alert rules: 5xx / auth error / LISTEN drop / backup fail / 2FA fail.
 */
import * as Sentry from "@sentry/nextjs";

export type AlertRule =
  | "5xx_error_rate"
  | "auth_error_rate"
  | "listen_notify_connection_drop"
  | "backup_failure"
  | "two_fa_verification_failure";

export interface AlertPayload {
  rule: AlertRule;
  message: string;
  level: "warning" | "error" | "fatal";
  tags?: Record<string, string>;
  extra?: Record<string, unknown>;
}

export function captureAlert(payload: AlertPayload): void {
  Sentry.captureMessage(`[1st-release] ${payload.rule}: ${payload.message}`, {
    level: payload.level,
    tags: { alert_rule: payload.rule, ...(payload.tags ?? {}) },
    extra: payload.extra,
  });
}

export const ALERT_THRESHOLDS: Readonly<Record<AlertRule, { threshold: number; windowSec: number }>> = {
  "5xx_error_rate": { threshold: 0.01, windowSec: 300 },
  auth_error_rate: { threshold: 0.05, windowSec: 300 },
  listen_notify_connection_drop: { threshold: 1, windowSec: 60 },
  backup_failure: { threshold: 1, windowSec: 86400 },
  two_fa_verification_failure: { threshold: 0.1, windowSec: 600 },
};
