# Audit-Fixes Registry Reference (Phase 11~20)

> **Phase 11~20 audit-fixes sprint (cj-style 154번째 wire)** —
> Reference for the 4 FINOPS_* action registries in
> `apps/api/core/audit_action.py` `_ActionRegistry._REGISTRY`. Each
> territory has exactly **8 actions** registered.

## §1. ActionClass enum

`apps/api/core/audit_action.py`:

```python
class ActionClass(str, Enum):
    MONTHLY_INPUT_PERIOD = "monthly_input_period"
    INVENTORY_LEDGER = "inventory_ledger"
    COST_CALCULATION = "cost_calculation"
    AI = "ai"
    FINOPS_SHOWBACK = "finops_showback"
    FINOPS_CHARGEBACK = "finops_chargeback"
    FINOPS_ANOMALY_DETECTION = "finops_anomaly_detection"
    FINOPS_BUDGET_ALERT = "finops_budget_alert"
    FINOPS_FORECASTING_CAPACITY_PLANNING = "finops_forecasting_capacity_planning"
    FINOPS_OPTIMIZATION = "finops_optimization"
    FINOPS_TAG_GOVERNANCE = "finops_tag_governance"
    FINOPS_REPORTING = "finops_reporting"
    FINOPS_SUSTAINABILITY = "finops_sustainability"
    FINOPS_COMMITMENT = "finops_commitment"
    FINOPS_PRICING = "finops_pricing"
    FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION = "finops_multi_cloud_unified_reconciliation"
    FINOPS_RESERVED_CAPACITY_PLANNING = "finops_reserved_capacity_planning"
    INFRA = "infra"  # NOT registered in _REGISTRY (audit-fixes-infrastructure sprint 보류)
```

## §2. _ActionRegistry._REGISTRY — 4 FINOPS_* territories

```python
_ActionRegistry._REGISTRY: Dict[ActionClass, Tuple[str, FrozenSet[str]]] = {
    ...
    ActionClass.FINOPS_REPORTING: (
        "audit_logs",
        frozenset({
            "executive_dashboard_viewed",
            "executive_dashboard_aggregated",
            "cross_module_kpi_calculated",
            "executive_report_generated",
            "executive_report_exported",
            "executive_report_dispatched",
            "finops_reporting_dry_run_executed",
            "executive_dashboard_kpi_refreshed",
        }),
    ),
    ActionClass.FINOPS_SUSTAINABILITY: (
        "audit_logs",
        frozenset({
            "sustainability_dashboard_viewed",
            "carbon_emissions_aggregated",
            "sustainability_kpi_selected",
            "sustainability_report_generated",
            "sustainability_report_exported",
            "sustainability_report_dispatched",
            "finops_sustainability_dry_run_executed",
            "sustainability_kpi_refreshed",
        }),
    ),
    ActionClass.FINOPS_COMMITMENT: (
        "audit_logs",
        frozenset({
            "commitment_dashboard_viewed",
            "commitment_inventory_aggregated",
            "commitment_kpi_selected",
            "commitment_report_generated",
            "commitment_report_exported",
            "commitment_report_dispatched",
            "finops_commitment_dry_run_executed",
            "commitment_kpi_refreshed",
        }),
    ),
    ActionClass.FINOPS_PRICING: (
        "audit_logs",
        frozenset({
            "pricing_dashboard_viewed",
            "cross_module_pricing_kpi_calculated",
            "pricing_report_generated",
            "pricing_report_exported",
            "pricing_report_dispatched",
            "pricing_scheduled_dispatch_evaluated",
            "finops_pricing_dry_run_executed",
            "pricing_kpi_refreshed",
        }),
    ),
    ...
}
```

## §3. AuditAction Literal union

```python
AuditAction = Union[
    MonthlyInputPeriodAction,
    InventoryLedgerAction,
    CostCalculationAction,
    AIAction,
    FinopsShowbackAction,
    FinopsChargebackAction,
    FinopsAnomalyDetectionAction,
    FinopsBudgetAlertAction,
    FinopsForecastingCapacityPlanningAction,
    FinopsOptimizationAction,
    FinopsTagGovernanceAction,
    FinopsReportingAction,  # 8 values: see §2
    FinopsSustainabilityAction,  # 8 values
    FinopsCommitmentAction,  # 8 values
    FinopsPricingAction,  # 8 values
    FinopsMultiCloudUnifiedReconciliationAction,
    FinopsReservedCapacityPlanningAction,
]
```

Per-territory Literal declarations:

```python
FinopsReportingAction = Literal[
    "executive_dashboard_viewed",
    "executive_dashboard_aggregated",
    "cross_module_kpi_calculated",
    "executive_report_generated",
    "executive_report_exported",
    "executive_report_dispatched",
    "finops_reporting_dry_run_executed",
    "executive_dashboard_kpi_refreshed",
]

FinopsSustainabilityAction = Literal[
    "sustainability_dashboard_viewed",
    "carbon_emissions_aggregated",
    "sustainability_kpi_selected",
    "sustainability_report_generated",
    "sustainability_report_exported",
    "sustainability_report_dispatched",
    "finops_sustainability_dry_run_executed",
    "sustainability_kpi_refreshed",
]

FinopsCommitmentAction = Literal[
    "commitment_dashboard_viewed",
    "commitment_inventory_aggregated",
    "commitment_kpi_selected",
    "commitment_report_generated",
    "commitment_report_exported",
    "commitment_report_dispatched",
    "finops_commitment_dry_run_executed",
    "commitment_kpi_refreshed",
]

FinopsPricingAction = Literal[
    "pricing_dashboard_viewed",
    "cross_module_pricing_kpi_calculated",
    "pricing_report_generated",
    "pricing_report_exported",
    "pricing_report_dispatched",
    "pricing_scheduled_dispatch_evaluated",
    "finops_pricing_dry_run_executed",
    "pricing_kpi_refreshed",
]
```

## §4. Drift detector

3-way drift detection (CR 11-4 verbatim):

1. **`AuditAction` Literal** ↔ **`_ActionRegistry._REGISTRY` frozenset** — every Literal value MUST be in the frozenset.
2. **`AuditAction` Literal** ↔ **`ActionClass` enum** — every Literal value MUST be classified under exactly one `ActionClass`.
3. **Frontend TS mirror** (`apps/web/lib/finops/audit-actions-mirror.ts`) ↔ **backend `AuditAction` Literal** — every TS string MUST equal a backend Literal value.

Drift detector tests:

- `tests/api/core/test_audit_action_consistency.py` — backend Literal ↔ registry parity
- `apps/web/__tests__/audit-action-mirror.test.ts` — TS mirror parity

## §5. Cross-references

- **Canonical signature** — `docs/audit-fixes-canonical-signature.md`
- **24 broken sites recovery log** — `docs/audit-fixes-broken-sites-recovery.md`
- **Migration guide** — `docs/audit-fixes-migration-guide.md`
- **AD-49** — `docs/architecture-decisions/AD-49-phase-11-20-audit-fixes.md`
- **Routers reference** — `docs/api/routers/finops-executive-dashboard-routes.md`
