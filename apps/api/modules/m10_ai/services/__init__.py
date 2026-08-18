"""apps.api.modules.m10_ai.services — m10_ai service submodule.

Story 10.4 (cj-style Epic 10 5번째 진입점 = cj-style 33번째 epic 연속) —
A19 cohesion pattern 8 surface EXTENSION: service layer (T3) + DB
adapter (T3) for `InputPromoter.promote()` (AD-17 verbatim bind).

Reuses kernel from `packages.services.m10_ai.promoter_port`
(AD-5 stdlib-only pure kernel — kernel imports remain untouched).

Why a submodule (vs. extending `apps/api/modules/m10_ai/service.py`):
- A19 cohesion pattern 8 surface: each surface lives in its own file
  (kernel + port + db schema + service + handler + envelope +
  capability + audit). The pre-existing `service.py` houses
  InsightCacheService (10-2) + CommentService (10-3) — a new submodule
  `services/` separates the Story 10.4 promoter surface from those
  without polluting their file (CR 11-3 즉시 sweep 회피 pattern).
- AD-1 / AD-11 layering: handlers / envelopes import from
  `apps.api.modules.m10_ai.services.promoter_service` /
  `apps.api.modules.m10_ai.services.db_promoter_adapter`. UI never
  reaches into raw SQLAlchemy or the kernel directly.
- A35 forward-lock: future Story 10.4 follow-up sprint (D-10-4-DEFER-3
  separate epic M2 public endpoint) can extend this submodule without
  cross-cutting edits to InsightCacheService / CommentService.
"""
