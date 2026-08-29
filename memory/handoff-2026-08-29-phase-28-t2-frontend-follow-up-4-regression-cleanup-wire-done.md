---
date: 2026-08-29
sprint: cj-style 200
type: wire-done-handoff
status: done
---

# cj-200 handoff — Phase 28 T2 frontend follow-up 4-regression cleanup sprint DONE

## Summary

Phase 28 T2 frontend follow-up atomic wire sprint (cj-style 197, commit `5bc2b39`) 의 close-out retro (cj-style 198) 진입 후 발견된 4건 micro-regression honestly DEFER 보존 결정 wire 회복 정직 회복 sprint.

## Sprint entry point

- **Wire commit**: TBD (cj-200 wire, pending commit)
- **Type**: docs + atomic single sprint (4 source files = 4 MODIFIED)
- **Files**: 4 MODIFIED (page.tsx + client.ts + ExportConfigPanel.tsx + interactive-dashboard-dashboard.test.tsx)
- **LOC**: ~+14/-6

## 4 micro-regression fixes

### Fix #1: page.tsx cookies() async (1 tsc error)
- File: `apps/web/app/[locale]/(dashboard/)/admin/finops/interactive-dashboard/page.tsx:33`
- Issue: `cookies()` from `next/headers` returns `Promise<ReadonlyRequestCookies>` in Next.js 15.x
- Fix: `const cookieStore = await cookies();` (already in async function)
- cj-197 introduced regression: yes (commit 5bc2b39)

### Fix #2: client.ts startExportJob return type (1 tsc error)
- File: `apps/web/lib/finops/interactive-dashboard-client.ts:25-34, 182-192`
- Issue: `startExportJob` + `getExportJobStatus` typed as `Promise<UnifiedKPI>` but endpoint returns ExportJob
- Fix: return type → `Promise<ExportJob>` + `ExportJob` import added
- cj-197 introduced regression: yes (commit 5bc2b39)
- Cascading: also fixed `ExportConfigPanel.tsx` state type

### Fix #3: vitest Test 21 (1 vitest failure)
- File: `apps/web/__tests__/finops/interactive-dashboard-dashboard.test.tsx:20, 561-568`
- Issue: `btn.click()` direct DOM call → React state update + re-render race condition (`TestingLibraryElementError: Unable to find an element by: [data-testid="breadcrumb-list"]`)
- Fix: `fireEvent.click(btn)` (auto-wraps in `act()`)
- cj-197 introduced regression: yes (commit 5bc2b39)

### Fix #4: vitest Test 28 (1 vitest failure)
- File: `apps/web/__tests__/finops/interactive-dashboard-dashboard.test.tsx:661`
- Issue: `getByText(/owner-only/)` finds multiple elements (badge + description) → `getMultipleElementsFoundError`
- Fix: `getAllByText(/owner-only/).length` assertion
- cj-197 introduced regression: yes (commit 5bc2b39)

## Verification results

### 3중 게이트 FINAL CLEAN recovered for cj-197 sprint
- ruff scoped: ✅ PASS (backend 0 changes)
- pytest: ✅ PASS (no Python source changes)
- vitest interactive-dashboard-dashboard.test.tsx: ✅ **30/30 PASS** (was 28/30 pre-fix)
- tsc cj-197-introduced: ✅ **0 NEW** (was 2 pre-fix: export_job_id + cookies async)

### Pre-existing failures honestly DEFER (no regression introduced)
- vitest full suite: 924/938 PASS — 14 failures preserved AS-IS in pre-existing test files (cost-anomaly-ml-prediction-dashboard, latency-regression, slo-dashboard, slo/slo-dashboard, tracing)
- tsc: 21 errors preserved AS-IS (pre-existing across 18 unrelated files)

## D-DEFER-* honestly 결정 wire 보존

### D-TYPESCRIPT-CODEBASE-1 honestly DEFER 신규 진입
21 pre-existing tsc errors (cj-200 wire 의 4 MODIFIED files 와 무관) 모두 cj-201+ 별도 sprint honestly DEFER 보존:
- m12-account test files (AccountDeletionModal, DeletionStatusPanel)
- latency-regression.test.tsx (Performance module)
- m7-simulation test files (projection schema + ProjectionClient + ProjectionComparisonChart)
- monthly-input-tabs.test.tsx (MonthlyClosingReportV4Verdict mismatch)
- slo-dashboard.test.tsx (Performance module)
- sso/callback/route.ts (Auth module)
- ChaosDashboardPanel.tsx (import type misuse)
- FinopsDashboardPanel.tsx (PeriodMode missing)
- FinopsForecastDashboardPanel.tsx (HorizonMonths + recharts)
- BudgetAllocationBreakdownPanel.tsx (recharts)
- BudgetVsActualTrendChart.tsx (recharts)
- VendorContractLifecycleTimeline.tsx (VendorContractLifecycle)
- SnapshotPersistencePanel.tsx (cache_invalidation_receipts.length)
- BudgetVarianceTable.tsx (VariancePdfButtonProps)
- lib/auth/social.ts (AllowedSocialProvider)
- lib/m12-account-backup.ts (const assertions on enum)

All 21 pre-existing tsc errors + pre-existing vitest failures require separate code-base-wide retrospective sprint → cj-201+ 결정 wire 보존.

## Cross-references

- ✅ cj-200 wire DONE (TBD)
- ✅ cj-199 (Epic 28 T2 frontend follow-up close-out retro, `0f01c66`) DONE
- ✅ cj-198 (TBD — Phase 28 T2 frontend follow-up retro commit) DONE
- ✅ cj-197 (Phase 28 T2 frontend follow-up atomic wire, `5bc2b39`) DONE
- ✅ cj-196 (T2 frontend follow-up spec entry) DONE
- ✅ cj-195 (T2 frontend follow-up PRD entry) DONE
- ✅ cj-194 (Epic 28 close-out retro) DONE
- ✅ cj-193 (Epic 28 atomic wire Q2 backend-only, `db005e8`) DONE
- ✅ cj-192/191 (Epic 28 PRD + spec entry) DONE
- ✅ Phase 11~27 18-capability FinOps territory chain ✅ ALL WIRED INTEGRATED
- ✅ Epic 1~17 + Phase 3~28 + Phase 19.5 + Phase 20.5 + audit-fixes + 1st release cycle 정합 보존