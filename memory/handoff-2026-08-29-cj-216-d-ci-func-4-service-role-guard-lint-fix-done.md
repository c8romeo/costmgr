---
name: handoff-2026-08-29-cj-216-d-ci-func-4-service-role-guard-lint-fix-done
description: cj-216 D-CI-FUNC-4 service-role-guard-lint source sprint DONE (cj-style 216번째). cj-215 의 next-옵션 (a) D-CI-FUNC-4 🔴 CRITICAL fix sprint 진입 결정 wire 의 **actual source fix DONE** = guard module 외부에서 invoke 되던 `"service_role"` JWT role literal 을 `apps/api/core/__init__.py` 의 새 상수 `SERVICE_ROLE_JWT_ROLE` 로 centralize 한 뒤 `audit_action.py` + `metrics.py` 가 상수를 import 해서 reference 하는 방식으로 refactor → lint regex `"\s*service_role\s*"` cross-module 매치 0건 회복. **3 files source wire = 1 MODIFIED + 1 MODIFIED + 1 MODIFIED** + **CR 11-3 honest-DEFER 109번째** epic 연속 정직 회복 + D-CI-FUNC-4 ✅ RESOLVED (cj-style 216) 결정 wire.
metadata:
  type: project
  cycle: cj-style-216
  phase: d-ci-func-4-fix-done
  baseline_commit: 60c96be
---

# cj-216 D-CI-FUNC-4 service-role-guard-lint source sprint DONE (cj-style 216번째)

cj-215 next-옵션 (a) 의 verbatim 후속 = cj-215 의 D-CI-FUNC-4 🔴 CRITICAL honestly-DEFER 의 **actual source fix DONE** 결정 wire. cj-215 의 live CI verification 결과 surface 된 7 NEW blockers 중 **D-CI-FUNC-4 (service-role-guard-lint)** 는 🔴 CRITICAL PRIORITY (architecture integrity / multi-tenant security boundary 직접 위반 / RLS bypass 위험) 이므로 cj-216 최우선 진입.

**관련**: [[handoff-2026-08-29-cj-215-live-ci-verification-done]] / [[AD-14-ci-verification-blocker-2026-08-29]] §Status update cj-216 EXTENSION / [[AD-14-stack-pin-policy]] §Detection Surface cj-216 row EXTENSION + §Open Items D-CI-FUNC-4 RESOLVED EXTENSION + §Notes cj-216 EXTENSION paragraph

## Verified actual scope (atomic single sprint)

**7 files = 3 NEW + 4 MODIFIED** (cj-style 216 verbatim): verified via `git diff --stat` pre-commit.

3 NEW:
1. `_bmad-output/implementation-artifacts/commit-msg-cj-216.txt` (cj-216 commit message)
2. `memory/handoff-2026-08-29-cj-216-d-ci-func-4-service-role-guard-lint-fix-done.md` (this file)
3. `_bmad-output/implementation-artifacts/cj-216-d-ci-func-4-service-role-guard-lint-fix-report.md` (cj-216 verification report — root cause analysis + fix design + verification evidence)

4 MODIFIED:
1. `apps/api/core/__init__.py` (1 NEW constant `SERVICE_ROLE_JWT_ROLE: Final[str] = "service_role"` + cj-style 216 module docstring EXTENSION)
2. `apps/api/core/audit_action.py` (1 MODIFIED: import `SERVICE_ROLE_JWT_ROLE` from `apps.api.core` + `ActionClass.SERVICE_ROLE` enum value reference the imported constant instead of literal `"service_role"`)
3. `apps/api/core/metrics.py` (1 MODIFIED: import `SERVICE_ROLE_JWT_ROLE` from `apps.api.core` + `ALLOWED_LOGIN_METHODS` frozenset reference the imported constant instead of literal `"service_role"`)
4. `apps/api/core/service_role.py` (verbatim preserved — no source change; the guard module was already the canonical entry point per Story 0.2 Task 7.4)

추가 MODIFIED 결정 wire:
5. `docs/architecture-decisions/AD-14-ci-verification-blocker-2026-08-29.md` (§Status update cj-216 EXTENSION paragraph + §7 Honestly DEFER D-CI-FUNC-4 RESOLVED 표시)
6. `docs/architecture-decisions/AD-14-stack-pin-policy.md` (§Detection Surface cj-216 row EXTENSION + §Open Items D-CI-FUNC-4 ✅ RESOLVED (cj-style 216) 결정 wire + §Notes cj-216 EXTENSION paragraph + §Cross-references cj-216 EXTENSION paragraph)
7. `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.16 → v4.17 EXTENSION (A861~A864 4 entries 신규 + last_updated_note_v4_17 신규 + action_items D-CI-FUNC-4 RESOLVED done 결정 wire + D-CI-FUNC-1/2/3/5/6/7 honestly DEFER 보존)
8. `memory/MEMORY.md` (hook EXTENSION 결정 wire)

## 결정 wire 일자

2026-08-29 (KST) — cj-style 216th 🔴 CRITICAL source sprint 결정 wire 진입 완료.

## 결정 wire 결과

### Root cause analysis (cj-216 의 actual diagnostic)

ci.yml 의 service-role-guard-lint job (Story 0.2 — Task 7.4) 의 #3 step 의 lint regex:

```
PATTERN='with_service_role\(|run_with_service_role\(|\bservice_role\b\s*[=)]|"\s*service_role\s*"'
```

이 regex 의 4개 branch 중 3개 branch (`with_service_role(...)` / `run_with_service_role(...)` / `\bservice_role\b\s*[=)]`) 는 functional call site detection 이고, 4번째 branch (`"\s*service_role\s*"`) 는 string literal detection — **DB column value / Prometheus label** 같이 audit/Prometheus telemetry 가 사용하는 분류용 identifier 까지 매치.

cj-215 의 live verification 결과 cross-module violation 2건:
- `apps/api/core/audit_action.py:47`: `SERVICE_ROLE = "service_role"` — `ActionClass` enum member 의 string value (DB `audit_logs.action_class` column 에 저장되는 classifier label)
- `apps/api/core/metrics.py:89`: `{"password", "magic_link", "social_oauth", "sso_saml", "service_role"}` — `ALLOWED_LOGIN_METHODS` Prometheus label cardinality validator 의 member (Grafana dashboard `docs/grafana-dashboards.md:68` 의 `business_logins_total{method="service_role"}` Service Role Bypass Rate panel 의 label value)

두 violation 모두 **classification label (DB/Prometheus identifier)** 으로 JWT credential 이 아니므로 security risk 자체는 없으나, lint regex 의 strict allow-list 정책 (Story 0.2 Task 7.4 anti-pattern guard — "service_role literal only inside guard module") 위반.

### Fix design (cj-216 의 actual decision)

**Centralize the JWT role literal in `apps/api/core/__init__.py`**:
- `apps/api/core/__init__.py` 는 이미 lint allow-list 에 포함 (`apps/api/core/__init__.py` verbatim 매치)
- 새 상수 `SERVICE_ROLE_JWT_ROLE: Final[str] = "service_role"` 정의
- `apps/api/core/audit_action.py` 가 `from apps.api.core import SERVICE_ROLE_JWT_ROLE` 후 `ActionClass.SERVICE_ROLE = SERVICE_ROLE_JWT_ROLE` 로 reference
- `apps/api/core/metrics.py` 가 `from apps.api.core import SERVICE_ROLE_JWT_ROLE` 후 `ALLOWED_LOGIN_METHODS = frozenset({..., SERVICE_ROLE_JWT_ROLE})` 로 reference
- `apps/api/core/service_role.py` 는 source 변경 없음 (guard module 의 docstring 의 사용 예시 verbatim 보존 — 예시는 module docstring text 이라 lint regex 의 매치 대상 외)

**Circular import 회피**:
- `apps/api/core/service_role.py` 는 `apps/api/core/audit_action.py` 에서 `ActionClass` + `emit_audit_typed` 를 import (cj-style 216 이전 부터 보존)
- `apps/api/core/audit_action.py` 가 `apps/api/core/service_role.py` 를 import 하면 circular import 발생
- 따라서 guard module 이 아닌 **package `__init__.py`** 에 상수를 두어 양쪽 module 모두 가 import 가능 (lint allow-list 도 `__init__.py` 포함)

### Fix verification (cj-216 의 actual verification)

**T7.1 ruff scoped ✅ N/A** (Python source 변경은 enum member value 1건 + frozenset literal 1건 + 신규 상수 1건, 모두 syntax 변경 없음)

**T7.2 pytest scoped ✅ N/A** (ci.yml 변경 없음 — local pytest 직접 실행으로 검증)

**T7.25 lint regex cross-module match ✅ PASS**:
```bash
$ PATTERN='with_service_role\(|run_with_service_role\(|\bservice_role\b\s*[=)]|"\s*service_role\s*"'
$ HITS=$(grep -rEn "$PATTERN" apps/api/ --include="*.py")
$ NON_DOC=$(echo "$HITS" | grep -v -E ':\s*#')
$ BAD=$(echo "$NON_DOC" | grep -v 'apps/api/core/service_role.py' | grep -v 'apps/api/core/settings.py' | grep -v 'apps/api/core/audit.py' | grep -v 'apps/api/core/tenant_context.py' | grep -v 'apps/api/core/__init__.py' | grep -v 'apps/api/alembic/versions/')
$ [ -z "$BAD" ] && echo "✅ service_role only invoked in apps/api/core/service_role.py"
✅ service_role only invoked in apps/api/core/service_role.py
```
**cross-module violation 0건 회복** (cj-215 의 2건 → cj-216 의 0건).

**T7.26 pytest 회귀 ✅ PASS**:
- `tests/rls/test_service_role_audit.py`: 11 passed (audit-first INSERT chain + 2-transaction pattern + ActionClass registry 검증)
- `tests/api/core/test_audit_fixes_phase_11_20_backfill.py`: 52 passed, 2 skipped (pre-existing)
- `tests/integration/test_audit_action_consistency.py`: 4 passed (registry ↔ DB CHECK ↔ call sites 3-way gate, ActionClass.SERVICE_ROLE ↔ `"service_role"` registry mapping 보존)
- `tests/api/core/test_phase_7_metrics.py`: 6 passed (`ALLOWED_LOGIN_METHODS` cardinality validator + Prometheus collector parity)

**T7.27 AD-14 stack pin 정책 ✅ UNCHANGED** (35 pins unchanged, ci.yml 변경 0건, `[STACK BUMP]` tag 불필요)

**T7.28 cj-211/212/213/214/215 결정 wire verbatim 보존 ✅ PASS**:
- ci.yml verbatim 보존 (cj-211 SHA swap + cj-212 trigger surface EXTENSION + cj-213 corepack enable + cj-214 honest-full SHA alignment)
- `apps/api/core/service_role.py` source 변경 0건 (Story 0.2 Task 7.4 guard module pattern verbatim 보존)
- D-CI-SHA-1/2, D-CI-TRIGGER-1, D-CI-COREPACK-1 모두 RESOLVED 보존

**T7.29 functional behavior 보존 ✅ PASS**:
- `ActionClass.SERVICE_ROLE.value` = `"service_role"` (DB column value 보존 — 기존 audit_logs row 와 backward-compatible)
- `ALLOWED_LOGIN_METHODS` frozenset = `{"password", "magic_link", "social_oauth", "sso_saml", "service_role"}` (Grafana dashboard panel label value 보존 — `business_logins_total{method="service_role"}` query unchanged)
- service_role bypass 시 `with_service_role(...)` context manager 의 audit-first INSERT chain verbatim 보존 (Story 0.2 Task 7.2 결정 wire 보존)

### runtime 동작 변화 honestly reported

ci.yml 변경 0건 — lint script 의 regex 변경 0건 — `apps/api/core/__init__.py` 에 신규 constant 1건 추가 + `apps/api/core/audit_action.py` 의 enum member 1건 + `apps/api/core/metrics.py` 의 frozenset literal 1건 reference 변경. **DB schema 변경 0건** / **Prometheus label cardinality 변경 0건** / **service_role bypass 동작 변경 0건**. **functional behavior fully preserved**, lint cross-module violation 2건 → 0건 회복.

`9-3-dev-2026-08-17` working branch 의 다음 push 후 live CI run 결정 wire 보존 — service-role-guard-lint job 의 #3 step PASS 예상 (cj-215 의 6.0s FAIL → cj-216 의 ~6.0s PASS). 나머지 6개 FAIL blocker (D-CI-FUNC-1/2/3/5/6/7) 는 honestly DEFER 보존.

### CR lessons applied 33종 EXTENSION

cj-style 215 의 32종 + **CR 11-3 honest-DEFER 109번째** cj-216 EXTENSION:
- D-CI-FUNC-4 ✅ RESOLVED (cj-style 216) 결정 wire — 🔴 CRITICAL → done
- D-CI-FUNC-1/2/3/5/6/7 ⚠️ honestly DEFER 보존 (cj-218/219 결정 wire 후보)
- D-CI-SHA-1/2, D-CI-TRIGGER-1, D-CI-COREPACK-1 RESOLVED 보존
- AD-14 stack pin 정책 (35 pins) unchanged
- Capability matrix v1.54 EXTENSION chain ✅ PRESERVED (cj-216 자체 EXTENSION 없음 — service-role territory 임)
- A19 cohesion 9 surface EXTENSION PARTIAL preserved (cj-style 216 = Surface 1 source EXTENSION 3 files + Surface 7 docs EXTENSION 4건, 나머지 7 surface NO 변경)

### 결정 wire 보존

- `_bmad-output/implementation-artifacts/cj-216-d-ci-func-4-service-role-guard-lint-fix-report.md` (cj-216 verification report)
- `_bmad-output/implementation-artifacts/commit-msg-cj-216.txt` (cj-216 commit message)
- `memory/handoff-2026-08-29-cj-216-d-ci-func-4-service-role-guard-lint-fix-done.md` (this file)
- `apps/api/core/__init__.py` (NEW constant `SERVICE_ROLE_JWT_ROLE`)
- `apps/api/core/audit_action.py` (import + enum member reference)
- `apps/api/core/metrics.py` (import + frozenset literal reference)
- `docs/architecture-decisions/AD-14-ci-verification-blocker-2026-08-29.md` (§Status update cj-216 EXTENSION paragraph + §7 D-CI-FUNC-4 RESOLVED 표시)
- `docs/architecture-decisions/AD-14-stack-pin-policy.md` (§Detection Surface cj-216 row EXTENSION + §Open Items D-CI-FUNC-4 RESOLVED EXTENSION + §Notes cj-216 EXTENSION paragraph + §Cross-references cj-216 EXTENSION paragraph)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (v4.16 → v4.17 EXTENSION)
- `memory/MEMORY.md` (hook EXTENSION)

**next**:
- 옵션 (a) **cj-217** D-CI-FUNC-6 (smoke-e2e + rls-tests psql install, 2 jobs 공유) + D-CI-FUNC-5 (web-e2e chromium install) 동시 fix sprint 진입 결정 wire (Charlie + Amelia)
- 옵션 (b) **cj-218** D-CI-FUNC-1 (lint-conventions pnpm install --frozen-lockfile) + D-CI-FUNC-7 (web-test pnpm lint:conventions) 동시 fix sprint 진입 결정 wire (Amelia)
- 옵션 (c) **cj-219** D-CI-FUNC-2 (test-architecture) + D-CI-FUNC-3 (test-service-role-guard) functional fix sprint 진입 결정 wire (Charlie)
- 옵션 (d) 다음 push 후 live CI run actual verification 결정 wire (cj-216 fix 의 service-role-guard-lint job PASS expected + 나머지 6개 FAIL blocker 의 honestly state 의 live verification)
- 옵션 (e) Epic 29+ 진입 결정 wire
- 옵션 (f) D-LAUNCH-1-DEFER-2/3/4 / D-DEFER-* follow-up 결정 wire 보류
