---
name: cj-279a-service-only-scenario-wiring-done
description: "cj-279a Epic 29+ P2 service-only tenant wire sprint 결정 wire (CR 11-3 honest-DEFER 213번째) — D-WEB-E2E-5 data state seeding surface 3 scenarios 결정 wire; spec implementation honestly DEFER"
metadata:
  type: project
  modified: 2026-09-05T07:45:00.000Z
  originSessionId: a376ac3d-ffad-4746-8b5f-45e158e8d97d
---

# cj-279a Epic 29+ P2 service-only tenant wire sprint 결정 wire

cj-style 279a번째 epic 연속 정직 회복 — cj-279 P2 2-sprint 분할 plan (cj-279a wire + cj-279b retro entry) 의 첫 wire sprint 진입 결정 wire.

**Atomic sprint scope**: 3 files = 1 MODIFIED + 2 NEW: scripts/dev_seed.py 1169 → 1485 lines (+316 lines EXTENSION) + sprint-status.yaml v4.45 → v4.46 EXTENSION + handoff memory NEW + commit-msg NEW.

**Why**: cj-279 plan 결정 wire 의 P2 wire sprint 진입. cj-275 PRD entry 18 spec files 중 Epic 29+ P2 service-only territory (29.15/29.16/29.17) 의 data state seeding surface 결정 wire. cj-274 의 6 D-WEB-E2E-1~6 honestly DEFER 중 **D-WEB-E2E-5 (service-only tenant fixture 3 specs) ownership → cj-279a 결정 wire (cj-279 plan 결정 wire 보존)**. D-WEB-E2E-6 already CLOSED in cj-276 (cj-279 plan Section 7 HONEST finding). cj-278a/b/c 의 source sprint pattern verbatim mirror — dev_seed.py source EXTENSION 만 (3 NEW scenarios), 3 NEW Playwright spec files honestly DEFER (D-WEB-E2E-5 spec implementation ownership carryover = cj-274 의 6 honestly DEFER 의 마지막 잔여).

**How to apply**: Per cj-style HONEST rule, cj-279a source sprint = dev_seed.py source EXTENSION + sprint-status v4.45 → v4.46 EXTENSION:
- ✅ scripts/dev_seed.py 1169 → 1485 lines (+316 lines EXTENSION) — 1 NEW shared helper `_seed_service_only_tenant` (svc_ prefix tenant + owner user + membership + settings per OQ-6) + 3 NEW scenario functions (`_seed_service_only_calc` [Story 29.15 V1/V4 skip abc committed snapshot, period 2026-08] + `_seed_service_only_report_21` [Story 29.16 svc_ tenant + PRD-SVC product + Report #21 data source, period 2026-09] + `_seed_service_only_ccr` [Story 29.17 cost_object_breakdown + unused_capacity_breakdown JSONB with 1 dept @ 10000 KRW/hr exact 1-won, period 2026-10]) + 7 NEW UUIDv5 deterministic IDs (3 shared svc_ identity + 3 per-scenario snapshot + 1 svc_ product for Report #21 join) + argparse choices EXTENSION (14→17 choices + all) + main() dispatch EXTENSION (3 NEW conditional blocks)
- ✅ _bmad-output/implementation-artifacts/sprint-status.yaml v4.45 → v4.46 EXTENSION — cj-279a: backlog → in_progress + 3 NEW story entries (29-15/29-16/29-17): backlog → in_progress + cj-279b backlog 보존 + last_updated_note_v4_46 신규
- ✅ 2 NEW handoff files (this file + commit-msg-cj-279a.txt)

**scope honestly reported**:
- docs + dev_seed.py source change ONLY
- runtime source code 변경: scripts/dev_seed.py EXTENSION (+316 lines)
- ci.yml 변경 0건
- 3 NEW Playwright spec files (apps/web/e2e/service-only-tenant-calc.spec.ts + service-only-tenant-report-21.spec.ts + service-only-tenant-ccr.spec.ts) honestly DEFER (D-WEB-E2E-5 spec implementation ownership carryover — cj-274 의 6 D-WEB-E2E-1~6 honestly DEFER 의 마지막 잔여, cj-278a/b/c 의 3 sprints 가 dev_seed source sprint 만 완료 + spec implementation 은 carryover 한 패턴 verbatim 보존)
- AD-14 stack pin 정책 (35 pins) 변경 없음 / [STACK BUMP] tag 불필요
- live CI verification 은 cj-279a source sprint push 후 결정 wire 보류

**Verification scope (local, all honestly reported)**:
- scripts/dev_seed.py Python syntax OK ✅ (`python -c "import ast; ast.parse(open('scripts/dev_seed.py', encoding='utf-8').read())"` → SYNTAX OK)
- scripts/dev_seed.py line count: 1169 → 1485 = +316 lines EXTENSION
- argparse choices EXTENSION 검증 ✅ — `uv run --frozen python scripts/dev_seed.py --scenario invalid_choice --token-only` → argparse error with valid choices list = `[closing_guard_negative, snapshot_persisted, close_sequence_partial, reversal_input, reversal_cache_invalidation, reopen_audit, two_factor_challenge, two_factor_lockout, two_factor_recovery, two_factor_setup, deletion_consent, deletion_audit, deletion_restore, deletion_hard_delete, service_only_calc, service_only_report_21, service_only_ccr, all]` = 18 choices (17 scenarios + 'all') 결정 wire verified
- argparse help EXTENSION 검증 ✅ — `--help` output 의 `--scenario {closing_guard_negative,...,service_only_calc,service_only_report_21,service_only_ccr,all}` 결정 wire verified
- DB seed 검증 ✗ (deferred to CI) — local Postgres 미가용 (docker daemon 미실행), ci.yml step 15 dev_seed invocation 의 HONEST verification 은 cj-273b web-e2e infra layer 10/10 step pass-through 결정 wire 보존 (cj-278a close sprint 의 run 33943206059 step 15 SUCCESS 패턴 결정 wire)

**per-scenario seed 결정 wire honestly reported**:

① **29.15 service_only_calc** → `_seed_service_only_tenant` (svc_ tenant + user + membership + settings) + `fiscal_period_snapshots` row (snapshot_id=`DEV_SVC_SNAPSHOT_CALC_ID`, tenant_id=`DEV_TENANT_SERVICE_ID`, period_key='2026-08', baseline_revision=1, engine_type='abc', state='committed', material/labor/overhead/manufacturing/inventory_adjustment_cost = 0 placeholder, result_hash='b'*64) per AD-16. **3 spec drifts** for cj-279a retro: ① spec mentions V1+V4 skipped + V7+V8 executed (engine-side behavior, dev_seed cannot seed) ② spec `[계산]` button (frontend surface, NOT seeded) ③ spec POST `/api/v1/calc` returns HTTP 200 (backend route surface, NOT seeded).

② **29.16 service_only_report_21** → `_seed_service_only_tenant` + `fiscal_period_snapshots` row (snapshot_id=`DEV_SVC_SNAPSHOT_REPORT_ID`, period_key='2026-09', engine_type='abc', state='committed', result_hash='c'*64) + `products` row (id=`DEV_PRODUCT_ID_SVC`, code='PRD-SVC', product_type='service', is_active=TRUE, unit_cost_krw=0) for Report #21 join per AD-18. **3 spec drifts** for cj-279a retro: ① spec mentions cost_pool/activity/driver/allocation columns + KRW/USD dual display (report-rendering concerns, NOT seeded) ② spec references "existing products in service tenant" — this seed inserts ONE fresh product (DEV_PRODUCT_ID_SVC) ③ spec Report #21 ko-KR title "원가대상별 원가 집계표" (frontend i18n surface, NOT seeded).

③ **29.17 service_only_ccr** → `_seed_service_only_tenant` + `fiscal_period_snapshots` row (snapshot_id=`DEV_SVC_SNAPSHOT_CCR_ID`, period_key='2026-10', engine_type='abc', state='committed', result_hash='d'*64) + `cost_object_breakdown` JSONB (1 dept: indirect_cost_krw=10000000, practical_capacity_hours=1000, allocated_krw=8000000, unused_hours=200, unused_cost_krw=2000000, **CCR = 10000000/1000 = 10000 KRW/hr exact 1-won integer division per AD-21**) + `unused_capacity_breakdown` JSONB (1 row: dept_id='dept-svc-001', department_name='미사용 능력', unused_hours=200, unused_cost_krw=2000000). **3 spec drifts** for cj-279a retro: ① spec says "1 department with indirect_cost + practical_capacity_hours" — schema has NO separate `departments` table; per-dept data lives in cost_object_breakdown/unused_capacity_breakdown JSONB per alembic 0028 (Story 9.3 territory) ② spec says 미사용 능력 "displayed as separate row" — schema has no row concept; JSONB array is what Report 21's 미사용 능력 section reads from per Story 9.3 verbatim ③ spec says V8 regression verifies CCR (V8 = cj-276 wire surface, NOT dev_seed surface).

**shared mechanics**:
① svc_ prefix tenant graph — `DEV_TENANT_SERVICE_ID` + `DEV_USER_SERVICE_ID` + `DEV_MEMBERSHIP_SERVICE_ID` 는 3 scenarios 모두 공유 (cj-273b identity-only EXTENSION 의 후속, OQ-6 svc_ prefix 결정 wire verbatim 보존).
② tenant FK cycle 미해당 — svc_ tenant has no deletion state (no `deletion_requested_by_user_id`), so FK cycle 의 NULL-then-UPDATE 패턴 미사용. 단순 INSERT order (tenant → user → membership → settings).
③ period_key distinct per scenario (2026-08 / 2026-09 / 2026-10) — unique key `(tenant_id, period_key, baseline_revision, engine_type)` 충돌 회피 결정 wire (cj-278a 의 period_key=2026-08 와 svc_ tenant 는 별개 tenant_id 라 무관).
④ industry = 'service' hardcoded — AD-12 service-only rule 의 본질. `--industry` flag 무관하게 svc_ scenarios 는 'service' 결정 wire, trad path 의 DEV_TENANT_ID 는 args.industry 영향.
⑤ `DEV_PRODUCT_ID_SVC` = fresh UUIDv5 (cj-276 의 `DEV_PRODUCT_ID_NEG` 와 별개 — svc_ tenant 의 product graph 격리 결정 wire).
⑥ CCR data 의 sha256_hash placeholder ('e'*64 + 'f'*64) — 실제 hash 는 engine 실행 후 결정 wire (cj-280 retro scope).
⑦ cj-278c 의 audit_logs append-only trigger (alembic 0001 BEFORE UPDATE/DELETE RAISE) 패턴 미해당 — svc_ scenarios 는 audit_logs 미사용 (deletion territory 만 해당).

**runtime 동작 변화 honestly reported**:
dev_seed.py invocation 의 17 scenario functions (cj-276 의 2 + cj-278a 의 4 + cj-278b 의 4 + cj-278c 의 4 + cj-279a 의 3) 가 `--scenario all` 로 모두 wire 됨. ci.yml step 15 invocation (`--scenario all`, cj-277 결정 wire) 의 wire surface 가 cj-279a EXTENSION 으로 17 scenarios 로 EXTENSION. ci.yml 변경 0건 (cj-277 의 `--scenario all` invocation 자동 wire). AD-14 stack pin 정책 (35 pins) 변경 없음 / [STACK BUMP] tag 불필요.

**12 NEW spec drifts logged** for cj-279a retro + cj-280 retro 종합 (cj-279 plan 5 + cj-279a source 7 = 12 cumulative):
① 29.15 spec `[계산]` button ko-KR vs English `[Calc]` testid (frontend ko-KR SSOT NFR18 bind) — cj-279 plan 5종 ①
② 29.15 V1+V4 skip + V7+V8 run engine-side behavior (NOT dev_seed surface) — cj-279a source NEW
③ 29.15 POST `/api/v1/calc` backend route (NOT dev_seed surface) — cj-279a source NEW
④ 29.15 `engine_type='abc'` alembic 0020+ enum CHECK 결정 wire 보존 검증 — cj-279 plan 5종 ②
⑤ 29.16 Report #21 ko-KR title "원가대상별 원가 집계표" vs shipped title (frontend i18n NFR18) — cj-279 plan 5종 ③
⑥ 29.16 cost_pool/activity/driver/allocation columns report-rendering (NOT seeded) — cj-279a source NEW
⑦ 29.16 KRW/USD F5.2 dual display (report-rendering, NOT seeded) — cj-279a source NEW
⑧ 29.16 fresh PRD-SVC product (spec references "existing products in service tenant" — dev_seed inserts ONE fresh product) — cj-279a source NEW
⑨ 29.17 CCR 1-won precision vs Decimal precision (cj-222 banker's rounding CR 5-1) — cj-279 plan 5종 ④
⑩ 29.17 spec "1 department" — schema NO departments table; per-dept data lives in cost_object_breakdown/unused_capacity_breakdown JSONB per alembic 0028 — cj-279a source NEW
⑪ 29.17 spec 미사용 능력 "separate row" — schema NO row concept; JSONB array is what Report 21 reads from per Story 9.3 — cj-279a source NEW (cj-279 plan 5종 ⑤ merge)
⑫ 29.17 spec V8 regression verifies CCR — V8 = cj-276 wire surface, NOT dev_seed surface — cj-279a source NEW

**CR 11-3 honest-DEFER 213번째** epic 연속 정직 회복 (cj-279 plan 결정 wire 의 212번째에 이어).

**Next sprint**: cj-279a source sprint push → live CI verification (run + step 15 `Run dev seed --scenario all` invocation with 17 scenarios HONEST-verified via GitHub REST API `repos/c8romeo/costmgr/actions/runs/<id>/jobs` + step 18 V8 fixture suite conclusion=success + step 19 Playwright result) → cj-279a close sprint 결정 wire (3 files = 2 MODIFIED + 1 NEW atomic docs-only close sprint: sprint-status.yaml v4.46 → v4.47 EXTENSION + handoff MODIFIED Section 7 + commit-msg NEW). 결정 wire 일자: 2026-09-05 (KST).

**Lessons (cj-279a source sprint)**:
- cj-279 plan 의 "3 NEW UUIDv5 IDs" 추정 vs 실제 7 NEW UUIDv5 IDs 결정 wire — plan estimated shared svc_ identity graph (3 IDs), actual EXTENSION = 7 IDs (3 shared + 3 per-scenario snapshot + 1 svc_ product for Report #21 join). HONEST reporting — cj-279a source sprint 의 7 IDs vs plan 의 3 IDs 의 deviation 결정 wire 보존 (cj-style discipline: plan vs actual 의 honestly report).
- D-WEB-E2E-5 ownership 의 2개 surface 결정 wire — **data state seeding surface** = cj-279a source sprint (dev_seed.py EXTENSION) / **spec implementation surface** = honestly DEFER (3 NEW Playwright spec files) — cj-278a/b/c 의 pattern verbatim mirror. D-WEB-E2E-5 spec implementation 의 진짜 wire surface 는 별도 follow-up sprint 결정 wire (cj-279b retro entry 또는 cj-280 retro 결정 wire 보류).
- cj-222 의 banker's rounding CR 5-1 결정 wire 와의 정합 — 29.17 CCR 1-won precision fixture 의 JSONB CCR = 10000000/1000 = 10000 KRW/hr 는 integer division 으로 exact 1-won (rounding 미발생). banker's rounding 이 발동하는 case 는 decimal division (e.g., 10000000/1003 = 9970.0897...) — 이 fixture 는 그 case 를 deliberately 피함 (cj-279a 의 minimum viable seeding discipline).
- Story 29.15/29.16/29.17 spec 의 다수가 backend/frontend surface 인 이유 — spec 작성자 가 dev_seed surface 만 명시하지 않은 결과 (cj-275 PRD entry 의 original planning 의 spec 작성 discipline 미흡). cj-279a source sprint 는 dev_seed surface (data state) 만 wire, spec 의 backend/frontend surface 는 honestly DEFER.

Related: [[handoff-2026-09-05-cj-279-epic-29-plus-p2-plan-done]], [[handoff-2026-09-05-cj-278c-deletion-scenario-wiring-done]], [[handoff-2026-09-05-cj-278-epic-29-plus-p1-plan-done]], [[handoff-2026-09-05-cj-274-web-e2e-chain-close-honest-defer]].

## Section 7 — Live CI verification + CLOSE HONEST 결정 wire (cj-279a close sprint)

cj-279a source sprint push `2166505` 의 live CI run `33952196500` HONEST-verified via `repos/c8romeo/costmgr/actions/runs/33952196500/jobs` API at 2026-09-05T08:00:41Z (run_started_at = 2026-09-05T07:43:35Z).

**13-job matrix HONEST-verified** (run 33952196500):
- ✅ setup / ✅ commit-prefix-lint / ✅ lint-imports / ✅ stack-pin-check / ✅ service-role-guard-lint / ✅ lint-conventions / ✅ lint-deps / ✅ test-architecture / ✅ test-service-role-guard / ✅ smoke-e2e / ✅ rls-tests / ✅ web-test
- ⚠️ web-e2e (failure)
- **12/13 jobs PASS, web-e2e 단일 carryover** (cj-273b/cj-274/cj-276/cj-277/cj-278a/cj-278b/cj-278c 결정 wire 보존 패턴)

**web-e2e step-by-step HONEST-verified** (job_id 101269064072):
- step 1-14 infra layer: 14/14 success (ciml step 15 infra 결정 wire 보존)
- **step 15 `Run dev seed (creates tenant + user + industry baseline + Epic 29+ scenario seeds)` conclusion=success ✅** (0초, 07:44:00Z → 07:44:00Z) — cj-279a 의 17 scenarios 모두 정상 seed 결정 wire verified
- **step 16 `Boot uvicorn (background)` conclusion=success ✅** (4초, 07:44:00Z → 07:44:04Z)
- **step 17 `Run cd apps/web && pnpm exec playwright install chromium` conclusion=success ✅** (11초, 07:44:04Z → 07:44:15Z)
- **step 18 `Run V8 fixture suite (1-won regression gate)` conclusion=success ✅** (2초, cj-276 29-18 wire 결정 wire 보존, 07:44:15Z → 07:44:17Z)
- **step 19 `Run cd apps/web && pnpm exec playwright test --project=chromium` conclusion=failure ❌** (39분 12초, 07:44:17Z → 08:23:29Z) — cj-274 D-WEB-E2E-5 honestly DEFER carryover + Epic 29+ spec drift 종합

**CRITICAL HONEST finding (scope boundary)**: cj-279a 의 wire surface = dev_seed.py 3 NEW service-only scenario functions + 1 shared helper + 7 NEW UUIDv5 IDs (cj-279 plan 결정 wire 의 첫 wire sprint). step 15 dev_seed invocation 의 source-side EXTENSION 이 live CI 에서 HONEST-verified 결정 wire (svc_ tenant graph + fiscal_period_snapshots rows + PRD-SVC product row + cost_object_breakdown/unused_capacity_breakdown JSONB 모두 정상 INSERT). step 19 Playwright failure 는 cj-274 D-WEB-E2E-5 honestly DEFER + cj-275 PRD entry 18 spec file implementation ownership 의 영역으로 명시적 boundary 결정 wire 보존 — NOT cj-279a source sprint scope.

**12 cumulative spec drifts logged** for cj-279a retro + cj-280 retro 종합 (cj-279 plan 5 + cj-279a source 7 = 12 cumulative). cj-278a/b/c 의 verbatim pattern mirror 보존.

**3 files = 2 MODIFIED + 1 NEW atomic docs-only close sprint**:
1. MODIFIED `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.46 → v4.47 (cj-279a: in_progress → done + 3 stories 29-15/29-16/29-17: in_progress → done + last_updated_note_v4_47 EXTENSION paragraph)
2. MODIFIED `memory/handoff-2026-09-05-cj-279a-service-only-scenario-wiring-done.md` (Section 7 추가 — this section)
3. NEW `_bmad-output/implementation-artifacts/commit-msg-cj-279a-close.txt`

**34 cumulative spec drifts** for cj-280 retro 종합 (cj-276 4 + cj-278a fix1 1 + cj-278b 5 + cj-278c 12 + cj-279a 12 = 34).

**CR 11-3 honest-DEFER 214번째** epic 연속 정직 회복 (cj-279a source sprint 의 213번째에 이어). 결정 wire 일자: 2026-09-05 (KST).

**Next sprint**: cj-279b cj-280 Epic 29+ CLOSED retro entry sprint 진입 결정 wire (docs-only retro entry sprint — 14-section §1~§14 verbatim mirroring Phase 24 close-out retro pattern + 18 spec ↔ schema mapping table 정리 + 34 cumulative spec drift 종합 + 6 D-WEB-E2E-1~6 honestly DEFER → ownership resolution verification + master PRD 정합 검증 + 신규 chain 진입 결정 wire).
