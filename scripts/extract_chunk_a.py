"""Extract Chunk A (Frontend) files from the full Story 1.2 diff."""
from pathlib import Path
import re

CHUNK_A_FILES = [
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
]

src = Path("_bmad-output/implementation-artifacts/.review/story-1-2.diff").read_text(
    encoding="utf-8"
)
chunks = re.split(r"(?m)^diff --git ", src)
# First chunk is preamble (empty before first diff)
header = chunks[0]
body_chunks = chunks[1:]

selected = []
for chunk in body_chunks:
    # First line of each chunk is the header line "a/... b/..."
    header_line = chunk.splitlines()[0]
    # Extract the file path - find any path that matches our list
    for f in CHUNK_A_FILES:
        # Files with special chars are octal-escaped in git diff
        # Check if any of the paths appear in the header line
        norm_header = header_line.encode("utf-8").decode("unicode_escape", errors="ignore")
        if f.replace(" ", "\\ ") in header_line or f in norm_header or f.replace("(", "\\(") in header_line:
            selected.append("diff --git " + chunk)
            break
        # Fallback: compare basename + first path component
        # Use the original (non-escaped) path as anchor
        if f.replace("\\", "") in header_line.replace("\\", ""):
            selected.append("diff --git " + chunk)
            break

output = Path("_bmad-output/implementation-artifacts/.review/story-1-2-chunk-A.diff")
output.write_text(header + "".join(selected), encoding="utf-8")

# Stats
lines = output.read_text(encoding="utf-8").splitlines()
file_count = sum(1 for ln in lines if ln.startswith("diff --git"))
print(f"Chunk A: {file_count} files, {len(lines)} lines, output: {output}")
for ln in lines:
    if ln.startswith("diff --git"):
        print(f"  {ln[:120]}")