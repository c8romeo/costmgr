"""apps.api.jobs — scheduled cron entry points.

Story 1.3 — Task 1.3. + Story 12.2 — daily backup + retention sweep.

This package hosts the **periodic** jobs that run independently of
the FastAPI request/response lifecycle. They are invoked by the
external scheduler (Railway cron / GitHub Actions cron) and each
function takes an `AsyncSession` argument so it can be unit-tested
without standing up the scheduler.

Conventions:
- Each job function takes `session: AsyncSession` + `trace_id` + `now`.
- Pure orchestration only; business logic lives in the relevant service
  module (here, `apps.api.modules.m10_ai.service.run_document_retention`
  + `apps.api.modules.m12_account.services.backup_export_service`).
- Idempotent — re-running with the same `now` is a no-op.

Active cron jobs (Story 12.2 wire):
- `document_retention` — daily 03:00 KST (UTC 18:00), 90-day document
  soft-delete (Story 1.3).
- `backup_daily` — daily 02:00 KST (UTC 17:00), per-tenant 7-table JSON
  dump + INSERT tenant_backups (Story 12.2).
- `backup_retention` — daily 03:00 KST (UTC 18:00), per-tenant 30-day
  rolling soft-delete via UPDATE purged_at (Story 12.2).
"""
