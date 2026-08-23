# tests/api/core/test_phase_11_department_mapping.py —
# Phase 11 T3 (cj-style 107번째 wire) — Department mapping tests.
# 5 cases per cj-style Phase 10 SLO pattern verbatim mirror.
import re

import pytest

from apps.api.modules.finops.department_mapping import (
    COST_CENTER_ID_PATTERN,
    COST_CENTER_ID_REGEX,
    DepartmentCostCenterMapping,
    DepartmentMappingValidationError,
    auto_create_mapping,
    department_mapping_cache_key,
    generate_cost_center_id,
    validate_department_mapping,
)


def _valid_mapping(**overrides):
    base = {
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "department_id": "dept-1",
        "department_name": "Engineering",
        "cost_center_id": "CC-0001",
        "auto_created": False,
        "created_by": "user-1",
        "updated_by": "user-1",
    }
    base.update(overrides)
    return base


def test_valid_department_mapping_accepted():
    mapping = _valid_mapping()
    validated = validate_department_mapping(mapping)
    assert validated["cost_center_id"] == "CC-0001"
    assert "id" in validated
    assert "trace_id" in validated


def test_invalid_cost_center_id_pattern_rejected():
    mapping = _valid_mapping(cost_center_id="invalid_cc")
    with pytest.raises(DepartmentMappingValidationError):
        validate_department_mapping(mapping)


def test_missing_tenant_id_rejected():
    mapping = _valid_mapping()
    del mapping["tenant_id"]
    with pytest.raises(DepartmentMappingValidationError):
        validate_department_mapping(mapping)


def test_auto_create_generates_valid_cost_center_id():
    mapping = auto_create_mapping(
        tenant_id="11111111-1111-1111-1111-111111111111",
        department_id="dept-99",
        department_name="Marketing",
        actor_id="system",
    )
    assert COST_CENTER_ID_REGEX.match(mapping["cost_center_id"])
    assert mapping["auto_created"] is True
    assert mapping["created_by"] == "system"


def test_generate_cost_center_id_format():
    for _ in range(10):
        cc_id = generate_cost_center_id()
        assert re.match(COST_CENTER_ID_PATTERN, cc_id), f"{cc_id!r} did not match {COST_CENTER_ID_PATTERN}"


def test_department_mapping_cache_key_shape():
    key = department_mapping_cache_key("tenant-a", "dept-1")
    assert key == "cost_center_mapping:tenant-a:dept-1"


def test_audit_first_insert_payload_shape():
    from apps.api.modules.finops.department_mapping import (
        audit_first_insert_department_mapping_updated,
    )

    payload = audit_first_insert_department_mapping_updated(
        tenant_id="t1",
        department_id="d1",
        cost_center_id="CC-0001",
        actor_id="u1",
        auto_created=True,
        trace_id="trace-1",
    )
    assert payload["action"] == "department_mapping_updated"
    assert payload["action_class"] == "FINOPS"
    assert payload["module_id"] == "m19_finops"
    assert payload["tenant_id"] == "t1"
    assert payload["auto_created"] is True
    assert payload["audit_first"] is True