---
name: cr-11-2-lessons
description: Story 11.2 dev-story + 3중 게이트 sweep 교훈 (AUTHORIZABLE_TARGET_EVENT_TYPES auth-layer divergence + ALLOWED_SERVICE_SUBMODULES sweep + SDR claim parser line trick + post-sweep fix commit 패턴) — Epic 11+ auth-layer divergence / SDR drift sweep / post-sweep fix commit 진입 시 적용
metadata:
  type: feedback
---

Story 11.2 dev-story 완료 (in-progress → review). cj-style 3-story 분할 (Epic 5 retro §6 W1) 2번째. checkpoint commit `1dbb01f` (T1~T10 abnormal-halt recovery) + sweep commit `79e7c00` (T11 docs + 3중 게이트 + 4 post-sweep fixes) + sprint-status sync commit `6bc4654`.

**Why:** Epic 11 진입 시 동일 패턴 반복 가능성. 다음 story (11-3 snapshot-persistence-with-reverse) 또는 Epic 12+ 에서 auth-layer divergence / post-sweep fix commit 패턴 적용.

**How to apply:**

1. **AUTHORIZABLE_TARGET_EVENT_TYPES auth-layer divergence** — `packages/services/m11_close/reversal_authorization.py` 가 build-layer `REVERSIBLE_TARGET_EVENT_TYPES` (closing_snapshot 포함, reversal_negating 미포함) 를 그대로 사용하면 11-2 의도와 불일치. fix: 신규 상수 `AUTHORIZABLE_TARGET_EVENT_TYPES = (REVERSIBLE_TARGET_EVENT_TYPES - {"closing_snapshot"}) | {"reversal_negating", "reversal_corrected"}`. auth-layer: closing_snapshot AD-6 sealed reject / reversal_negating/corrected re-reversal allow (build-layer `validate_reversal_negating_constraints` 가 별도 self-reversal reject defense-in-depth). 11-1 test 의 non-reversible example 을 `reversal_negating` → `closing_snapshot` 으로 교체 (semantic shift).

2. **ALLOWED_SERVICE_SUBMODULES sweep after service layer wire** — `tests/architecture/test_api_calls_only_ports.py` `ALLOWED_SERVICE_SUBMODULES` frozenset 은 신규 service layer 가 import 하는 모든 `packages.services.*` submodule 을 cover 해야 함. service layer 작성 후 architecture test 가 fail 하면 즉시 submodule entries 추가 (architecture test 는 3중 게이트의 일부). 11-2 에서 3 entries (close_sequence_order + close_sequence_state + partial_close_guard) 추가.

3. **SDR drift detector claim parser line trick** — `tests/integration/test_sdr_test_count_drift.py` 의 CLAIM_PATTERNS 가 `(\d+)\s+passed` 를 `(\d+)\s+tests?\s+collected` 보다 먼저 매칭. 같은 line 안에 `X passed` 와 `Y tests collected` 가 있으면 `X` 만 잡혀서 `Y` 가 MAX 로 안 잡힘. fix: `Y tests collected` 만 있는 별도 line 추가 (예: `MAX SDR claim 갱신: **Y tests collected** (X → Y, +N ...)`).

4. **post-sweep fix commit 패턴** — 3중 게이트 sweep 후 발견된 fix 들은 1 commit 으로 묶어서 sweep commit 에 포함. commit message 형식: `@ Story N.M: T<M> done + 3중 게이트 final clean + N post-sweep fixes (in-progress → review)`. 각 fix 는 (a) 무엇이 fail 했는지 (b) 어떤 fix 적용 (c) 영향 범위 명시. 본 세션 4 fix: auth-layer reversibility + arch submodule allowlist + SDR claim separate line + ruff autofix.

5. **abnormal-halt recovery 패턴** — checkpoint commit (`1dbb01f`) 으로 T1~T10 partial 보존 + sweep commit (`79e7c00`) 으로 T11 잔여 + 3중 게이트 + post-sweep fix 통합. dev-story 가 중단되어도 working tree 가 stable 한 상태로 commit 가능.

6. **T10 frontend + T11.8-T11.10 V8 골든 fixture = DEFERRED to bmad-code-review sweep** — Epic 11 진입 시 frontend (vitest + RTL + Playwright) 와 V8 fixture JSON 파일 + regression test extension 은 dev-story 의 일부만 wire 하고 나머지는 bmad-code-review sweep 에서 carry-over. spec 파일에 명시적 `**DEFERRED — bmad-code-review sweep**` 마커 필수 (handoff 시 carry-over 항목 추적 가능).

Cross-refs: [[cr-6-1-lessons]] (V4 naming collision + ALLOWED_SERVICE_SUBMODULES 동기화) / [[cr-6-2-lessons]] (V4 3-source contract + SDR drift detector 정합 시점) / [[handoff-2026-08-08-11-2-spec-ready]] (11-2 spec baseline).