---
name: cj-222-d-ci-func-8-alembic-graph-sweep-done
description: "cj-style 222 D-CI-FUNC-8 alembic graph 단일 head 정직 sweep source-only sprint — DOUBLE BUG root cause (revision 번호 중복 + 존재하지 않는 down_revision) fix wire + 2 files = 2 RENAMED + 7 insertions + 7 deletions"
metadata:
  type: project
  originSessionId: cj-222-2026-08-31
  modified: 2026-08-31T00:00:00.000Z
---

# cj-222 D-CI-FUNC-8 alembic graph 단일 head 정직 sweep DONE (2026-08-31)

cj-style **222번째** atomic single source-only sprint (cj-221 의 123번째 → cj-222 의 124번째 chain). Epic 28 retro §12 옵션 (b) 의 `0055 → 0054` dangling alembic graph 정직 sweep 결정 wire 진입 완료 + D-CI-FUNC-8 HIGH priority blocker 해소.

## root cause (DOUBLE BUG in Phase 26 alembic migration)

`apps/api/alembic/versions/0055_phase_26_cost_anomaly_ml_prediction.py`:

1. **revision 번호 중복 (typo)**: `revision = "0055_phase_26_cost_anomaly_ml_prediction"` → `0055_phase_23_unit_economics` 와 **중복**. Phase 26 wire 진입 시점의 revision 번호 typo, 정상 sequential 정수는 `0058`.

2. **down_revision 비존재 (typo)**: `down_revision = "0054_phase_25_vendor_management"` → **존재하지 않는 revision**. Phase 22 의 revision 은 `0054_phase_22_chargeback_settlement` 이고 Phase 25 의 revision 은 `0057_phase_25_vendor_management`. Phase 25 의 suffix 와 Phase 22 의 revision 번호를 혼동한 typo.

`alembic -c apps/api/alembic.ini history` invocation 자체가:
```
KeyError: '0054_phase_25_vendor_management'
```
로 fail → alembic graph 깨진 상태에서 `alembic upgrade head` 가 어떤 DB 에도 못 적용.

## fix wire (Option A 정직 renumber 채택)

2 files = 2 RENAMED, 7 insertions(+), 7 deletions(-) (실측 `git diff --stat HEAD`):

1. **Phase 26 rename + fix**:
   - `apps/api/alembic/versions/0055_phase_26_cost_anomaly_ml_prediction.py` → `apps/api/alembic/versions/0058_phase_26_cost_anomaly_ml_prediction.py` (`git mv`, git history 보존)
   - `revision` field: `"0055_phase_26_cost_anomaly_ml_prediction"` → `"0058_phase_26_cost_anomaly_ml_prediction"` (5번째 line)
   - `down_revision` field: `"0054_phase_25_vendor_management"` → `"0057_phase_25_vendor_management"` (31번째 line)

2. **Phase 28 rename + fix** (Phase 26 다음 sequential 정수):
   - `apps/api/alembic/versions/0058_phase_28_interactive_dashboard.py` → `apps/api/alembic/versions/0059_phase_28_interactive_dashboard.py` (`git mv`)
   - `revision` field: `"0058_phase_28_interactive_dashboard"` → `"0059_phase_28_interactive_dashboard"` (65번째 line)
   - `down_revision` field: `"0057_phase_25_vendor_management"` → `"0058_phase_26_cost_anomaly_ml_prediction"` (66번째 line)

**Result**: alembic graph topology 가 단일 chain 으로 정직 회복:
```
0057_phase_25_vendor_management
  └── 0058_phase_26_cost_anomaly_ml_prediction
       └── 0059_phase_28_interactive_dashboard (single head)
```

## verification (cj-222 5-step FINAL CLEAN)

- **T7.1 ruff scoped**: ✅ PASS (`ruff check` on 2 files → `All checks passed!`)
- **T7.2 pytest 회귀**: ✅ PASS (`pytest tests/architecture tests/cost_engine tests/rls/test_service_role_audit.py -q` → 598 passed, 1 skipped, 13 warnings — pre-existing skip + warnings 보존, regression 0건)
- **T7.3 alembic graph 단일 head**: ✅ VERIFIED
  - `alembic -c apps/api/alembic.ini history` → 정상 history 출력 (KeyError 해소)
  - `alembic -c apps/api/alembic.ini heads` → `0059_phase_28_interactive_dashboard (head)` 단일 head 1건
- **T7.4 AD-14 stack pin 정책 (35 pins)**: ✅ UNCHANGED (ci.yml 변경 0건, Python source 변경 0건 — alembic revision 만 변경, `[STACK BUMP]` tag 불필요)
- **T7.5 FINAL CLEAN**: ✅ PASS

## runtime 동작 변화

**0건**. alembic graph topology 만 정직 회복, 실제 migration 적용 안된 fresh state. 다음 `alembic upgrade head` invocation 시 Phase 23 → Phase 24 → Phase 25 → Phase 26 → Phase 28 단일 chain 정상 진행 expected.

## 부수 효과

**D-CI-FUNC-5/6 PARTIAL 잔여 해소** (cj-218 의 honestly-DEFER 의 unmasked blocker 해소):
- D-CI-FUNC-5: cj-217 의 `pnpm playwright install chromium` step fix 는 ✅ DONE 보존, 본 cj-222 fix 와 무관 (browser binary download 의 separate root cause 는 별도 honestly-DEFER 보존).
- D-CI-FUNC-6: cj-217 의 smoke-e2e + rls-tests 의 `Install psql` step fix 는 ✅ DONE 보존, 본 cj-222 fix 가 **cj-217 fix 의 unmasked 한 downstream Alembic blocker 해소**.

## files (atomic single source-only sprint)

```
RM apps/api/alembic/versions/0055_phase_26_cost_anomaly_ml_prediction.py -> apps/api/alembic/versions/0058_phase_26_cost_anomaly_ml_prediction.py
RM apps/api/alembic/versions/0058_phase_28_interactive_dashboard.py -> apps/api/alembic/versions/0059_phase_28_interactive_dashboard.py
M  _bmad-output/implementation-artifacts/sprint-status.yaml (D-CI-FUNC-8 RESOLVED entry)
?? _bmad-output/implementation-artifacts/commit-msg-cj-222.txt
?? memory/handoff-2026-08-31-cj-222-d-ci-func-8-alembic-graph-sweep-done.md
M  memory/MEMORY.md (hook EXTENSION)
```

`git diff --stat HEAD` verified:
```
...ediction.py => 0058_phase_26_cost_anomaly_ml_prediction.py} | 10 +++++-----
...ive_dashboard.py => 0059_phase_28_interactive_dashboard.py} |  4 ++--
2 files changed, 7 insertions(+), 7 deletions(-)
```

## 결정 wire 일자

2026-08-31 (KST)

## next 결정 wire 후보 (사용자 결정 보류)

(i) **live CI verification**: 다음 push 후 run_id + 13 job matrix honest aggregation, smoke-e2e + rls-tests 의 `Apply Alembic migration` step PASS expected

(ii) **D-CI-FUNC-3 service-role-guard test FAIL fix** (cj-style 223번째 candidate, LOW priority) — unit test mock fixture drift 가능성, 별도 sprint 결정 wire

(iii) **Epic 28 T2 frontend follow-up sprint 진입** (cj-style 195번째 carry-over) — Epic 28 wire Q2 backend-only sprint 의 honestly DEFER 회복 결정 wire

(iv) **Epic 29+ 신규 territory 진입 결정 wire** (Phase 29 territory 진입 = cj-style 다음 4-entry-point cycle)

## Cross-references

- ✅ Epic 28 atomic wire Q2 backend-only `db005e8` (cj-style 193번째)
- ✅ Epic 28 retro `epic-28-retro-2026-08-29.md` (cj-style 194번째) — §12 옵션 (b) 의 `0055 → 0054` dangling alembic graph 정직 sweep carry-over 보존
- ✅ cj-218 PARTIAL honestly-DEFER (cj-style 111번째) — D-CI-FUNC-8 의 unmasked blocker 신규 surface 결정 wire
- ✅ cj-221 sprint scope 결정 wire (cj-style 123번째) — D-CI-FUNC-3 / D-CI-FUNC-7 등 의 carry-over 보존
- ✅ Phase 23 PRD entry → spec entry → wire → close-out retro (cj-style 162~165) — 정상 `0055_phase_23_unit_economics` chain 보존
- ✅ Phase 26 PRD entry → spec entry → wire → close-out retro (cj-style 179~182) — 정상 `0055_phase_26_cost_anomaly_ml_prediction` 결정 wire (cj-181 wire 진입 시점의 revision 번호 typo, cj-222 에서 정직 회복)
- ✅ Phase 28 PRD entry → spec entry → wire → close-out retro (cj-style 191~194) — 정상 `0058_phase_28_interactive_dashboard` 결정 wire (cj-222 에서 `0059_phase_28_interactive_dashboard` 로 정직 renumber)

## CR 11-3 honest-DEFER 124번째

cj-style 222번째 epic 연속 정직 회복 (cj-221 의 123번째에 이어) — D-CI-FUNC-8 honestly-DEFER 의 actual source fix wire 결정 wire. Epic 28 retro §12 옵션 (b) 의 carry-over 정직 sweep 회복 + smoke-e2e + rls-tests functional test 의 downstream blocker 해소.

---

**Why:** Epic 28 wire Q2 backend-only sprint 진입 후 carry-over 로 honestly DEFER 보존된 `0055 → 0054` dangling alembic graph 가 실제 ci.yml smoke-e2e + rls-tests 의 functional test blocker 로 surface. alembic graph 단일 head 정직 회복 결정 wire 진입이 필요했음.

**How to apply:** D-CI-FUNC-8 의 root cause 가 alembic graph dangling revision 일 경우, `alembic -c apps/api/alembic.ini history` 의 KeyError message 가 직접적 root cause indicator. `revision` 필드 (sequential 정수 검증) + `down_revision` 필드 (parent revision 실제 존재 검증) 2개 모두 검증 후 minimal-scope fix wire 적용. Phase wire 진입 시점의 revision 번호 typo 는 cj-style 222번째 에서 정직 회복. 다음 alembic migration 작성 시 pre-commit hook 으로 `revision` sequential 검증 추가 결정 wire 보류.
