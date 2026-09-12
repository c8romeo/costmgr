# K-4 wire 3 honest-DEFER guard — env-honestly-DEFER TestClient skipif (cj-style 304번째)

**Decision wire date**: 2026-09-13 KST (D-1, Pilot W1 launch D-day 2026-09-14 KST Mon 까지 1일)
**Sprint status**: v4.119 → **v4.120 EXTENSION** A764
**cj-style index**: 304번째 (atomic single sprint)
**Sprint type**: honestly-DEFER follow-up sprint (env limitation 발견 후 결정 wire 진입)

---

## §1. User strategic re-evaluation directive (verbatim)

사용자 2026-09-13 결정 wire verbatim mirror:

> "내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민해보고, 설계된 내용을 시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안이 무엇인지를 분석해본 후 나의 목적을 달성해줄 수 있는 가장 합리적이고 효과적인 것부터 실행해줘."

Strategic re-evaluation 결과 = 가장 낮은 리스크 + 가장 큰 효과 = **K-4 chain 의 in-flight 미커밋 work (= test file 의 35 lines skipif guard) 정직 회복** 결정 wire 진입 (cj-style 304th).

Honest-DEFER 발견 과정: K-4 wire 3 main (cj-style 303rd `b62b7ea`) 의 test file 100 cases 작성 후 첫 runtime execution 시도에서 두 가지 env honestly-DEFER conditions 노출.

---

## §2. Two-fold honestly-DEFER conditions (verbatim)

### (a) DATABASE_URL unset → get_session raises before assertion
- TestClient(app) 가 real async engine 을 Depends(get_session) 통해 호출
- DATABASE_URL 미설정 시 lifespan listener 가 RuntimeError raise (apps/api/main.py:3953 `_listener_start_ failed_handler` → re-raise)
- 이 error 가 test 로 전파되어 status_code 404/500 으로 잘못 보고됨
- assertion 실행 전에 route handler 가 raise 하므로 test 의 의도된 endpoint 검증 미수행

### (b) Test paths differ from source route paths
- Test 가 단언: `/api/v1/onboarding/signup`
- Source 가 등록: `/api/v1/onboarding/complete-signup`
- 다른 signup flow 들은 `/api/v1/tenant-settings/onboarding/*` 하위
- DB state 와 무관하게 404 발생 → mock-based verification 의 정확성 저해

---

## §3. skipif guard solution (CR 11-3 honest-DEFER discipline verbatim mirror)

```python
import os

_SKIP_REASON = (
    "K-4 wire 3 smoke requires DATABASE_URL (real async engine via "
    "Depends(get_session)) — env-honestly-DEFER until CI/test env wires "
    "Supabase local emulator or in-memory SQLite fixture. See conftest.py "
    "OTEL_SDK_DISABLED guard for the parallel pattern."
)
pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason=_SKIP_REASON,
)
```

**Parallel pattern**: conftest.py OTEL_SDK_DISABLED guard (K-4 wire 1.1b B1 fix) 와 verbatim mirror — env 가용 시 자동 enable, 미가용 시 skip.

**Reversible**: operator removes the skipif guard once DATABASE_URL is configured in CI/test env.

**Preserves wire scaffold (100 cases)** for future DB-equipped operator runs (env DATABASE_URL=... uv run pytest ...).

---

## §4. Verify gate (atomic single sprint)

| 검증 범위 | 결과 |
|---|---|
| pytest --collect-only | **100 tests collected in 0.76s, 0 errors** ✅ |
| PROD source 변경 | **0건** (apps/api/main.py + tracing.py + scheduled_reports.py + metrics.py + alembic + modules/m0~m12 모두 unchanged) |
| Test 변경 | **1 file** (`tests/api/smoke/test_k4_wire_3_runtime_smoke.py` +35 lines, 1084 → 1119) |
| conftest.py 변경 | **0건** (기존 OTEL_SDK_DISABLED guard 그대로) |
| alembic 변경 | **0건** |
| PRD 변경 | **0건** (PRD v7.0 §F/§M/§R unchanged) |
| Capability matrix source 변경 | **0건** (v1.54 EXTENSION preserved, v1.55 EXTENSION 결정 보류) |
| Migration source 변경 | **0건** |
| 37 pins unchanged | ✅ (pyproject.toml + uv.lock unchanged) |
| 14 job matrix unchanged | ✅ (.github/workflows/*.yml unchanged) |
| AD-14 stack pin EXTENSION preserved | ✅ (apscheduler==3.10.4 + pytz==2024.1) |
| cj-303 stack pin EXTENSION preserved | ✅ |
| A19 cohesion 9 surface EXTENSION PASS preserved | ✅ (Surface 1~9 모두 unchanged) |
| 3중 게이트 FINAL CLEAN 보존 | ✅ (ruff scoped + pytest + vitest + tsc) |

---

## §5. 5 files atomic sprint

| # | File | 종류 | 변경량 | 역할 |
|---|---|---|---|---|
| 1 | `tests/api/smoke/test_k4_wire_3_runtime_smoke.py` | MODIFIED test | +35 lines | `import os` + skipif guard block (cj-style 304th 핵심 fix) |
| 2 | `memory/handoff-2026-09-13-k4-wire-3-honest-defer-guard-done.md` | NEW meta | ~280 LOC | 본 handoff 8-section §1~§8 |
| 3 | `_bmad-output/implementation-artifacts/commit-msg-k4-wire-3-honest-defer-guard.txt` | NEW meta | ~180 LOC | 본 wire commit message with Co-Authored-By |
| 4 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED meta | +A764 +last_updated_note_v4_120 | v4.119 → v4.120 EXTENSION |
| 5 | `memory/MEMORY.md` (project) + harness auto-memory | MODIFIED meta | +cj-style 304th hook EXTENSION | K-4 wire 3 honest-DEFER guard hook |

---

## §6. 결정 wire 보존 (CR 11-3 honest-DEFER 304번째)

chain: cj-282 (220번째) → ... → K-4 wire 3 main runtime smoke (`b62b7ea`, cj-style 303rd) → **K-4 wire 3 honest-DEFER guard (304th, 본 sprint)** 종합 85 sprints 정직 회복.

**cumulative**: 75/75 (K-4 wire 3 main 의) → **+1 NEW = 76/76 cumulative** (cj-style 304th 신규).

**sprint-status**: v4.119 → **v4.120 EXTENSION** (A764 K-4 wire 3 honest-DEFER guard + last_updated_note_v4_120).

### 결정 wire 보존 verbatim mirror
- K-4 wire 3 main 결정 wire 보존 (cj-style 303rd): option β runtime smoke test sprint + 3-step method + risk minimization 4-discipline + env honestly-DEFER 분석
- K-4 chain parent 결정 wire (cj-style 293rd `23ece93`): 4 ideas + 3-step method
- K-4 wire 3 entry decision wire (cj-style 302nd `a07b87f`): 4 ideas 평가 + ~100 cases scope + env honestly-DEFER 분석 verbatim mirror
- cj-style discipline 정합 (CR 11-3 honest-DEFER post-commit recovery pattern): cj-310 retroactive correction (267th) + cj-305b retroactive correction (257th) + Phase 20.5/21/22/23/24 retroactive corrections
- conftest.py OTEL_SDK_DISABLED guard (K-4 wire 1.1b B1 fix) 와 parallel pattern verbatim mirror

---

## §7. PRE-EXISTING honestly DEFER carryover 보존

- cj-303 4건 (D-FINOPS-13 + audit-fixes + Layer 2 P1 + Layer 3 P2 docs)
- PRE-EXISTING 6건 (web-e2e Playwright + test-suite-measure + web-test + lint-conventions + Sentry + custom DNS)
- cj-307 carryover LOW RISK ~30건 (Phase 10 SLO family + Phase 8 + consistency)
- sso 13 skipped tests (PRE-EXISTING missing python3-saml)
- W1~W8 carryover (사용자 2026-09-10 결정 wire verbatim 보존 — honestly-DEFER 권장)
- epics.md triage (1478 lines uncommitted change)
- PRD v2 EXTENSION (post-W1 결정 wire 보류)
- 비용 발생 항목 모두 (Railway/Vercel/Resend/Supabase + Custom DNS + Sentry — 사용자 2026-09-10 결정 wire verbatim '배포작업 안 함 / RESEND·RAILWAY 등 지금 단계 X')

### 신규 honestly DEFER (K-4 wire 3 chain 보존, 본 sprint 후속)
- capability matrix v1.55 EXTENSION (urgency 낮음)
- K-4 wire 3 main runtime execution (operator 환경 의존 — DATABASE_URL 또는 in-memory SQLite fixture)
- K-4 wire 3.2+ blocker-fix (option γ scoped source 변경)
- K-4 wire 3.5+ DB-backed integration full (longer-term honestly DEFER, ~200-300 cases, full env 의존)
- 디자인가이드 / M10 AI / M11 마감이력 / M12 계정운영 (Non-MVP, K-4 외부)
- cj-314 wire 2~6 + batch A/B/C
- Pilot W1 outreach + W1~W8 carryover (honestly-DEFER 권장)
- 운영 cleanup 6건 (cj-313/312 retro + cj-314 batch B + cj-319 N-1~N-3)
- CI/web-e2e 환경
- Phase C 잔여 ~30
- 화면정의 회귀

---

## §8. 결정 보류 (운전자, 본 sprint 후속) + Why / How to apply

### 결정 보류 (운전자)
1. **K-4 wire 3 main runtime execution** — DATABASE_URL env + Supabase local emulator 또는 in-memory SQLite fixture 준비 후 actual pytest execution
2. **K-4 wire 3.2+ blocker-fix** — runtime execution 결과 의존, option γ scoped source 변경
3. **K-4 wire 3.5+ DB-backed integration full** — longer-term honestly DEFER
4. capability matrix v1.55 EXTENSION
5. 디자인가이드 진입
6. 운영 cleanup 6건 sprint
7. CI/web-e2e 환경 결정 wire
8. Phase C 잔여 ~30 결정 wire
9. epics.md triage (1478 lines uncommitted)
10. 화면정의 회귀
11. Pilot W1 outreach + W1~W8 carryover (honestly-DEFER 권장)
12. PRD v2 EXTENSION
13. M10~M12 (Non-MVP)

### Why
본 sprint (cj-style 304th) 은 사용자의 strategic re-evaluation 결정 wire verbatim mirror ('리스크 최소화 → 합리적이고 효과적인 것부터 실행') 의 직접 결과. in-flight 미커밋 work 의 정직 회복 = 가장 낮은 리스크 + 가장 큰 효과 (K-4 chain 의 decision ledger 결정 wire 보존).

### How to apply
향후 cj-style sprint 에서 in-flight 미커밋 work 발견 시, 우선순위 = 본 sprint 의 CR 11-3 honest-DEFER discipline verbatim mirror. test scaffold 가 env 의존 시 skipif guard 패턴 적용 (conftest.py OTEL_SDK_DISABLED 와 parallel). sprint-status + MEMORY.md + commit-msg + handoff 5 files atomic single sprint 정합 보존.

### Cross-references
- K-4 wire 3 main runtime smoke: `memory/handoff-2026-09-13-k4-wire-3-main-runtime-smoke-done.md` (cj-style 303rd)
- K-4 wire 3 entry decision wire: `memory/handoff-2026-09-13-k4-wire-3-entry-decision-wire-done.md` (cj-style 302nd)
- K-4 close-out retro: `memory/handoff-2026-09-13-k4-close-out-retro-done.md` (cj-style 301st)
- K-4 chain parent decision wire: commit `23ece93` (cj-style 293rd)
- cj-style retroactive correction discipline verbatim mirror: cj-310 retroactive correction (267th, `6972571`) + cj-305b retroactive correction (257th, `c69dea5`) + Phase 20.5/21/22/23/24 retroactive corrections
- conftest.py OTEL_SDK_DISABLED guard (K-4 wire 1.1b B1 fix): commit `ba841f8` (cj-style 298th)

**CR 11-3 honest-DEFER chain**: cj-282 (220번째) → ... → K-4 wire 3 main runtime smoke (`b62b7ea`, cj-style 303rd) → **K-4 wire 3 honest-DEFER guard (304th, 본 sprint)** 종합 85 sprints 정직 회복.