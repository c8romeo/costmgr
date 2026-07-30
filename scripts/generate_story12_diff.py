"""Generate Story 1.2 review diff by combining staged and untracked file diffs."""
import subprocess
from pathlib import Path

modified_files = [
    "apps/web/components/settings/wizard/SettingsWizardClient.tsx",
    "apps/web/components/settings/wizard/FiscalYearStartStep.tsx",
    "apps/web/components/settings/wizard/CurrencyStep.tsx",
    "apps/web/components/settings/wizard/LanguageStep.tsx",
    "apps/web/components/settings/wizard/AllocationCriteriaStep.tsx",
    "apps/web/components/calc/CalcButton.tsx",
    "apps/web/components/calc/CalculatorBanner.tsx",
    "apps/web/hooks/useSettingsCompletion.ts",
    "apps/web/app/[locale]/(dashboard)/settings/wizard/page.tsx",
    "apps/web/lib/api-client.ts",
    "apps/web/components/sidebar/Sidebar.tsx",
    "apps/web/components/sidebar/MenuContext.tsx",
    "apps/web/app/[locale]/(dashboard)/page.tsx",
    "apps/api/modules/m0_onboarding/services/settings_service.py",
    "docs/conventions.md",
    "docs/README.md",
    "tests/architecture/test_api_calls_only_ports.py",
    "_bmad-output/implementation-artifacts/1-2-settings-wizard-calculation-block.md",
]

new_files = [
    "tests/api/test_settings_wizard.py",
    "tests/api/test_settings_wizard_isolation.py",
    "tests/integration/test_completion_consistency.py",
    "apps/api/alembic/versions/0004_tenant_settings_onboarding_extend.py",
    "docs/settings-wizard.md",
    "docs/PRD-외부-링크.md",
]

output = Path("_bmad-output/implementation-artifacts/.review/story-1-2.diff")
output.parent.mkdir(parents=True, exist_ok=True)

# Use git add -N (intent-to-add) for untracked files so `git diff HEAD` works
print("Staging untracked files with intent-to-add...")
for f in modified_files + new_files:
    if not Path(f).exists():
        continue
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", f],
        capture_output=True, text=True,
    )
    status = result.stdout.strip()[:2]
    if status.startswith("??"):
        subprocess.run(["git", "add", "-N", f], check=False, capture_output=True)

# Now run git diff HEAD with all files
print("Running git diff HEAD...")
all_files = modified_files + new_files
result = subprocess.run(
    ["git", "diff", "HEAD", "--"] + all_files,
    capture_output=True,
)
# Decode stdout with utf-8 (replacing decode errors)
diff_text = result.stdout.decode("utf-8", errors="replace")
output.write_text(diff_text, encoding="utf-8")

# Count stats
lines = output.read_text(encoding="utf-8").splitlines()
file_count = sum(1 for ln in lines if ln.startswith("diff --git"))
add_count = sum(1 for ln in lines if ln.startswith("+") and not ln.startswith("+++"))
del_count = sum(1 for ln in lines if ln.startswith("-") and not ln.startswith("---"))

print(f"Output: {output}")
print(f"Lines: {len(lines)}")
print(f"Files: {file_count}")
print(f"+{add_count} -{del_count}")