#!/usr/bin/env python3
"""Verify the exact committed binary suite; execution evidence is in the manifest."""
import hashlib
import json
from pathlib import Path
import struct
import sys


def verify(root):
    manifest = json.loads((root / 'manifest.json').read_text())
    assert manifest['schema_version'] == 1, 'Unsupported manifest schema'
    entries = manifest['binaries']
    expected = [entry['file'] for entry in entries]
    assert entries and len(expected) == len(set(expected)), 'Empty suite or duplicate files'
    assert all(Path(name).name == name and name.endswith('.bin') for name in expected), 'Invalid binary name'
    actual = {path.name for path in root.glob('*.bin')}
    assert actual == set(expected), f'Binary inventory differs: expected {sorted(expected)}, found {sorted(actual)}'
    for entry in entries:
        data = (root / entry['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry['sha256'], f"Hash mismatch: {entry['file']}"
        assert len(data) >= 64 and data[:6] == b'\x7fELF\x02\x01', f"Expected ELF64 little-endian: {entry['file']}"
        assert struct.unpack_from('<HH', data, 16) == (2, 243), f"Expected RISC-V executable: {entry['file']}"
        print(f"OK {entry['file']} {entry['sha256']}")


if __name__ == '__main__':
    try:
        verify(Path(__file__).resolve().parent)
    except (AssertionError, OSError, ValueError, KeyError) as error:
        sys.exit(str(error))
