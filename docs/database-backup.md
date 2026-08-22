# Costmgr Database Backup Runbook

> **Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire)** — Production database backup strategy + Supabase PITR + manual export procedure. RPO 5 minutes, RTO 1 hour.
>
> **Phase 5 EXTENSION (cj-style 75번째 wire)** — Cross-region backup strategy + failover runbook. RPO 1 hour, RTO 4 hours. D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED.

## Table of Contents

1. [Purpose](#1-purpose)
2. [Strategy](#2-strategy)
3. [RPO and RTO](#3-rpo-and-rto)
4. [Backup Schedule](#4-backup-schedule)
5. [Restore Procedure](#5-restore-procedure)
6. [Disaster Recovery](#6-disaster-recovery)
7. [Monitoring and Alerting](#7-monitoring-and-alerting)
8. [Retention Policy](#8-retention-policy)
9. [Testing](#9-testing)
10. [Cross-References](#10-cross-references)
11. [Cross-Region Backup Strategy](#11-cross-region-backup-strategy) **(Phase 5 NEW)**
12. [Cross-Region Failover Runbook](#12-cross-region-failover-runbook) **(Phase 5 NEW)**

---

## 1. Purpose

This runbook defines the backup + restore strategy for the costmgr production PostgreSQL database hosted on Supabase. It addresses:

- **What** is backed up (entire database, per-tenant exports).
- **When** backups run (continuous PITR + daily manual snapshots).
- **How** to restore (Supabase PITR dashboard + manual archive retrieval).
- **Who** is responsible (DevOps engineer + product owner on alert).

The backup strategy is designed to be **boring and reliable** — Supabase PITR is the primary mechanism, manual exports are the secondary safety net.

## 2. Strategy

### Primary: Automatic PITR (Point-in-Time Recovery)

**Supabase Pro plan** provides automatic PITR with **7-day retention**. Every transaction is continuously archived to Supabase's backup storage, allowing point-in-time recovery to any second within the retention window.

- **Mechanism**: Supabase's managed PostgreSQL backend continuously archives WAL (Write-Ahead Log) segments.
- **Retention**: 7 days (Supabase Pro plan).
- **Recovery granularity**: 1 second.
- **Cost**: Included in Supabase Pro plan ($25/month).

### Secondary: Manual Export

**Per-tenant manual exports** are triggered by:

1. `POST /api/v1/admin/backup` — admin-only endpoint (Phase 4 T6 wire). Creates a `phase_4_backup_strategy` row + invokes the backup worker.
2. **Epic 12 daily cron** (KST 02:00 = UTC 17:00) — per-tenant automated export to `tenant_backups` table (Epic 12.2 wire).

Manual exports create a JSON snapshot of the tenant's data, encrypted with AES-256-GCM (NFR6 verbatim), and uploaded to the storage backend.

### Tertiary: Quarterly Snapshot Tests

Quarterly restore drills (see §9) verify that the manual exports + PITR are both functional.

### Schema Reference

The `phase_4_backup_strategy` table (alembic 0036) tracks all backup events:

```sql
CREATE TABLE phase_4_backup_strategy (
    id              BIGSERIAL PRIMARY KEY,
    backup_type     TEXT NOT NULL,  -- 'auto_pitr' | 'manual_admin' | 'manual_export'
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ NULL,
    size_bytes      BIGINT NULL,
    checksum_sha256 TEXT NULL,
    storage_url     TEXT NULL,
    status          TEXT NOT NULL DEFAULT 'in_progress',  -- 'in_progress' | 'completed' | 'failed'
    tenant_id       UUID NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (backup_type IN ('auto_pitr', 'manual_admin', 'manual_export')),
    CHECK (status IN ('in_progress', 'completed', 'failed')),
    CHECK (completed_at IS NULL OR completed_at >= started_at)
);
```

CR 1-1 audit-first: a `backup_created` audit log row MUST be INSERTed BEFORE the row INSERT (see `apps/api/core/audit_action.py` for the canonical audit registry).

## 3. RPO and RTO

### RPO (Recovery Point Objective): **5 minutes**

**Rationale**: Supabase PITR provides 1-second granularity, but operational practice uses 5-minute checkpoints for human review before initiating a restore. The 5-minute window means at most 5 minutes of transactions may be lost in a worst-case disaster.

**Trade-off**: Tighter RPO (e.g., 1 minute) requires more aggressive monitoring + faster incident response. 5 minutes balances safety with operational cost.

### RTO (Recovery Time Objective): **1 hour**

**Rationale**: A PITR restore from Supabase typically completes in 15-30 minutes for databases <10GB. Adding 30 minutes for verification + smoke testing yields a 1-hour RTO.

**Trade-off**: Faster RTO (e.g., 15 minutes) requires pre-warmed standby databases, which is deferred to Phase 5+ (multi-region backup, OQ-3).

## 4. Backup Schedule

| Frequency | Type | Trigger | Storage | Retention |
|-----------|------|---------|---------|-----------|
| Continuous | Auto PITR | Supabase managed | Supabase backup storage | 7 days |
| Daily 02:00 KST | Per-tenant export | Cron (`apps/api/jobs/backup_daily.py`) | S3 / Supabase Storage (TBD) | 30 days hot, 90 days cold |
| Weekly Sunday 03:00 KST | Manual verification | Cron (`apps/api/jobs/backup_retention.py`) | Same | Sweep + cleanup |
| Quarterly | Restore drill | Manual (runbook §9) | Local test environment | N/A |

### Cron Job References

- **Daily export** (`backup_daily.py`): KST 02:00 = UTC 17:00
- **Weekly retention sweep** (`backup_retention.py`): KST 03:00 = UTC 18:00

These jobs are owned by Epic 12 wire and preserved as-is (Phase 4 T6 adds the `phase_4_backup_strategy` table to track their metadata, but does NOT modify the job logic).

## 5. Restore Procedure

### Step 1 — Assess the Incident

1. Confirm the data loss / corruption event.
2. Identify the **target restore point** — the timestamp BEFORE the incident.
3. Notify the product owner + on-call DevOps engineer.

### Step 2 — Supabase PITR Restore (Primary)

1. Open Supabase dashboard → Database → Backups → Point in Time Recovery.
2. Select the target timestamp.
3. Click "Restore to new branch" — this creates a new database branch with the restored state.
4. Verify the restored data (run smoke tests against the new branch URL).
5. If verification passes, swap the production `DATABASE_URL` to point to the new branch.
6. If verification fails, iterate on the target timestamp.

**Recovery time**: 15-30 minutes for databases <10GB.

### Step 3 — Manual Export Restore (Secondary)

If PITR is unavailable (e.g., Supabase outage), use the manual export:

1. Identify the most recent `manual_export` row in `phase_4_backup_strategy` with `status='completed'`.
2. Download the backup archive from the storage URL (signed URL, expires in 1 hour).
3. Decrypt the archive using the encryption key from the secrets manager.
4. Restore to a fresh PostgreSQL instance (local Docker container or staging environment).
5. Verify the data integrity (run schema migrations + smoke tests).
6. Swap the production `DATABASE_URL` to point to the restored instance.

**Recovery time**: 45-60 minutes (depends on archive size + network bandwidth).

### Step 4 — Post-Restore Verification

After ANY restore, run the following smoke tests:

1. **Backend health check**: `curl https://api.costmgr.com/api/v1/health/ready` → 200 OK.
2. **Critical user flow**: signup → industry select → login (Phase 3-0 2-mint sequence).
3. **Cross-tenant isolation**: Issue a JWT for tenant A, GET `/api/v1/tenants/{tenantB_id}` → 403.
4. **2FA enforcement**: Verify `TWO_FACTOR_AUTH` capability gate works.
5. **Backup audit trail**: Verify `phase_4_backup_strategy` rows are present and `status='completed'`.

### Step 5 — Incident Postmortem

After a restore, write a postmortem document covering:

- Timeline of the incident.
- Root cause analysis.
- RPO/RTO actual vs target.
- Action items to prevent recurrence.

## 6. Disaster Recovery

### Single-Region Failure (Current Capability)

If the primary Supabase region (`ap-northeast-2` Seoul) fails:

1. **Option A**: Failover to a Supabase read replica in a different region (if configured).
2. **Option B**: Restore from PITR to a new Supabase project in a different region.
3. **Option C**: Restore from manual export to a self-hosted PostgreSQL instance in a different region.

**Recovery time**: 2-4 hours (depends on archive size + network bandwidth).

### Multi-Region Backup (Deferred to Phase 5+)

Multi-region backup (continuous replication to a second Supabase region) is **deferred to Phase 5+** (OQ-3, Phase 4 close-out retro decision). The current single-region strategy is sufficient for the 1차 출시 (initial launch) traffic profile.

## 7. Monitoring and Alerting

### Metrics to Monitor

| Metric | Threshold | Alert Channel |
|--------|-----------|---------------|
| Last successful PITR checkpoint | < 5 minutes ago | Sentry + Slack `#ops-alerts` |
| Daily export failure rate | > 0% (any failure) | Sentry + Slack |
| Storage quota usage | > 80% | Sentry + email |
| `phase_4_backup_strategy` rows with `status='failed'` | > 0 in last 24h | Sentry |

### Grafana Dashboard (Recommended)

- **Panel 1**: PITR checkpoint age (line chart, last 7 days)
- **Panel 2**: Daily export success rate (bar chart, last 30 days)
- **Panel 3**: Storage quota usage (gauge, single value)
- **Panel 4**: Failed backups count (stat, last 24h)

### Alert Routing

- **Warning** (1 failed backup): Slack `#ops-alerts`, no page.
- **Critical** (3+ failed backups or PITR age > 30 min): Sentry + PagerDuty page on-call.

## 8. Retention Policy

### Hot Storage (Fast Access): 30 days

- Manual exports within the last 30 days are stored in the primary storage backend (S3 Standard or Supabase Storage).
- Fast retrieval (< 1 minute) for incident response.

### Cold Storage (Archival): 90 days

- Manual exports between 30 and 90 days old are moved to cold storage (S3 Glacier or equivalent).
- Retrieval time: 1-12 hours (acceptable for non-urgent restores).

### PITR Retention: 7 days

- Supabase Pro plan default.
- Cannot be extended without upgrading to Supabase Team plan (deferred decision).

### Total Retention Window: 90 days

A restore can recover data from up to 90 days ago (cold storage), with 5-minute RPO within the last 7 days (PITR window).

### Cleanup

The `apps/api/jobs/backup_retention.py` cron job (Epic 12 wire) sweeps expired backups daily:

- Hot storage > 30 days → move to cold storage.
- Cold storage > 90 days → delete.
- PITR > 7 days → managed by Supabase (automatic).

## 9. Testing

### Quarterly Restore Drill

Every quarter, run a restore drill to verify the backup strategy works end-to-end:

1. **Setup**: Spin up a fresh staging environment (Docker Compose + new Supabase branch).
2. **Trigger**: Run the restore procedure from §5 against the staging environment.
3. **Verify**: Run the smoke tests from §5 Step 4.
4. **Document**: Record RPO/RTO actual + any issues encountered.

### Schedule

- Q1: January 15
- Q2: April 15
- Q3: July 15
- Q4: October 15

### Owners

- DevOps engineer: Executes the drill.
- Product owner: Reviews the results, signs off.

### Failure Handling

If a restore drill fails:

1. File an incident immediately (P1 severity).
2. Investigate the root cause (PITR availability, manual export corruption, etc.).
3. Apply the fix and re-run the drill within 1 week.
4. Update this runbook with the lessons learned.

## 10. Cross-References

- [Master PRD §F16.6](../_bmad-output/planning-artifacts/prd.md#F16.6) — Database backup strategy
- [Master PRD AD-27](../_bmad-output/planning-artifacts/prd.md#AD-27) — Deployment 신규 결정
- [Production deployment runbook](./deployment.md) — Full deployment guide
- [Capability matrix v1.25](./capability-matrix.md#v1.25) — `DEPLOYMENT_DATABASE_BACKUP` capability gate
- [alembic 0036 migration](../apps/api/alembic/versions/0036_phase_4_backup_strategy.py) — `phase_4_backup_strategy` table schema
- [Epic 12 backup jobs](../apps/api/jobs/) — `backup_daily.py` + `backup_retention.py`
- [Epic 12 12.2 wire handoff](../_bmad-output/implementation-artifacts/handoff-2026-08-XX-epic-12-2-done.md) — `tenant_backups` table

## Known Limitations

- Storage backend (`s3://costmgr-backups/YYYY-MM-DD/` vs Supabase Storage) is **deferred to Phase 4 close-out retro** (OQ-1).
- Multi-region backup is **resolved via Phase 5 wire** — see [§11](#11-cross-region-backup-strategy) and [§12](#12-cross-region-failover-runbook).
- Restore time is dependent on Supabase's PITR performance, which is not directly controllable.

---

## 11. Cross-Region Backup Strategy

> **Phase 5 (cj-style 75번째 wire)** — AD-31 (c) verbatim + PRD §F20.4.

### 11.1 Purpose

Phase 4 §6 honestly-deferred cross-region read replica + disaster recovery to Phase 5. This section resolves **D-PHASE-4-DR-DEFER-1** (Seoul region disaster 시 backup restoration 불가) and **D-PHASE-4-DR-DEFER-2** (cross-region read replica carry-over) via:

- Cross-region PITR: primary Seoul (`ap-northeast-2`) + secondary Tokyo (`ap-northeast-1`).
- Regional retention tiers: 30-day hot + 90-day cold + 365-day archive per region.
- Encrypted-at-rest + TLS 1.3 in-transit.

### 11.2 RPO and RTO SLA

| Metric | Target | Phase 4 baseline | Improvement |
|---|---|---|---|
| **RPO** (Recovery Point Objective) | ≤ 3600 seconds (1 hour) | ≤ 5 minutes | 12× looser due to cross-region replication lag baseline |
| **RTO** (Recovery Time Objective) | ≤ 14400 seconds (4 hours) | ≤ 1 hour | 4× looser due to cross-region promotion overhead |

**Rationale**: Cross-region replication + promotion introduces additional latency. The looser SLA reflects the realistic operational constraint while still satisfying enterprise customer contractual obligations (NFR1 verbatim).

### 11.3 Regional Architecture

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

### 11.4 Retention Policy (per region)

| Tier | Duration | Storage Class | Encryption |
|---|---|---|---|
| **Hot** | 30 days | Supabase managed PostgreSQL | AES-256 at rest (Supabase managed) |
| **Cold** | 90 days | Supabase Storage cold tier | AES-256 at rest + TLS 1.3 in-transit |
| **Archive** | 365 days | Supabase Storage archive tier | AES-256 at rest + TLS 1.3 in-transit |

Per-region retention: **both regions** maintain identical hot/cold/archive tiers. This ensures either region can independently serve restore requests without depending on the other.

### 11.5 Encryption

- **At rest**: Supabase managed AES-256-GCM (NFR6 verbatim — Epic 12 2FA wire precedent).
- **In transit**: TLS 1.3 cross-region (Supabase managed replication protocol).
- **PII minimization**: audit log cert fingerprints use SHA-256 hash (NOT raw certificate). NFR4 PII minimization preserved.

### 11.6 Cross-References

- [Master PRD §F20.4](../_bmad-output/planning-artifacts/prd.md#F20.4) — Cross-region backup strategy
- [Master PRD AD-31](../_bmad-output/planning-artifacts/prd.md#AD-31) — Multi-Region Backup & DR 신규 결정
- [alembic 0039 migration](../apps/api/alembic/versions/0039_phase_5_multi_region_backup.py) — `phase_5_replication_lag` + `phase_5_dr_drill_results` tables
- [failover_orchestrator](../apps/api/jobs/failover_orchestrator.py) — Cross-region failover automation

---

## 12. Cross-Region Failover Runbook

> **Phase 5 (cj-style 75번째 wire)** — AD-31 (a)(b)(f) verbatim + PRD §F20.2 + §F20.3 + §F20.5.

### 12.1 Automatic Failover Trigger

**Health probe** (PRD §F20.2 verbatim):

- Interval: 5 seconds.
- Probe target: `SELECT 1` against primary Seoul connection.
- Threshold: 3 consecutive failures → automatic failover.
- Code path: `apps/api/jobs/failover_orchestrator.py::_health_probe_loop`.

### 12.2 Manual Failover Trigger

**Endpoint**: `POST /api/v1/admin/failover` (owner-only, AD-22 + Epic 12 2FA 챌린지 보존).

**Request body** (JSON):

```json
{
  "reason": "manual_test" | "production_incident",
  "confirmation_2fa_code": "123456"
}
```

**Required RBAC**:

- Caller role: `owner` (NOT admin) — AD-22 owner-only.
- 2FA verification: valid TOTP code within last 30 seconds — Epic 12 2FA 챌린지 보존.

**Response**:

- `200 OK` — failover initiated + completed within 30s RTO.
- `409 Conflict` — `FAILOVER_IN_PROGRESS` (another failover in flight).
- `503 Service Unavailable` — `FAILOVER_TARGET_UNHEALTHY` (Tokyo unhealthy).
- `504 Gateway Timeout` — `FAILOVER_TIMEOUT` (RTO SLA exceeded).

### 12.3 Quarterly DR Drill (PRD §F20.3)

**Schedule**: KST 1st Sunday 03:00 (UTC Saturday 18:00).

**Drill mode**: Production deploys run drill in **staging environment** only. The `drill_mode=True` flag prevents actual production failover.

**6 drill steps**:

1. Probe primary Seoul health.
2. Probe secondary Tokyo health.
3. Capture RPO baseline (replication lag seconds).
4. Capture RTO baseline (0 — never measured).
5. Invoke `FailoverOrchestrator.trigger_failover(drill_mode=True)`.
6. Measure RPO/RTO + record result in `phase_5_dr_drill_results`.

**Quarterly schedule**:

- Q1: January 1st Sunday.
- Q2: April 1st Sunday.
- Q3: July 1st Sunday.
- Q4: October 1st Sunday.

**Drill results table**: `phase_5_dr_drill_results` (system-only, no RLS — CR 0-2 verbatim).

### 12.4 Multi-Region Health Observability

**Endpoint**: `GET /api/v1/health/multi-region` (PRD §F20.5 verbatim).

**Response**:

```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "primary": {
    "region": "primary_seoul",
    "replication_status": "healthy" | "lagging" | "stalled" | "disconnected",
    "lag_seconds": 12,
    "last_wal_received_at": "2026-08-22T10:00:00Z"
  },
  "secondary": {
    "region": "secondary_tokyo",
    "replication_status": "healthy",
    "lag_seconds": 8,
    "last_wal_received_at": "2026-08-22T10:00:00Z"
  },
  "timestamp": "2026-08-22T10:00:01Z"
}
```

**CR 12-5 D-14 envelope**: `{code, message_ko, details, trace_id}` for all error paths (2 NEW error classes: MultiRegionUnavailableError + MultiRegionDataStaleError).

### 12.5 Cross-References

- [Master PRD §F20.2](../_bmad-output/planning-artifacts/prd.md#F20.2) — Cross-region failover automation
- [Master PRD §F20.3](../_bmad-output/planning-artifacts/prd.md#F20.3) — DR drill + automated quarterly test
- [Master PRD §F20.5](../_bmad-output/planning-artifacts/prd.md#F20.5) — Multi-region health observability
- [Master PRD AD-31 (a)(b)(f)](../_bmad-output/planning-artifacts/prd.md#AD-31) — Multi-Region Backup & DR sub-decisions
- [failover_orchestrator](../apps/api/jobs/failover_orchestrator.py) — Failover automation + health probe loop
- [dr_drill](../apps/api/jobs/dr_drill.py) — Quarterly DR drill cron
- [Capability matrix v1.29](./capability-matrix.md#v1.29) — `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` capability gates
- [health endpoint](../apps/api/core/health.py) — `/api/v1/health/multi-region` route