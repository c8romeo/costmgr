# Phase 5 Multi-Region Backup & Disaster Recovery

> **Phase 5 (cj-style 75번째 wire)** — Multi-Region Backup & Disaster Recovery territory overview. Resolves Phase 4 close-out retro §6 honestly-deferred D-PHASE-4-DR-DEFER-1 + D-PHASE-4-DR-DEFER-2.

## Overview

Phase 5 wires cross-region replication + automatic + manual failover + quarterly DR drill + multi-region health observability for the costmgr production database hosted on Supabase.

**Primary region**: Seoul (`ap-northeast-2`)
**Secondary region**: Tokyo (`ap-northeast-1`)

## Architecture

```
┌─────────────────┐   WAL streaming   ┌─────────────────┐
│  Primary Seoul  │ ────────────────► │ Secondary Tokyo │
│ (ap-northeast-2)│  (async, 60s lag) │ (ap-northeast-1) │
└─────────────────┘                   └─────────────────┘
        │                                       │
        ▼                                       ▼
 30-day hot                            30-day hot
 90-day cold                           90-day cold
 365-day archive                       365-day archive
 (Seoul region)                        (Tokyo region)
```

## SLA

| Metric | Target |
|---|---|
| **RPO** (Recovery Point Objective) | ≤ 3600 seconds (1 hour) |
| **RTO** (Recovery Time Objective) | ≤ 14400 seconds (4 hours) |
| **Failover RTO** (cross-region promotion) | ≤ 30 seconds |

## Components

### Database Schema
- `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` —
  `phase_5_replication_lag` + `phase_5_dr_drill_results` tables.
- System-only tables — NO RLS (CR 0-2 verbatim Epic 13/14 LISTEN/NOTIFY pattern).

### Failover Orchestration
- `apps/api/jobs/failover_orchestrator.py` — automatic + manual failover.
- 5-second health probe interval.
- 3 consecutive failures → automatic failover.
- 3 NEW error classes (CR 12-5 D-14 envelope):
  - `FailoverInProgressError` (409)
  - `FailoverTargetUnhealthyError` (503)
  - `FailoverTimeoutError` (504)

### DR Drill
- `apps/api/jobs/dr_drill.py` — quarterly DR drill cron.
- KST 1st Sunday 03:00 (UTC 18:00 Saturday).
- Q1/Q2/Q3/Q4 quarterly schedule.
- 3 NEW error classes:
  - `DRDrillTimeoutError` (504)
  - `DRDrillSecondaryUnhealthyError` (503)
  - `DRDrillRPOLimitExceededError` (500)

### Multi-Region Health Observability
- `apps/api/core/health.py` EXTENSION — `/api/v1/health/multi-region` endpoint.
- `apps/web/app/api/health/multi-region/route.ts` NEW — Next.js Edge Runtime proxy.
- `apps/api/core/observability.py` EXTENSION — Sentry breadcrumb failover.

### Capability Matrix v1.29 EXTENSION
- `MULTI_REGION_BACKUP` (industry-agnostic, CR 12-1 L4).
- `MULTI_REGION_FAILOVER` (industry-agnostic, CR 12-1 L4).
- All 4 industries granted.

### Audit Actions
- `ActionClass.INFRA` — NEW.
- `InfraAction` literal — 4 NEW values:
  - `replica_status_changed`
  - `failover_initiated`
  - `failover_completed`
  - `dr_drill_completed`
- All audit-first INSERT (CR 1-1 verbatim).

## Failover Triggers

### 1. Automatic (Health Probe)
- 5-second interval primary region probe.
- 3 consecutive failures → automatic failover.
- No operator intervention required.

### 2. Manual (`POST /api/v1/admin/failover`)
- Owner-only RBAC (AD-22).
- 2FA 챌린지 required (Epic 12 2FA 게이트 보존).
- 30-second RTO SLA.

### 3. Scheduled Drill (`apps/api/jobs/dr_drill.py`)
- Quarterly cron KST 1st Sunday 03:00.
- STAGING environment only (`drill_mode=True` flag).
- 6 drill steps + RPO/RTO measurement.

## Security

- **Encryption at rest**: Supabase managed AES-256-GCM (NFR6 verbatim).
- **Encryption in transit**: TLS 1.3 cross-region.
- **PII minimization**: audit log cert fingerprints use SHA-256 hash (NOT raw certificate). NFR4 preserved.

## Cross-References

- [Master PRD §F20](../_bmad-output/planning-artifacts/prd.md#F20) — Phase 5 territory definition
- [Master PRD AD-31](../_bmad-output/planning-artifacts/prd.md#AD-31) — Multi-Region Backup & DR sub-decisions
- [Capability matrix v1.29](./capability-matrix.md#v1.29) — `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER`
- [database-backup.md](./database-backup.md) — Phase 4 EXTENSION with cross-region strategy + failover runbook
- [alembic 0039](../apps/api/alembic/versions/0039_phase_5_multi_region_backup.py) — Phase 5 tables migration
- [failover_orchestrator](../apps/api/jobs/failover_orchestrator.py) — Failover automation
- [dr_drill](../apps/api/jobs/dr_drill.py) — Quarterly DR drill

## Known Limitations

- Production failover promotion requires Supabase API wiring (deferred to actual deploy).
- `cross_region_backup.py` script (Phase 4 close-out retro §6 forward-reference) — deferred to Phase 5 wire follow-up sprint.
- Manual trigger endpoint `POST /api/v1/admin/failover` route handler — deferred to T7 admin routes sprint.