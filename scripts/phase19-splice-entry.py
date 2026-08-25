#!/usr/bin/env python3
"""Splice 1: Add phase-19-spec-entry after phase-19-prd-entry."""
PATH = r"C:\Users\c8rom\desktop\costmgr\_bmad-output\implementation-artifacts\sprint-status.yaml"

with open(PATH, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8-sig')
lines = text.splitlines(keepends=True)
print(f"Total lines before: {len(lines)}")

target_idx = None
for i, line in enumerate(lines):
    if line.startswith('  phase-19-prd-entry: done'):
        target_idx = i
        break
assert target_idx is not None, "Could not find phase-19-prd-entry line"

new_entry = "  phase-19-spec-entry: backlog  # 2026-08-25 — Phase 19 spec entry: ready-for-dev (cj-style 138th wire pending)\n"
lines.insert(target_idx + 1, new_entry)
print(f"Inserted at line {target_idx + 2}")

with open(PATH, 'wb') as f:
    f.write(b'\xef\xbb\xbf' + ''.join(lines).encode('utf-8'))

print(f"Final line count: {len(lines)}")
print("Splice 1 complete!")
