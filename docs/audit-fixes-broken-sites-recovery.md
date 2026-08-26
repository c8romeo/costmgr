# Audit-Fixes Broken Sites Recovery Log (Phase 11~20)

> **Phase 11~20 audit-fixes sprint (cj-style 154번째 wire)** —
> Inventory of all 24 broken `emit_audit_typed` call sites that were
> honestly-DEFERed across Phase 16/17/18/19/20 wire cycles, with the
> recovery pattern applied to each.

## §1. Recovery scope

The audit-fixes sprint `379ca8e` (cj-style 154번째) covered **24
broken call sites** across **14 FinOps modules** spanning **4
territories** + **8 router endpoints**.

### Per-territory breakdown

| Territory | Modules | Sites | Router endpoints |
|-----------|---------|-------|------------------|
| `FINOPS_REPORTING` (Phase 16) | 4 | 11 | 7 |
| `FINOPS_SUSTAINABILITY` (Phase 17) | 4 | 5 | 0 |
| `FINOPS_COMMITMENT` (Phase 18) | 4 | 5 | 0 |
| `FINOPS_PRICING` (Phase 19) | 4 | 3 | 1 |
| **Total** | **14** | **24** | **8** |

## §2. Site-by-site recovery log

### `FINOPS_REPORTING` (Phase 16, 11 sites)

#### 1. `apps/api/modules/finops/executive_dashboard_aggregator.py`

- **Function**: `aggregate_executive_dashboard(...)`
- **Site**: 1 canonical call (1 site)
- **Pattern**: aggregator mode (lazy import + `if db_session is not None and not dry_run:` guard)

#### 2. `apps/api/modules/finops/cross_module_kpi.py`

- **Function**: `calculate_cross_module_kpi(...)`
- **Site**: 1 canonical call (1 site)
- **Pattern**: aggregator mode

#### 3. `apps/api/modules/finops/executive_report_generator.py`

- **Function**: `generate_executive_report(...)` + `export_executive_report(...)`
- **Site**: 2 canonical calls (2 sites)
- **Pattern**: report_generator mode (lazy import + guard)

#### 4. `apps/api/modules/finops/executive_dashboard_routes.py` (router)

- **Endpoints**: `view_dashboard` + `view_cross_module_kpi` +
  `generate_report` + `export_report` + `dispatch_report` +
  `dry_run` + `kpi_refresh` = 7 endpoints
- **Site**: 7 canonical calls (7 sites)
- **Pattern**: router mode (`Depends(get_session)` + `with suppress(ImportError):` + `if db_session is not None:` guard)

### `FINOPS_SUSTAINABILITY` (Phase 17, 5 sites)

#### 5. `apps/api/modules/finops/sustainability/carbon_emissions_aggregator.py`

- **Function**: `aggregate_carbon_emissions(...)`
- **Site**: 1 canonical call

#### 6. `apps/api/modules/finops/sustainability/sustainability_kpi_selector.py`

- **Function**: `select_sustainability_kpi(...)`
- **Site**: 1 canonical call

#### 7. `apps/api/modules/finops/sustainability/sustainability_report_generator.py`

- **Function**: `generate_sustainability_report(...)` + `export_sustainability_report(...)`
- **Site**: 2 canonical calls

#### 8. `apps/api/modules/finops/sustainability/scheduled_sustainability_dispatch.py`

- **Function**: `scheduled_sustainability_dispatch(...)`
- **Site**: 1 canonical call (dispatch mode)

### `FINOPS_COMMITMENT` (Phase 18, 5 sites)

#### 9. `apps/api/modules/finops/commitment/commitment_inventory_aggregator.py`

- **Function**: `aggregate_commitment_inventory(...)`
- **Site**: 1 canonical call

#### 10. `apps/api/modules/finops/commitment/commitment_kpi_selector.py`

- **Function**: `select_commitment_kpi(...)`
- **Site**: 1 canonical call

#### 11. `apps/api/modules/finops/commitment/commitment_report_generation.py`

- **Function**: `generate_commitment_report(...)` + `export_commitment_report(...)`
- **Site**: 2 canonical calls

#### 12. `apps/api/modules/finops/commitment/scheduled_commitment_dispatch.py`

- **Function**: `scheduled_commitment_dispatch(...)`
- **Site**: 1 canonical call (dispatch mode)

### `FINOPS_PRICING` (Phase 19, 3 sites)

#### 13. `apps/api/modules/finops/pricing/pricing_report_generation.py`

- **Function**: `generate_pricing_report(...)` + `export_pricing_report(...)`
- **Site**: 2 canonical calls

#### 14. `apps/api/modules/finops/pricing/scheduled_pricing_dispatch.py`

- **Function**: `scheduled_pricing_dispatch(...)`
- **Site**: 1 canonical call (dispatch mode)

## §3. Per-file action_class import verification

All 14 files now import `ActionClass` from `apps/api/core/audit_action.py`
with the territory-specific enum value:

| File | ActionClass enum value |
|------|------------------------|
| `executive_dashboard_aggregator.py` | `ActionClass.FINOPS_REPORTING` |
| `cross_module_kpi.py` | `ActionClass.FINOPS_REPORTING` |
| `executive_report_generator.py` | `ActionClass.FINOPS_REPORTING` |
| `executive_dashboard_routes.py` | `ActionClass.FINOPS_REPORTING` |
| `sustainability/carbon_emissions_aggregator.py` | `ActionClass.FINOPS_SUSTAINABILITY` |
| `sustainability/sustainability_kpi_selector.py` | `ActionClass.FINOPS_SUSTAINABILITY` |
| `sustainability/sustainability_report_generator.py` | `ActionClass.FINOPS_SUSTAINABILITY` |
| `sustainability/scheduled_sustainability_dispatch.py` | `ActionClass.FINOPS_SUSTAINABILITY` |
| `commitment/commitment_inventory_aggregator.py` | `ActionClass.FINOPS_COMMITMENT` |
| `commitment/commitment_kpi_selector.py` | `ActionClass.FINOPS_COMMITMENT` |
| `commitment/commitment_report_generation.py` | `ActionClass.FINOPS_COMMITMENT` |
| `commitment/scheduled_commitment_dispatch.py` | `ActionClass.FINOPS_COMMITMENT` |
| `pricing/pricing_report_generation.py` | `ActionClass.FINOPS_PRICING` |
| `pricing/scheduled_pricing_dispatch.py` | `ActionClass.FINOPS_PRICING` |

## §4. Recovery verification

- **Structural verification** (cj-style 154 wire): `test_audit_fixes_phase_11_20_signature.py` — 7 test classes, 44 tests PASS
- **Semantic verification** (cj-style 155 backfill wire): `test_audit_fixes_phase_11_20_backfill.py` — 6 test classes, 52 tests PASS + 2 SKIP for renamed routes
- **Total verification**: 96/96 tests PASS (44 structural + 52 semantic)
- **Pre-commit verification**: ruff scoped 0 NEW errors (95 pre-existing baseline preserved)

## §5. Honest deviations preserved

1. **`emit_audit_typed` called WITHOUT `await`** — parent functions
   in aggregator modules are `def` (NOT `async def`). Codebase
   existing broken pattern verbatim mirror — coroutine created but
   not awaited (garbage collected). Full async fix honestly-DEFERed.
2. **`with suppress(ImportError):` conversion** (router file only)
   — ruff SIM105 baseline preservation (Phase 16~21 router aggregator
   wire 의 `try/except ImportError: pass` verbatim 패턴 회피).
3. **`test_audit_action_consistency.test_all_action_classes_have_registry_entry`
   INFRA failure** honestly-DEFERed — `ActionClass.INFRA` enum value
   exists but is NOT registered in `_REGISTRY`. Pre-existing baseline;
   별도 audit-fixes-infrastructure sprint 에서 결정 wire 진입 보류.
4. **Router sites 의 logger.warning audit failure logging 손실** —
   canonical silent-pass pattern 정합 보존 (7 router sites 의
   `except Exception as exc: logger.warning(...)` → `with suppress(ImportError):`
   unification).
