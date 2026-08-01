"""apps.api.jobs — scheduled cron entry points.

Story 1.3 — Task 1.3.

This package hosts the **periodic** jobs that run independently of
the FastAPI request/response lifecycle. They are invoked by the
external scheduler (Railway cron / GitHub Actions cron) and each
function takes an `AsyncSession` argument so it can be unit-tested
without standing up the scheduler.

Conventions:
- Each job function takes `session: AsyncSession` + `trace_id` + `now`.
- Pure orchestration only; business logic lives in the relevant service
  module (here, `apps.api.modules.m10_ai.service.run_document_retention`).
- Idempotent — re-running with the same `now` is a no-op.
"""
