---
epic: 4
epic_title: Cost Calculation & Verification
document_type: Pre-existing Failure Batch — Epic 4 Retro Action Item
date: 2026-08-02
source: Story 4.1 SDR (AI) F-4 ~ F-11
status: pending
---

# Epic 4 회고 시 Pre-existing Failures 한 번에 정리 권고

## 배경

Story 4.1 dev-story 완료 후 `uv run pytest --tb=line` 실행 시 **7 pre-existing pytest failures** + **1 pre-existing ruff error** 식별. 모두 Story 4.1 scope 외 + Story 4.2/4.3/4.4 진입 전 **environment synchronization 권고 시점** = Epic 4 회고(retrospective).

Epic 1+2+3 회고 패턴(`bmad-retrospective` lightweight ~25분)에 따라, 회고 시 1 action item으로 일괄 처리 권고.

## 식별된 8건 (7 pytest + 1 ruff)

### 1. `tests/cost_engine/test_money_purity.py:27: PT011` (ruff)

| 필드 | 값 |
|---|---|
| **Severity** | LOW |
| **Origin** | Story 0.1 baseline code |
| **Root cause** | Story 0.4 added `PT` (pytest-style) rule to ruff config; Story 0.1 baseline code wasn't re-validated |
| **Impact** | Story 4.1 scope = 0 (Story 0.1 file, NOT touched) |
| **Fix** | 1-line: add `match=` parameter to `pytest.raises(ValueError)` or use specific exception type |
| **Effort** | 1 minute |
| **Owner** | Amelia (Developer) |

```python
# Current (line 27):
with pytest.raises(ValueError):
    to_krw(Decimal("1000.5"))

# Fixed:
with pytest.raises(ValueError, match="fractional decimal"):
    to_krw(Decimal("1000.5"))
```

### 2. `test_uploaded_documents_columns_match_migration` (pytest)

| 필드 | 값 |
|---|---|
| **Severity** | LOW |
| **Origin** | Story 1.3 (AI document extraction) |
| **Root cause** | `ai_documents` table column drift between alembic 0008 + current ORM model |
| **Impact** | NOT Story 4.1/4.2 scope (engine kernel + calc endpoint) |
| **Fix** | Re-sync alembic 0008 migration with `apps/api/core/db_models.py::AIDocument` model |
| **Effort** | 30 min (1 migration file + ORM model compare) |
| **Owner** | Amelia (Developer) |
| **Reference** | `tests/api/test_input_draft_orm.py::test_uploaded_documents_columns_match_migration` |

### 3. `test_api_does_not_import_engine_core_or_adapters` (pytest, Story 1.2 issue)

| 필드 | 값 |
|---|---|
| **Severity** | LOW |
| **Origin** | Story 1.2 (settings wizard) — re-export pattern |
| **Root cause** | `apps/api/core/money.py:25` does `from packages.cost_engine.core.money import KRW, USD, ...` — reverse-direction (api → engine core). Architecture test added later in Story 2.x flagged the original pattern. |
| **Impact** | NOT Story 4.1/4.2 scope (engine kernel + calc endpoint) |
| **Fix options** | (a) Re-export via `apps.api.core.money.__init__` wrapper without re-importing engine internals; (b) Re-classify as "engine monetary type" exception in `tests/architecture/test_api_calls_only_ports.py::ALLOWED_SERVICE_SUBMODULES` |
| **Effort** | 1-2 hours (decide option + apply) |
| **Owner** | Amelia (Developer) + Charlie (Senior Dev) for decision |
| **Reference** | `apps/api/core/money.py:25` + `tests/architecture/test_api_calls_only_ports.py` |

### 4. `test_api_root_does_not_import_services` (pytest, pre-existing)

| 필드 | 값 |
|---|---|
| **Severity** | LOW |
| **Origin** | Pre-existing (likely Story 0.1 main.py wiring) |
| **Root cause** | `apps/api/main.py` likely imports a service module directly instead of going through handler-level dependency injection |
| **Impact** | NOT Story 4.1/4.2 scope (engine kernel + calc endpoint) |
| **Fix** | Audit `apps/api/main.py` + module handler imports; route handlers should call service factories, not import service modules at module level |
| **Effort** | 1-2 hours (audit + refactor) |
| **Owner** | Amelia (Developer) |
| **Reference** | `tests/architecture/test_api_calls_only_ports.py::test_api_root_does_not_import_services` |

### 5. `test_ruff_passes_on_clean_repo` cp949 (pytest, CR 0.4 lesson)

| 필드 | 값 |
|---|---|
| **Severity** | LOW |
| **Origin** | Story 0.1/0.4 (clean_repo convention) |
| **Root cause** | Windows Korean locale default cp949 can't decode UTF-8 source file (likely `docs/cost-engine.md` 한글 characters, newly added in Story 4.1 T7.1, OR older `docs/conventions.md`) |
| **Sub-evidence** | Story 4.1 dev agent used `Write` (UTF-8 direct) for `docs/cost-engine.md` (Debug Log); but test runner's subprocess may still hit cp949 |
| **Impact** | NOT Story 4.1/4.2 scope (Story 4.1 + 4.2 new files use UTF-8) |
| **Fix** | Pin subprocess encoding to UTF-8 in `test_ruff_passes_on_clean_repo` fixture: `subprocess.run(..., encoding="utf-8", errors="replace")` or `env={**os.environ, "PYTHONIOENCODING": "utf-8"}` |
| **Effort** | 15 minutes (1 test fixture update) |
| **Owner** | Amelia (Developer) |
| **Reference** | `tests/integration/test_conventions_lint.py::test_ruff_passes_on_clean_repo` |

### 6-8. `test_stack_pin_check` (3 cases, pydantic-core 2.27.2 → 2.33.2 drift)

| 필드 | 값 |
|---|---|
| **Severity** | LOW |
| **Origin** | Story 0.4 chunk-B (TS/Python ROUND_HALF_EVEN parity applied pydantic-core pin sync) |
| **3 failing cases** | `test_node_check_passes_when_pinned` + `test_py_check_passes_when_pinned` + `test_check_handles_bom_prefixed_yaml` |
| **Root cause** | Story 0.4 applied pydantic-core pin 2.27.2 → 2.33.2 in `apps/api/pyproject.toml` (CR 0.3 lesson: TS/Python parity required); but `STACK_PIN.yaml` reference value still 2.27.2 (not bumped) |
| **Impact** | NOT Story 4.1/4.2 scope |
| **Fix options** | (a) Run [STACK BUMP] workflow on `apps/api/pyproject.toml` to update `STACK_PIN.yaml` reference to 2.33.2; (b) Revert pydantic-core back to 2.27.2 (but TS side then breaks parity) |
| **Recommended fix** | (a) — update `STACK_PIN.yaml` to 2.33.2 + use [STACK BUMP] commit tag (CR 0.3 lesson) |
| **Effort** | 15 minutes (1 yaml file update + commit) |
| **Owner** | Amelia (Developer) |
| **Reference** | `tests/integration/test_stack_pin_check.py` + `STACK_PIN.yaml` + `apps/api/pyproject.toml` |

## 권고 처리 방법

### Option A: Epic 4 회고 시 1 action item으로 일괄 처리 (권장)

```
A1: Pre-existing infra failures (8건) 일괄 수정
    - F-1: PT011 in test_money_purity.py:27 (1 min)
    - F-2: test_uploaded_documents_columns_match_migration (30 min)
    - F-3: apps/api/core/money.py reverse-direction (1-2 hour, decision 필요)
    - F-4: test_api_root_does_not_import_services (1-2 hour)
    - F-5: test_ruff_passes_on_clean_repo cp949 (15 min)
    - F-6/7/8: test_stack_pin_check pydantic-core (15 min)
    Total: 4-7 hours (1 day)
    Success criteria: uv run pytest (full) = 0 failed + uv run ruff check = 0 errors
    Owner: Amelia (Developer) + Charlie (Senior Dev) decision support
    Deadline: Epic 4 회고 후 ~1주 (Story 4.3 진입 전)
```

### Option B: Story 4.2 dev-story 시작 전 즉시 처리 (block-on-failure)

```
Story 4.2 T0 (pre-dev-story):
  1. F-5 (cp949) — 15 min
  2. F-6/7/8 (stack-pin) — 15 min
  3. F-1 (PT011) — 1 min
  4. F-2 (DB schema) — 30 min
  Total: 1 hour
  Skip F-3/F-4 (architecture decisions) — defer to Epic 4 retro
  Success criteria: full pytest = 2 failed (F-3/F-4) + 0 ruff errors
  Owner: Amelia (Developer)
```

### Option C: 그대로 두고 Story 4.2 진행 (비권장)

- 7 pre-existing failures 그대로 둔 채 Story 4.2 dev-story 진행
- Story 4.2 dev-story 완료 시 pre-existing failures는 여전히 fail
- Epic 4 회고에서 8건 일괄 처리 (Option A와 동일)
- **위험**: Story 4.2/4.3/4.4 dev-story 중 pre-existing failures와 새 failures 구분 어려움 (CR 1.1 lesson)

## 권고: Option A (Epic 4 회고 시 1 action item)

**근거**:
1. Epic 1+2+3 회고 패턴과 일치 (lightweight ~25분 회고 시 pre-existing failures 한 번에 정리)
2. Story 4.2 dev-story 시작 전 F-5/F-6/F-7/F-8만 처리 (4건 = 1 hour) — **즉시 가능** (block-on)
3. F-3/F-4 (architecture decisions) + F-2 (DB schema sync) — Epic 4 회고 시 Charlie (Senior Dev) + Alice (Product Owner)와 결정
4. Story 4.2 + 4.3 + 4.4 완료 후 Epic 4 회고 시점에 0 pre-existing failures 상태 보장

**즉시 실행 (Story 4.2 T0, 1 hour)**:
- F-1 PT011 — Amelia (1 min)
- F-5 cp949 encoding pin — Amelia (15 min)
- F-6/7/8 STACK_PIN.yaml sync — Amelia (15 min)
- F-2 alembic 0008 re-sync — Amelia (30 min)

**Epic 4 회고 시 결정 필요**:
- F-3 architecture decision (re-export vs allowlist) — Charlie
- F-4 services leak refactor — Amelia + Alice (priority)

## 다음 단계

1. **즉시** (Story 4.2 T0): F-1/F-2/F-5/F-6/F-7/F-8 처리 (1 hour, Amelia)
2. **Story 4.2 dev-story 시작**: T1~T7 (기존 spec 그대로)
3. **Story 4.2 완료 시점**: F-3/F-4 architecture decision + fix (2-4 hours, Amelia + Charlie)
4. **Epic 4 회고 시**: 본 문서를 action item source로 사용, "Pre-existing infra failures 일괄 정리" 1 action item으로 close
5. **Story 4.3 + 4.4 dev-story**: 0 pre-existing failures 상태에서 진행 (CR 1.1 lesson — pre-existing vs new failure 구분 명확)

## References

- Story 4.1 SDR (AI) findings F-4 ~ F-11 — `_bmad-output/implementation-artifacts/4-1-pure-cost-engine-no-i-o-no-clock.md` §Senior Developer Review (AI)
- Epic 1 회고 A1~A4 follow-through — `_bmad-output/implementation-artifacts/epic-1-retro-2026-08-01.md`
- Epic 2 회고 A1~A4 follow-through — `_bmad-output/implementation-artifacts/epic-2-retro-2026-08-01.md`
- Epic 3 회고 A1~A5 follow-through — `_bmad-output/implementation-artifacts/epic-3-retro-2026-08-02.md`
- CR 0.3 lesson — STACK_PIN must match installed — memory `cr-0-3-lessons`
- CR 0.4 lesson — PowerShell Out-File cp949 + ruff PT rules — memory `cr-0-4-lessons`
- CR 1.1 lesson — pre-existing vs new failure distinction — memory `cr-1-1-lessons`
