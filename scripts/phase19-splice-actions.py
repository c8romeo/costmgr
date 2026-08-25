#!/usr/bin/env python3
"""Splice 2: Insert A519~A523 block before Phase 17 spec entry section header."""
import io
PATH = r"C:\Users\c8rom\desktop\costmgr\_bmad-output\implementation-artifacts\sprint-status.yaml"
BLOCK_PATH = r"C:\Users\c8rom\desktop\costmgr\scripts\phase19-action-items.txt"

with open(PATH, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8-sig')
lines = text.splitlines(keepends=True)

# Find the Phase 17 spec entry section header
header_idx = None
for i, line in enumerate(lines):
    if '# ===== Phase 17 spec entry' in line:
        header_idx = i
        break
assert header_idx is not None, "Could not find Phase 17 spec entry header"
print(f"Phase 17 spec entry header at line {header_idx + 1}")

# Read the new block
with open(BLOCK_PATH, 'rb') as f:
    block_raw = f.read()
# Skip UTF-8 BOM if present
if block_raw.startswith(b'\xef\xbb\xbf'):
    block_raw = block_raw[3:]
block_text = block_raw.decode('utf-8')
new_block_lines = block_text.splitlines(keepends=True)

# Insert before the header
lines = lines[:header_idx] + new_block_lines + lines[header_idx:]

with open(PATH, 'wb') as f:
    f.write(b'\xef\xbb\xbf' + ''.join(lines).encode('utf-8'))

print(f"Final line count: {len(lines)}")
print(f"Inserted {len(new_block_lines)} new lines before line {header_idx + 1}")
print("Splice 2 complete!")
