#!/usr/bin/env python3
"""Splice 3: Prepend last_updated_note_v3_48 before v3_47 line."""
PATH = r"C:\Users\c8rom\desktop\costmgr\_bmad-output\implementation-artifacts\sprint-status.yaml"
NOTE_PATH = r"C:\Users\c8rom\desktop\costmgr\scripts\phase19-splice-note.txt"

with open(PATH, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8-sig')
lines = text.splitlines(keepends=True)

# Find the existing v3_47 note
v347_idx = None
for i, line in enumerate(lines):
    if line.startswith('last_updated_note_v3_47:'):
        v347_idx = i
        break
assert v347_idx is not None, "Could not find v3_47 note"
print(f"v3_47 note at line {v347_idx + 1}")

with open(NOTE_PATH, 'rb') as f:
    note_raw = f.read()
if note_raw.startswith(b'\xef\xbb\xbf'):
    note_raw = note_raw[3:]
note_text = note_raw.decode('utf-8').rstrip('\n\r')
note_line = note_text + '\n'

lines.insert(v347_idx, note_line)

with open(PATH, 'wb') as f:
    f.write(b'\xef\xbb\xbf' + ''.join(lines).encode('utf-8'))

print(f"Inserted note before line {v347_idx + 1}")
print(f"Final line count: {len(lines)}")
print("Splice 3 complete!")
