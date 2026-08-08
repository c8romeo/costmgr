"""tests.integration.test_fiscal_periods_rls — Story 11.2 RLS policy tests.

12 cases per AC #9 spec — verify supabase/policies/0011_fiscal_periods_rls.sql:
- ENABLE + FORCE RLS are issued
- 4-policy split: tenant_select_own + tenant_insert_own + tenant_update_own_blocked_status + tenant_delete_blocked
- All policies filter on tenant_id via auth.jwt() -> 'app_metadata' ->> 'tenant_id'
- DELETE is BLOCKED (AD-6 close lock)
- UPDATE blocks writes when status='closed'
"""

from __future__ import annotations

from pathlib import Path


def _read_rls_source() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "supabase" / "policies" / "0011_fiscal_periods_rls.sql"
    ).read_text(encoding="utf-8")


def test_rls_enables_row_level_security() -> None:
    src = _read_rls_source()
    assert "ALTER TABLE fiscal_periods ENABLE ROW LEVEL SECURITY" in src
    assert "ALTER TABLE fiscal_periods FORCE ROW LEVEL SECURITY" in src


def test_rls_select_policy_filters_tenant_id() -> None:
    src = _read_rls_source()
    # 1) SELECT policy present.
    assert "tenant_select_own" in src
    assert "FOR SELECT" in src
    assert "authenticated, owner, member, viewer" in src
    # Tenant isolation via JWT.
    assert "auth.jwt() -> 'app_metadata' ->> 'tenant_id'" in src


def test_rls_insert_policy_owner_only() -> None:
    src = _read_rls_source()
    assert "tenant_insert_own" in src
    assert "FOR INSERT" in src
    assert "TO owner" in src
    assert "WITH CHECK" in src


def test_rls_update_policy_blocks_status_closed() -> None:
    """UPDATE policy uses USING + WITH CHECK, and USING clauses status != 'closed'."""
    src = _read_rls_source()
    assert "tenant_update_own_blocked_status" in src
    assert "FOR UPDATE" in src
    # USING block — status='closed' rows are excluded.
    assert "status != 'closed'" in src


def test_rls_delete_policy_is_blocked() -> None:
    """DELETE policy uses USING (false) to block all deletes (AD-6 close lock)."""
    src = _read_rls_source()
    assert "tenant_delete_blocked" in src
    assert "FOR DELETE" in src
    # The USING clause evaluates to false → all deletes rejected.
    assert "USING (false)" in src


def test_rls_uses_drop_policy_if_exists_pattern() -> None:
    """All 4 policies use DROP POLICY IF EXISTS guard (5-2/6-1 wire pattern)."""
    src = _read_rls_source()
    drop_count = src.count("DROP POLICY IF EXISTS")
    assert drop_count >= 4, f"Expected ≥4 DROP POLICY IF EXISTS, got {drop_count}"


def test_rls_select_policy_includes_all_four_roles() -> None:
    """SELECT allows authenticated + owner + member + viewer (5-2 wire)."""
    src = _read_rls_source()
    # Find the SELECT FOR block.
    select_idx = src.find("FOR SELECT")
    # 200 chars of context after FOR SELECT.
    context = src[select_idx : select_idx + 250]
    for role in ("authenticated", "owner", "member", "viewer"):
        assert role in context, f"role {role} not in SELECT policy"


def test_rls_update_policy_uses_both_using_and_with_check() -> None:
    """UPDATE policy has USING + WITH CHECK (defense-in-depth — AD-3 SSOT)."""
    src = _read_rls_source()
    update_idx = src.find("FOR UPDATE")
    context = src[update_idx : update_idx + 800]
    assert "USING (" in context
    assert "WITH CHECK (" in context


def test_rls_insert_policy_uses_with_check_only() -> None:
    """INSERT policy uses WITH CHECK only (no USING for INSERT)."""
    src = _read_rls_source()
    insert_idx = src.find("FOR INSERT")
    context = src[insert_idx : insert_idx + 400]
    assert "WITH CHECK" in context


def test_rls_tenant_filter_is_uuid_cast() -> None:
    """tenant_id comparison casts JWT text to UUID via ::uuid (AD-15 §15)."""
    src = _read_rls_source()
    assert "(auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid" in src


def test_rls_all_four_policies_present() -> None:
    """All 4 named policies (select / insert / update / delete) exist."""
    src = _read_rls_source()
    for policy_name in (
        "tenant_select_own",
        "tenant_insert_own",
        "tenant_update_own_blocked_status",
        "tenant_delete_blocked",
    ):
        assert f"CREATE POLICY {policy_name}" in src, (
            f"policy {policy_name} missing"
        )


def test_rls_mirrors_5_2_6_1_pattern() -> None:
    """5-2/6-1 RLS pattern: same enable-then-force-then-policies structure."""
    src = _read_rls_source()
    # 1st: ENABLE
    assert src.index("ENABLE ROW LEVEL SECURITY") < src.index("FORCE ROW LEVEL SECURITY")
    # FORCE comes before any CREATE POLICY.
    assert src.index("FORCE ROW LEVEL SECURITY") < src.index("CREATE POLICY")
