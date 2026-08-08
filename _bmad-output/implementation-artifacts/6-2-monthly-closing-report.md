---
baseline_commit: 418ca2d
target_key: 6-2-monthly-closing-report
epic: 6
story_id: 6.2
title: Monthly Closing Report — closing snapshot + ledger events + capability gate
status: review
---

# Story 6.2: Monthly Closing Report — closing snapshot + ledger events + capability gate

Status: ready-for-dev

> Epic 6 두 번째 스토리. Epic 5 close-out retro §6 cj-style 3-story 분할 (6-1 → 6-2 → 6-3) — 6-1 = Closing Period Service + closing_snapshot ledger event wire (DONE commit 418ca2d) → 6-2 = Monthly Closing Report (closing snapshot consumer + ledger events join + KRW/USD dual display + capability gate) → 6-3 = Closing PDF Export + ko-KR labels. 6-1 wire foundation 그대로 활용: ① closing_period_service.evaluate_closing_period (read-only aggregate) + confirm_closing_period (write) ② closing_snapshot ledger event (5-2 11번째 event_type, AD-2 append-only) ③ V4 closing-period-consistency verifier (closing snapshot ↔ ledger aggregate 양방향 검증) ④ `MONTHLY_CLOSING_REPORT` capability (matrix v1.8 — manufacturing 3종 ✅ / service-only ❌) ⑤ ActionClass.CLOSING_PERIOD 3 values + VerificationAction V4 value forward-lock (A5 wire) ⑥ Alembic 0017 monthly_input_periods 4 NEW columns + 1 SQL CHECK constraint ⑦ closing-period.md §V4 골든 fixture deferred (T10.5 carry-over) close-out (A11 결정).
>
> **baseline_commit = 418ca2d** (Story 6.1 bmad-code-review 3rd sweep done, 3중 게이트 final clean 1164 passed + 127 skipped + 0 failed in 73.68s). Story 6.2 spec 진입 시점에 Epic 5 close-out retro §7 A11 결정 (V8 12 시나리오 골든 파일에 closing_snapshot + ledger_period_closing fixture 추가 + byte-identical CI gate wire) + A8 (Epic 6 close-out 시점에 Epic 3.3 inline projection 제거 — 5-2 commit + 1 epic maintenance window 종료) + A10 (MONTHLY_CLOSING_REPORT capability 신규 — 6-1 spec v1.3 wire 완료, 6-2 spec 본문 matrix v1.8 reference) + A12 (5-3 T12.2 test file deferred close-out done 2026-08-07) 모두 spec 본문에 반영. **Epic 6 2번째 진입점**: monthly closing report = read-only aggregator (closing_snapshot + ledger events + fiscal_period_snapshots join) + KRW/USD dual display frontend (PRD §F5.2) + V8 16-fixture matrix extension (A11 wire) + 6-1 T10.5 deferred V4 골든 fixture close-out (carry-over dedup).
>
> **cj-style 3-story 분할 (Epic 5 retro §6 W1)** — Epic 5 5-1 (opening auto-carry) → 5-2 (inventory_ledger append-only events) → 5-3 (closing_guard + V3 verification + frontend banner) 패턴의 Epic 6 적용형. 6-1 (closing_period service + closing_snapshot wire + V4 verification) → 6-2 (monthly closing report = closing snapshot consumer + KRW/USD dual display + V8 fixture extension) → 6-3 (closing PDF export + ko-KR labels). 3-story 모두 **additive** — wire contract 호환 + 사용자 흐름 무중단. Epic 5 retro §6 §11 "Epic 6 6-2 spec 진입: A11 (V8 fixture 확장) — closing snapshot + ledger events 골든 파일 fill" 결정 그대로 적용.

<!-- dev-context: Epic 5 close-out retro (2026-08-07) — Epic 5 셋 다 done (5-1 + 5-2 + 5-3 + 0.5 plumbing + A5 + A7). A12 T12.2 test file deferred close-out done (closing invariant TS mirror parity, commit 74f3a30). Epic 5 회고 §6 명시: 6-1 = Closing Period Service + closing_snapshot ledger event wire (DONE commit 418ca2d). 6-2 = Monthly Closing Report (closing snapshot consumer + KRW/USD dual display + capability gate MONTHLY_CLOSING_REPORT). 6-3 = Closing PDF Export + ko-KR labels.

Epic 5 close-out retro (2026-08-07) §7 A11 결정 — "Epic 6 6-2 spec 진입 시: V8 12 시나리오 골든 파일에 closing_snapshot + ledger_period_closing fixture 추가 + byte-identical CI gate wire". 6-1 carry-over 13th defer (V4 골든 fixture fill deferred to T10.5 follow-up) close-out도 6-2 spec 진입 시점에 dedup 결정 (A11 V8 fixture extension 진입점에 V4 골든 fixture 동시 fill).

Epic 5 close-out retro (2026-08-07) §7 A8 결정 — Epic 3.3 inline projection deprecation timeline = Epic 6 close-out 시점에 결정 (5-2 commit + 1 epic maintenance window 종료). 6-1 spec 본문 §A8 timeline 명시 완료. 6-2 wire는 inline projection 보존 상태로 wire (1 epic maintenance window 진행 중). Epic 6 close-out 시점에 fold-in vs deprecate 결정.

Epic 5 close-out retro (2026-08-07) §7 A9 결정 — Epic 11 reversal module wire 진입점 (5-1 + 5-2 carry) = Epic 11 spec 진입 시점에 결정. 6-2 wire는 reversal 모듈 무관 (read-only report). Epic 6 close-out retro 시점에 A9 carry-over 결정.

Epic 5 close-out retro (2026-08-07) §7 A10 결정 — Epic 6 reporting capability 신규 = MONTHLY_CLOSING_REPORT (manufacturing 3종 ✅ / service-only ❌). 6-1 spec v1.3 wire 완료 (matrix v1.8 latest). 6-2 spec 본문 §A10 capability matrix v1.8 reference.

Epic 5 close-out retro (2026-08-07) §7 A12 결정 — 5-3 T12.2 test file deferred close-out done (2026-08-07). 6-2 spec 본문 §A12 reference.

Epic 4 close-out retro (2026-08-03) A3 cj-style — 3-story 분할 유지 (5-1 → 5-2 → 5-3) + inline projection deprecation = 5-2 commit 완료 + Epic 6 close-out 시점에 legacy path 제거 (Epic 5 retro §7 A8 결정, 6-1 spec 본문 §A8 + 6-2 spec 본문 §A8 timeline 명시).

Epic 4 close-out retro (2026-08-03) A5 — A5 Full Phase 1+2+4 done. Epic 5 5-1 + 5-3 + 6-1 audit log 일관성 보장 + A5 forward-lock + drift detector pattern 정착. 6-2 wire 동일 패턴 적용 (V4 골든 fixture fill 시 audit_action = 'verify_v4_closing_period_consistency' 추가).

Epic 4 close-out retro (2026-08-03) A6 — 0.5 plumbing = 5-3 spec 진입 전 dep. ✅ done 2026-08-05 (commit ead1974) — shadcn Tabs / sonner / vitest / Playwright 4종 wire. 6-2 frontend MonthlyClosingReportPanel 진입점 가능 (shadcn Card + Tabs + Table + Recharts).

Epic 4 close-out retro (2026-08-03) A7 — Epic 4 carry (async test pattern + SDR overclaim) Epic 5 + 6-1 wire. 6-2 동일 적용.

**Story 0.5 (2026-08-05)** — frontend plumbing wire ✅ done. shadcn Tabs / sonner / vitest + RTL + MSW / Playwright / next-intl / INDUSTRY_ICON fill / 10 ACs all green. **6-2 frontend 진입 전 dep satisfied**. docs/frontend-toolchain.md v1.0 SSOT.

**Story 0-2 (2026-07-29)** — RLS 인프라 + audit_logs INSERT-only with `BEFORE UPDATE OR DELETE` trigger 패턴이 Epic 0에서 wire됨. AD-2 + AD-3 SSOT. 6-2 wire는 RLS 위에서 동작 (read-only — service_role bypass 불요요).

**Story 1.1 (2026-07-29)** — Industry enum SSOT (manufacturing / manufacturing_service / service / manufacturing_service_other) + capability matrix v1.0. 6-2 capability gate = MONTHLY_CLOSING_REPORT (6-1 wire 완료, matrix v1.8).

**Story 2.2 (2026-08-01)** — BOM matrix 100% validation. 6-2 BOM data 활용 (5-3 W1 BOM-aware reconciliation 결과 + 5-2 production_output_inbound + production_material_consumption ledger events → closing report의 BOM-aware 자재별 기말 집계).

**Story 3.1 (2026-08-01)** — monthly_input_periods + monthly_input_rows 테이블 (Alembic 0009). 6-2 read-only aggregate 진입점 (monthly_input_periods + monthly_input_rows + inventory_ledger + fiscal_period_snapshots 4 namespace SSOT).

**Story 3.3 (2026-08-01)** — `monthly_input_periods.opening_inventory` JSONB column (Alembic 0011) + `MonthlyInputStateResponse.warnings` + `is_blocked` + `top_n_severity` 4 fields + F2.3 음수재고 입력 시 즉시 경고. **Epic 5 retro §7 A8 — 6-2 wire 시점 inline projection 보존 (1 epic maintenance window 진행 중), Epic 6 close-out 시점에 fold-in vs deprecate 결정**.

**Story 4.1 (2026-08-02)** — engine returns state='draft' (AD-22 boundary strengthening). 6-2 closing report = service layer ownership (engine은 closing report 의미 모름).

**Story 4.2 (2026-08-03)** — REPEATABLE READ + audit-first (CR 1.1) + calc_log + AD-22 state transition. **6-2 wire는 4-2 calc result + 5-2 ledger aggregate + 6-1 closing snapshot aggregate 3-source read-only join**.

**Story 4.3 (2026-08-03)** — V1·V4·V7·V8 verification + verdict + A5 forward-lock + Industry enum SSOT. **6-2 wire는 V4 (6-1 wire) verification surface 위에 additive — closing report의 V4 verdict 표시 = closing snapshot 일관성 결과**.

**Story 4.4 (2026-08-03, commit 80f4494)** — A5 forward-lock (verify_v8_golden_match + Alembic 0014 verification_log CHECK 4-value expansion) + 12 fixture matrix. **6-2 A11 wire = V8 골든 fixture 14 → 16 (V4 closing-period-snapshot PASS/FAIL 2 시나리오 골든 신규) + V8 골든 fixture 16 → 18 (closing_snapshot + ledger_period_closing 2 시나리오 골든 신규)** = 18 fixture matrix.

**Story 5.1 (2026-08-04, commit b4b84da)** — opening_carry_chain wire + 4 hooks into monthly_input_service. **5-1 carry-over to 6-2**: opening_inventory JSONB → closing report의 opening_snake 표시 (당월 기초 = 전월 기말).

**Story 5.2 (2026-08-04, commit 7a13eb9)** — inventory_ledger append-only events + 4 routes + 11 values event_type CHECK + PostgreSQL BEFORE UPDATE OR DELETE row-level trigger + AD-22 reversal entrypoint forward-fill. **5-2 carry-over to 6-2**: closing_snapshot (5-2 11번째 event_type) + 11-value event_type whitelist = closing report의 ledger events source. V4 골든 fixture fixture_publisher CLI `--industry manufacturing --include-closing-period-snapshot` 추가 (6-1 carry-over).

**Story 5.3 (2026-08-06, commit 079f6a7)** — closing_guard pure kernel + closing_guard_service + 3 routes + MonthlyInputStateResponse 5 NEW fields + 6 NEW frontend files + 3 vitest scenarios + 32 patches P1-P32 (3 sweeps). **5-3 carry-over to 6-2**: `closing_guard_invariant` + `closing_guard_blocked` + `closing_guard_audit_trail` (MonthlyInputStateResponse 5 NEW fields 중 3개) = closing report의 부수 정보 표시.

**Story 6.1 (2026-08-08, commit 418ca2d)** — closing_period service + closing_snapshot ledger event wire + V4 verification + MonthlyInputStateResponse 4 NEW fields + 4 NEW frontend files + 9 vitest scenarios + 17 PATCH + 1 DECISION + 13 DEFER items closed out sweeping. **6-1 carry-over to 6-2**: (a) `closing_period_service.evaluate_closing_period` = 6-2 read-only aggregator 입력 source, (b) `closing_snapshot_count` field = 6-2 closing report 상단 KPI 표시, (c) `closing_period_audit_trail` field = 6-2 audit-trail list 표시, (d) `closing_period_finalized_at` field = 6-2 finalized_at timestamp 표시, (e) `closing_period_status` field = 6-2 status 4 codes 표시, (f) `MONTHLY_CLOSING_REPORT` capability = 6-2 capability gate 재사용, (g) `ActionClass.CLOSING_PERIOD` 3 values = 6-2 audit log emission trace, (h) V4 verification = 6-2 closing snapshot 일관성 표시, (i) 6-1 carry-over 13th defer (V4 골든 fixture fill deferred to T10.5) → 6-2 A11 wire 시점에 dedup 결정 (V4 골든 fixture 16-fixture matrix로 동시 fill).

**A12 (2026-08-07, commit 74f3a30)** — T12.2 test file deferred close-out done. Epic 5 close-out retro §7 A12 close-out 완료.

**A8 (Epic 5 retro §7 결정, 2026-08-07)** — Epic 3.3 inline projection deprecation timeline: Epic 6 close-out 시점에 inline projection 제거 (5-2 commit + 1 epic maintenance window 종료 시점). 6-2 spec 본문 §A8 timeline 명시. 6-2 wire는 inline projection 보존 상태로 wire (1 epic maintenance window 진행 중), Epic 6 close-out 시점에 fold-in 결정.

**A9 (Epic 5 retro §7 결정, 2026-08-07)** — Epic 11 reversal module wire 진입점은 Epic 11 spec 진입 시점에 결정 (deferred). 6-2 wire는 reversal 모듈 무관 (read-only report). Epic 6 close-out retro 시점에 A9 carry-over 결정.

**A10 (Epic 5 retro §7 결정, 2026-08-07)** — Epic 6 reporting capability 신규: MONTHLY_CLOSING_REPORT capability (manufacturing 3종 ✅ / service-only ❌). 6-1 spec v1.3 wire 완료 (matrix v1.8 latest). 6-2 spec 본문 §A10 capability matrix v1.8 reference.

**A11 (Epic 5 retro §7 결정, 2026-08-07)** — V8 12 시나리오 골든 파일에 closing_snapshot + ledger_period_closing fixture 추가 + byte-identical CI gate wire. 6-2 spec 진입 시점에 wire. **6-1 T10.5 deferred V4 골든 fixture fill (6-1 13th defer) 동시 dedup 결정** — V4 closing-period-snapshot PASS/FAIL 2 골든 + A11 closing_snapshot + ledger_period_closing 2 골든 = 4 NEW 골든 files. V8_FIXTURE_COUNT 16 → 18.

**AD-1 (modular monolith + hexagonal core)** — 6-2 wire는 engine pure helper + service layer + handlers 표준 3-tier 패턴 (5-1/5-2/5-3/6-1 동일).

**AD-2 (append-only ledger)** — 6-2 wire는 read-only — ledger INSERT 없음. 5-2 inventory_ledger SSOT + RLS 4-policy 그대로 read-only 활용.

**AD-3 (RLS)** — 6-2 wire는 RLS 위에서 동작 (read-only — service_role bypass 불요요). Closing snapshot ledger event = warehouse only select.

**AD-4 (atomicity)** — 6-2 wire는 read-only — REPEATABLE READ isolation level read-only transaction (no write).

**AD-6 (close lock)** — 6-2 wire는 monthly_input_periods.status='closed' 상태 read-only 표시. AD-6 close lock 보존.

**AD-8 (monetary types)** — 6-2 wire 핵심: KRW/USD dual display (PRD §F5.2 + ADR). KRW = BIGINT (정수) + USD = NUMERIC(18,2) (소수 2자리) + tenant_settings.baseline.currency_pair = USD/KRW 환율 source.

**AD-11 (layer rule)** — pure helpers = `packages/services/m4_inventory/monthly_closing_report.py` (NEW) + `packages/cost_engine/monthly_closing_report_aggregator.py` (NEW). service layer = `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py` (NEW). engine은 monthly_closing_report 의미 모름 (service-layer ownership — 4-1 wire 패턴 동일).

**AD-12 (verification ordering)** — V4 wire (6-1) = closing snapshot 일관성 verification. 6-2 wire는 V4 verdict envelope read-only 표시 (closing report의 V4 row).

**AD-15 (cross-language parity)** — TS mirror drift detector `tests/integration/test_monthly_closing_report_label_consistency.py` (NEW) + vitest wire (Story 0.5 AC #4 done). Decimal serialization parity (KRW 정수 + USD 소수 2자리).

**AD-16 (fiscal snapshot contract)** — 6-2 wire는 fiscal_period_snapshots read-only consumer (M3 + M11만 writer). 6-1 closing_snapshot ledger event + 4-2 fiscal_period_snapshots = closing report의 cost data source.

**AD-18 (single product identity)** — `inventory_ledger.product_id` (UUID v7) = PRODUCT(product_id) SSOT. monthly_closing_report per-product aggregation = product_id SSOT.

**AD-22 (append-only-leaning + reversal)** — 6-2 wire는 read-only (no write). correction은 Epic 11 reversal module ships 후 (A9 결정 deferred).

**AD-23 (4-namespace pattern)** — monthly_input_periods + monthly_input_rows + inventory_ledger + audit_logs + fiscal_period_snapshots 5 namespace read-only aggregate. 6-2 wire는 5 namespace 모두 read-only aggregate.

**AD-24 (typed period-key)** — 'YYYY-MM' 형식 SSOT. monthly_closing_report per period_key. monthly_closing_report service는 `monthly_input_periods.period_key` AD-24 typed.

**PRD §F4.3 (월 마감 E2E)** — 6-1 primary AC: closing_period service로 closing 시점 ledger aggregate 영구화. 6-2 carry-over: closing_snapshot ledger event = 6-2 closing report 입력 source.

**PRD §F5 (마감 보고서)** — **6-2 PRIMARY AC**: monthly closing report = 마감 보고서. closing snapshot + ledger events + fiscal_period_snapshots 3-source read-only join. V4 verdict envelope + status 4 codes + audit-trail 표시.

**PRD §F5.2 (KRW/USD dual display)** — **6-2 PRIMARY AC**: KRW/USD dual display. KRW = BIGINT (정수) + USD = NUMERIC(18,2) (소수 2자리) + tenant_settings.baseline.currency_pair = USD/KRW 환율 source.

**PRD §V4 (closing snapshot 일관성 verification)** — 6-1 V4 wire 신규: closing snapshot 일관성 verification. 6-2 wire는 V4 verdict envelope read-only 표시 (closing report의 V4 row).

**PRD §A11 (오류의 가시화)** — 6-1 wire closing_period service = Layer 3 (마감 확정 시 snapshot). 6-2 wire closing report = Layer 3 + closing snapshot V4 verification 시각화.

**PRD §6.1 (산식 체인)** — 6-2 wire는 fiscal_period_snapshots.engine_type='trad' + cost data (material_cost / labor_cost / overhead_cost / manufacturing_cost) read-only 표시.

**PRD §6.2 (수불부)** — 5-2/5-3 wire와 동일 (PRD §6.2 normalized). 6-2 wire는 수불부 read-only aggregate.

**PRD §9 (21 reports)** — 6-2 wire는 21 reports와 별도 (Monthly Closing Report = 1 specific report). 21 reports는 Epic 6 close-out 시점에서 별도 결정 (Epic 5 retro §6 cj-style 6-1/6-2/6-3 분할 결정). 6-3 closing PDF export = 21 reports 기반 + closing snapshot extension.

**PRD §12 (AI)** — 6-2 wire는 AI 무관 (read-only report). 6-3에서 AI commentary 활용 가능.

**0.5 plumbing** — 6-2 frontend MonthlyClosingReportPanel 진입 시점 frontend toolchain 완비 (shadcn Card + Tabs + Table + sonner / vitest / Playwright / next-intl). MonthlyClosingReportPanel = ClosingPeriodConfirmationPanel (6-1 wire) 위에 additive panel. -->

## Story

As a **사장님**,

I want **월 마감을 확정한 다음 (1) 그 시점의 closing snapshot + ledger events + fiscal_period_snapshots 3-source join 결과를 한 페이지에서 Monthly Closing Report로 보고 (2) KRW 정수 + USD 소수 2자리로 동시 표시되며 (3) V4 closing-period-consistency verdict envelope + status 4 codes + audit-trail + BOM-aware 자재별 기말 집계 + V8 fixture byte-identical 골든 매트릭스 (A11 wire)가 보이고 (4) service-only 업종은 진입 자체가 거부되는 것**,

so that **회계사·세무사에게 전달할 마감본이 한눈에 보이고, closing snapshot 일관성 검증이 시각화되며, V8 16-fixture matrix extension (A11 wire)으로 6-1 T10.5 deferred V4 골든 fixture fill까지 동시 close-out되며, PRD §F5 (마감 보고서) + §F5.2 (KRW/USD dual display) + §V4 (closing snapshot 일관성 verification) wire contract가 정확히 closed됨** — AD-2 (append-only ledger — read-only consumer) · AD-4 (atomicity — read-only transaction) · AD-6 (fiscal-period close lock — read-only) · AD-8 (monetary types — KRW/USD dual display) · AD-11 (layer rule) · AD-12 (verification ordering V1 → V4 → V3 → V7 → V8) · AD-15 (cross-language parity) · AD-16 (fiscal snapshot contract — read-only consumer) · AD-18 (single product identity) · AD-22 (append-only-leaning + reversal — read-only consumer) · AD-23 (4-namespace pattern + 5 namespace read-only aggregate) · AD-24 (typed period-key) · PRD §F4.3 (월 마감 E2E — 6-1 wire carry-over) · PRD §F5 (마감 보고서 — 6-2 PRIMARY) · PRD §F5.2 (KRW/USD dual display — 6-2 PRIMARY) · PRD §V4 (closing snapshot 일관성 verification — 6-1 wire carry-over) · PRD §A11 (입력 시 경고 + 마감 시 차단 + 마감 확정 시 snapshot 3-layer — 6-1 wire carry-over) · A8 (Epic 6 close-out 시점에 inline projection 제거) · A9 (Epic 11 reversal deferred — 6-2 read-only) · A10 (MONTHLY_CLOSING_REPORT capability 신규 — 6-1 wire 완료) · A11 (V8 16-fixture matrix extension — 6-2 PRIMARY) · Story 0.5 frontend plumbing · Epic 5 5-1 (opening auto-carry) + 5-2 (inventory_ledger) + 5-3 (closing_guard) + 6-1 (closing_period service) carry-over.

## Acceptance Criteria

1. **Given** Epic 5 5-1 (opening auto-carry chain) + 5-2 (inventory_ledger append-only events, `closing_snapshot` 11번째 event_type) + 5-3 (closing_guard + V3 verification + ClosingGuardBanner) + 6-1 (closing_period service + closing_snapshot ledger event wire + V4 closing-period-consistency verification + MONTHLY_CLOSING_REPORT capability wire + ClosingPeriodConfirmationPanel) backend/frontend wire 완료 + Story 3.3 (음수재고 입력 시 즉시 경고) + Story 4-2 (REPEATABLE READ + is_blocked close-time hook) + Story 4-3 (verification surface V1/V4/V7/V8) + Story 4-4 (V8 골든 fixture 12 매트릭스) + 0.5 frontend plumbing ✅ done (shadcn Card / Tabs / sonner / vitest / Playwright / next-intl) + A12 (T12.2 test file deferred close-out done) + 6-1 T10.5 deferred V4 골든 fixture fill (6-1 13th defer — 6-2 A11 spec 진입 시점에 dedup 결정)
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 책임 분리 + wire contract 정렬이 유지된다:
     - **Pure kernel #1 (NEW `packages/services/m4_inventory/monthly_closing_report.py`)** — `aggregate_monthly_closing_report(closing_snapshot_events: list[ClosingSnapshotEvent], ledger_events: list[InventoryLedgerEvent], fiscal_period_snapshots: list[FiscalPeriodSnapshot], tenant_settings: TenantSettings) -> MonthlyClosingReportAggregate` (read-only aggregator — closing snapshot events + ledger events + fiscal_period_snapshots join → MonthlyClosingReportAggregate). + `format_period_closing_krw_usd(amount_krw: int, currency_pair: CurrencyPair) -> PeriodClosingDisplay` (KRW 정수 + USD 소수 2자리 dual display formatting — AD-8 + PRD §F5.2). + `compute_usd_from_krw(amount_krw: int, exchange_rate: Decimal) -> Decimal` (pure USD 환산 — `tenant_settings.baseline.currency_pair.usd_krw_rate` 기준). + `classify_report_view_mode(ledger_event_count: int, closing_snapshot_count: int, fiscal_period_snapshot_count: int) -> ReportViewMode` (CLOSING_REPORT_READY / CLOSING_REPORT_PARTIAL / CLOSING_REPORT_EMPTY — CLOSING_REPORT_READY = 3 source 모두 ≥ 1; CLOSING_REPORT_PARTIAL = 일부만 ≥ 1; CLOSING_REPORT_EMPTY = 3 source 모두 0건). + `is_monthly_closing_report_allowed(mode: ReportViewMode) -> bool` (= mode == CLOSING_REPORT_READY). + `MONTHLY_CLOSING_REPORT_TITLE_KO: Final[str] = "월 마감 보고서"` + `MONTHLY_CLOSING_REPORT_EMPTY_KO: Final[str] = "마감 데이터 없음"` (Korean constants — AD-15 §11 SSOT). stdlib-only (no DB, no clock, no random). banker's rounding via `QTY_QUANTUM` from `inventory_projection` (CR 0-4 lesson + AD-15 parity). USD 환산 ROUND_HALF_EVEN precision to 2 decimal places (AD-15 §11). 1 typed exception (`MonthlyClosingReportError`, NO HTTP mapping — pure helper owns domain semantics).
     - **Pure kernel #2 (NEW `packages/cost_engine/monthly_closing_report_aggregator.py`)** — `verify_monthly_closing_report_consistency(*, ledger_aggregate: dict[UUID, Decimal], closing_snapshot_aggregate: dict[UUID, Decimal], fiscal_period_snapshot_aggregate: dict[UUID, Decimal], product_whitelist: set[UUID]) -> V4Verdict` (V4 wire extension — closing snapshot 일관성 + fiscal_period_snapshot aggregate 일치 검증; verdict = PASS / FAIL / SKIP). **AD-11 layer rule**: cost_engine pure helper는 stdlib-only (no sqlalchemy import) — service layer가 ledger aggregate + closing_snapshot aggregate + fiscal_period_snapshot aggregate + product whitelist를 인자로 전달. **AD-12 ordering**: V4 rule의 `previous_status='failed'` 시 SKIP 발동 = Story 4-3 ordering invariant 보존. stdlib-only. 1 typed exception (`MonthlyClosingReportInconsistencyError`).
     - **Service layer #1 (NEW `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py`)** — `MonthlyClosingReportService` class with 3 operations:
       - `get_monthly_closing_report(session, *, tenant_id, period_key) -> MonthlyClosingReportResponse` (read-only aggregator — 6-1 `closing_period_service.evaluate_closing_period` + 5-2 `LedgerService.query_period_closing` + 4-2 `fiscal_period_snapshots` query + T1 pure kernel `aggregate_monthly_closing_report` + `format_period_closing_krw_usd` + `classify_report_view_mode` + `is_monthly_closing_report_allowed` dispatch).
       - `get_monthly_closing_report_audit_trail(session, *, tenant_id, period_key) -> list[AuditLogEntry]` (CR 1.1 observability — `closing_period_*` + `fiscal_period_snapshot_*` + `verification_v4_*` audit entries, time DESC, last 10).
       - `verify_monthly_closing_report_v4(session, *, tenant_id, period_key, calc_result_id: UUID) -> V4Verdict` (V4 verification dispatch — 6-1 V4 wire extension + 4-3 V4 placeholder fill 진입점).
     - **Wire trigger (extension `apps/api/modules/m4_inventory/handlers.py`)** — 3 NEW routes:
       - `GET /api/v1/inventory/monthly-closing-report?period_key=...` — read-only closing report endpoint. Returns `MonthlyClosingReportResponse` (`{ period_key: str, view_mode: "CLOSING_REPORT_READY"|"CLOSING_REPORT_PARTIAL"|"CLOSING_REPORT_EMPTY", allowed: bool, closing_per_product: list[ClosingPerProductRow], closing_snapshot_count: int, ledger_event_count: int, fiscal_period_snapshot_count: int, finalized_at: str | None, v4_verdict: V4Verdict | None, audit_trail: list[AuditLogEntry], currency_pair: CurrencyPair }`). AD-15 envelope + capability gate `MONTHLY_CLOSING_REPORT` (A10 — 6-1 wire 완료).
       - `GET /api/v1/inventory/monthly-closing-report/audit-trail?period_key=...` — closing report audit log emission trace (CR 1.1 observability). Returns audit_logs entries filtered by `action='closing_period_*' OR action='fiscal_period_snapshot_*' OR action='verify_v4_closing_period_consistency'`. Capability gate.
       - `GET /api/v1/inventory/monthly-closing-report/v4-verdict?period_key=...` — V4 closing-period-consistency verdict read-only endpoint. Returns V4Verdict envelope (PASS / FAIL / SKIP). Capability gate.
     - **A5 forward-lock (`apps/api/core/audit_action.py` extension)** — `MonthlyClosingReportAction` Literal 1 value 신규 채움: `monthly_closing_report_viewed` (closing report 조회 audit — read-only report의 자체 audit log). + `VerificationAction` Literal 기존 `verify_v4_closing_period_consistency` 6-1 wire 그대로 (6-2 추가 변경 없음). A5 drift detector 동시 통과.

2. **Given** AC #1 pure kernel + service layer + wire trigger + A5 forward-lock
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 frontend wire 발동 (AC #2 — MonthlyClosingReportPanel + shadcn Card + Table + Recharts + sonner toast wire):
     - **TS mirror helper #1 (NEW `apps/web/lib/monthly-closing-report.ts`)** — 6-2 frontend logic (wire path mirror). Exports:
       ```typescript
       export type ReportViewMode = "CLOSING_REPORT_READY" | "CLOSING_REPORT_PARTIAL" | "CLOSING_REPORT_EMPTY";
       export interface ClosingPerProductRow {
         product_id: string;
         product_code: string;
         product_name: string;
         opening_qty: string;  // 5-1 carry-over
         closing_qty: string;  // 6-1 wire
         closing_qty_usd: string;  // AD-8 USD dual display
         delta: string;  // closing_qty - opening_qty
         delta_usd: string;
         ledger_event_count: number;
       }
       export interface MonthlyClosingReportResponse {
         period_key: string;
         view_mode: ReportViewMode;
         allowed: boolean;
         closing_per_product: ClosingPerProductRow[];
         closing_snapshot_count: number;
         ledger_event_count: number;
         fiscal_period_snapshot_count: number;
         finalized_at: string | null;
         v4_verdict: V4Verdict | null;
         audit_trail: AuditLogEntry[];
         currency_pair: { from_currency: string; to_currency: string; rate: string; rate_source_ko: string; rate_as_of: string };
       }
       export function buildMonthlyClosingReportState(response: MonthlyClosingReportResponse): MonthlyClosingReportState;
       export function isMonthlyClosingReportAllowed(state: MonthlyClosingReportState): boolean;
       export function formatMonthlyClosingReportTitleKo(state: MonthlyClosingReportState): string;  // "월 마감 보고서 — 2026-07"
       export function formatMonthlyClosingReportEmptyKo(state: MonthlyClosingReportState): string;  // "마감 데이터 없음"
       export function formatClosingPerProductRowKo(row: ClosingPerProductRow): string;  // "PRD-001 / 제품 A / 기초 100 / 기말 120 / USD 90.91"
       export function formatCurrencyPairDisplayKo(pair: CurrencyPair): string;  // "1 USD = 1,320 KRW (한국은행 2026-07-25)"
       ```
     - **TS mirror helper #2 (extension `apps/web/lib/closing-period.ts`)** — 6-1 wire file extension. Add `MonthlyClosingReportView` interface export (MonthlyClosingReportResponse → MonthlyClosingReportState projection).
     - **TS mirror helper #3 (NEW `apps/web/lib/monthly-closing-report-parity.ts`)** — TS↔Python SSOT parity helper. Decimal serialization parity (KRW 정수 + USD 소수 2자리 + banker's rounding + QTY_QUANTUM).
     - **MonthlyClosingReportPanel (NEW `apps/web/components/m2-input/MonthlyClosingReportPanel.tsx`)** — ClosingPeriodConfirmationPanel (6-1 wire) 위에 additive panel. shadcn `<Card>` + `<Table>` + Recharts `<BarChart>` pattern:
       - When `report_view_mode=CLOSING_REPORT_READY` → (a) 상단 KPI 박스 4개: `closing_snapshot_count` (e.g., 12건) + `ledger_event_count` (e.g., 250건) + `fiscal_period_snapshot_count` (e.g., 12건) + `v4_verdict` (PASS/FAIL/SKIP). (b) 중간 Table: `closing_per_product` rows (top 10개 제품) — 각 row = `PRD-001 / 제품 A / 기초 100개 / 기말 120개 / USD 90.91 / delta +20 / ledger events 8건`. (c) 하단 Recharts BarChart: product별 closing_qty 시각화. (d) 우측 sidebar: `finalized_at` + `audit_trail` (last 5 entries) + `currency_pair` display.
       - When `report_view_mode=CLOSING_REPORT_PARTIAL` → 일부 빈 source 표시 + "잠시 후 갱신" sonner `toast.info`. KPI 박스 4개 중 빈 source = "데이터 없음" 회색 placeholder.
       - When `report_view_mode=CLOSING_REPORT_EMPTY` → "마감 데이터 없음" Alert 표시 + Table / Chart 비노출 + audit-trail empty.
     - **MonthlyClosingReportRoute (NEW `apps/web/app/m2-input/period/[period_key]/monthly-closing-report/page.tsx`)** — Next.js App Router page. server-side fetch + client-side hydration. capability gate UI (service-only tenant → 403 INDUSTRY_NOT_SUPPORTED redirect).
     - **MonthlyInputTabs extension** — `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire + 6-1 extension) extension. 마감 tab (5-3 3-tab 구조) 안에 MonthlyClosingReportPanel wire (ClosingPeriodConfirmationPanel right side extension). 6-1 + 6-2 vertical stack = ClosingGuardBanner + ClosingPeriodConfirmationPanel + MonthlyClosingReportPanel.
     - **Capability-gated UI** — service-only tenant (`tenant_settings.industry === 'service'`) → MonthlyClosingReportPanel 비노출 + MonthlyClosingReportRoute 진입 시 403 INDUSTRY_NOT_SUPPORTED redirect + sonner `toast.error('업종 미지원: 월 마감 보고서는 제조 업종만 지원합니다.')` 표시. Capability matrix v1.8 (A10 결정) `MONTHLY_CLOSING_REPORT` capability SSOT.

3. **Given** AC #2 TS mirror + MonthlyClosingReportPanel + MonthlyClosingReportRoute + capability gate
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 wire contract 발동 (AC #3 — closing report signal source = 6-1 closing_period aggregate + 5-2 ledger events + 4-2 fiscal_period_snapshots 3-source join):
     - **`MonthlyInputStateResponse` extension (NEW 5 fields)**:
       - `monthly_closing_report_view_mode: ReportViewMode` (closing report 준비 상태 — 6-1 closing_period_status와 별도 필드)
       - `monthly_closing_report_closing_snapshot_count: int` (6-1 wire carry-over — closing_snapshot ledger event count)
       - `monthly_closing_report_ledger_event_count: int` (5-2 wire — 전체 ledger event count)
       - `monthly_closing_report_fiscal_period_snapshot_count: int` (4-2 wire — fiscal_period_snapshots count)
       - `monthly_closing_report_v4_verdict: V4Verdict | None` (6-1 V4 wire — closing snapshot 일관성 verdict)
     - **6-1 + 5-1 + 5-2 + 5-3 carry fields 보존**: 16 fields = `opening_inventory` + `opening_inventory_locked` + `opening_inventory_lock_reason_ko` (5-1) + `ledger_events_count` + `ledger_period_closing` + `inventory_ledger_enabled` + `reversal_request_enabled` (5-2) + `closing_guard_invariant` + `closing_guard_blocked` + `closing_guard_audit_trail` + `production_consumption_events` + `v3_verdict` (5-3) + `closing_period_status` + `closing_snapshot_count` + `closing_period_audit_trail` + `closing_period_finalized_at` (6-1) 그대로. 6-2 = 5 fields 신규 추가. 합계 21 fields.
     - **`MonthlyInputService.get_state` extension** — wire `monthly_closing_report_service.get_monthly_closing_report(session, tenant_id, period_key)` 호출 결과 + audit_trail query → 5 NEW fields populate.
     - **Read-only transaction pattern (extension `MonthlyInputService.get_state` + NEW `MonthlyInputService.get_monthly_closing_report`)** — REPEATABLE READ isolation level (4-2 wire 패턴) + no write (read-only aggregator). 6-1 confirm_closing_period 동일 session에서 동시 호출 시 충돌 방지.
     - **ClosingPerProductRow join (extension `MonthlyInputService.get_monthly_closing_report`)** — 3-source JOIN:
       1. `inventory_ledger` WHERE `event_type='closing_snapshot'` AND `period_key=:period_key` (6-1 wire) → per-product closing_qty.
       2. `inventory_ledger` 전체 WHERE `period_key=:period_key` (5-2 wire) → per-product ledger_event_count.
       3. `monthly_input_periods.opening_inventory` JSONB (5-1 wire) → per-product opening_qty.
       4. `fiscal_period_snapshots` WHERE `period_key=:period_key` AND `engine_type='trad'` (4-2 wire) → per-product fiscal_period_snapshot_count.
       5. Joins on `product_id` (UUID v7 SSOT — AD-18) + tenant_id (RLS — AD-3).
     - **KRW/USD dual display format (extension `MonthlyInputService.get_monthly_closing_report`)** — closing_per_product row:
       - `closing_qty_krw`: str (KRW 정수) — DB BIGINT 그대로.
       - `closing_qty_usd`: str (USD 소수 2자리) — `closing_qty_krw / exchange_rate` USD 환산 (banker's rounding to 2 decimals).
       - `delta_krw`: str (KRW 정수) — `closing_qty_krw - opening_qty_krw`.
       - `delta_usd`: str (USD 소수 2자리) — `delta_krw / exchange_rate` USD 환산.
       - `currency_pair`: `{ from_currency: 'USD', to_currency: 'KRW', rate: '1,320', rate_source_ko: '한국은행', rate_as_of: '2026-07-25' }` (`tenant_settings.baseline.currency_pair` SSOT).
     - **V4 verdict envelope wire (extension 6-1 + 4-3 V4 wire)** — `verification_log.action='verify_v4_closing_period_consistency'` (6-1 wire) + `top_failure.code='V4'` (4-3 wire) 그대로 보존. 6-2 wire는 V4 verdict envelope read-only 표시 (closing report의 V4 row).

4. **Given** AC #1~#3 backend wire + AC #2 frontend wire + 5-1/5-2/5-3/6-1/0.5/A12 carry-over
   **When** 본 스토리 commit 안에서 6-1 carry-over close + A11 capability matrix v1.8 wire + A11 V8 16-fixture matrix extension wire
   **Then** 다음 defense-in-depth + carry-over wire 발동 (AC #4 — A11 V8 16-fixture matrix extension + A8 inline projection timeline + closing report audit):
     - **A11 V8 16-fixture matrix extension (AC #4 — **A11 PRIMARY wire**)** — `packages/cost_engine/tests/regression_v8/fixtures/` 4 NEW 골든 files:
       1. `v4_closing_period_pass_manufacturing.json` (6-1 T10.5 deferred fill)
       2. `v4_closing_period_fail_manufacturing.json` (6-1 T10.5 deferred fill)
       3. `closing_snapshot_manufacturing.json` (A11 신규)
       4. `ledger_period_closing_manufacturing.json` (A11 신규)
       `V8_FIXTURE_COUNT 14 → 18` (6-1 14 골든 + 6-2 4 NEW). `fixture_publisher` CLI `--industry manufacturing --include-closing-period-snapshot --include-closing-snapshot` 추가.
     - **V8 byte-identical 골든 확장** — Story 4-4 14 fixture matrix × 6-2 4 NEW 골든 = 18 fixture matrix. `tests/regression_v8/test_regression_v8_fixtures.py` extension — 18 lock_sha256 + 18 byte-identical + 18 100x determinism + 4 NEW golt-12 shape + 4 NEW industry skip matrix cases. V8 mandatory CI gate 보존.
     - **A11 capability matrix v1.8 (extension `docs/capability-matrix.md`)** — Epic 5 retro §7 A10 결정 + 6-1 wire 완료:
       ```markdown
       | Capability | manufacturing | mfg+service | mfg+service+other | service-only |
       |------------|---------------|-------------|--------------------|--------------|
       | ... 기존 14+ capabilities (5-1/5-2/5-3/6-1) ... |
       | MONTHLY_CLOSING_REPORT (6-1 wire v1.3) | ✅ | ✅ | ✅ | ❌ INDUSTRY_NOT_SUPPORTED |
       ```
       Changelog v1.8 (6-1 wire done) + 6-2 reference: 6-2 spec 진입 시 MONTHLY_CLOSING_REPORT capability wire (manufacturing 3종 ✅ / service-only ❌) — 6-1 spec v1.3 wire 완료 reference.
     - **A8 inline projection deprecation timeline (Epic 5 retro §7 A8 결정)** — `docs/monthly-closing-report.md` (NEW 6-2) §timeline 섹션 명시:
       ```markdown
       ### A8 — Epic 3.3 inline projection deprecation timeline
       - **5-2 commit + 1 epic maintenance window 종료 시점 = Epic 6 close-out 시점**
       - 6-1 wire 시점 (Epic 6 진입점): inline projection 보존 (1 epic maintenance window 진행 중) + closing_period snapshot은 ledger aggregate (5-2 wire) 사용
       - 6-2 wire 시점 (Epic 6 2번째): inline projection 보존 상태로 wire + monthly_closing_report aggregator는 ledger aggregate + 5-2 wire + 6-1 wire + 4-2 wire 4-source read-only join
       - 6-3 wire: inline projection 보존 상태로 wire
       - Epic 6 close-out 시점에 fold-in vs deprecate 결정 (Epic 11 reversal 진입 시 inline projection 완전 제거)
       ```
     - **MonthlyClosingReport audit log wire (AC #3 #4)** — `audit_logs.action='monthly_closing_report_viewed'` (ActionClass.MONTHLY_CLOSING_REPORT 신규 value) 1 value. INSERT to audit_logs (immutable, AD-2). payload = self-describing (CR 1.1 lesson). read-only report의 자체 audit log emission trace.
     - **SQL CHECK constraint 추가 없음 (AC #4)** — 6-2 wire는 read-only aggregator. 6-1 wire Alembic 0017 chk_closing_period_status 그대로 활용. NEW Alembic migration 불요요.
     - **W4 vitest activation (Story 6-1 + 5-3 carry-over close)** — `tests/integration/test_monthly_closing_report_label_consistency.py` (NEW) + 5-3 `tests/integration/test_closing_period_label_consistency.py` extension. 3 NEW 6-2 cases 추가 (monthly_closing_report_view_mode_label_ko_parity, monthly_closing_report_title_ko_parity, monthly_closing_report_currency_pair_ko_parity). vitest infra (Story 0.5 AC #4 done) 활용. pytest.skip markers removed.
     - **W5 isolated service layer tests (Story 6-1 carry-over close)** — `tests/api/m4_inventory/test_monthly_closing_report_service.py` (NEW) — 12 cases: get_monthly_closing_report CLOSING_REPORT_READY success (3), CLOSING_REPORT_PARTIAL empty source (3), CLOSING_REPORT_EMPTY all 0 (2), KRW/USD dual display formatting (2), audit-first emission trace (2).
     - **6-2 AC #2 wire trigger frontend tests (Story 0.5 vitest + RTL wire)** — `apps/web/__tests__/monthly-closing-report-panel.test.tsx` (NEW) — 6 scenarios:
       1. `test_monthly_closing_report_panel_shows_when_ready` — view_mode=CLOSING_REPORT_READY → KPI 박스 4개 + Table + Recharts BarChart 모두 표시.
       2. `test_monthly_closing_report_panel_shows_partial` — view_mode=CLOSING_REPORT_PARTIAL → 일부 빈 source 표시 + "잠시 후 갱신" sonner toast.
       3. `test_monthly_closing_report_panel_shows_empty` — view_mode=CLOSING_REPORT_EMPTY → "마감 데이터 없음" Alert 표시 + Table/Chart 비노출.
       4. `test_monthly_closing_report_currency_pair_krw_usd_display` — KRW 1,320,000 + USD 1,000.00 (rate 1,320) dual display 검증.
       5. `test_monthly_closing_report_v4_verdict_pass` — V4 verdict PASS → KPI 박스에 "PASS" 녹색 + audit-trail에 `closing_period_confirmed` 표시.
       6. `test_monthly_closing_report_v4_verdict_fail` — V4 verdict FAIL → KPI 박스에 "FAIL" 빨강 + audit-trail에 `closing_period_snapshot_inconsistency` 표시.
     - **MonthlyInputTabs extension tests (vitest + RTL)** — `apps/web/__tests__/monthly-input-tabs.test.tsx` (5-3 wire + 6-1 extension) extension. 3 NEW 6-2 scenarios 추가 (MonthlyClosingReportPanel render, currency_pair display, service-only tenant hide).

5. **Given** AC #1~#4 backend wire + frontend wire + carry-over close + capability matrix v1.8 + V8 16-fixture matrix extension
   **When** 본 스토리 dev-story 진입 시 6-1 ClosingPeriodConfirmationPanel 위에 additive + 6-2 frontend MonthlyClosingReportPanel
   **Then** 다음 3-layer defense wire 발동 (AC #5 — PRD §A11 입력 시 경고 + 마감 시 차단 + 마감 확정 시 snapshot 3-layer + closing report 시각화):
     - **Layer 1 (입력 시 경고)** — Story 3.3 inline projection + 5-2 ledger aggregate 동시 활용. 음수 기초재고 / 출고 > 기초재고 입력 시 sonner `toast.warning` (5-3 wire 그대로).
     - **Layer 2 (마감 시 차단)** — Story 5.3 `closing_guard_service.request_close_attempt` + 4-2 `is_blocked` 위 additive. 음수 기말재고 발생 시 409 NEGATIVE_CLOSING_INVENTORY typed envelope + ClosingGuardBanner red Alert (5-3 wire 그대로).
     - **Layer 3 (마감 확정 시 snapshot)** — Story 6.1 `closing_period_service.confirm_closing_period` dispatch. CLOSING_READY 시 ledger INSERT (closing_snapshot event_type) + monthly_input_periods.status='closed' UPDATE + audit INSERT (atomic transaction). 409 ALREADY_CLOSED 시 멱등성 보장 (idempotent no-op skip).
     - **Layer 4 (마감 보고서 시각화)** — **6-2 `monthly_closing_report_service.get_monthly_closing_report`** dispatch. CLOSING_REPORT_READY 시 KPI 박스 4개 + Table + Chart + audit-trail 모두 표시. read-only aggregator의 시각화 Layer.
     - **Capability gate** — `Capability.MONTHLY_CLOSING_REPORT` (6-1 v1.8 wire) + `Capability.INVENTORY_LEDGER` (5-2 wire) + `Capability.MONTHLY_INPUT_PRODUCTION` (3-1 wire) 3 capabilities 모두 MONTHLY_CLOSING_REPORT 진입점에서 검증. service-only tenant → 403 INDUSTRY_NOT_SUPPORTED typed envelope (A10 결정).

6. **Given** AC #1~#5 backend + frontend + ClosingPeriodConfirmationPanel + MonthlyClosingReportPanel + capability gate
   **When** 본 스토리 dev-story 진입 시 V4 verification wire + V8 16-fixture matrix extension
   **Then** 다음 verification sync 발동 (AC #6 — V4 (closing snapshot 일관성) verification ↔ ledger aggregate ↔ closing_snapshot ledger events ↔ fiscal_period_snapshots 4-source 양방향 동기화 + V8 16-fixture matrix extension):
     - **V4 verdict wire (extension 6-1 + 4-3 V4 wire)** — V4 verifier dispatch 4-source read-only join:
       1. ledger aggregate = 5-2 `query_period_closing` 결과 (per product qty).
       2. closing_snapshot aggregate = inventory_ledger `event_type='closing_snapshot'` aggregate (per product qty).
       3. fiscal_period_snapshot aggregate = `fiscal_period_snapshots` engine_type='trad' aggregate (per product cost).
       4. product whitelist = 현재 tenant 활성 product UUID set.
       → `verify_monthly_closing_report_consistency` (T2 pure kernel) dispatch.
     - **V4 골든 fixture wire (extension `packages/cost_engine/tests/regression_v8/fixtures/`)** — 6-1 T10.5 deferred 골든 fill (6-1 13th defer close-out) + A11 신규:
       1. `v4_closing_period_pass_manufacturing.json` (6-1 T10.5 deferred fill) — ledger aggregate == closing_snapshot aggregate per product + V4 verdict = `passed` + audit `closing_period_confirmed`.
       2. `v4_closing_period_fail_manufacturing.json` (6-1 T10.5 deferred fill) — ledger aggregate != closing_snapshot aggregate (per-product qty 불일치) + V4 verdict = `failed` + audit `closing_period_snapshot_inconsistency` + top_failure.code='V4' + Korean message "마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요".
       3. `closing_snapshot_manufacturing.json` (A11 신규) — closing snapshot per-product qty + finalized_at ISO-8601 + audit_trail entries.
       4. `ledger_period_closing_manufacturing.json` (A11 신규) — ledger events per period (event_type='closing_snapshot' 포함) + ledger_event_count.
       V8_FIXTURE_COUNT 14 → 18. 4-4 `fixture_publisher` CLI `--industry manufacturing --include-closing-period-snapshot --include-closing-snapshot` 추가.
     - **V8 byte-identical 골든 확장** — Story 4-4 14 fixture matrix × 6-2 4 NEW 골든 = 18 fixture matrix. `tests/regression_v8/test_regression_v8_fixtures.py` extension — 18 lock_sha256 + 18 byte-identical + 18 100x determinism + 4 NEW golt-12 shape + 4 NEW industry skip matrix cases. V8 mandatory CI gate 보존.
     - **Verification ordering invariant (AD-12)** — V1 fail 시 V4 SKIP. V4 fail 시 V3 SKIP. V3 fail 시 V7 SKIP. V7 fail 시 V8 SKIP. abort-on-fail 패턴 그대로 (Story 4-3 + 5-3 + 6-1 wire).
     - **4-2 calc endpoint close-time hook (Epic 3 A4 wire) 위에 additive** — `POST /api/v1/calc` 응답 시 verdict field:
       - V4 fail → `top_failure.code='V4'` + `top_failure.message_ko='마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요'` + block_reason='CLOSING_PERIOD_SNAPSHOT_INCONSISTENCY'.
       - V4 pass → verdict.status='verified' + closing period snapshot OK.
     - **Industry skip matrix (4-3 wire 패턴)** — manufacturing / manufacturing_service / manufacturing_service_other → V4 RUN. service-only → V4 SKIP (inventory 의미 없음 + A10 MONTHLY_CLOSING_REPORT capability gate 동등 발동).

7. **Given** AC #1~#6 backend + frontend + V4 sync + V8 16-fixture matrix extension + verification ordering
   **When** 본 스토리 dev-story 진입 시 audit-first + idempotent no-op + A5 forward-lock + A7 wire + A8 inline projection timeline + A11 V8 16-fixture matrix
   **Then** 다음 audit + drift + A7 wire 발동 (AC #7 — A5 forward-lock + A7 wire + A8 timeline + A10 capability + A11 V8 골든 + A12 carry-over close):
     - **`apps/api/core/audit_action.py` extension** — `MonthlyClosingReportAction = Literal["monthly_closing_report_viewed"]` 1 value 신규 (closing report 조회 audit). + `VerificationAction` Literal 기존 `verify_v4_closing_period_consistency` 6-1 wire 그대로 (6-2 추가 변경 없음). **A5 forward-lock**: `_ActionRegistry._REGISTRY[ActionClass.MONTHLY_CLOSING_REPORT]` accepted frozenset 1 value fill + `_REGISTRY[ActionClass.VERIFICATION]` accepted frozenset 6 values 그대로 (6-1 wire 완료).
     - **A5 drift detector (`tests/services/test_audit_action_centralization.py` extension)** — ActionClass.MONTHLY_CLOSING_REPORT 1 new action 검증 pass. drift count = 0 유지.
     - **3-way consistency drift detector (`tests/integration/test_audit_action_consistency.py` extension)** — A5 forward-lock:
       - registry ↔ DB CHECK: ActionClass.MONTHLY_CLOSING_REPORT 1 value (registry SSOT) + ActionClass.VERIFICATION 6 values (registry SSOT + Story 4-3 wire 4 values + 5-3 wire 1 value + 6-1 wire 1 value) + ActionClass.CLOSING_PERIOD 3 values (6-1 wire).
       - call sites AST-grep: `emit_audit(` raw in `apps/api/modules/m4_inventory/` + `apps/api/modules/m6_verification/` = 0 (5-1 + 5-2 + 5-3 + 6-1 + 6-2 모두 typed).
       - verified DB constraint contents match published alembic migration files (Alembic 0013 + 0014 + 0015 + 0016 + 0017 모두 일치).
     - **A7 wire (Epic 4 close-out retro A7 — async test pattern + SDR overclaim)** — Story 5-2 + 5-3 + 6-1 wire pattern 그대로:
       - Async test pattern (CR 4-3 F-1) — 모든 service-layer test `def test_x(): asyncio.run(_impl())` wrapper (pytest-asyncio 금지).
       - SDR overclaim detector — `tests/integration/test_sdr_test_count_drift.py` 2 cases (5-1 + 5-2 + 5-3 + 6-1 + 6-2 wire pattern).
     - **`MonthlyClosingReportService.get_monthly_closing_report` CR 1.1 audit-first wire**:
       1. read-only aggregator — no INSERT + no UPDATE.
       2. **`emit_audit_typed(action_class=ActionClass.MONTHLY_CLOSING_REPORT, action='monthly_closing_report_viewed', ..., payload={period_key, tenant_id, view_mode, closing_snapshot_count, ledger_event_count, fiscal_period_snapshot_count, v4_verdict_status, actor_id, trace_id})`** INSERT to audit_logs (조회 자체 audit).
       3. CR 1.1 idempotent re-view 시 audit skip (read-only report — 한 조회당 1 audit).
     - **6-1 T10.5 deferred V4 골든 fixture fill (6-1 13th defer close-out)** — A11 spec 진입 시점에 dedup 결정. 6-1 carry-over 13th defer = V4 closing-period-snapshot PASS/FAIL 2 NEW 골든 fill. 6-2 AC #4 wire에 동시 dedup 결정:
       - `v4_closing_period_pass_manufacturing.json` + `v4_closing_period_fail_manufacturing.json` 2 NEW 골든 file (6-1 T10.5 deferred fill).
       - 6-1 closing-period.md §V4 골든 fixture deferred to T10.5 carry-over 결정 = 6-2 A11 wire에 통합 close-out.
       - 6-2 A11 spec 본문 §carry-over close-out 명시: "6-1 T10.5 deferred V4 골든 fixture fill = 6-2 A11 V8 16-fixture matrix extension wire에 통합 close-out".
     - **PR 일관성 guard** — Alembic 0017 migration 그대로 (6-2 wire는 NEW Alembic migration 추가 불요요). 5-3 + 6-1 cross-check (`tests/integration/test_alembic_migration_chain.py` extension — V4 closing period snapshot guard wire에 필수).

8. **Given** AC #1~#7 backend + frontend + V4 + audit + drift + A7 + A8 timeline + A10 capability + A11 V8 16-fixture matrix + A12 carry-over
   **When** 본 스토리 10 task (T1-T10) 실행
   **Then** 다음 tests wire 발동 (AC #8 — 3중 게이트 + drift detector + A5 + A7 + frontend vitest + Playwright):
     - **Pure kernel (2 NEW files — ~30 cases)**:
       - `tests/services/m4_inventory/test_monthly_closing_report.py` (NEW) — 18 cases: aggregate_monthly_closing_report (5), format_period_closing_krw_usd (3 — KRW 1,320,000 / USD 1,000.00 / rate 1,320), compute_usd_from_krw (2), classify_report_view_mode (3 CLOSING_REPORT_READY/CLOSING_REPORT_PARTIAL/CLOSING_REPORT_EMPTY/edge), is_monthly_closing_report_allowed (2), MONTHLY_CLOSING_REPORT_TITLE_KO + MONTHLY_CLOSING_REPORT_EMPTY_KO constants (2), banker's rounding (2 — CR 0-4 lesson), Decimal serialization parity (2).
       - `tests/cost_engine/test_monthly_closing_report_aggregator.py` (NEW) — 12 cases: V4 verdict PASS/FAIL/SKIP (3), 4-source aggregate 일치 검증 (3 — ledger + closing_snapshot + fiscal_period_snapshot + product whitelist), product whitelist mismatch (2), industry='service' skip (2), ordering invariant (V4 fail 후 abort, 2), banker's rounding (2).
     - **Service layer (3 NEW files — ~28 cases)**:
       - `tests/api/m4_inventory/test_monthly_closing_report_service.py` (NEW) — 12 cases (AC #4 wire spec).
       - `tests/api/m6_verification/test_monthly_closing_report_v4_verifier.py` (NEW) — 8 cases: verify_v4_closing_period_consistency PASS/FAIL (2), industry skip (1), product whitelist mismatch (1), ordering invariant (1), audit emission (1), idempotent (1), empty period (1).
       - `tests/api/m2_input/test_monthly_input_monthly_closing_report.py` (NEW) — 8 cases: get_monthly_closing_report CLOSING_REPORT_READY success (2), CLOSING_REPORT_PARTIAL empty source (2), audit-first ordering (2), idempotent re-view skip (2).
     - **3-way consistency drift detector (extension A5)** — `tests/integration/test_audit_action_consistency.py` extension — 4 NEW cases:
       - ActionClass.MONTHLY_CLOSING_REPORT registry ↔ DB CHECK consistency (2 cases).
       - ActionClass.VERIFICATION 6-2 unchanged ↔ Story 4-3 wire 4 values + 5-3 wire 1 value + 6-1 wire 1 value consistency (2 cases).
     - **V8 16-fixture matrix extension (AC #4 #6)** — `tests/regression_v8/test_regression_v8_fixtures.py` extension — 4 NEW 골든 + 18 fixture matrix:
       1. `v4_closing_period_pass_manufacturing.json` (6-1 T10.5 deferred fill) — 1 lock_sha256 + 1 byte-identical + 1 100x determinism + 1 V4 PASS shape + 1 industry skip matrix.
       2. `v4_closing_period_fail_manufacturing.json` (6-1 T10.5 deferred fill) — 1 lock_sha256 + 1 byte-identical + 1 100x determinism + 1 V4 FAIL shape + 1 industry skip matrix.
       3. `closing_snapshot_manufacturing.json` (A11 신규) — 1 lock_sha256 + 1 byte-identical + 1 100x determinism + 1 golt-12 shape + 1 industry skip matrix.
       4. `ledger_period_closing_manufacturing.json` (A11 신규) — 1 lock_sha256 + 1 byte-identical + 1 100x determinism + 1 golt-12 shape + 1 industry skip matrix.
       총 18 lock_sha256 + 18 byte-identical + 18 100x determinism + 18 golt-12 shape + 18 industry skip matrix = 90 cases (이전 14 골든 × 3 = 42 + 6-2 4 NEW × 5 = 20 = 62 골든 cases + 18 industry skip matrix + 18 fixture_publisher CLI smoke = 90 cases).
     - **V8 골든 fill CLI smoke (Story 4-4 + 6-1 carry-over close)** — `tests/integration/test_regression_v8_publisher.py` extension — 4 NEW cases:
       1. `test_v4_closing_period_pass_manufacturing_publish` — `--industry manufacturing --include-closing-period-snapshot` → 2 NEW 골든 file 생성 검증.
       2. `test_v4_closing_period_fail_manufacturing_publish` — `--industry manufacturing --include-closing-period-snapshot` → 2 NEW 골든 file 생성 검증.
       3. `test_closing_snapshot_manufacturing_publish` — `--industry manufacturing --include-closing-snapshot` → 1 NEW 골든 file 생성 검증.
       4. `test_ledger_period_closing_manufacturing_publish` — `--industry manufacturing --include-closing-snapshot` → 1 NEW 골든 file 생성 검증.
     - **KRW/USD dual display format tests (AC #3)** — `tests/api/m4_inventory/test_monthly_closing_report_krw_usd.py` (NEW) — 6 cases: KRW 1,320,000 / rate 1,320 → USD 1,000.00 (2), KRW 0 / rate 1,320 → USD 0.00 (2), banker's rounding 1,325,000 / rate 1,000 → USD 1,325.00 (banker's rounding — ROUND_HALF_EVEN verifies) (2).
     - **SQL CHECK constraint test (AC #4)** — 6-2 wire는 NEW Alembic migration 추가 불요요. 6-1 wire Alembic 0017 chk_closing_period_status 그대로 활용. `tests/integration/test_closing_period_sql_check.py` (6-1 wire) 그대로 보존.
     - **frontend vitest (Story 0.5 wire)** — 21 scenarios:
       1. `apps/web/__tests__/monthly-closing-report-panel.test.tsx` (NEW) — 6 scenarios (AC #4 wire spec).
       2. `apps/web/__tests__/monthly-input-tabs.test.tsx` (5-3 wire + 6-1 extension) extension — 3 NEW 6-2 scenarios 추가 (MonthlyClosingReportPanel render, currency_pair display, service-only tenant hide).
       3. `apps/web/__tests__/monthly-closing-report-route.test.tsx` (NEW) — 12 scenarios: page load + KPI 박스 4개 + Table rendering + Recharts BarChart render + V4 verdict PASS/FAIL/SKIP + audit-trail list + currency_pair display + service-only 403 redirect + 409 CLOSING_PERIOD_BLOCKED + 409 ALREADY_CLOSED + 409 EMPTY_PERIOD.
     - **Playwright E2E (Story 0.5 wire)** — 6 E2E scenarios:
       1. `tests/e2e/monthly-closing-report.spec.ts` (NEW) — 6 scenarios.
       2. happy-path: [월 입력] → 6 stream 입력 → [마감] tab → ClosingPeriodConfirmationPanel → [마감 확정] → MonthlyClosingReportPanel 자동 표시 → KPI 박스 4개 + Table + Chart 검증.
       3. partial-path: 6 stream 일부만 입력 → CLOSING_REPORT_PARTIAL 표시 → "잠시 후 갱신" sonner toast 검증.
       4. KRW/USD dual display: 제품 A closing_qty 1,320,000 / rate 1,320 → USD 1,000.00 cell 검증.
       5. V4 verdict PASS: closing snapshot 일치 → KPI PASS 녹색 + audit-trail `closing_period_confirmed` 표시.
       6. V4 verdict FAIL: closing snapshot 불일치 (test scenario) → KPI FAIL 빨강 + audit-trail `closing_period_snapshot_inconsistency` 표시.
       7. service-only 차단: service-only tenant 진입 → 403 INDUSTRY_NOT_SUPPORTED + sonner toast.error.
       8. capability gate: MONTHLY_CLOSING_REPORT capability 미보유 tenant → 403 typed envelope + MonthlyClosingReportPanel 비노출.

9. **Given** AC #1~#8 backend + frontend + V4 + V8 16-fixture matrix + audit + drift + A7 + A8 timeline + A10 capability + A11 V8 골든 + A12 carry-over close
   **When** 본 스토리 dev-story 진입 시 Story 0.5 frontend plumbing 위 additive + 6-1 ClosingPeriodConfirmationPanel 위에 additive
   **Then** 다음 3-layer defense + read-only visualization wire 발동 (AC #9 — PRD §A11 4-layer + closing report + 6-1 wire carry-over + capability gate):
     - **PRD §A11 4-layer (extension 6-1 3-layer)** — 6-1 wire 3-layer 위에 additive Layer 4 closing report 시각화:
       1. **Layer 1 (입력 시 경고)** — Story 3.3 inline projection + 5-2 ledger aggregate 동시 활용. 음수 기초재고 / 출고 > 기초재고 입력 시 sonner `toast.warning` (5-3 wire 그대로).
       2. **Layer 2 (마감 시 차단)** — Story 5.3 `closing_guard_service.request_close_attempt` + 4-2 `is_blocked` 위 additive. 음수 기말재고 발생 시 409 NEGATIVE_CLOSING_INVENTORY typed envelope + ClosingGuardBanner red Alert (5-3 wire 그대로).
       3. **Layer 3 (마감 확정 시 snapshot)** — Story 6.1 `closing_period_service.confirm_closing_period` dispatch. CLOSING_READY 시 ledger INSERT (closing_snapshot event_type) + monthly_input_periods.status='closed' UPDATE + audit INSERT (atomic transaction). 409 ALREADY_CLOSED 시 멱등성 보장 (idempotent no-op skip).
       4. **Layer 4 (마감 보고서 시각화)** — **6-2 `monthly_closing_report_service.get_monthly_closing_report`** dispatch. 3-source read-only aggregate (closing_snapshot + ledger events + fiscal_period_snapshots) + KRW/USD dual display (AD-8 + PRD §F5.2) + V4 verdict envelope (6-1 wire) + audit-trail list (CR 1.1) 한 페이지 시각화.
     - **Capability gate (3-tier defense)** — `Capability.MONTHLY_CLOSING_REPORT` (6-1 v1.8 wire) + `Capability.INVENTORY_LEDGER` (5-2 wire) + `Capability.MONTHLY_INPUT_PRODUCTION` (3-1 wire) 3 capabilities 모두 MONTHLY_CLOSING_REPORT 진입점 + read-only endpoints + V4 verifier 진입점에서 검증. service-only tenant → 403 INDUSTRY_NOT_SUPPORTED typed envelope (A10 결정).

10. **Given** AC #1~#9 backend + frontend + V4 + V8 16-fixture matrix + audit + drift + A7 + A8 timeline + A10 capability + A11 V8 골든 + A12 carry-over + PRD §A11 4-layer + capability gate
    **When** 본 스토리 10 task (T1-T10) 실행 + 6-1 carry-over close + A11 V8 16-fixture matrix extension wire
    **Then** 다음 defense-in-depth + read-only visualization wire 발동 (AC #10 — 6-1 carry-over close + A11 V8 골든 + 5-1/5-2/5-3/6-1 founding + docs 5 NEW + 4 EXTENSION + 3중 게이트 mandatory CI):
      - **Backend 6 NEW files**: 
        1. `packages/services/m4_inventory/monthly_closing_report.py` (NEW pure kernel #1) — aggregate_monthly_closing_report + format_period_closing_krw_usd + compute_usd_from_krw + classify_report_view_mode + is_monthly_closing_report_allowed + MONTHLY_CLOSING_REPORT_TITLE_KO + MONTHLY_CLOSING_REPORT_EMPTY_KO constants.
        2. `packages/cost_engine/monthly_closing_report_aggregator.py` (NEW pure kernel #2) — verify_monthly_closing_report_consistency (V4 extension 4-source).
        3. `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py` (NEW service layer) — MonthlyClosingReportService class with 3 operations.
        4. `apps/api/modules/m4_inventory/handlers.py` (extension) — 3 NEW routes (GET /monthly-closing-report + GET /monthly-closing-report/audit-trail + GET /monthly-closing-report/v4-verdict).
        5. `apps/api/core/audit_action.py` (extension) — MonthlyClosingReportAction = Literal["monthly_closing_report_viewed"] 1 value 신규 + ActionClass.MONTHLY_CLOSING_REPORT 1 NEW class + _REGISTRY 1 value fill.
        6. `apps/api/modules/m2_input/services/monthly_input_service.py` (extension) — MonthlyInputService.get_monthly_closing_report NEW method + get_state 5 NEW fields populate.
      - **Backend 8 EXTENSION files**:
        1. `apps/api/alembic/versions/0017_closing_period.py` (6-1 wire) — 그대로 활용 (NEW Alembic migration 추가 불요요).
        2. `apps/api/main.py` (extension) — 0 NEW exception handlers (6-2 wire는 read-only aggregator, 6-1 wire 5 NEW exception handlers 그대로 활용).
        3. `apps/api/core/capability.py` (extension) — Capability.MONTHLY_CLOSING_REPORT 6-1 wire 그대로 활용.
        4. `apps/api/modules/m6_verification/services/verification_runner.py` (extension) — V4 verification wire 6-1 wire 그대로 활용 (no change).
        5. `apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py` (6-1 wire) — extension. 4-source aggregate (closing_snapshot + ledger events + fiscal_period_snapshots + product whitelist) 동시 검증.
        6. `apps/api/core/pydantic_schemas.py` (extension) — MonthlyClosingReportRow + MonthlyClosingReportResponse Pydantic v2 schemas.
        7. `tests/regression_v8/fixtures/` (extension) — 4 NEW 골든 files (v4_closing_period_pass_manufacturing.json + v4_closing_period_fail_manufacturing.json + closing_snapshot_manufacturing.json + ledger_period_closing_manufacturing.json).
        8. `tests/integration/test_alembic_migration_chain.py` (extension) — V4 closing period snapshot guard wire에 필수 (6-1 wire pattern 그대로).
      - **Frontend 4 NEW files**:
        1. `apps/web/lib/monthly-closing-report.ts` (NEW TS mirror) — type definitions + format helpers.
        2. `apps/web/lib/monthly-closing-report-parity.ts` (NEW TS↔Python SSOT parity helper) — Decimal serialization + QTY_QUANTUM banker's rounding.
        3. `apps/web/components/m2-input/MonthlyClosingReportPanel.tsx` (NEW component) — shadcn Card + Table + Recharts BarChart pattern.
        4. `apps/web/app/m2-input/period/[period_key]/monthly-closing-report/page.tsx` (NEW Next.js App Router page) — server-side fetch + client-side hydration + capability gate.
      - **Frontend 4 EXTENSION files**:
        1. `apps/web/lib/closing-period.ts` (6-1 wire) — MonthlyClosingReportView interface export 추가.
        2. `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire + 6-1 extension) — MonthlyClosingReportPanel wire (ClosingPeriodConfirmationPanel right side extension).
        3. `apps/web/lib/m2-input-warnings.ts` (3-3 wire) — 그대로 활용 (no change).
        4. `apps/web/messages/ko-KR.json` (extension) — 11 NEW strings (panel_title_ko + panel_subtitle_ko + kpi_closing_snapshot_count + kpi_ledger_event_count + kpi_fiscal_period_snapshot_count + kpi_v4_verdict + table_opening_qty + table_closing_qty + table_closing_qty_usd + table_delta + table_delta_usd + toast_view_partial + toast_view_empty + toast_error_krw_usd_rate_missing + toast_error_industry_not_supported).
      - **Test 8 NEW + 8 EXTENSION files**: ~110 NEW cases 추가 (pure 30 + service 28 + drift 4 + V8 16-fixture matrix 20 + V8 publisher CLI 4 + KRW/USD 6 + 6-1 carry-over close 12 + TS mirror parity 9 + frontend vitest 21 + Playwright E2E 6).
      - **docs 5 NEW + 4 EXTENSION**:
        1. `docs/monthly-closing-report.md` (NEW) — Story 6.2 operator/dev guide.
        2. `docs/closing-period.md` (6-1 wire) — §V4 골든 fixture deferred to T10.5 → 6-2 carry-over close-out 명시 (v4_closing_period_pass_manufacturing.json + v4_closing_period_fail_manufacturing.json 6-2 A11 wire에 통합).
        3. `docs/capability-matrix.md` (extension) — v1.8 (6-1 wire done) + 6-2 reference (no change).
        4. `docs/conventions.md` (extension) — §0.5 + §9 + §10.7 + §11 (audit actions + monthly closing report wire).
        5. `docs/cost-engine.md` (extension) — §V4 (closing snapshot 일관성) + §V8 (1원 단위 회귀) + §V8 골든 18 fixtures matrix.
        6. `docs/architecture-inventory.md` (extension) — m4_inventory module 6-2 wire 3 NEW routes + 3 NEW services + 2 NEW pure kernels.
        7. `docs/inventory-ledger.md` (extension) — §5.2 (Story 6.2 closing report aggregator).
        8. `docs/closing-guard.md` (extension) — §5.3 (5-3 wire) + §6.2 (Story 6.2 closing report 시각화 layer).
      - **3중 게이트 mandatory CI**:
        - ruff scoped (6-2 surface + 6-1 carry-over close 33 files) All checks passed.
        - import-linter 2 KEPT 0 broken (cost_engine_forbidden_io + engine_core_to_adapters_forbidden).
        - pytest **1,164 + 110 = 1,274+ passed + 127 skipped + 0 failed** in 73.68s + 6-2 carry-over (final 6-2 wave) **1,274 + 49 = 1,323+ passed + 127 skipped + 0 failed** (T10.5 carry-over close-out 49 NEW tests).
        - frontend vitest 21 scenarios (6-2 panel + 6-2 route + 6-2 tabs extension) + 23 carry-over (5-3 baseline + 6-1 carry-over) = 44 scenarios.
        - Playwright E2E 6 scenarios (6-2 NEW) + 11 carry-over (5-3 + 6-1) = 17 scenarios.

## Dev Agent Guardrails

### Critical Architecture Compliance

- **AD-1 Modular Monolith + Hexagonal Core** — 6-2 wire는 engine pure helper + service layer + handlers 표준 3-tier 패턴 (5-1/5-2/5-3/6-1 동일). `packages/cost_engine/monthly_closing_report_aggregator.py` (NEW pure kernel #2) + `packages/services/m4_inventory/monthly_closing_report.py` (NEW pure kernel #1) + `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py` (NEW service layer) + `apps/api/modules/m4_inventory/handlers.py` (extension handlers).
- **AD-2 Append-only ledger** — 6-2 wire는 read-only consumer. 5-2 inventory_ledger SSOT + RLS 4-policy + PostgreSQL `BEFORE UPDATE OR DELETE` trigger 그대로 활용. closing_snapshot ledger event (6-1 wire) = read-only select.
- **AD-3 Multi-tenant RLS** — 6-2 wire는 RLS 위에서 동작 (read-only). `tenant_id` 자동 derive from JWT (AD-3 SSOT). service_role bypass 불요요 (read-only aggregator).
- **AD-4 Atomicity** — 6-2 wire는 read-only transaction. REPEATABLE READ isolation level (4-2 wire 패턴) + no write.
- **AD-6 Fiscal-period close lock** — 6-2 wire는 monthly_input_periods.status='closed' 상태 read-only 표시. AD-6 close lock 보존.
- **AD-8 Monetary types** — **6-2 PRIMARY**: KRW = BIGINT (정수) + USD = NUMERIC(18,2) (소수 2자리) + tenant_settings.baseline.currency_pair = USD/KRW 환율 source. KRW/USD dual display (PRD §F5.2).
- **AD-11 Dependency direction** — 6-2 pure kernel #1 (services m4_inventory) = stdlib-only. pure kernel #2 (cost_engine) = stdlib-only. NO sqlalchemy import (engine layer). service layer가 ledger aggregate + closing_snapshot aggregate + fiscal_period_snapshot aggregate + product whitelist 인자로 전달.
- **AD-12 Verification ordering** — V1 → V4 → V3 → V7 → V8 ordering 보존. 6-2 wire는 V4 verdict envelope read-only 표시 (V4 wire 6-1). abort-on-fail 패턴 (Story 4-3 + 5-3 + 6-1 wire).
- **AD-15 Cross-language parity** — TS mirror drift detector `tests/integration/test_monthly_closing_report_label_consistency.py` (NEW) + Decimal serialization parity (KRW 정수 + USD 소수 2자리 + banker's rounding + QTY_QUANTUM).
- **AD-16 Fiscal snapshot contract** — 6-2 wire는 fiscal_period_snapshots read-only consumer (M3 + M11만 writer). 6-1 closing_snapshot ledger event + 4-2 fiscal_period_snapshots = closing report의 cost data source.
- **AD-18 Single product identity** — `inventory_ledger.product_id` (UUID v7) = PRODUCT(product_id) SSOT. monthly_closing_report per-product aggregation = product_id SSOT.
- **AD-22 Reversal construction** — 6-2 wire는 read-only consumer. correction은 Epic 11 reversal module ships 후 (A9 결정 deferred). 6-2 wire는 closing_period만 read + A9 carry-over 결정.
- **AD-23 4-namespace pattern + 5 namespace read-only** — monthly_input_periods + monthly_input_rows + inventory_ledger + audit_logs + fiscal_period_snapshots 5 namespace read-only aggregate. 6-2 wire는 5 namespace 모두 read-only aggregate.
- **AD-24 Typed period-key** — 'YYYY-MM' 형식 SSOT. monthly_closing_report per period_key. monthly_closing_report service는 `monthly_input_periods.period_key` AD-24 typed.

### Critical Lessons Applied (Meta-Learning)

- **CR 1.1 audit-first + idempotent no-op** — 6-2 wire는 read-only aggregator, but `monthly_closing_report_viewed` 자체 audit log INSERT (조회 trace). idempotent re-view 시 audit skip (1 view = 1 audit).
- **CR 4-3 async test pattern** — 모든 service-layer test `def test_x(): asyncio.run(_impl())` wrapper (pytest-asyncio 금지). 6-2 wire 12 cases 동일 pattern.
- **CR 4-3 SDR overclaim detector** — `tests/integration/test_sdr_test_count_drift.py` 2 cases (5-1 + 5-2 + 5-3 + 6-1 + 6-2 wire pattern).
- **CR 4-4 V8 골든 byte-identical** — 6-2 wire = V8 16-fixture matrix extension (4 NEW 골든 files). 모든 골든 byte-identical CI gate.
- **CR 0-4 banker's rounding parity** — `QTY_QUANTUM = Decimal("0.0001")` (NUMERIC(18,4)) + `quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)`. USD 환산 ROUND_HALF_EVEN precision to 2 decimal places.
- **CR 2-1 capability matrix 4 epic 연속 자산** — `MONTHLY_CLOSING_REPORT` capability 6-1 wire v1.8 그대로 활용. 6-2 spec 본문 §A10 matrix v1.8 reference.
- **CR 6-1 V4 naming collision** — 6-1 wire V4 cost/income slot (post-confirm consistency step 2.5) + 6-2 wire V4 closing-period-consistency slot (6-1 wire) + 6-2 wire V4 4-source aggregator (NEW extension). 6-2 AC #6 V4 verdict wire = 6-1 V4 wire + 4-source aggregator extension.
- **CR 6-1 local import shadowing F823** — monthly_input_service.py 6-1 wire F823 fix (line 1120 redundant local import) + 6-2 wire 동일 F823 lint scoped 적용.

### Library/Framework Requirements

- **stack pin (AD-14)** — 6-2 wire는 stack pin 변동 0. Node 24.18 LTS / Next.js 16.2.11 / React 19.2.8 / TypeScript 7.0.2 / Tailwind 4.3.3 / FastAPI 0.139.2 / Python 3.12 / PostgreSQL 17 / structlog 26.1.0 / uv 0.11.32 / OpenTelemetry 1.44.0 그대로 활용.
- **shadcn Card primitive** — 6-2 wire 신규 도입. `pnpm dlx shadcn@latest add card` (Story 0.5 wire + 6-1 wire + 6-3 wire). 6-2 wire = Card primitive (KPI 박스 4개 + Table + Chart container).
- **shadcn Table primitive** — 6-2 wire 신규 도입. `pnpm dlx shadcn@latest add table`. 6-2 wire = Table primitive (closing_per_product rows).
- **Recharts BarChart** — 6-2 wire 신규 도입. PRD §F5 wire + ADR. 6-3 wire (PDF export)는 Recharts SVG → PDF 변환.
- **decimal.js** — 6-2 wire KRW/USD dual display. TS Decimal serialization parity (banker's rounding + QTY_QUANTUM).
- **next-intl** — 6-2 wire ko-KR.json 11 NEW strings (Story 0.5 + 6-1 wire + 6-2 wire + 6-3 wire 통합).
- **sonner** — 6-2 wire toast.success + toast.error + toast.info (5-3 + 6-1 wire + 6-2 wire).

### File Structure Requirements

#### Backend 6 NEW files

1. `packages/services/m4_inventory/monthly_closing_report.py` (NEW pure kernel #1) — stdlib-only AD-11 layer rule.
2. `packages/cost_engine/monthly_closing_report_aggregator.py` (NEW pure kernel #2) — stdlib-only AD-11 layer rule.
3. `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py` (NEW service layer) — MonthlyClosingReportService class.
4. `apps/api/modules/m4_inventory/handlers.py` (extension) — 3 NEW routes (read-only).
5. `apps/api/core/audit_action.py` (extension) — MonthlyClosingReportAction 1 value + ActionClass.MONTHLY_CLOSING_REPORT 1 NEW class.
6. `apps/api/modules/m2_input/services/monthly_input_service.py` (extension) — MonthlyInputService.get_monthly_closing_report NEW method.

#### Backend 8 EXTENSION files

1. `apps/api/alembic/versions/0017_closing_period.py` (6-1 wire) — 그대로 활용 (NEW Alembic migration 추가 불요요).
2. `apps/api/main.py` (extension) — 0 NEW exception handlers (6-2 wire는 read-only).
3. `apps/api/core/capability.py` (extension) — Capability.MONTHLY_CLOSING_REPORT 6-1 wire 그대로 활용.
4. `apps/api/modules/m6_verification/services/verification_runner.py` (extension) — V4 verification wire 6-1 wire 그대로 활용 (no change).
5. `apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py` (6-1 wire) — extension. 4-source aggregate (closing_snapshot + ledger events + fiscal_period_snapshots + product whitelist) 동시 검증.
6. `apps/api/core/pydantic_schemas.py` (extension) — MonthlyClosingReportRow + MonthlyClosingReportResponse Pydantic v2 schemas.
7. `tests/regression_v8/fixtures/` (extension) — 4 NEW 골든 files (v4_closing_period_pass_manufacturing.json + v4_closing_period_fail_manufacturing.json + closing_snapshot_manufacturing.json + ledger_period_closing_manufacturing.json).
8. `tests/integration/test_alembic_migration_chain.py` (extension) — V4 closing period snapshot guard wire에 필수 (6-1 wire pattern).

#### Frontend 4 NEW files

1. `apps/web/lib/monthly-closing-report.ts` (NEW TS mirror) — type definitions + format helpers.
2. `apps/web/lib/monthly-closing-report-parity.ts` (NEW TS↔Python SSOT parity helper) — Decimal serialization + QTY_QUANTUM banker's rounding.
3. `apps/web/components/m2-input/MonthlyClosingReportPanel.tsx` (NEW component) — shadcn Card + Table + Recharts BarChart pattern.
4. `apps/web/app/m2-input/period/[period_key]/monthly-closing-report/page.tsx` (NEW Next.js App Router page) — server-side fetch + client-side hydration + capability gate.

#### Frontend 4 EXTENSION files

1. `apps/web/lib/closing-period.ts` (6-1 wire) — MonthlyClosingReportView interface export 추가.
2. `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire + 6-1 extension) — MonthlyClosingReportPanel wire.
3. `apps/web/lib/m2-input-warnings.ts` (3-3 wire) — 그대로 활용 (no change).
4. `apps/web/messages/ko-KR.json` (extension) — 11 NEW strings.

### Testing Requirements

- **3중 게이트 mandatory CI**:
  - ruff scoped (6-2 surface + 6-1 carry-over close 33 files) All checks passed.
  - import-linter 2 KEPT 0 broken (cost_engine_forbidden_io + engine_core_to_adapters_forbidden).
  - pytest 1,164+ 110 + 49 = 1,323+ passed + 127 skipped + 0 failed.
  - frontend vitest 21 + 23 = 44 scenarios.
  - Playwright E2E 6 + 11 = 17 scenarios.
- **Async test pattern (CR 4-3 F-1)** — `def test_x(): asyncio.run(_impl())` wrapper.
- **SDR overclaim detector (CR 4-3 F-2)** — 6-2 wire = A7 wire pattern + 2 NEW cases.
- **V8 골든 byte-identical (CR 4-4)** — 18 lock_sha256 + 18 byte-identical + 18 100x determinism + 18 golt-12 shape + 18 industry skip matrix = 90 cases.
- **V8 publisher CLI smoke (6-1 carry-over close)** — 4 NEW cases (V4 closing-period PASS/FAIL + closing_snapshot + ledger_period_closing).
- **KRW/USD dual display format tests** — 6 cases (KRW 1,320,000 / rate 1,320 → USD 1,000.00 + banker's rounding parity).
- **SQL CHECK constraint test** — 6-1 wire test 그대로 활용 (6-2 wire NEW Alembic migration 추가 불요요).

## Tasks (T1-T10, 70+ subtasks)

### T1. Pure kernel #1 — `packages/services/m4_inventory/monthly_closing_report.py` (NEW)
- T1.1 — `aggregate_monthly_closing_report` (closing_snapshot_events + ledger_events + fiscal_period_snapshots → aggregate)
- T1.2 — `format_period_closing_krw_usd` (KRW 정수 + USD 소수 2자리 dual display)
- T1.3 — `compute_usd_from_krw` (pure USD 환산 — banker's rounding)
- T1.4 — `classify_report_view_mode` (CLOSING_REPORT_READY/PARTIAL/EMPTY)
- T1.5 — `is_monthly_closing_report_allowed` (= mode == CLOSING_REPORT_READY)
- T1.6 — `MONTHLY_CLOSING_REPORT_TITLE_KO` + `MONTHLY_CLOSING_REPORT_EMPTY_KO` constants
- T1.7 — banker's rounding via `QTY_QUANTUM` from `inventory_projection` (CR 0-4 lesson)
- T1.8 — 1 typed exception (`MonthlyClosingReportError`)

### T2. Pure kernel #2 — `packages/cost_engine/monthly_closing_report_aggregator.py` (NEW)
- T2.1 — `verify_monthly_closing_report_consistency` (4-source aggregate 일치 검증 — V4 extension)
- T2.2 — V4 verdict PASS/FAIL/SKIP (AD-12 ordering 보존)
- T2.3 — industry='service' → V4 SKIP (4-3 wire pattern + A10 capability gate 동등)
- T2.4 — 1 typed exception (`MonthlyClosingReportInconsistencyError`)

### T3. Service layer #1 — `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py` (NEW)
- T3.1 — `MonthlyClosingReportService.get_monthly_closing_report` (3-source read-only join)
- T3.2 — `MonthlyClosingReportService.get_monthly_closing_report_audit_trail` (CR 1.1 observability)
- T3.3 — `MonthlyClosingReportService.verify_monthly_closing_report_v4` (V4 verification dispatch)
- T3.4 — REPEATABLE READ isolation level (4-2 wire pattern) + no write
- T3.5 — 3-source JOIN: inventory_ledger closing_snapshot + inventory_ledger 전체 + monthly_input_periods opening_inventory + fiscal_period_snapshots engine_type='trad' (AC #3)
- T3.6 — KRW/USD dual display format (closing_qty_krw + closing_qty_usd + delta_krw + delta_usd + currency_pair)
- T3.7 — CR 1.1 audit-first ordering for `monthly_closing_report_viewed`

### T4. Wire trigger — `apps/api/modules/m4_inventory/handlers.py` (extension)
- T4.1 — `GET /api/v1/inventory/monthly-closing-report?period_key=...` — read-only closing report endpoint
- T4.2 — `GET /api/v1/inventory/monthly-closing-report/audit-trail?period_key=...` — audit log emission trace
- T4.3 — `GET /api/v1/inventory/monthly-closing-report/v4-verdict?period_key=...` — V4 verdict read-only
- T4.4 — Capability gate `MONTHLY_CLOSING_REPORT` (6-1 wire 완료)
- T4.5 — 409 typed envelopes 확장 (409 EMPTY_PERIOD → 409 CLOSING_REPORT_EMPTY_READY)

### T5. A5 forward-lock + A11 capability matrix + 6-1 carry-over close
- T5.1 — `apps/api/core/audit_action.py` extension — MonthlyClosingReportAction 1 value + ActionClass.MONTHLY_CLOSING_REPORT 1 NEW class + _REGISTRY 1 value fill
- T5.2 — `docs/capability-matrix.md` v1.8 reference (6-1 wire done) + 6-2 reference (no change)
- T5.3 — A5 drift detector (`tests/services/test_audit_action_centralization.py` extension) — ActionClass.MONTHLY_CLOSING_REPORT 1 new action 검증 pass
- T5.4 — 3-way consistency drift detector (`tests/integration/test_audit_action_consistency.py` extension) — 4 NEW cases
- T5.5 — 6-1 carry-over close (T10.5 deferred V4 골든 fixture fill) 명시: 6-2 AC #4 wire에 통합 close-out

### T6. A11 V8 16-fixture matrix extension (AC #4 #6 — **A11 PRIMARY wire**)
- T6.1 — `v4_closing_period_pass_manufacturing.json` (6-1 T10.5 deferred fill)
- T6.2 — `v4_closing_period_fail_manufacturing.json` (6-1 T10.5 deferred fill)
- T6.3 — `closing_snapshot_manufacturing.json` (A11 신규)
- T6.4 — `ledger_period_closing_manufacturing.json` (A11 신규)
- T6.5 — `fixture_publisher` CLI `--industry manufacturing --include-closing-period-snapshot --include-closing-snapshot` 추가
- T6.6 — `tests/regression_v8/test_regression_v8_fixtures.py` extension — 18 fixture matrix + 90 cases
- T6.7 — `tests/integration/test_regression_v8_publisher.py` extension — 4 NEW cases
- T6.8 — V8 mandatory CI gate 보존 (industry skip matrix + byte-identical + 100x determinism)

### T7. Frontend wire — TS mirror + MonthlyClosingReportPanel + MonthlyClosingReportRoute
- T7.1 — `apps/web/lib/monthly-closing-report.ts` (NEW TS mirror) — type definitions + format helpers
- T7.2 — `apps/web/lib/monthly-closing-report-parity.ts` (NEW TS↔Python SSOT parity helper)
- T7.3 — `apps/web/lib/closing-period.ts` (6-1 wire) — MonthlyClosingReportView interface export 추가
- T7.4 — `apps/web/components/m2-input/MonthlyClosingReportPanel.tsx` (NEW) — shadcn Card + Table + Recharts BarChart pattern
- T7.5 — `apps/web/app/m2-input/period/[period_key]/monthly-closing-report/page.tsx` (NEW) — Next.js App Router page
- T7.6 — `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire + 6-1 extension) — MonthlyClosingReportPanel wire
- T7.7 — `apps/web/messages/ko-KR.json` (extension) — 11 NEW strings
- T7.8 — Capability-gated UI (service-only tenant → MonthlyClosingReportPanel 비노출 + 403 redirect)

### T8. frontend vitest + RTL + Playwright E2E
- T8.1 — `apps/web/__tests__/monthly-closing-report-panel.test.tsx` (NEW) — 6 scenarios
- T8.2 — `apps/web/__tests__/monthly-input-tabs.test.tsx` (5-3 wire + 6-1 extension) extension — 3 NEW 6-2 scenarios
- T8.3 — `apps/web/__tests__/monthly-closing-report-route.test.tsx` (NEW) — 12 scenarios
- T8.4 — `tests/e2e/monthly-closing-report.spec.ts` (NEW) — 6 E2E scenarios (happy-path + partial-path + KRW/USD dual display + V4 PASS/FAIL + service-only 차단 + capability gate)

### T9. backend tests ~70 cases
- T9.1 — `tests/services/m4_inventory/test_monthly_closing_report.py` (NEW) — 18 cases (T1 pure kernel #1)
- T9.2 — `tests/cost_engine/test_monthly_closing_report_aggregator.py` (NEW) — 12 cases (T2 pure kernel #2)
- T9.3 — `tests/api/m4_inventory/test_monthly_closing_report_service.py` (NEW) — 12 cases (T3 service layer #1)
- T9.4 — `tests/api/m6_verification/test_monthly_closing_report_v4_verifier.py` (NEW) — 8 cases (T3 V4 verifier)
- T9.5 — `tests/api/m2_input/test_monthly_input_monthly_closing_report.py` (NEW) — 8 cases (T3 service layer)
- T9.6 — `tests/api/m4_inventory/test_monthly_closing_report_krw_usd.py` (NEW) — 6 cases (AC #3 KRW/USD dual display)
- T9.7 — `tests/integration/test_monthly_closing_report_label_consistency.py` (NEW) — 9 cases (AD-15 cross-language parity)
- T9.8 — `tests/integration/test_monthly_closing_report_v4_verdict.py` (NEW) — 4 cases (V4 verification wire)

### T10. docs 5 NEW + 4 EXTENSION + 3중 게이트 mandatory CI + carry-over close
- T10.1 — `docs/monthly-closing-report.md` (NEW) — Story 6.2 operator/dev guide (6-1 closing-period.md pattern)
- T10.2 — `docs/closing-period.md` (6-1 wire) — §V4 골든 fixture deferred to T10.5 → 6-2 carry-over close-out 명시
- T10.3 — `docs/capability-matrix.md` (extension) — v1.8 reference + 6-2 reference (no change)
- T10.4 — `docs/conventions.md` (extension) — §0.5 + §9 + §10.7 + §11 (audit actions + monthly closing report wire)
- T10.5 — 6-1 carry-over close (T10.5 deferred V4 골든 fixture fill) — 6-2 A11 wire에 통합 close-out
- T10.6 — `docs/cost-engine.md` (extension) — §V4 + §V8 + §V8 골든 18 fixtures matrix
- T10.7 — `docs/architecture-inventory.md` (extension) — m4_inventory module 6-2 wire 3 NEW routes + 3 NEW services + 2 NEW pure kernels
- T10.8 — `docs/inventory-ledger.md` (extension) — §5.2 (Story 6.2 closing report aggregator)
- T10.9 — `docs/closing-guard.md` (extension) — §5.3 (5-3 wire) + §6.2 (Story 6.2 closing report 시각화 layer)
- T10.10 — 3중 게이트 mandatory CI: ruff scoped (6-2 surface + 6-1 carry-over close 33 files) / import-linter 2 KEPT 0 broken / pytest 1,164+ 110 + 49 = 1,323+ passed + 127 skipped + 0 failed / frontend vitest 21 + 23 = 44 scenarios / Playwright E2E 6 + 11 = 17 scenarios.

## Deferrals (10 items)

1. **6-3 closing PDF export + ko-KR labels** — Epic 6 3-story 분할 3번째. 6-2 wire는 read-only web report + KRW/USD dual display. 6-3 wire = PDF A4 인쇄 최적화 + ko-KR labels (next-intl + Recharts SVG → PDF 변환).
2. **Epic 11 reversal module wire 진입점 (`reversal_negating` + `reversal_corrected` event type fill + `opening_inventory_unlocked` action)** — Epic 11 spec 진입 시점에 결정 (A9 carry-over). 6-2 wire는 read-only (correction은 Epic 11 reversal module ships 후).
3. **6-1 T10.5 deferred V4 골든 fixture fill** — 6-2 A11 wire에 통합 close-out (T6.1 + T6.2).
4. **5-3 W1 production_material_consumption emit** — Epic 11 BOM authority 진입 시 (5-3 carry-over).
5. **5-2 W4 `_emit_inventory_ledger_event_for_row` isolated unit tests** — Epic 6 spec 진입 시 또는 Epic 11 reversal 진입 시 (5-2 carry-over).
6. **M14 l2-input-opening-carry.ts** — 5-1 frontend toast (Epic 4 A6) wire done. 6-2 wire는 read-only aggregator frontend (NO closing-period frontend conflict).
7. **Epic 6 close-out retro A8 inline projection deprecation 결정** — Epic 6 close-out 시점에 fold-in vs deprecate 결정 (A8).
8. **Epic 6 close-out retro A9 carry-over 결정** — Epic 11 reversal module wire 진입점 (A9).
9. **5-3 T12.2 test file (closing invariant TS mirror parity) ≥ 10 cases** — Story 6.1 carry-over (A12 done 2026-08-07). 6-2 wire는 ≥ 9 NEW cases (AC #4 wire spec).
10. **6-2 T10.5 closing_period.md §V4 골든 fixture deferred to T10.5 → 6-2 carry-over close-out 명시** — 6-2 A11 wire (T6.1 + T6.2) + 6-2 docs (T10.2 + T10.5) 통합 close-out.

## Open Questions (7 with cj-style defaults)

1. **OQ1: monthly_closing_report view_mode = CLOSING_REPORT_PARTIAL fallback policy** — (a) "잠시 후 갱신" sonner toast + 자동 retry (3 attempts + 5s backoff) (default), (b) 자동 retry 없이 manual refresh button, (c) 로딩 스피너만 표시. **cj-style default**: (a) 자동 retry — read-only aggregator는 일시적 partial state 가능 (5-2/5-3/6-1 wire 패턴 그대로).
2. **OQ2: V4 fail 시 closing report UI 처리** — (a) KPI 박스에 "FAIL" 빨강 + audit-trail `closing_period_snapshot_inconsistency` 표시 (default), (b) KPI 박스에 "V4 FAIL" + 닫힌 lock icon + "마감 블록됨" sonner toast.error, (c) KPI 박스 표시 + audit-trail + 페이지 lock. **cj-style default**: (a) — 6-1 wire CR 1.1 self-describing audit payload pattern 그대로.
3. **OQ3: KRW/USD dual display 정밀도** — (a) USD 소수 2자리 (default — AD-8 SSOT), (b) USD 소수 4자리 (banker's rounding QTY_QUANTUM), (c) USD 표시 없이 KRW only. **cj-style default**: (a) — AD-8 monetary types SSOT + PRD §F5.2 wire.
4. **OQ4: 환율 source (`tenant_settings.baseline.currency_pair`)** — (a) 한국은행 (default — PRD §F5.2 명시), (b) USD/KRW 자동 fallback (Perplexity API), (c) tenant manual override. **cj-style default**: (a) — PRD §F5.2 SSOT + service-only tenant은 PRD §F5.2 무관 (capability gate 동등).
5. **OQ5: closing_per_product row sort order** — (a) closing_qty DESC (default — 큰 액수의 마감 우선), (b) product_code ASC (PRD §9 21 reports 1:1 매칭), (c) delta_qty DESC (변동 큰 순). **cj-style default**: (a) — 6-2 wire 표준 패턴 + 5-3 wire V3 severity sort pattern + CR 5-3 test pin contract 그대로.
6. **OQ6: V4 verdict envelope wire timing** — (a) closing_period confirm 시점에 emit (default — 6-1 wire 그대로), (b) closing_report view 시점에 on-demand emit, (c) calc endpoint (4-2 wire) 응답 시점에 emit. **cj-style default**: (a) — 6-1 wire V4 emit 그대로 + 6-2 wire read-only view.
7. **OQ7: A11 V8 16-fixture matrix extension timing** — (a) 6-2 wire commit 안에 V8 fixture 14 → 18 (default — A11 결정), (b) 6-2 wire commit + 별도 V8 fixture follow-up Story, (c) 6-3 wire (PDF export) commit 안에 V8 fixture 18 → 20. **cj-style default**: (a) — Epic 5 retro §7 A11 결정 그대로.

## Change Log

- **2026-08-08** — Story 6.2 spec created (bmad-create-story). baseline_commit = 418ca2d (6-1 3rd sweep done). 6-2 = Monthly Closing Report — closing snapshot + ledger events + capability gate. cj-style 3-story 분할 (Epic 5 retro §6) 2번째. PRD §F5 (마감 보고서) + §F5.2 (KRW/USD dual display) PRIMARY. 6-1 wire foundation reuse: closing_period_service + closing_snapshot ledger event + V4 verifier + MONTHLY_CLOSING_REPORT capability (matrix v1.8). A11 (V8 16-fixture matrix extension) PRIMARY. A8 (Epic 6 close-out 시점에 inline projection 제거) timeline. A9 (Epic 11 reversal deferred) read-only. A10 (MONTHLY_CLOSING_REPORT capability wire done). 6-1 T10.5 deferred V4 골든 fixture fill carry-over close-out (A11 wire에 통합). 6-1 carry-over close + 5-1/5-2/5-3 carry-over + 0.5 plumbing + A12 carry-over. 10 ACs / 10 tasks / 70+ subtasks. 6 NEW backend files + 8 EXTENSION + 4 NEW frontend files + 4 EXTENSION + 8 NEW test files + 8 EXTENSION + 5 NEW docs + 4 EXTENSION. ~110 NEW tests + 49 carry-over close-out = 159 NEW tests. 18 fixture matrix V8 byte-identical CI gate. 3중 게이트 mandatory CI.

## Status

ready-for-dev
