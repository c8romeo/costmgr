---
name: handoff-2026-08-26-phase-20-5-wire-done
description: Phase 20.5 Critical Gap Resolution carry-over wire DONE (cj-style 147번째). Layer 1 P0 router include 4 routers 신규 생성 + main.py include. 10 files atomic single sprint = 6 NEW + 4 MODIFIED.
metadata:
  type: project
---

# Phase 20.5 Critical Gap Resolution carry-over wire DONE — cj-style 147번째

## 결정 wire 요약

Phase 20.5 (Critical Gap Resolution carry-over) wire 진입 완료. Phase 20.5 spec entry (cj 146) 의 3-Layer territory 중 Layer 1 P0 critical functional gap fix 결정 wire.

- **cj-style 진입점**: 147번째 (baseline_commit: `e23141d` Phase 20.5 spec entry commit, parent: cj 146)
- **결정 wire 일자**: 2026-08-26 (KST)
- **files**: 10 files atomic single sprint = **6 NEW + 4 MODIFIED**
  - 4 NEW FastAPI routers (`sustainability_routes.py` + `commitment_routes.py` + `pricing_routes.py` + `multi_cloud_routes.py`)
  - 1 NEW handoff memory (this file)
  - 1 NEW commit-msg (PowerShell here-string 회피)
  - 1 MODIFIED `apps/api/main.py` (4 routers include_router 신규)
  - 1 MODIFIED `apps/api/modules/finops/multi_cloud/__init__.py` (9 aggregator function re-exports)
  - 1 MODIFIED `apps/api/modules/finops/multi_cloud/serializers.py` (ALL_NEGOTIATION_COMMITMENT_TERMS constant 신규)
  - 1 MODIFIED `memory/MEMORY.md` hook EXTENSION
  - 1 MODIFIED `sprint-status.yaml` v3.56 → v3.57 EXTENSION

## Phase 20 close-out retro honest deviation ① P0 critical fix 결정 wire

Phase 20 close-out retro `f361016` (cj-style 145번째) 의 4 honest deviations 중 ① apps/api/main.py NOT MODIFIED — multi_cloud router 미 include 정직 회복 결정 wire.

### 발견 사실

Phase 17/18/19/20 wire cycles (`97cfe4e` + `67059cf` + `8db3cfc` + `52dad7f`) created aggregator modules BUT DID NOT create FastAPI router files. routers 가 아예 존재하지 않았음. Layer 1 P0 fix 는 단순 include 만이 아니라 **router creation + include** 결정 wire.

### Layer 1 P0 결정 wire 진입 결과

- 4 NEW FastAPI routers 생성 (executive_dashboard_routes.py Phase 16 wire 패턴 verbatim 미러)
- 32 NEW endpoints (8 per router × 4 routers)
- capability-gated (FINOPS_SUSTAINABILITY + FINOPS_COMMITMENT + FINOPS_PRICING + FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION)
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory

### 부수 발견 사실 (정직 회복)

Phase 20 wire `52dad7f` 의 추가 honest deviations:
- **`multi_cloud/__init__.py` 누락 constant**: `ALL_NEGOTIATION_COMMITMENT_TERMS` 가 serializers.py 에 정의되지 않음. Phase 20.5 wire 에서 보충 결정 wire.
- **`multi_cloud/__init__.py` 누락 re-exports**: aggregator functions (`reconcile_multi_cloud_*`, `run_negotiation_bot`, `track_blended_unblended_diff`, `integrate_marketplace_saas_pricing`, `validate_*`) 가 submodules 에 정의됐으나 `multi_cloud/__init__.py` 에서 re-export 안됨. Phase 20.5 wire 에서 보충 결정 wire (9 NEW function re-exports).

## 결정 wire 분석 — risk minimization

| 옵션 | technical debt 영향 | 리스크 | 가치 | 권장 |
|---|---|---|---|---|
| (a) Phase 21+ 신규 진입 | 누적 debt ↑↑ | 상 | 낮음 | ❌ |
| **(c) Phase 20.5 Layer 1+2+3 진입** | debt ↓↓↓ | **하** | **최고** | ✅ **선택** |

Phase 20.5 wire 의 scope 재조정 결정 wire:
- **Layer 1 P0 router include**: ✅ INCLUDED (4 routers + main.py + 2 multi_cloud file fixes)
- **Layer 2 P1 pytest backfill**: ❌ DEFERRED (honest deviation, Phase 20.6+ carry-over 보류)
- **Layer 3 P2 docs backfill**: ❌ DEFERRED (honest deviation, Phase 20.6+ carry-over 보류)

## 3 ACs §F37.1~§F37.3 verbatim → 36 sub-ACs (12+12+12)

- §F37.1 Layer 1 P0 — apps/api/main.py router include_router() (12 sub-ACs)
  - F37.1-1~F37.1-4: 4 routers import + include_router (sustainability + commitment + pricing + multi_cloud) ✅ WIRED
  - F37.1-5: include_router 위치 (executive_dashboard_router 호출 직후) ✅ WIRED
  - F37.1-6~F37.1-7: prefix="/api/v1" + tags 통일 ✅ WIRED
  - F37.1-8: FastAPI ContextVar 보존 (CR 1-1) ✅ WIRED
  - F37.1-9: audit-first INSERT 8 NEW 자동 활성화 ⚠️ 보류 (emit_audit_typed signature mismatch)
  - F37.1-10: Epic 12 2FA 챌린지 mandatory ✅ WIRED
  - F37.1-11: NFR3 P95 ≤ 500ms 검증 ⚠️ N/A (functional router 등록만)
  - F37.1-12: A19 cohesion 9 surface EXTENSION PASS ✅ PRESERVED

- §F37.2 Layer 2 P1 — pytest test backfill (12 sub-ACs)
  - F37.2-1~F37.2-12: 모든 sub-ACs ❌ DEFERRED (honest deviation)

- §F37.3 Layer 3 P2 — docs backfill (12 sub-ACs)
  - F37.3-1~F37.3-12: 모든 sub-ACs ❌ DEFERRED (honest deviation)

## Dev Notes 18종 (CR lessons applied)

CR 0-2 RLS + CR 1-1 ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 9-6 commit message discipline + CR 11-3 honest-DEFER 37번째 (Phase 20 close-out retro honest deviation ① 정직 회복 + Layer 2 P1 + Layer 3 P2 보류 = 3 honest deviations) + CR 11-4 + P-015 + CR 12-1 L4 + CR 12-5 D-14 envelope 보존 + CR 12-5 D-PARITY-01 inversion 보존 + CR 12-5 D-GATE-01 inversion 보존 + A19 cohesion 9 surface EXTENSION PASS + A36 SDR 4-step + AD-14 stack pin + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + AD-47 + AD-48

## D-DEFER-* honestly 결정 wire 보존

- D-FINOPS-1~8 ✅ ALL RESOLVED 보존
- D-FINOPS-9 honestly DEFER 보존
- **Phase 20.5 Layer 2 P1 + Layer 3 P2 honestly DEFER 보존** — Phase 20.6+ 로 carry-over 결정 wire 진입 보류
- **emit_audit_typed signature mismatch honestly DEFER 보존** — audit-fixes sprint 에서 결정 wire 진입 보류
- CR 11-3 honest-DEFER 37번째 epic 연속 정직 회복 verification 결정 wire

## 결정 wire 일자 + next

- 결정 wire 일자: 2026-08-26 (KST)
- next 옵션:
  - (a) Phase 20.5 close-out retro 진입 결정 wire (cj-style 148번째) — 14-section §1~§14 verbatim retro document
  - (b) Phase 20.6 pytest + docs backfill sprint 진입 결정 wire (Layer 2 + Layer 3 정직 회복)
  - (c) audit-fixes sprint 진입 결정 wire (emit_audit_typed signature mismatch 정직 회복)
  - (d) Epic 21+ 진입 결정 wire
  - (e) D-DEFER-* follow-up 결정 wire 보류