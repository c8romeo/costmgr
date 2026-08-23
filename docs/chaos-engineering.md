# Chaos Engineering / Game Day Runbook (Phase 9)

> Phase 9 (cj-style 99번째 wire) — Chaos Engineering / Game Day territory
> (PRD §F25 + AD-36 (a)~(g) sub-decisions).

## 1. 목적 (Purpose)

This runbook governs the quarterly chaos game day + continuous chaos
production-safe experiments for the Cost Manager platform. Chaos
engineering proactively validates system resilience under fault
injection, complementing the existing observability (Phase 7),
performance/load testing (Phase 8), and DR (Phase 5) baselines.

## 2. 책임자 (Owners)

- **Owner**: tenant owner (AD-22 owner-only RBAC)
- **SRE on-call**: primary escalation contact
- **2FA 챌린지**: Epic 12 mandatory for L3~L5 blast radius (CR 12-5 L3)

## 3. 사전 준비 (Pre-flight)

1. Verify tenant is `staging` (production game days require explicit
   owner + 2FA + 24h advance notice via Slack `#chaos-game-day`).
2. Confirm blast radius (L1~L5) + intensity (low/medium/high) +
   duration (1~600s) + abort conditions (1~4 rules).
3. Owner-only ACK at the chaos dashboard.
4. 2FA 챌린지 통과 (Epic 12 verbatim, AD-22 owner-only).
5. Slack notification to `#chaos-game-day` channel.

## 4. Communication Channel

- **Slack**: `#chaos-game-day` (real-time experiment status updates).
- **PagerDuty**: owner-only manual trigger escalation path.
- **Sentry**: Phase 7 breadcrumb for fault injection events.

## 5. Experiment Schedule

Quarterly cadence (KST 1st Sunday 03:00 = UTC 18:00):

- **Q1**: January-March (1st Sunday 03:00 KST)
- **Q2**: April-June (1st Sunday 03:00 KST)
- **Q3**: July-September (1st Sunday 03:00 KST)
- **Q4**: October-December (1st Sunday 03:00 KST)

Continuous chaos (L1 single_request only, production-safe) runs at
5% traffic with 60s duration + 30s auto-rollback.

## 6. Abort Conditions

1. `steady_state_metric > 1.5x baseline` — auto-abort.
2. `error_rate > 5%` — auto-abort.
3. `experiment_duration > max` — auto-abort.
4. `external abort signal via POST /api/v1/admin/chaos/{experiment_id}/abort` —
   manual abort (owner-only AD-22 + 2FA 챌린지 Epic 12 정합).

## 7. Rollback Strategy

4 strategies (PRD §F25.6.2 verbatim):

- **automatic**: abort condition trigger 시 30s 이내 fault 제거.
- **manual**: owner-only + 2FA 챌린지 Epic 12 정합.
- **hybrid**: 5min 이상 진행 시 manual confirm 필요.
- **scheduled_abort**: duration_seconds 만료 시 자동 abort.

## 8. Observation Checklist

- [ ] Phase 7 OpenTelemetry trace_id propagation 확인.
- [ ] Prometheus custom metrics (`business_chaos_experiments_total` +
      `business_chaos_auto_rollback_total` + `business_chaos_observations_seconds`)
      확인.
- [ ] Sentry breadcrumb capture 확인.
- [ ] Slack `#chaos-game-day` 실시간 communication 확인.
- [ ] PagerDuty integration owner-only AD-22 RBAC 확인.

## 9. Post-Mortem Template

`docs/chaos-game-day-{yyyymmdd}.md` 5 sections:

1. Experiment Summary
2. Observed Metrics
3. Auto-Rollback Performance
4. Blast Radius Assessment
5. Follow-up Actions

## 10. Lessons Learned Archive

Phase 8 wire `60d4ea1` 의 SLO/SLI lessons learned + Phase 7 wire
`59b56cd` 의 observability lessons learned + Phase 5 wire `f093f8c`
의 DR drill lessons learned 모두 보존. 신규 chaos 실험 시 lessons
learned archive 검토 후 반영.

## 11. Quarterly Review

매 분기 1회 owner + SRE on-call + 2FA 챌린지 통과 후 retrospective:

- 실험 success rate (target ≥ 95%).
- Auto-rollback tTR (target ≤ 30s).
- Blast radius escalation 건수.
- Continuous chaos statistics 검토.

## 12. Safety Mechanisms (6 layers)

PRD §F25.6.3 verbatim:

1. Abort conditions 4 rules.
2. Blast radius 5 levels.
3. Owner-only RBAC AD-22 (L3~L5 + manual abort + 2FA 챌린지 Epic 12).
4. Dry-run mode default (audit-first INSERT `chaos_experiment_dryrun`).
5. Steady state verification (auto-rollback 후 5min baseline recovery).
6. Circuit breaker (5 consecutive experiments failure 시 1h cool-down).

## 13. Compliance & Audit

CR 1-1 verbatim audit-first INSERT 4 NEW actions:

- `chaos_experiment_started` — BEFORE fault injection.
- `chaos_experiment_completed` — AFTER auto-rollback.
- `chaos_experiment_aborted` — manual / condition-trigger abort.
- `chaos_rollback_triggered` — auto-rollback strategy executed.

Routes to `audit_logs` (ActionClass.CHAOS_ENGINEERING).

## 14. Continuous Improvement

Quarterly retrospective 결정 wire 보존:
- D-CHAOS-1 honestly DEFER 보존 (Phase 8 close-out retro §10 + Phase 7
  close-out retro §10 verbatim 해소).
- 신규 D-CHAOS-* follow-up 결정 wire 보존.

---

Last updated: 2026-08-24 (Phase 9 wire, cj-style 99번째).
Cross-references:
- PRD: §F25 verbatim + AD-36 sub-decisions.
- Spec: `phase-9-chaos-engineering-wire.md`.
- Phase 8 wire: `60d4ea1` (SLO/SLI + latency budget baseline).
- Phase 7 wire: `59b56cd` (observability stack integration).
- Phase 5 wire: `f093f8c` (multi-region failover integration).
