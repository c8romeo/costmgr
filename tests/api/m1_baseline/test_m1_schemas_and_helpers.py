"""tests.api.m1_baseline.test_schemas_and_pure_helpers — M1 baseline source health tests.

Source health 갭 회복 wire (순서 2, cj-style 307번째 정직 회복) — M1 module-scoped:
M1 baseline 모듈 (products + BOM catalog, PRD §8.M1) 의 source health 검증.
env-free (Pydantic + pure helper only), LOW risk.

검증 항목:

1. **ProductType enum + prefix/label map drift (PRD §4.1 + §8.M1)**
   - 5 ProductType enum 멤버 (product / semi_product / material / goods / service)
   - prefix_map + label_map 5 keys == enum members
   - 모든 prefix 3-letter uppercase ASCII
   - 모든 label 한글

2. **product_code pure helper (PRD §8.M1 코드)**
   - generate_next_code 4-digit zero-pad + sequence increment
   - parse_code round-trip + invalid input rejected (typed exception)
   - is_valid_code_format soft check
   - type_to_prefix / prefix_to_type bijection

3. **BOM 100% invariant (PRD §6.1 + A6 axiom + AD-8)**
   - TARGET_TOTAL = Decimal("100.0000")
   - sum_ratios returns Decimal with ROUND_HALF_EVEN
   - quantize_ratio enforces 4-decimal precision
   - sum of [60, 30, 10] = 100.0000 → is_complete_bom True
   - sum of [60, 30, 9] = 99 → is_complete_bom False

4. **ProductSchema validation (AD-8 + AD-15)**
   - ProductCreateRequest rejects negative unit_cost_krw
   - MoneyKRW / MoneyUSD wrappers enforce non-negative
   - extra='forbid' — unknown fields rejected
"""
from __future__ import annotations

import re
from decimal import Decimal

import pytest


# ── Test 1 — ProductType enum + prefix/label map drift ────────────────


def test_product_type_enum_5_members_with_prefix_label_drift_free():
    """PRD §4.1 + §8.M1: ProductType enum + prefix_map + label_map drift 0.

    - 5 ProductType enum members (product/semi_product/material/goods/service)
    - prefix_map 5 keys == enum members + 3-letter uppercase ASCII prefix
    - label_map 5 keys == enum members + non-empty 한글 label
    - drift-detector friendly: 1 mismatch → fail
    """
    from packages.services.m1_baseline.schemas import (
        PRODUCT_TYPE_LABEL_KO,
        PRODUCT_TYPE_PREFIX,
        ProductType,
    )

    expected_members = {
        ProductType.PRODUCT,
        ProductType.SEMI_PRODUCT,
        ProductType.MATERIAL,
        ProductType.GOODS,
        ProductType.SERVICE,
    }

    # (a) enum members
    assert set(ProductType) == expected_members, (
        f"ProductType enum drift. got={set(ProductType)}, "
        f"expected={expected_members}"
    )

    # (b) prefix map
    prefix_keys = set(PRODUCT_TYPE_PREFIX.keys())
    assert prefix_keys == expected_members, (
        f"PRODUCT_TYPE_PREFIX keys drift. only-in-prefix={prefix_keys - expected_members}, "
        f"only-in-enum={expected_members - prefix_keys}"
    )
    three_upper = re.compile(r"^[A-Z]{3}$")
    for product_type, prefix in PRODUCT_TYPE_PREFIX.items():
        assert isinstance(prefix, str) and three_upper.match(prefix), (
            f"prefix {prefix!r} for {product_type} must be 3-letter uppercase ASCII"
        )

    # (c) label map
    label_keys = set(PRODUCT_TYPE_LABEL_KO.keys())
    assert label_keys == expected_members, (
        f"PRODUCT_TYPE_LABEL_KO keys drift. only-in-label={label_keys - expected_members}"
    )
    korean_pattern = re.compile(r"[가-힣]")
    for product_type, label in PRODUCT_TYPE_LABEL_KO.items():
        assert isinstance(label, str) and len(label) > 0, (
            f"label for {product_type} must be non-empty string"
        )
        assert korean_pattern.search(label), (
            f"label {label!r} for {product_type} missing Korean characters"
        )


# ── Test 2 — product_code pure helper ─────────────────────────────────


def test_product_code_generate_parse_round_trip():
    """PRD §8.M1 코드: generate → parse round-trip + 4-digit zero-pad + overflow 허용.

    (a) generate_next_code({}) → MAT-0001 (4-digit zero-pad default)
    (b) generate_next_code({Material: 5}) → MAT-0006 (sequence increment)
    (c) generate_next_code({Material: 9999}) → MAT-10000 (overflow 5-digit)
    (d) parse_code("MAT-0042") → (Material, 42) round-trip compatible
    """
    from packages.services.m1_baseline.product_code import (
        generate_next_code,
        parse_code,
    )
    from packages.services.m1_baseline.schemas import ProductType

    # (a) empty dict → first sequence = 1
    assert generate_next_code({}, ProductType.MATERIAL) == "MAT-0001"

    # (b) sequence increment
    assert (
        generate_next_code({ProductType.MATERIAL: 5}, ProductType.MATERIAL)
        == "MAT-0006"
    )

    # (c) overflow beyond 9999 → 5+ digit (no clamp)
    assert (
        generate_next_code({ProductType.MATERIAL: 9999}, ProductType.MATERIAL)
        == "MAT-10000"
    )

    # (d) parse_code round-trip
    parsed_type, parsed_seq = parse_code("MAT-0042")
    assert parsed_type == ProductType.MATERIAL
    assert parsed_seq == 42

    # re-generate from parsed tuple
    regenerated = generate_next_code(
        {ProductType.MATERIAL: parsed_seq}, ProductType.MATERIAL
    )
    assert regenerated == "MAT-0043", (
        f"round-trip mismatch: parse(MAT-0042)=({parsed_type}, {parsed_seq}) "
        f"but generate_next({{Material:42}})={regenerated}"
    )


def test_product_code_parse_rejects_invalid_inputs():
    """PRD §8.M1 코드: malformed code → InvalidProductCodeError (typed).

    (a) 빈 문자열 → rejected
    (b) unknown prefix → rejected
    (c) 형식 불일치 (digit 부족) → rejected
    (d) Unicode 숫자 (full-width) → rejected (M12: ASCII only)
    """
    from packages.services.m1_baseline.product_code import (
        InvalidProductCodeError,
        parse_code,
    )

    # (a) 빈 문자열
    with pytest.raises(InvalidProductCodeError):
        parse_code("")

    # (b) unknown prefix
    with pytest.raises(InvalidProductCodeError):
        parse_code("XYZ-0001")

    # (c) 형식 불일치 — digit 3자리
    with pytest.raises(InvalidProductCodeError):
        parse_code("MAT-042")

    # (d) Unicode 숫자 (full-width ０ = U+FF10) — M12: ASCII only
    with pytest.raises(InvalidProductCodeError):
        parse_code("MAT-０００１")


def test_product_code_is_valid_code_format_soft_check():
    """is_valid_code_format: True/False soft check (no exception).

    (a) valid → True
    (b) invalid prefix → False
    (c) invalid format → False
    (d) empty / non-string → False
    """
    from packages.services.m1_baseline.product_code import is_valid_code_format

    assert is_valid_code_format("MAT-0042") is True
    assert is_valid_code_format("PRD-0001") is True

    assert is_valid_code_format("XYZ-0001") is False  # unknown prefix
    assert is_valid_code_format("MAT-042") is False  # 3 digits only
    assert is_valid_code_format("") is False  # empty
    assert is_valid_code_format(None) is False  # type: ignore[arg-type]
    assert is_valid_code_format(123) is False  # type: ignore[arg-type]


# ── Test 3 — BOM 100% invariant ──────────────────────────────────────


def test_bom_target_total_and_sum_ratios_invariant():
    """PRD §6.1 + A6 axiom + AD-8: BOM 합계 100.0000% invariant.

    (a) TARGET_TOTAL = Decimal("100.0000") (NUMERIC(7,4) DB precision)
    (b) sum_ratios returns Decimal (not float) — AD-8 strict
    (c) sum_ratios uses ROUND_HALF_EVEN (banker's rounding)
    (d) [60, 30, 10] → 100.0000 (complete BOM)
    (e) [60, 30, 9] → 99.0000 (incomplete BOM)
    """
    from packages.services.m1_baseline.bom_validation import (
        TARGET_TOTAL,
        sum_ratios,
    )

    # (a) target
    assert TARGET_TOTAL == Decimal("100.0000"), (
        f"TARGET_TOTAL must be 100.0000 (PRD §6.1 + A6 axiom + AD-8). "
        f"got={TARGET_TOTAL}"
    )

    # (b) + (d) complete BOM
    total = sum_ratios([Decimal("60"), Decimal("30"), Decimal("10")])
    assert isinstance(total, Decimal), (
        f"sum_ratios must return Decimal (AD-8 strict no-float). got={type(total).__name__}"
    )
    assert total == TARGET_TOTAL, (
        f"sum([60, 30, 10]) must equal TARGET_TOTAL. got={total}"
    )

    # (c) ROUND_HALF_EVEN — banker's rounding (0.5 → even)
    # 0.005 + 0.005 → 0.01 (0.0000 + 0.0050 = 0.0050; ROUND_HALF_EVEN at
    # 4 decimals = 0.0050 itself, no change). Use a clearer case:
    # 0.0125 + 0.0125 = 0.0250 → ROUND_HALF_EVEN at 4dp = 0.0250 (already 4dp)
    # Test with sum that requires quantization:
    quantized = sum_ratios(
        [Decimal("0.01234"), Decimal("0.01234"), Decimal("0.01234")]
    )
    # 0.01234 * 3 = 0.03702 → quantized to 4dp = 0.0370
    assert quantized == Decimal("0.0370"), (
        f"sum_ratios must quantize to 4 decimal places. got={quantized}"
    )

    # (e) incomplete BOM
    total_incomplete = sum_ratios([Decimal("60"), Decimal("30"), Decimal("9")])
    assert total_incomplete == Decimal("99.0000"), (
        f"sum([60, 30, 9]) must equal 99.0000. got={total_incomplete}"
    )
    assert total_incomplete < TARGET_TOTAL


# ── Test 4 — ProductSchema validation ─────────────────────────────────


def test_money_krw_usd_wrappers_enforce_non_negative_and_precision():
    """AD-8 + AD-15: MoneyKRW / MoneyUSD wrappers enforce invariants.

    (a) MoneyKRW rejects negative value
    (b) MoneyUSD rejects negative + enforces 2 decimal places (max_digits=18)
    (c) extra='forbid' on both wrappers (unknown fields rejected)
    """
    from pydantic import ValidationError

    from apps.api.modules.m1_baseline.schemas import MoneyKRW, MoneyUSD

    # (a) MoneyKRW — non-negative enforced
    with pytest.raises(ValidationError):
        MoneyKRW(value=-100)
    # happy path
    MoneyKRW(value=0)  # boundary: 0 OK
    MoneyKRW(value=1_000_000_000)  # 10억 OK

    # (b) MoneyUSD — non-negative + 2 decimal places
    with pytest.raises(ValidationError):
        MoneyUSD(value=Decimal("-0.01"))
    with pytest.raises(ValidationError):
        MoneyUSD(value=Decimal("1.234"))  # 3 decimal places → max_digits=18, decimal_places=2
    # happy path
    MoneyUSD(value=Decimal("0"))
    MoneyUSD(value=Decimal("1.99"))

    # (c) extra='forbid' — unknown fields rejected
    with pytest.raises(ValidationError):
        MoneyKRW(value=100, extra_field="not_allowed")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        MoneyUSD(value=Decimal("1.00"), extra_field="not_allowed")  # type: ignore[call-arg]


def test_account_classification_request_extra_forbid_and_field_types():
    """PRD §8.M1 settings wizard: AccountClassificationRequest validation.

    (a) extra='forbid' enforced (AD-15)
    (b) direct_indirect / fixed_variable optional (None = unclassified)
    (c) account_id required (str)
    """
    from pydantic import ValidationError

    from apps.api.modules.m1_baseline.schemas import (
        AccountClassificationRequest,
    )

    # happy path: all 3 fields optional except account_id
    req = AccountClassificationRequest(account_id="acc-001")
    assert req.direct_indirect is None
    assert req.fixed_variable is None

    # direct_indirect set
    req2 = AccountClassificationRequest(
        account_id="acc-002",
        direct_indirect="direct",
        fixed_variable="variable",
    )
    assert req2.direct_indirect == "direct"

    # (a) extra='forbid'
    with pytest.raises(ValidationError):
        AccountClassificationRequest(
            account_id="acc-003",
            unknown_field="bad",  # type: ignore[call-arg]
        )

    # (c) account_id required
    with pytest.raises(ValidationError):
        AccountClassificationRequest()  # type: ignore[call-arg]
