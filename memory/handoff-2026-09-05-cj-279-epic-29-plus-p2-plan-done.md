---
name: cj-279-epic-29-plus-p2-plan-done
description: "cj-279 Epic 29+ P2 2-sprint 분할 plan 결정 wire (CR 11-3 honest-DEFER 212번째) — D-WEB-E2E-5 service-only tenant + cj-280 retro entry 결정 wire; D-WEB-E2E-6 V8 runner already CLOSED in cj-276 (HONEST finding)"
metadata:
  type: project
  modified: 2026-09-05T07:30:00.000Z
  originSessionId: a376ac3d-ffad-4746-8b5f-45e158e8d97d
---

# cj-279 Epic 29+ P2 2-sprint 분할 plan 결정 wire

cj-style 279번째 epic 연속 정직 회복 — cj-278 plan (3-sprint 분할 4+4+4 = m11/2FA/deletion) 의 P1 wire 3 sprint 모두 CLOSED HONEST 후속 = Epic 29+ P2 wire sprint 진입 결정 wire.

**Atomic sprint scope**: 2 files = 1 MODIFIED + 1 NEW: sprint-status.yaml v4.44 → v4.45 EXTENSION (2 NEW entries + comment block + last_updated_note_v4_45) + handoff memory NEW.

**Why**: cj-274 honestly DEFERRED 6 D-WEB-E2E-1~6 to Epic 29+. cj-275 PRD entry 18 spec files 결정 wire. cj-276 P0 minimum viable wire (29.1 closing-guard + 29.3 snapshot persistence + **29.18 V8 fixture runner** — D-WEB-E2E-6 absorbed into P0 sprint per original cj-275 PRD plan) + cj-277 OQ-3 dev_seed `--scenario all` wiring + cj-278 P1 3-sprint 분할 plan + cj-278a m11 wire + cj-278b 2FA wire + cj-278c deletion wire 5-sprint chain 모두 CLOSED HONEST (cj-276/cj-278a/b/c 12/13 jobs PASS + 1 web-e2e step-19 carryover 패턴 결정 wire 보존). cj-278c close sprint 결정 wire (`bc58b42`) 의 live CI run `33950467090` HONEST-verified via `repos/c8romeo/costmgr/actions/runs/33950467090/jobs` API at 2026-09-05T06:55:02Z: step 15 dev_seed invocation 14 scenarios 모두 정상 seed 결정 wire. cj-279 = Epic 29+ P2 wire sprint 진입 결정 wire.

**How to apply**: Per cj-style HONEST rule, cj-279 is scoped as **docs-only entry plan sprint** (mirroring cj-278 entry plan pattern):
- ✅ sprint-status.yaml v4.44 → v4.45 EXTENSION — cj-279: backlog 신규 entry + cj-279a: backlog 신규 entry + cj-279b: backlog 신규 entry + 3 NEW story entries (29-15-service-only-tenant-calc + 29-16-service-only-tenant-report-21 + 29-17-service-only-tenant-ccr) + 36-line comment block (cj-279 P2 2-sprint 분할 plan + per-sprint dev_seed scenario function list + OQ-6 svc_ prefix 결정 + dev_seed CLI flag EXTENSION 결정 + D-WEB-E2E-5/6 ownership honestly 결정) + last_updated_note_v4_45 신규
- ✅ 2 NEW handoff files (this file + commit-msg-cj-279.txt)

**CRITICAL HONEST finding** (cj-style discipline 보존): **D-WEB-E2E-6 (V8 fixture runner) was ALREADY CLOSED in cj-276 P0** — sprint-status v4.35+ 의 `29-18-v8-fixture-runner: done # cj-276 — .github/workflows/ci.yml web-e2e job V8 step EXTENSION (-m v8_regression BEFORE playwright test) ✅ HONEST-verified via run 33936056936 step 18 conclusion=success` verbatim 보존. Story 29.18 spec file `_bmad-output/implementation-artifacts/epic-29-plus-18-v8-fixture-runner.md` 의 `wire_sprint: "cj-276 (Sprint 1, P0 minimum viable)"` field 도 cj-275 PRD entry sprint 의 original plan 결정 wire 보존. D-WEB-E2E-6 = `apps/web/e2e/...` spec file 미존재 (Story 29.18 = ci.yml EXTENSION 만, dev_seed 미사용) → "V8 fixture runner 1 spec" = "V8 fixture runner ci.yml step" = cj-276 wire surface 결정 wire 보존. **cj-279 의 actual wire scope = D-WEB-E2E-5 service-only tenant fixture ONLY** (3 stories 29.15/29.16/29.17). 결정 wire 일자: 2026-09-05 (KST).

**P2 2-sprint 분할 결정 wire** (cj-278 3-sprint 분할 plan 의 pattern verbatim 보존):
- **cj-279a**: D-WEB-E2E-5 service-only tenant wire sprint — Stories 29.15 (service-only V1/V4 skip calc) + 29.16 (service-only Report #21) + 29.17 (service-only CCR 1-won precision). dev_seed.py EXTENSION: 3 NEW scenario functions (`_seed_service_only_calc` + `_seed_service_only_report_21` + `_seed_service_only_ccr`) + 1 NEW CLI flag (`--industry service` 또는 별도 `--service-only` flag — cj-273b identity-only EXTENSION 의 후속) + OQ-6 svc_ prefix for service-only tenant_id. backend surface: service-only industry engine path (apps/api/modules/m1_industry/service/ 또는 packages/services/m5_engine/service_only/) + Report #21 (apps/api/modules/m5_reports/) + CCR (M9 CCRPort.compute per AD-21). Playwright spec surface: 3 NEW spec files (apps/web/e2e/service-only-tenant-calc.spec.ts + apps/web/e2e/service-only-tenant-report-21.spec.ts + apps/web/e2e/service-only-tenant-ccr.spec.ts) per OQ-5 4-shard 균등 분할 — service-only 3 specs add to web-e2e runtime.
- **cj-279b**: cj-280 Epic 29+ CLOSED retro entry sprint — docs-only retro entry sprint (14-section §1~§14 verbatim mirroring Phase 24 close-out retro `phase-24-close-out-2026-08-27.md` pattern verbatim). scope: 18 spec ↔ schema mapping table 정리 (cj-276/cj-278a/b/c 의 24 spec drifts 종합) + 6 D-WEB-E2E-1~6 honestly DEFER → ownership resolution verification + master PRD 정합 검증 + 신규 chain 진입 결정 wire (cj-style chain post-Epic 29+ CLOSED 다음).
- **cj-280**: 별도 sprint (cj-279 plan 결정 wire 외부) — Epic 29+ CLOSED retro 결정 wire sprint.

**rationale 5종**:
1. **atomic 단위 = 3 stories** (cj-276 P0 의 3 stories 와 동일 magnitude — cj-style atomic single sprint discipline 보존)
2. **domain cohesion** (cj-279a service-only = 1 backend module m1_industry/service + 1 report module m5_reports + 1 CCR port m9_ccr — 모두 service industry path 의 EXTENSION 으로 자연스러움)
3. **per-sprint rollback 가능** (1 sprint = 1 commit = 1 rollback unit)
4. **per-sprint HONEST verification granularity** (cj-278 의 3-sprint 분할 의 4+4+4 와 동일 discipline 보존)
5. **cj-279b 를 docs-only retro entry 로 배치** — cj-279a wire sprint 의 12 spec drift + 24 cumulative spec drift 의 정리는 별도 docs-only sprint 에서 (cj-280 의 retro decision wire 의 사전 정리)

**D-WEB-E2E-5 ownership absorbed**: cj-274 의 6 D-WEB-E2E-1~6 honestly DEFER 중 D-WEB-E2E-5 (service-only tenant fixture 3 specs) → cj-279a 결정 wire (cj-279 plan 결정 wire 보존). **D-WEB-E2E-6 (V8 fixture runner) → cj-276 결정 wire 보존 (cj-275 PRD entry 의 original plan)** — cj-279 의 P2 wire scope 에는 미포함 (cj-276 P0 의 29-18 wire 가 이미 결정 wire).

**OQ-6 결정** (cj-275 PRD OQ 보류 → cj-279 진입 시 결정): service-only tenant_id prefix = `svc_` (별도 prefix 로 격리 — cj-273b dev_seed identity-only EXTENSION 의 후속). 결정 근거: 5종: ① svc_ prefix 로 `--scenario service_only_calc` invocation 시 별도 tenant 격리 (DEV_TENANT_ID = trad tenant 와 분리) ② spec 명세의 `tenant_id='svc_TEN-001'` 와 dev_seed 의 svc_ prefix 일치 (Epic 29+ PRD §4.5 가정 verbatim 보존) ③ per-spec fixture isolation (다른 13 scenarios 와 cross-contamination 회피) ④ audit_logs 결정 surface 에서 svc_ prefix 로 service-only events 필터링 가능 ⑤ Report #21 + CCR 1-won 의 engine_state 분리 (service vs trad 경로). 결정 wire 일자: 2026-09-05 (KST).

**dev_seed CLI flag EXTENSION 결정** (cj-273b identity-only EXTENSION 의 후속): scripts/dev_seed.py 의 argparse choices EXTENSION — cj-278c 의 14 choices + 'all' → cj-279a 의 17 choices + 'all' (3 NEW service-only scenarios 추가). 별도 `--industry service` flag 또는 `--service-only` flag EXTENSION 결정 wire 보류 (cj-279a 진입 시 review). 결정 근거: minimal-scope EXTENSION (기존 argparse 결정 wire 보존 + 3 NEW choices EXTENSION 만), cj-273b 의 identity-only EXTENSION 의 후속 (cj-274 chain CLOSED 후 첫 industry-specific EXTENSION).

**Spec naming 결정 wire 보존** (cj-278 Option 2 결정 wire verbatim): Epic 29+ spec_file_path (예: service-only-tenant-calc.spec.ts) 가 기존 spec file (예: ???) 과 이름 mismatch → cj-280 retro 에서 mapping 결정 wire 보류. cj-279a 의 3 NEW Playwright spec files 는 Epic 29+ PRD spec_file_path 그대로 사용 결정 wire (service-only-tenant-calc.spec.ts + service-only-tenant-report-21.spec.ts + service-only-tenant-ccr.spec.ts). 기존 service-only spec file 의 부재 보존 (Epic 29+ 의 신규 domain territory).

**Verification scope** (local, all honestly reported):
- sprint-status.yaml syntax OK ✅ (YAML safe_load passed)
- sprint-status.yaml v4.45 EXTENSION: 2 NEW cj-279a/cj-279b entries + 3 NEW story entries + 36-line comment block + last_updated_note_v4_45 신규
- 5 spec drifts logged for cj-279a retro (services-only territory 의 potential spec drifts):
  ① 29.15 spec says `[계산]` button (ko-KR) but UI may use English `[Calc]` 또는 별도 testid — frontend ko-KR SSOT 의 NFR18 bind 후 cj-279a source sprint 에서 검증
  ② 29.15 spec says `engine_type='abc'` but schema uses `engine_type` enum column — alembic 0020+ 결정 wire 보존 검증
  ③ 29.16 spec says Report #21 "원가대対象별 원가 집계표" (ko-KR per NFR18) but shipped Report #21 의 title 결정 wire 보존 검증
  ④ 29.17 spec says CCR 1-won precision = no rounding error > 1 KRW but code uses Decimal precision = cj-222 의 banker's rounding CR 5-1 결정 wire 보존 검증
  ⑤ 29.17 spec says "미사용 능력 displayed as separate row" but no specific row schema — cj-279a source sprint 의 reporting component 검증

**scope honestly reported**: docs-only entry plan 결정 wire — runtime source code 변경 0건 (sprint-status.yaml + handoff memory only). ci.yml 변경 0건. AD-14 stack pin 정책 (35 pins) 변경 없음 / [STACK BUMP] tag 불필요. live CI verification 은 cj-279a source sprint push 후 결정 wire 보류.

**runtime 동작 변화 honestly reported**: 0건 (docs-only sprint — dev_seed.py / ci.yml / spec files / backend / frontend 변경 0건).

**CLOSED ✅ HONEST 결정 wire** — cj-279 의 entry plan 결정 wire (cj-279a service-only wire sprint + cj-279b retro entry sprint + cj-280 별도 retro 결정 wire) 결정 wire 보존. cj-278 3-sprint 분할 plan 의 verbatim pattern 미러 (cj-279a + cj-279b = 2 sprints, cj-278a/b/c = 3 sprints — 동일 docs-only entry plan 결정 wire 보존).

**CR 11-3 honest-DEFER 212번째** epic 연속 정직 회복 (cj-278c close sprint 의 211번째에 이어).

**Next sprint**: cj-279a service-only wire sprint 진입 결정 wire — dev_seed.py EXTENSION 3 NEW scenarios (_seed_service_only_calc + _seed_service_only_report_21 + _seed_service_only_ccr) + 3 NEW UUIDv5 deterministic IDs (svc_ prefix) + argparse choices EXTENSION (14→17 choices) + main() dispatch EXTENSION (3 NEW conditional blocks) + 3 NEW Playwright spec files (service-only-tenant-calc.spec.ts + service-only-tenant-report-21.spec.ts + service-only-tenant-ccr.spec.ts) + sprint-status v4.45 → v4.46 EXTENSION.

**Lessons (cj-279 entry plan)**:
- cj-274 의 6 D-WEB-E2E-1~6 honestly DEFER 의 ownership 결정 wire 가 cj-276~cj-279 의 5 sprint chain 으로 모두 wire — D-WEB-E2E-1~4 (cj-276 + cj-278a + cj-278b + cj-278c) + D-WEB-E2E-5 (cj-279a pending) + D-WEB-E2E-6 (cj-276 P0 에서 absorbed). cj-274 의 honest-DEFER 의 FRONT-END 결정 surface 모두 wire 결정 wire 보존.
- cj-278 plan 의 3-sprint 분할 pattern 의 verbatim 미러 — 1 entry plan sprint + N wire sprints 의 결정 wire discipline. cj-279 의 2-sprint 분할 (cj-279a wire + cj-279b retro entry) 도 동일 pattern 보존 (cj-278 3-sprint 분할 의 reduced 2-sprint version).
- Story 29.18 (V8 fixture runner) 의 cj-276 P0 absorption 결정 wire 보존 — cj-275 PRD entry sprint 의 original wire sprint plan 의 P0 minimum viable 결정 wire (cj-275 PRD entry 의 wire sprints plan 의 1st entry = cj-276 P0 = 3 stories 29.1+29.3+29.18) 의 verbatim 보존. cj-279 P2 의 wire scope = 3 service-only stories (D-WEB-E2E-5) + D-WEB-E2E-6 이미 CLOSED.
- OQ-6 svc_ prefix 결정 wire 의 5 근거 (격리 + spec 일치 + cross-contamination 회피 + audit 필터링 + engine_state 분리) — OQ 결정 discipline 보존 (Epic 29+ PRD §0 OQ 가정 → cj-279 진입 시 결정).

**Why: How to apply**: cj-279 = Epic 29+ P2 wire sprint entry decision wire (docs-only). P2 2-sprint 분할 (cj-279a wire + cj-279b retro entry). D-WEB-E2E-5 ownership → cj-279a. D-WEB-E2E-6 already CLOSED in cj-276 P0 (HONEST finding). OQ-6 svc_ prefix 결정 wire. dev_seed CLI flag EXTENSION 결정 wire 보류 (cj-279a 진입 시 review). Related: [[handoff-2026-09-05-cj-278c-deletion-scenario-wiring-done]], [[handoff-2026-09-05-cj-278-epic-29-plus-p1-plan-done]], [[handoff-2026-09-05-cj-276-epic-29-plus-p0-minimum-viable-closed]], [[handoff-2026-09-05-cj-275-epic-29-plus-prd-entry-sprint-done]], [[handoff-2026-09-05-cj-274-web-e2e-chain-close-honest-defer]].

## Section 7 — CRITICAL HONEST finding (D-WEB-E2E-6 boundary)

**D-WEB-E2E-6 (V8 fixture runner) ownership boundary**: cj-274 의 6 D-WEB-E2E-1~6 honestly DEFER 의 D-WEB-E2E-6 → cj-275 PRD entry sprint 의 wire sprint plan 의 P0 minimum viable (cj-276) 결정 wire 보존. cj-276 atomic single sprint 결과 (run 33936056936 step 18 V8 fixture suite conclusion=success ✅ HONEST-verified via repos/c8romeo/costmgr/actions/runs/33936056936/jobs API at 2026-09-05T02:24:59Z) 로 D-WEB-E2E-6 ownership → cj-276 결정 wire.

**sprint-status v4.35+ 보존 verbatim**:
- `29-18-v8-fixture-runner: done # cj-276 — .github/workflows/ci.yml web-e2e job V8 step EXTENSION (-m v8_regression BEFORE playwright test) ✅ HONEST-verified via run 33936056936 step 18 conclusion=success`
- Story 29.18 spec file metadata 의 `wire_sprint: "cj-276 (Sprint 1, P0 minimum viable)"` 결정 wire 보존
- dev_seed_scenario: "N/A (V8 fixture 별도, dev_seed 미사용)" 결정 wire 보존 (V8 = ci.yml EXTENSION, no dev_seed, no spec file)
- spec_file_path: "N/A (ci.yml EXTENSION, no spec file)" 결정 wire 보존

**boundary 결정 wire**: D-WEB-E2E-6 의 spec 명세 (`apps/web/e2e/v8-fixture-runner.spec.ts` 등) 부재 — Story 29.18 는 ci.yml EXTENSION 만 (V8 pytest invocation step BEFORE Playwright execution per Epic 29+ PRD §4.6). 따라서 cj-279 P2 wire scope 에 D-WEB-E2E-6 미포함.

**cj-279 P2 actual wire scope = 3 stories** (D-WEB-E2E-5 service-only tenant fixture ONLY):
- Story 29.15 (D-WEB-E2E-5 1/3) — service-only V1/V4 skip calc
- Story 29.16 (D-WEB-E2E-5 2/3) — service-only Report #21
- Story 29.17 (D-WEB-E2E-5 3/3) — service-only CCR 1-won precision

**story 29.18 status 결정 wire**: `29-18-v8-fixture-runner: done` (cj-276 P0 결정 wire 보존) — cj-279 의 development_status 에 신규 entry 미추가 (cj-276 에서 이미 done 결정 wire).

Related: [[handoff-2026-09-05-cj-276-epic-29-plus-p0-minimum-viable-closed]].
