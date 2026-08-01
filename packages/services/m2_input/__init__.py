"""packages.services.m2_input — Monthly Input Capture (Story 3.1).

Pure-Python orchestration for the six-stream monthly input domain.
Mirrors the architecture pattern of `m0_onboarding` (Story 1.2):
- stdlib-only modules under this package
- no DB / no clock / no random (AD-1 / AD-5)
- consumed by `apps/api/modules/m2_input/*` (FastAPI routers) AND
  the TS mirror at `apps/web/lib/m2-input-completion.ts` (drift verified by
  `tests/integration/test_m2_input_label_consistency.py`)

Public surface (Story 3.1):
- `stream_completion.STREAM_LABELS_KO` — PRD §8.M2(b) Korean labels
- `stream_completion.STREAM_ORDER` — tab order (주문 → 생산 → … → 인원)
- `stream_completion.STREAMS_FOR_INDUSTRY` — capability_mask by Industry
- `stream_completion.compute_stream_completion` — per-stream completion bool
- `stream_completion.is_all_streams_complete` — aggregate gate
- `stream_completion.format_fte_headcount` — Story 3.2 hook (read-only here)
- `stream_completion.compute_fte_wage_krw` — Story 3.2 hook (read-only here)

Future (not in Story 3.1):
- `MonthInputAdapter` — AD-13 engine-input normalization; written when
  Epic 4 first_calc endpoint is in scope.
- `InputPromoter.promote` — AD-17 promotion from AI drafts; Story 3.4+.
"""