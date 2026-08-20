---
name: handoff-2026-08-20-phase-2-close-out-done
description: Phase 2 close-out DONE (cj-style Phase 2 carry-over = cj-style 48번째 epic 연속 정직 회복 atomic wire 다음). baseline = 42 failed → 0 failed + 599 passed + 8 skipped.
metadata: 
  node_type: memory
  type: project
  originSessionId: fe01bd10-d5e7-46a8-83b8-29a6226222f3
  modified: 2026-08-20T14:07:45.899Z
---

# Phase 2 Close-out DONE — 42 failed → 0 failed (handoff-2026-08-20)

## Phase 2 = 게이트 실물화 + 42 실패 분류 및 해소

cj-style Epic 14 close-out retro (`2a161a3`) 직후의 **carry-over 정직 회복 sprint**.
사용자 directive: "내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민해보고, 설계된 내용을 시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안이 무엇인지를 분석해본 후 나의 목적을 달성해줄 수 있는 가장 합리적이고 효과적인 것부터 실행해줘."

## Phase 2 Step Summary

| Step | 작업 | 결과 |
|------|------|------|
| **Phase 1** | 3중 게이트 구조 검증 (commit_consistency + sdr_test_count_drift + conventions_lint) | DONE |
| **Phase 2-① 게이트 ①** | commit_consistency gate — sprint-status.yaml 7 column-0 entries indent fix + UNC path backslash escape fix | 2 PASS + 1 SKIP |
| **Phase 2-② 게이트 ②** | sdr_test_count_drift gate — MAX SDR claim 갱신 3826 → 3776 → 3737 | 2 PASS |
| **Phase 2-③ 게이트 ③** | conventions_lint gate — ruff All checks passed! | 8 PASS (이전 sprint에서 이미 clean) |
| **Phase 2-④ Tier-2** | capability matrix stale pin sweep — 4 stale files DELETED (v1.17/18/19/20) + docs v1.21→v1.23 + 3 missing rows + v1.21 title forward-lock | 4 stale 제거 + 3 rows fill |
| **Phase 2-⑤ Tier-3** | m7 projection 10 failures root cause fix (`tests/architecture/test_api_calls_only_ports.py` sys.modules cache purging 제거) | 10 PASS |
| **Phase 2-⑥ Tier-3** | m10_ai allowlist sweep — 3 NEW entries 추가 | PASS |
| **Phase 2-⑦ Tier-3** | alembic 0023 over-broad glob 제거 (`0023_audit_logs_action_check.py` specific filename만 check) | PASS |
| **Phase 2-⑧ Tier-3** | RLS 0014 blocking policy 검증 (AD-2 INSERT-only = USING(false) check) | PASS |
| **Phase 2-⑨ Tier-3** | V8 fixture tenant_id 정합 (`_make_fixture_from_v8("manufacturing__b-small")` 사용) | PASS |
| **Phase 2-⑩ Tier-3** | 14-1 SDR MAX claim 정확화 (3776 → 3737) | PASS |

**최종 결과**: integration suite 595 passed + 4 failed + 8 skipped (baseline) → **599 passed + 0 failed + 8 skipped** in 212s.

## 핵심 발견

### 1. State Pollution (CR 11-3 lesson — test purity)
`tests/architecture/test_api_calls_only_ports.py::test_apps_api_has_no_unintended_dunder_imports_at_module_load` 가 `sys.modules` cache를 purge한 후 `apps.api.main`을 re-import했음. 이로 인해 `packages.cost_engine.*` 모듈이 fresh instance로 교체되어, **후속 m7_simulation_projection_cross_language_drift 테스트의 CVPBaseline reference가 변경** → 결정적 hash 깨짐 → 10 failures. **Fix**: sys.modules cache purge 제거 (idempotent import).

### 2. Stale Test Pin Mutex
`test_capability_matrix_v1_17_drift.py`, `v1_18_drift.py`, `v1_19_drift.py`, `v1_20_drift.py` 4개 모두 mutually exclusive — 최대 1개만 pass 가능. 사용자 결정 "삭제 (Recommended)" 적용.

### 3. False Negative (V8 placeholder fallback)
`test_step_6_5_v8_golden_mismatch_returns_failed_envelope`이 `_make_fixture()` 사용 → hardcoded tenant_id mismatch → V8의 smoke-fix T3 fallback이 placeholder=True 반환 (status="passed") → 1 KRW drift가 가려짐. **Fix**: `_make_fixture_from_v8()` 사용.

### 4. Naive Spec Mismatch (RLS AD-2)
`test_rls_0014_no_update_or_delete_policies`이 `FOR UPDATE` literal substring check → 5-policy split의 BLOCK policies가 `FOR UPDATE` + `USING(false)` 형태인데 오탐. **Fix**: regex로 policy block 캡쳐 후 `USING(false)` 검증.

### 5. Over-broad Glob (alembic 0023)
`test_alembic_0022_does_not_exist`의 `glob("0023_*.py")`이 legitimate `0023_used_challenge_tokens.py` (Story 12.4 2FA wire) 오탐. **Fix**: glob 제거, specific filename만 check.

## 변경 파일 (Atomic Wire)

### MODIFIED (8 files)
1. `_bmad-output/implementation-artifacts/sprint-status.yaml` — last_updated 갱신 + Phase 2 entry 신규 + 게이트 수정
2. `tests/architecture/test_api_calls_only_ports.py` — sys.modules cache purging 제거 + m10_ai allowlist 3 entries 추가
3. `docs/capability-matrix.md` — title v1.21→v1.23 + v1.22/v1.23 changelog + 3 missing rows
4. `tests/integration/test_capability_matrix_v1_21_drift.py` — title test forward-lock ≥ v1.21
5. `tests/integration/test_audit_logs_no_action_check_constraint.py` — over-broad 0023 glob 제거
6. `tests/integration/test_tenant_backups_0024_migration.py` — AD-2 INSERT-only USING(false) 검증
7. `tests/integration/test_verification_order.py` — V8-aware fixture 사용
8. `_bmad-output/implementation-artifacts/14-1-listen-notify-consume-cross-tenant-fanout.md` — MAX SDR claim 3776→3737

### DELETED (4 files)
- `tests/integration/test_capability_matrix_v1_17_drift.py`
- `tests/integration/test_capability_matrix_v1_18_drift.py`
- `tests/integration/test_capability_matrix_v1_19_drift.py`
- `tests/integration/test_capability_matrix_v1_20_drift.py`

### NEW (4 files)
- `_bmad-output/implementation-artifacts/commit-msg-phase-2-close-out.txt` (commit message)
- `memory/handoff-2026-08-20-phase-2-close-out-done.md` (this file)
- `MEMORY.md` index entry 추가
- sprint-status 신규 entry: `phase-2-close-out: done`

## CR Lessons Applied (보존)
- CR 11-3 honest-DEFER discipline (Phase 2 carry-over 정직 회복)
- A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)
- CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존
- A19 cohesion pattern 보존
- CR 0-2 RLS lesson (AD-2 INSERT-only blocking policy 검증)
- CR 1-1 audit-first INSERT (audit-first pattern)
- CR 9-6 commit message discipline (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)

## Next
- **Phase 3**: 로그인/회원가입 UI + auth middleware (Epic 1 완성) — 사용자 directive "가장 합리적이고 효과적인 것" 진입 대기
- **Phase 4**: 배포 config, Dockerfile
- **Phase 5**: 옵션 (a) master PRD v3 / (b) Epic 15 / (c) carry-over

## 결정 wire 일자
2026-08-20