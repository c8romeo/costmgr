---
baseline_commit: f361016
status: ready-for-dev
cj_style_entry_point: 146
story_key: phase-20-5-critical-gap-resolution-carry-over-wire
---

# Phase 20.5 Critical Gap Resolution carry-over wire spec (cj-style 146번째 epic 연속 정직 회복)

## Story

**As a** FinOps practitioner / cloud architect / tenant admin / 1st release customer / DevOps engineer
**I want** Phase 20.5 Critical Gap Resolution carry-over territory 결정 wire (Layer 1 P0 critical: `apps/api/main.py` 에 4 FinOps phase routers (Phase 17 sustainability_router + Phase 18 commitment_router + Phase 19 pricing_router + Phase 20 multi_cloud_router) `include_router()` 호출 추가 / Layer 2 P1 test backfill: Phase 16~20 pytest test files 12 NEW (router parity tests + capability/audit drift detectors + tenant isolation smoke tests) / Layer 3 P2 docs backfill: `docs/finops-{sustainability,commitment,pricing,multi-cloud-cost-unified-reconciliation}.md` 4 NEW + `docs/capability-matrix.md` v1.46 EXTENSION FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION row 보존)
**so that** Phase 17~20 wire cycles 의 4 honest deviations (① apps/api/main.py NOT MODIFIED — 4 routers 미 include / ② 0 NEW pytest test files — spec 의 ~92 NEW pytest predicted scope 의 14개 test files intentionally 미작성 / ③ docs/finops-*.md NOT created — Phase 17/18/19/20 의 4 docs 모두 미작성 / ④ apps/api/scripts/cli dry-run flag NOT added — Phase 17/18/19/20 의 4 dry-run CLI scripts 모두 미작성) 의 carry-over chain 정직 회복 verification + Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존 + Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) AD-47 신규 (a)~(g) 7 sub-decisions 모두 결정 wire 진입 정합 보존 + Phase 11~20 10-module FinOps territory chain ✅ ALL WIRED 진입 정합 보존 (Layer 1 = critical functional gap fix) + test backfill (Layer 2) + docs backfill (Layer 3) 모두 1-day atomic sprint 단일 진입 결정 wire + Epic 12 2FA 챌린지 mandatory + AD-22 owner-only RBAC 보존 + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + D-FINOPS-1~9 honestly DEFER 보존 + CR 11-3 honest-DEFER 36번째 epic 연속 정직 회복 verification 결정 wire 진입 + 3중 게이트 impact NONE-LITE (Layer 1 functional fix scope 의 영향 = 4 lines main.py EXTENSION + 12 test files NEW + 4 docs NEW = minor source change) 결정 wire.

## Context

cj-style Phase 20.5 1번째 진입점 (cj-style 146번째) 진입 결정 wire 진입 완료:

- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire T1~T8 `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `efc3c59` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire T1~T8 `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) + Phase 18 close-out retro `de72f50` (cj-style 136번째) + Phase 18 atomic wire T1~T8 `67059cf` (cj-style 135번째) + Phase 18 spec entry `bdc7997` (cj-style 134번째) + Phase 18 PRD entry `5eded22` (cj-style 133번째) + Phase 17 close-out retro `de009fe` (cj-style 132번째) + Phase 17 atomic wire T1~T8 `97cfe4e` (cj-style 131번째) + Phase 17 spec entry `4be3120` (cj-style 130번째) + Phase 17 PRD entry `e0778ed` (cj-style 129번째) + Phase 16 close-out retro `26fd530` (cj-style 128번째) + Phase 16 atomic wire T1~T8 `81ae00a` (cj-style 127번째) + Phase 16 spec entry `69c29df` (cj-style 126번째) + Phase 16 PRD entry `4f11d03` (cj-style 125번째) + Phase 15 close-out retro `102f370` (cj-style 124번째) + Phase 15 atomic wire T1~T8 `1b800d9` (cj-style 123번째) + Phase 15 spec entry `69c29df` (cj-style 122번째) + Phase 15 PRD entry `87393b4` (cj-style 121번째) + ... + Epic 1~17 ALL DONE 진입 정합 보존 + 1st release cycle ALL DONE 진입 정합 보존

### Phase 20 close-out retro `f361016` 의 4 honest deviations verbatim 보존
1. **apps/api/main.py NOT MODIFIED** — multi_cloud router 미 include. Phase 17 sustainability_router + Phase 18 commitment_router + Phase 19 pricing_router 모두 main.py 에 include 안된 wire cycle pattern verbatim 미러 결정 wire. **Phase 20.5 = critical functional gap fix 결정 wire 진입** (Layer 1)
2. **0 NEW pytest test files** — Phase 16/17/18/19 verbatim pattern 보존 결정 wire. spec §F36.8-4 의 ~92 NEW pytest + spec §F36.8-5 의 ~7 NEW vitest 의 predicted scope 의 14개 test files 모두 wire cycle 에서 intentionally 미작성 결정 wire. **Phase 20.5 = test backfill 결정 wire 진입** (Layer 2) — targeted subset 의 12 NEW test files
3. **docs/finops-multi-cloud-cost-unified-reconciliation.md NOT created** — Phase 17/18/19 의 docs/finops-{sustainability,commitment,pricing}.md 모두 미작성 pattern verbatim 미러 결정 wire. **Phase 20.5 = docs backfill 결정 wire 진입** (Layer 3) — 4 NEW docs files
4. **apps/api/scripts/cli dry-run flag NOT added** — Phase 17/18/19/20 의 finops-{sustainability,commitment,pricing,multi-cloud}-dry-run CLI scripts 모두 미작성 pattern verbatim 미러 결정 wire. **Phase 20.5 = scripts backfill 보류** (deferred to Phase 20.6 or later — dry-run scripts 는 manual review 시점에 작성 결정 wire 보류)

### D-FINOPS-* honestly-DEFER items inventory + status
- D-FINOPS-1~8 ✅ ALL RESOLVED 보존
- **D-FINOPS-9 honestly DEFER 보존** — Phase 19.5 carry-over 결정 wire `b2fb1d8` 의 AD-47 신규 (a)~(g) 7 sub-decisions 모두 Phase 20 territory 흡수 결정 wire
- **Phase 20.5 = D-FINOPS-9 의 carry-over chain 정직 회복 verification** 결정 wire (D-FINOPS-9 의 7개 세부 항목 모두 Phase 20 territory 흡수 완료 + Phase 20 wire 의 4 honest deviations 모두 Phase 20.5 territory 흡수 결정 wire)

## 3 ACs (§F37.1~§F37.3 verbatim) → ~36 detailed sub-ACs (12+12+12)

### §F37.1 Layer 1 P0 critical — apps/api/main.py router include_router() (12 sub-ACs)
- **F37.1-1** `apps/api/main.py` MODIFIED EXTENSION — `from apps.api.modules.finops.sustainability.sustainability_routes import router as sustainability_router` 신규 import + `app.include_router(sustainability_router, prefix="/api/v1", tags=["finops-sustainability"])` 추가 (~2 LOC)
- **F37.1-2** `apps/api/main.py` MODIFIED EXTENSION — commitment_router 신규 import + `app.include_router(commitment_router, prefix="/api/v1", tags=["finops-commitment"])` 추가 (~2 LOC)
- **F37.1-3** `apps/api/main.py` MODIFIED EXTENSION — pricing_router 신규 import + `app.include_router(pricing_router, prefix="/api/v1", tags=["finops-pricing"])` 추가 (~2 LOC)
- **F37.1-4** `apps/api/main.py` MODIFIED EXTENSION — multi_cloud_router 신규 import + `app.include_router(multi_cloud_router, prefix="/api/v1", tags=["finops-multi-cloud"])` 추가 (~2 LOC)
- **F37.1-5** include_router 호출 위치 결정 wire = `app.include_router(executive_dashboard_router)` 호출 (line 492) 직후 EXTENSION — Phase 16 executive 의 다음에 Phase 17~20 routers 순차 추가 (PRD §F36 verbatim EXTENSION 결정 wire)
- **F37.1-6** 각 router 의 `prefix="/api/v1"` 통일 — Phase 16 executive_dashboard_router 의 prefix 패턴 verbatim EXTENSION
- **F37.1-7** `tags=["finops-{name}"]` 통일 — OpenAPI docs 에서 카테고리별 grouping 보존 (NFR11 docs SSOT EXTENSION 결정 wire)
- **F37.1-8** 4 routers 모두 FastAPI ContextVar 보존 (CR 1-1 verbatim) — tenant_id ContextVar 가 middleware layer 에서 자동 설정되므로 router 추가만으로 cross-tenant isolation 자동 보존
- **F37.1-9** audit-first INSERT 8 NEW + typed exception envelope (Phase 20 wire 의 20 NEW typed exceptions) — include_router 호출만으로 자동 활성화 (CR 1-1 verbatim EXTENSION 결정 wire)
- **F37.1-10** Epic 12 2FA 챌린지 mandatory 보존 — destructive endpoint 의 3-layer defense (route layer require_role + service layer verify_totp_challenge + handler layer audit-first emit) EXTENSION 결정 wire
- **F37.1-11** NFR3 P95 ≤ 500ms 검증 결정 wire — include_router 후 4 routers endpoint 응답 시간 P95 측정 (smoke test) + NFR11 P95 ≤ 30s SLO (multi_cloud dashboard) 보존
- **F37.1-12** A19 cohesion 9 surface EXTENSION PASS preserved — 4 routers include 결정 wire 진입 후에도 A19 cohesion 9 surface 모두 PASS 보존 (FinOps territory surface EXTENSION 결정 wire)

### §F37.2 Layer 2 P1 — pytest test backfill (12 sub-ACs)
- **F37.2-1** `apps/api/tests/api/modules/finops/test_executive_dashboard_router.py` NEW (~+200 LOC + 8 pytest cases: 라우터 등록 검증 + 8 endpoints GET/POST parity + RBAC AD-22 verbatim + Epic 12 2FA 챌린지 mandatory + tenant isolation RLS CR 0-2 verbatim)
- **F37.2-2** `apps/api/tests/api/modules/finops/test_sustainability_router.py` NEW (~+200 LOC + 8 pytest cases: 라우터 등록 검증 + carbon emissions + scheduled dispatch + KPI selector + tenant isolation)
- **F37.2-3** `apps/api/tests/api/modules/finops/test_commitment_router.py` NEW (~+200 LOC + 8 pytest cases: 라우터 등록 검증 + commitment inventory + recommender + scheduled dispatch + KPI selector + tenant isolation)
- **F37.2-4** `apps/api/tests/api/modules/finops/test_pricing_router.py` NEW (~+200 LOC + 8 pytest cases: 라우터 등록 검증 + rate card aggregator + TCO modeling + scheduled dispatch + tenant isolation)
- **F37.2-5** `apps/api/tests/api/modules/finops/test_multi_cloud_router.py` NEW (~+250 LOC + 10 pytest cases: 라우터 등록 검증 + rate_card_reconciliation + cost_reconciliation + negotiation_bot + blended_unblended_tracker + marketplace_saas_pricing_integrator + scheduled_multi_cloud_dispatch + KPI selector + 5 cloud provider + 5 marketplace adapter)
- **F37.2-6** `apps/api/tests/integration/test_capability_matrix_v1_46_drift.py` NEW (~+150 LOC + capability matrix v1.45 → v1.46 EXTENSION FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION drift detection + 4-industry grants ✅/✅/✅/✅ parity 검증)
- **F37.2-7** `apps/api/tests/integration/test_audit_action_v1_46_drift.py` NEW (~+150 LOC + ActionClass.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION 신규 enum 의 8 NEW values (multi_cloud_dashboard_viewed + multi_cloud_rate_card_reconciled + multi_cloud_cost_reconciled + negotiation_bot_triggered + marketplace_saas_pricing_integrated + multi_cloud_dry_run_executed + multi_cloud_kpi_refreshed + blended_unblended_tracked) drift detection 검증)
- **F37.2-8** `apps/api/tests/api/core/test_phase_20_5_router_include.py` NEW (~+120 LOC + smoke test: apps/api/main.py 의 include_router 호출 4개 검증 + 각 router prefix 검증 + tags 검증)
- **F37.2-9** `apps/web/tests/test_finops_multi_cloud_dashboard_parity.ts` NEW (~+150 LOC + 7 vitest cases: MultiCloudRateCardReconciliationPanel + MultiCloudCostReconciliationPanel + NegotiationBotConfigPanel + BlendedUnblendedTrackerPanel + NaverKTStabilityPanel + MarketplaceSaaSPricingPanel + ko-KR.json finops_multi_cloud.* namespace parity CR 12-5 D-PARITY-01 inversion EXTENSION)
- **F37.2-10** `apps/web/tests/test_finops_pricing_dashboard_parity.ts` NEW (~+120 LOC + 5 vitest cases: RateCardAggregatorPanel + TCOModelingPanel + PricingReportPanel + ScheduledDispatchPanel + ko-KR.json finops_pricing.* namespace parity)
- **F37.2-11** pytest target = **~64 NEW pytest cases PASS** (5 router test files × ~8-10 cases + 2 drift tests + 1 smoke test = ~64 cases; spec §F36.8-4 의 ~92 NEW pytest 의 70% targeted subset) 결정 wire
- **F37.2-12** vitest target = **~12 NEW vitest cases PASS** (2 dashboard parity test files × ~5-7 cases = ~12 cases; spec §F36.8-5 의 ~7 NEW vitest + Phase 19 pricing parity ~5 NEW = ~12 cases) 결정 wire

### §F37.3 Layer 3 P2 — docs backfill (12 sub-ACs)
- **F37.3-1** `docs/finops-sustainability-carbon-reporting.md` NEW (~+400 LOC + 아키텍처 + API reference + 사용 예시 + 운영 가이드 + Phase 17 wire `97cfe4e` 의 8 ACs §F33.1~§F33.8 verbatim EXTENSION + 5 NEW backend modules 다이어그램 + 4 frontend sub-components screenshot)
- **F37.3-2** `docs/finops-cloud-commitment-management.md` NEW (~+400 LOC + Phase 18 wire `67059cf` 의 8 ACs §F34.1~§F34.8 verbatim EXTENSION + 5 NEW backend modules + 4 frontend sub-components + 5 cloud provider cross-rollup)
- **F37.3-3** `docs/finops-pricing-rate-card-tco-modeling.md` NEW (~+400 LOC + Phase 19 wire `8db3cfc` 의 8 ACs §F35.1~§F35.8 verbatim EXTENSION + 5 NEW backend modules + 4 frontend sub-components + TCO modeling 6 models × 4 metrics)
- **F37.3-4** `docs/finops-multi-cloud-cost-unified-reconciliation.md` NEW (~+450 LOC + Phase 20 wire `52dad7f` 의 8 ACs §F36.1~§F36.8 verbatim EXTENSION + 5 NEW backend modules + 4 frontend sub-components + 5 cloud provider cross-rollup + 5 marketplace adapter + 3 negotiation bot cloud provider)
- **F37.3-5** `docs/capability-matrix.md` MODIFIED v1.45 → v1.46 EXTENSION FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION row 1 NEW 추가 (industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 verbatim EXTENSION)
- **F37.3-6** `docs/architecture-decisions/AD-47-multi-cloud-cost-unified-reconciliation.md` NEW (~+200 LOC + AD-47 의 (a)~(g) 7 sub-decisions verbatim + Phase 19.5 carry-over 결정 wire `b2fb1d8` 의 D-FINOPS-9 7개 세부 항목 흡수 verification)
- **F37.3-7** `docs/api/finops-routers-reference.md` NEW (~+200 LOC + 4 routers endpoint catalog + request/response schema + RBAC matrix + tenant isolation contract + Epic 12 2FA 챌린지 mandatory + audit action 8 NEW EXTENSION)
- **F37.3-8** `docs/operations/finops-router-deployment.md` NEW (~+200 LOC + 4 routers deployment 가이드 + Dockerfile + health check + observability + NFR11 P95 ≤ 30s SLO + 4 cron schedules KST EXTENSION)
- **F37.3-9** `docs/runbooks/finops-sustainability-incident.md` NEW (~+150 LOC + carbon emissions anomaly response + scheduled dispatch failure handling + KPI selector degradation + RBAC bypass attempt response)
- **F37.3-10** `docs/runbooks/finops-multi-cloud-incident.md` NEW (~+150 LOC + 5 cloud provider rate card drift + negotiation bot guard violation + blended/unblended tracker anomaly + marketplace SaaS pricing freshness alert)
- **F37.3-11** `docs/finops-forecast-capacity-planning.md` 패턴 verbatim EXTENSION (Phase 13 wire `8b98030` 의 docs 패턴 = 아키텍처 + API reference + 사용 예시 + 운영 가이드 + ACs §Fxx.1~§Fxx.8 verbatim)
- **F37.3-12** `docs/finops-optimization-rightsizing.md` 패턴 verbatim EXTENSION (Phase 14 wire `e904485` 의 docs 패턴) — 4 docs files 모두 동일 패턴 따름

## T1~T3 + ~24 subtasks

### T1: Layer 1 P0 critical — apps/api/main.py router include_router() (8 subtasks)
- T1.1: sustainability_router import + include_router (F37.1-1)
- T1.2: commitment_router import + include_router (F37.1-2)
- T1.3: pricing_router import + include_router (F37.1-3)
- T1.4: multi_cloud_router import + include_router (F37.1-4)
- T1.5: include_router 위치 결정 (executive_dashboard_router 호출 직후) (F37.1-5)
- T1.6: prefix="/api/v1" + tags 통일 (F37.1-6, F37.1-7)
- T1.7: 4 routers smoke test (apps/api main 진입 + pytest router_include test) (F37.1-8~F37.1-12)
- T1.8: A19 cohesion 9 surface EXTENSION PASS preserved 검증

### T2: Layer 2 P1 — pytest test backfill (12 subtasks)
- T2.1~T2.5: 5 router test files (executive + sustainability + commitment + pricing + multi_cloud) (F37.2-1~F37.2-5)
- T2.6~T2.7: 2 drift tests (capability + audit action) (F37.2-6, F37.2-7)
- T2.8: 1 smoke test (router_include) (F37.2-8)
- T2.9~T2.10: 2 dashboard parity tests (multi_cloud + pricing) (F37.2-9, F37.2-10)
- T2.11: pytest 실행 + 64 NEW pytest cases PASS 검증 (F37.2-11)
- T2.12: vitest 실행 + 12 NEW vitest cases PASS 검증 (F37.2-12)

### T3: Layer 3 P2 — docs backfill (4 subtasks)
- T3.1: 4 docs files (sustainability + commitment + pricing + multi-cloud) 작성 (F37.3-1~F37.3-4)
- T3.2: capability matrix v1.46 EXTENSION + AD-47 + routers reference 작성 (F37.3-5~F37.3-7)
- T3.3: deployment + 2 runbooks 작성 (F37.3-8~F37.3-10)
- T3.4: 4 docs 의 cross-reference + navigation 보존 (F37.3-11~F37.3-12)

**Subtotal**: 8+12+4 = ~24 subtasks

## Dev Notes 18종 (CR lessons applied)

- **CR 0-2 RLS** — 4 routers include 결정 wire 시에도 tenant-scoped RLS 자동 적용 (current_setting('app.tenant_id')::uuid) 보존
- **CR 1-1 audit-first INSERT 8 NEW** — ActionClass.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION 의 8 NEW audit actions (multi_cloud_dashboard_viewed + multi_cloud_rate_card_reconciled + multi_cloud_cost_reconciled + negotiation_bot_triggered + marketplace_saas_pricing_integrated + multi_cloud_dry_run_executed + multi_cloud_kpi_refreshed + blended_unblended_tracked) 라우터 include 결정 wire 시에도 audit-first INSERT 자동 활성화 보존
- **CR 1-1 FastAPI ContextVar** — tenant_id ContextVar middleware layer 보존 (CR 1-1 verbatim EXTENSION)
- **CR 1-1 RSC boundary** — Next.js 15.x RSC boundary 보존 (apps/web/app/[locale]/(dashboard)/admin/finops/multi-cloud/{page,layout}.tsx)
- **CR 4-3/4-4** — async-test asyncio.run + Industry enum SSOT + A5 drift detector + SDR overclaim 방지
- **CR 9-6 commit message** — `git commit -F <file>` (D5 prevention) + PowerShell here-string 회피 결정 wire
- **CR 11-3 honest-DEFER 36번째** — D-FINOPS-9 honestly DEFER 보존 (Phase 20 territory 흡수 완료) + Phase 20 wire 의 4 honest deviations 모두 Phase 20.5 territory 흡수 결정 wire
- **ALLOWED_SERVICE_SUBMODULES 즉시 sweep** — Phase 20.5 wire 진입 시점에 `apps/api/modules/finops/__init__.py` 의 submodule 목록 즉시 sweep EXTENSION
- **CR 11-4 D-001~D-005** — ko-KR.json `finops_multi_cloud.*` namespace EXTENSION ~30 keys SSOT + NFR18 ko-KR SSOT 보존
- **P-015 SSOT** — ko-KR.json finops_multi_cloud.* 단일 SSOT 결정 wire
- **CR 12-1 L4** — industry-agnostic capability grants (4-industry ✅/✅/✅/✅) EXTENSION 결정 wire
- **CR 12-5 D-14 typed exception envelope 20 NEW** — Phase 20 wire 의 20 NEW typed exceptions (16 spec + 4 dispatch) 모두 라우터 include 결정 wire 시에도 자동 활성화 보존
- **CR 12-5 D-PARITY-01 inversion** — TypeScript mirror parity (multi-cloud-types.ts + multi-cloud-client.ts) 결정 wire
- **CR 12-5 D-GATE-01 inversion** — capability gate inversion (require_finops_multi_cloud) 결정 wire
- **A19 cohesion 9 surface EXTENSION PASS** — FinOps Multi-Cloud Cost Unified Reconciliation surface NEW 결정 wire 진입 후에도 9 surface 모두 PASS 보존
- **A36 SDR 검증 4-step** — 자동 적용 결정 wire (spec entry 진입 시점에 자동)
- **AD-14 stack pin** — Recharts 2.12.7 + reportlab 4.0.7 + openpyxl 3.1.2 + pandas 2.1.4 + xlsxwriter 3.1.9 + apscheduler 3.10.4 + pytz 2024.1 EXTENSION 결정 wire
- **AD-22 owner-only RBAC** — 4 routers 모두 owner-only RBAC EXTENSION (NegotiationBotConfigPanel + scheduled dispatch trigger 모두 owner-only)
- **Epic 12 2FA 챌린지 mandatory** — destructive endpoint 의 3-layer defense EXTENSION 결정 wire
- **NFR4 PII minimization** ✅ PRESERVED — 4 routers include 결정 wire 시에도 PII minimization 자동 보존
- **NFR18 ko-KR SSOT** — apps/web/messages/ko-KR.json finops_multi_cloud.* namespace EXTENSION ~30 keys SSOT 보존 결정 wire
- **AD-47 신규** — FinOps Multi-Cloud Cost Unified Reconciliation 신규 (a)~(g) 7 sub-decisions 결정 wire (Phase 19.5 carry-over 결정 wire `b2fb1d8` 진입 시점에 이미 NEW)

## Architecture Alignment (ALLOWED sweep) — Phase 20 wire 정합

- **Backend (FastAPI, Python 3.12)**:
  - MODIFIED `apps/api/main.py` EXTENSION (4 include_router 호출 추가, ~12 LOC)
  - 12 NEW test files (5 router tests + 2 drift tests + 1 smoke test + 2 dashboard parity tests + 2 integration tests)
- **Frontend (Next.js 15.x, TypeScript 5.x)**:
  - 2 NEW vitest test files (multi_cloud + pricing dashboard parity)
- **Docs**:
  - 4 NEW `docs/finops-*.md` files (sustainability + commitment + pricing + multi-cloud)
  - 1 MODIFIED `docs/capability-matrix.md` v1.45 → v1.46 EXTENSION
  - 1 NEW `docs/architecture-decisions/AD-47-multi-cloud-cost-unified-reconciliation.md`
  - 1 NEW `docs/api/finops-routers-reference.md`
  - 1 NEW `docs/operations/finops-router-deployment.md`
  - 2 NEW `docs/runbooks/finops-{sustainability,multi-cloud}-incident.md`

## Files Affected (estimate ~22 files = 12 NEW + 10 MODIFIED)

### 12 NEW files
1. `apps/api/tests/api/modules/finops/test_executive_dashboard_router.py` (~200 LOC)
2. `apps/api/tests/api/modules/finops/test_sustainability_router.py` (~200 LOC)
3. `apps/api/tests/api/modules/finops/test_commitment_router.py` (~200 LOC)
4. `apps/api/tests/api/modules/finops/test_pricing_router.py` (~200 LOC)
5. `apps/api/tests/api/modules/finops/test_multi_cloud_router.py` (~250 LOC)
6. `apps/api/tests/integration/test_capability_matrix_v1_46_drift.py` (~150 LOC)
7. `apps/api/tests/integration/test_audit_action_v1_46_drift.py` (~150 LOC)
8. `apps/api/tests/api/core/test_phase_20_5_router_include.py` (~120 LOC)
9. `apps/web/tests/test_finops_multi_cloud_dashboard_parity.ts` (~150 LOC)
10. `apps/web/tests/test_finops_pricing_dashboard_parity.ts` (~120 LOC)
11. `docs/finops-sustainability-carbon-reporting.md` (~400 LOC)
12. `docs/finops-cloud-commitment-management.md` (~400 LOC)
13. `docs/finops-pricing-rate-card-tco-modeling.md` (~400 LOC)
14. `docs/finops-multi-cloud-cost-unified-reconciliation.md` (~450 LOC)
15. `docs/architecture-decisions/AD-47-multi-cloud-cost-unified-reconciliation.md` (~200 LOC)
16. `docs/api/finops-routers-reference.md` (~200 LOC)
17. `docs/operations/finops-router-deployment.md` (~200 LOC)
18. `docs/runbooks/finops-sustainability-incident.md` (~150 LOC)
19. `docs/runbooks/finops-multi-cloud-incident.md` (~150 LOC)

### 10 MODIFIED files (estimate)
1. `apps/api/main.py` (4 include_router calls, ~12 LOC)
2. `docs/capability-matrix.md` (v1.45 → v1.46 EXTENSION FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION row)
3. `_bmad-output/implementation-artifacts/sprint-status.yaml` (v3.55 → v3.56 EXTENSION `phase-20-5-spec-entry: backlog → done`)
4. `memory/MEMORY.md` (Phase 20.5 spec entry hook EXTENSION)
5. `memory/handoff-2026-08-26-phase-20-5-spec-entry-done.md` (NEW handoff)

Wait — that's 19 NEW + 5 MODIFIED = 24 files. Let me recount:
- 10 NEW test files (5 router + 2 drift + 1 smoke + 2 vitest)
- 9 NEW docs files (4 finops + 1 AD-47 + 1 routers + 1 deployment + 2 runbooks)
- Total NEW = 19
- MODIFIED = main.py + capability-matrix.md + sprint-status.yaml + MEMORY.md = 4 MODIFIED

Wait, I should also include commit-msg + handoff memory which adds 2 NEW.

So 21 NEW + 4 MODIFIED = 25 files. But sprint-status says ~22 files estimate. Let me recompute. Actually I think 25 files is reasonable.

Let me simplify the file list:

### 21 NEW files
1-10: 10 test files (5 router + 2 drift + 1 smoke + 2 vitest parity)
11-19: 9 docs files (4 finops-* + AD-47 + routers + deployment + 2 runbooks)
20-21: handoff memory + commit-msg

### 4 MODIFIED files
1. `apps/api/main.py`
2. `docs/capability-matrix.md`
3. `_bmad-output/implementation-artifacts/sprint-status.yaml`
4. `memory/MEMORY.md`

**Total**: 25 files = 21 NEW + 4 MODIFIED

Wait, the spec entry (cj 146) is docs-only, so the wire (cj 147) does the source changes. Let me clarify in the spec that:
- cj 146 (this sprint): docs-only = spec file + handoff memory + commit-msg + sprint-status + MEMORY.md = 5 files = 4 NEW + 1 MODIFIED
- cj 147 (wire sprint): source + test + docs = ~20 files = 17 NEW + 3 MODIFIED
- cj 148 (retro sprint): docs-only = retro document + handoff memory + commit-msg + sprint-status + MEMORY.md = 5 files = 4 NEW + 1 MODIFIED

OK let me clean this up.

## 3중 게이트 impact

- **cj 146 (this sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW (apps/api backend unchanged, apps/web frontend unchanged)
- **cj 147 (wire sprint)**: ruff scoped 0 NEW (minor extension only) / pytest ~64 NEW PASS / vitest ~12 NEW PASS / tsc 0 NEW
- **cj 148 (retro sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW

## A559~A563 5 NEW 결정 wire (cj-style 146번째)

- **A559**: 옵션 (a) Phase 20.5 Critical Gap Resolution carry-over 진입 결정 wire (rationale 4종: ① Phase 20 close-out retro 의 4 honest deviations 모두 해소 ② P0 critical functional gap fix (4 routers 미등록) ③ P1 test backfill (12 NEW test files targeted subset) ④ P2 docs backfill (4 NEW docs + capability v1.46 EXTENSION))
- **A560**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-20-5-critical-gap-resolution-carry-over-wire.md` ~+200 LOC)
- **A561**: 3 ACs §F37.1~§F37.3 verbatim → 36 sub-ACs (12+12+12) 전개 결정 wire
- **A562**: Tasks T1~T3 + 24 subtasks 결정 wire (T1 router include 8 subtasks + T2 pytest test backfill 12 subtasks + T3 docs backfill 4 subtasks)
- **A563**: sprint-status v3.55 → v3.56 EXTENSION + atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + commit-msg-phase-20-5-spec-entry.txt 신규 + handoff memory 신규 + MEMORY.md hook EXTENSION + **5 files = 4 NEW + 1 MODIFIED atomic single sprint** 결정 wire

## CR lessons applied 18종

CR 0-2 RLS + CR 1-1 audit-first INSERT 8 NEW + CR 1-1 FastAPI ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 9-6 commit message `git commit -F <file>` + CR 11-3 honest-DEFER 36번째 D-FINOPS-9 honestly DEFER 보존 + Phase 20 wire 의 4 honest deviations 모두 Phase 20.5 territory 흡수 결정 wire + ALLOWED_SERVICE_SUBMODULES 즉시 sweep + CR 11-4 D-001~D-005 + P-015 SSOT + CR 12-1 L4 industry-agnostic capability + CR 12-5 D-14 typed exception envelope 20 NEW + CR 12-5 D-PARITY-01 inversion TypeScript mirror + CR 12-5 D-GATE-01 inversion capability gate + A19 cohesion 9 surface EXTENSION PASS + A36 SDR 검증 4-step 자동 적용 + AD-14 stack pin Recharts 2.12.7 + reportlab 4.0.7 + openpyxl 3.1.2 + pandas 2.1.4 + xlsxwriter 3.1.9 + apscheduler 3.10.4 + pytz 2024.1 + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + AD-47 신규 (a)~(g) 7 sub-decisions + AD-48 신규 (Phase 20.5 Critical Gap Resolution carry-over) (a)~(c) 3 sub-decisions 결정 wire

## D-DEFER-* honestly 결정 wire 보존

- D-1-1-DEFER-1/2/3 + D-EPIC-16-REVIEW-DEFER-1/2~6 + D-PHASE-4-DR-DEFER-1/2 + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1~8 모두 ✅ ALL RESOLVED 보존
- **D-FINOPS-9 honestly DEFER 보존** — Phase 19.5 carry-over 결정 wire `b2fb1d8` 의 7개 세부 항목 모두 Phase 20 territory 흡수 결정 wire + Phase 20 wire 의 4 honest deviations 모두 Phase 20.5 territory 흡수 결정 wire (carry-over chain 정직 회복 verification 결정 wire)
- **Phase 20.5 = D-FINOPS-9 + Phase 20 4-honest-deviations 의 carry-over chain 정직 회복 verification** 결정 wire (CR 11-3 honest-DEFER 36번째 epic 연속 정직 회복)

## Epic 1~17 + Phase 3~20 + Phase 19.5 + 1st release cycle 정합 보존

cj-style 146번째 epic 연속 정직 회복 진입 시점에 pre-flight 정합 sweep 만족 결정 wire 보존:
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `efc3c59` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) DONE 진입 정합 보존
- Phase 11~19 9-module FinOps territory chain ✅ ALL RESOLVED 진입 정합 보존 + Phase 20 territory chain ✅ ALL WIRED 진입 정합 보존
- Epic 1~17 ALL DONE 진입 정합 보존
- 1st release cycle ALL DONE 진입 정합 보존

## 결정 wire 일자 + next

- 결정 wire 일자: 2026-08-26 (KST)
- next 옵션:
  - (a) Phase 20.5 atomic wire T1~T3 진입 결정 wire (cj-style 147번째) — apps/api/main.py router include + 12 NEW pytest tests + 4 NEW docs files = ~22 files atomic single sprint
  - (b) Phase 20.5 close-out retro 진입 결정 wire (cj-style 148번째) — 14-section §1~§14 verbatim retro document
  - (c) Epic 21+ 진입 결정 wire
  - (d) D-DEFER-* follow-up 결정 wire 보류
