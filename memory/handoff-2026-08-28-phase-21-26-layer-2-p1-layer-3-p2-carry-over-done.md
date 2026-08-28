---
name: handoff-2026-08-28-phase-21-26-layer-2-p1-layer-3-p2-carry-over-done
description: Phase 21~26 Layer 2 P1 + Layer 3 P2 carry-over sprint DONE (cj-style 189번째) — 5 NEW pytest router drift files + 1 NEW include smoke + 6 NEW docs, 46/46 NEW pytest PASS
metadata:
  type: project
---

# Phase 21~26 Layer 2 P1 + Layer 3 P2 carry-over DONE (cj-style 189번째)

옵션 (b) 진입 결정 wire — cj-style 188 (`836a8d4`) 의 next-옵션 (b) verbatim.
cj-style 188 이 Phase 17~20 routers 를 3-layer complete 로 backfill 한 직후,
Phase 21~26 territory 의 동일 backfill 진입.

## Verified actual scope (atomic single sprint)

**16 files = 14 NEW + 2 MODIFIED** (source 변경 0건 — test + docs only sprint):

6 NEW pytest test files under `tests/api/modules/finops/`:
- `test_phase_21_reserved_capacity_router.py` — 8 cases
- `test_phase_22_chargeback_settlement_router.py` — 8 cases
- `test_phase_23_unit_economics_router.py` — 8 cases
- `test_phase_24_budget_planning_router.py` — 8 cases
- `test_phase_25_vendor_management_router.py` — 8 cases
- `test_phase_21_26_router_include.py` — 6 cases (smoke + Phase 26 no-router pin)

= **46/46 NEW pytest PASS**, 전체 `tests/api/modules/finops/` **82/82 PASS**.

6 NEW docs files under `docs/`:
- `finops-reserved-capacity-router.md` (Phase 21)
- `finops-chargeback-settlement-router.md` (Phase 22)
- `finops-unit-economics-router.md` (Phase 23)
- `finops-budget-planning-router.md` (Phase 24)
- `finops-vendor-management-router.md` (Phase 25)
- `finops-cost-anomaly-ml-prediction-no-router.md` (Phase 26 — no-router 명시 문서)

추가 2 NEW: `_bmad-output/implementation-artifacts/commit-msg-cj-189.txt` +
이 handoff memory 파일 = **14 NEW**.
2 MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml`
(v3.96 → v3.97 EXTENSION) + `memory/MEMORY.md` (hook EXTENSION).

## Honest findings (수정하지 않고 실제 상태를 pin)

1. **Phase 26 에는 FastAPI router 가 없다.** `cost_anomaly_ml_prediction/`
   패키지 전체에 `APIRouter` 가 없고 `main.py` 도 이 패키지를 참조하지 않음.
   → router 문서 대신 no-router 문서를 작성하고,
   `test_phase_21_26_router_include.py` Test 6 가 그 부재를 pin.
   나중에 router 를 붙이면 이 테스트가 의도적으로 실패함.

2. **Phase 25 request models 는 `extra="forbid"` 를 선언하지 않는다.**
   Phase 21 은 5개 모델 전부 `ConfigDict(extra="forbid")` 인데 Phase 25 의
   7개 모델은 pydantic 기본 `ignore`. Test 6 은 **실제 상태**(`extra is None`)를
   assert 하여 정직성을 유지 — forbid 로 조이는 것은 별도 source sprint.

3. **Prefix 가 territory 마다 다르다.** Phase 21 `/api/v1/admin/finops/...`,
   Phase 22·23 `/api/v1/finops/...`, Phase 24 `/finops/...`,
   Phase 25 `/api/finops/...`. 정규화는 별도 routing sprint.

4. **Serializer 에 `validate_*` 함수가 없다.** Phase 20 패턴의 Test 8
   (`validate_* raises on missing fields`) 을 그대로 못 미러하여, 대신 각
   territory 의 threshold/cap 상수 invariant 를 pin 하는 Test 8 로 대체.

## 3중 게이트

- ruff scoped: `All checks passed!` (신규 6 파일 + `tests/api/modules/finops/` 전체)
- pytest: **46/46 NEW PASS**, dir 전체 **82/82 PASS** in 1.19s
- vitest: N/A (backend test + docs only sprint)
- tsc: N/A (backend test + docs only sprint)

## A19 cohesion 9 surface

Surface 2 testing + Surface 8 docs EXTENSION 만. 나머지 7 surface NO 변경.
Capability matrix v1.36 → v1.52 EXTENSION chain ✅ PRESERVED (18 steps, orthogonal).

## next

- 옵션 (a) Epic 27+ 진입 — Phase 28 territory 선정
- 옵션 (b) Phase 25 `extra="forbid"` 조이기 source sprint (위 honest finding 2)
- 옵션 (c) FinOps router prefix 정규화 sprint (위 honest finding 3)
- 옵션 (d) D-DEFER-* follow-up 보류
