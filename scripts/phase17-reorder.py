#!/usr/bin/env python3
"""Phase 17 close-out fix: re-order phase-17-wire + phase-17-retrospective to be
consecutive with phase-17-spec-entry (before phase-7-wire).
"""

import io
import sys

PATH = r'_bmad-output/implementation-artifacts/sprint-status.yaml'

with io.open(PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines before: {len(lines)}", file=sys.stderr)

# Find the indices of phase-17-wire, phase-17-retrospective, phase-17-spec-entry, phase-7-wire
spec_idx = None
wire_idx = None
retro_idx = None
phase7_wire_idx = None

for i, line in enumerate(lines):
    if line.startswith('  phase-17-spec-entry:'):
        spec_idx = i
    elif line.startswith('  phase-17-wire:'):
        wire_idx = i
    elif line.startswith('  phase-17-retrospective:'):
        retro_idx = i
    elif line.startswith('  phase-7-wire:'):
        phase7_wire_idx = i

print(f"spec_idx={spec_idx}, wire_idx={wire_idx}, retro_idx={retro_idx}, phase7_wire_idx={phase7_wire_idx}", file=sys.stderr)

assert spec_idx is not None, "phase-17-spec-entry not found"
assert wire_idx is not None, "phase-17-wire not found"
assert retro_idx is not None, "phase-17-retrospective not found"
assert phase7_wire_idx is not None, "phase-7-wire not found"
assert spec_idx < phase7_wire_idx < wire_idx < retro_idx, "Order assumption broken"

# Extract wire and retro entries
wire_entry = lines[wire_idx]
retro_entry = lines[retro_idx]

# Remove them from their current position
# wire_idx < retro_idx, so remove retro first (higher index), then wire
new_lines = lines[:wire_idx] + lines[wire_idx+1:retro_idx] + lines[retro_idx+1:]

# Find new indices after removal
new_spec_idx = spec_idx  # spec_idx unchanged
new_phase7_idx = phase7_wire_idx - 1  # one removal before it
new_wire_insert_idx = new_spec_idx + 1  # right after spec entry

# Insert wire and retro entries before phase-7-wire
new_lines = new_lines[:new_wire_insert_idx] + [wire_entry, retro_entry] + new_lines[new_wire_insert_idx:]

print(f"Total lines after: {len(new_lines)}", file=sys.stderr)

# Write back
with io.open(PATH, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("OK: phase-17-wire + phase-17-retrospective moved before phase-7-wire", file=sys.stderr)