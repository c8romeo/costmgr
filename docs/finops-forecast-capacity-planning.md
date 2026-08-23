# FinOps Forecasting & Capacity Planning (Phase 13)

> **Phase 13 (cj-style 115번째 wire)** — FinOps Forecasting & Capacity Planning territory.

## §1. Introduction

This runbook covers the FinOps Forecasting & Capacity Planning system
introduced in Phase 13 (cj-style 115번째 wire). It extends the Phase 11
Showback/Chargeback territory and the Phase 12 Cost Anomaly Detection &
Budget Alerting territory with forward-looking 12-month forecasts,
90-day capacity headroom analysis, and 4-input budget burn-rate
projections.

PRD §F29.1~§F29.8 (8 ACs → 92 sub-ACs).

## §2. Capability Gate

`Capability.FINOPS_FORECASTING_CAPACITY_PLANNING` is granted to all 4
industries (manufacturing + service + manufacturing_service +
manufacturing_service_other) per CR 12-1 L4 industry-agnostic precedent.

Dependency helper: `require_finops_forecast` in
`apps/api/dependencies/capability.py`.

## §3. Forecast Definition DSL

The `ForecastDefinition` TypedDict has 11 fields:

- `forecast_id` (UUID)
- `tenant_id` (UUID)
- `target_metric` (5 options: department / cost_center /
  product_line / service / tenant_total)
- `dimension_value` (specific dept/cost_center/etc value)
- `horizon_months` (4 options: 3m / 6m / 12m / 24m)
- `model_type` (4 options: arima / prophet / lstm / ensemble)
- `confidence_level` (4 options: 80 / 90 / 95 / 99)
- `retraining_cron` (cron expression)
- `status` (3 options: active / paused / expired)
- `created_at` (ISO 8601)
- `updated_at` (ISO 8601)

The `parse_forecast_definition()` pure validator enforces 6 validation
rules (CR 11-4 P-015 verbatim).

## §4. Forecast Engine

`generate_forecast()` runs 4 time series models in parallel:

- **ARIMA** (statsmodels==0.14.1 AD-14 stack pin) — p=2 d=1 q=2
- **Prophet** (prophet==1.1.5 AD-14 stack pin) —
  seasonality_mode='multiplicative' + 8 KST holidays
- **LSTM** (tensorflow==2.15.0 AD-14 stack pin) — hidden_layers=50 +
  epochs=100 + batch_size=32
- **Ensemble** — 3-of-4 voting consensus (median of 3 model predictions)

Historical baseline source = last 12-month from
`phase_11_finops_showback` + `phase_12_finops_anomaly_detection`.

## §5. Capacity Headroom

`analyze_capacity_headroom()` analyzes 3 resource types:

- **compute** — primary model: LSTM
- **storage** — primary model: Prophet
- **network** — primary model: ARIMA

Saturation thresholds: OK (<70%), WARNING (70-89%), CRITICAL (≥90%).
Default lookahead = 90 days.

## §6. Budget Burn-Rate

`project_budget_consumption()` uses 4-input burn-rate formula:

```
burn_rate = (consumed_budget / elapsed_days) /
            (total_budget - consumed_budget / remaining_days)
```

3-level severity routing:
- warning (110%) → Slack only
- critical (130%) → Slack + PagerDuty
- exceeded (150%) → Slack + PagerDuty + Email

24h dedup window (PRD §F29.4.5 verbatim).

## §7. Forecast Accuracy + Retraining

`track_forecast_accuracy()` computes MAE + MAPE + RMSE with banker's
rounding (CR 5-1 verbatim). MAPE > 20% for 3 consecutive periods
triggers model retraining.

Retraining cron: `'0 3 * * 0'` KST Sunday 03:00 (UTC 18:00 Saturday).

## §8. Dashboard

`/admin/finops/forecast` — RSC page with 5 sub-components:

1. `ForecastHorizonSelector` (4 horizon options)
2. `ForecastChart` (Recharts 2.12.7 LineChart + 95% CI shading)
3. `CapacityHeadroomGauge` (Recharts 2.12.7 RadialBarChart)
4. `BudgetBurnRatePanel` (3-level severity visualization)
5. `ForecastAccuracyPanel` (MAE/MAPE/RMSE + per-model accuracy table)

## §9. Dry-Run Mode

3 CLI flags:

- `--finops-forecast-dry-run`
- `--finops-capacity-dry-run`
- `--finops-burnrate-dry-run`

Audit-first INSERT `forecast_dry_run_executed` (CR 1-1 verbatim).

## §10. Audit Actions

7 NEW audit actions via `ActionClass.FINOPS_FORECAST`:

- `forecast_definition_updated`
- `forecast_generated`
- `capacity_headroom_analyzed`
- `budget_burn_rate_projected`
- `forecast_accuracy_degraded`
- `model_retraining_triggered`
- `forecast_dry_run_executed`

## §11. Capability Matrix

Capability matrix v1.38 → **v1.39** EXTENSION.

`FINOPS_FORECASTING_CAPACITY_PLANNING` (industry-agnostic ✅/✅/✅/✅).

## §12. Tests

~43 NEW pytest cases across 7 files:

- `tests/api/core/test_phase_13_forecast_definition.py` (6 cases)
- `tests/api/core/test_phase_13_forecast_engine.py` (8 cases)
- `tests/api/core/test_phase_13_capacity_headroom.py` (6 cases)
- `tests/api/core/test_phase_13_budget_burnrate.py` (6 cases)
- `tests/api/core/test_phase_13_forecast_accuracy_tracker.py` (6 cases)
- `tests/api/core/test_phase_13_audit_action.py` (7 cases)
- `tests/integration/test_capability_matrix_v1_39_drift.py` (8 cases)

## §13. AD-22 + Epic 12 2FA 챌린지

All 5 forecast endpoints (definition / generation / capacity / budget
burn-rate / model retraining) require owner role AND 2FA 챌린지
per Epic 12 wire `a63646c`.

## §14. NFR4 PII Minimization

Forecast data contains only business metrics + cost amounts (no PII).
AD-22 owner-only RBAC preserves PII minimization discipline.

---

**Wire scope**: T1~T8 (Phase 13 atomic wire, cj-style 115번째).
**Baseline**: `77ed55f` (Phase 13 spec entry DONE).
**Capability matrix**: v1.38 → v1.39.
**Sprint-status**: v3.26 → v3.27.