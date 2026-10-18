"""Inventory executable string candidates without treating binary noise as text.

Dry run by default. Japanese candidates are written only under ignored source/.
The public summary contains counts/addresses, never script passages.
"""
import argparse
import collections
import hashlib
import json
import re
import struct
from pathlib import Path

from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
JP = re.compile(r'[\u3041-\u3096\u30a1-\u30fa\u4e00-\u9fff]')
KANA = re.compile(r'[\u3041-\u3096\u30a1-\u30fa]')


def plausible(text):
    return (2 <= len(text) <= 1024 and len(JP.findall(text)) >= 2
            and all(c.isprintable() or c in '\n\r\t' for c in text)
            and not any(0xe000 <= ord(c) <= 0xf8ff for c in text))


def collect():
    path = ROOT / 'work/source/EBOOT.decrypted.elf'
    data = path.read_bytes()
    with path.open('rb') as stream:
        elf = ELFFile(stream)
        sections = [(s.name, s['sh_addr'], s['sh_offset'], s.data())
                    for s in elf.iter_sections() if s.name in ('.rodata', '.data')]
    rows = []
    for name, address, offset, blob in sections:
        # UTF-16 strings in this game are aligned. Split on aligned terminators;
        # the maximal run is retained, never a guessed Japanese-looking suffix.
        start = 0
        for end in range(0, len(blob) - 1, 2):
            if blob[end:end + 2] != b'\0\0':
                continue
            raw = blob[start:end]
            try:
                text = raw.decode('utf-16-le')
            except UnicodeDecodeError:
                text = ''
            if plausible(text):
                rows.append(dict(section=name, address=address + start, file_offset=offset + start,
                                 encoding='utf-16-le', source_jp=text,
                                 source_sha256=hashlib.sha256(raw).hexdigest(),
                                 kana_present=bool(KANA.search(text)), status='candidate_unreviewed'))
            start = end + 2
        # Narrow literals are byte-terminated and may be CP932 in PSP code.
        for match in re.finditer(rb'[^\x00]{2,2048}\x00', blob):
            raw = match.group()[:-1]
            try:
                text = raw.decode('cp932')
            except UnicodeDecodeError:
                continue
            if plausible(text):
                rows.append(dict(section=name, address=address + match.start(),
                                 file_offset=offset + match.start(), encoding='cp932', source_jp=text,
                                 source_sha256=hashlib.sha256(raw).hexdigest(),
                                 kana_present=bool(KANA.search(text)), status='candidate_unreviewed'))
    # A stored pointer is useful evidence, though its absence is not exclusion:
    # MIPS instructions can materialize an address without storing the pointer.
    for row in rows:
        needle = struct.pack('<I', row['address'])
        row['literal_pointer_offsets'] = [m.start() for m in re.finditer(re.escape(needle), data)]
    return rows, dict(version='0.2.2', source_elf_sha256=hashlib.sha256(data).hexdigest(),
                      candidate_records=len(rows), by_encoding=dict(collections.Counter(r['encoding'] for r in rows)),
                      candidates_with_kana=sum(r['kana_present'] for r in rows),
                      candidates_with_stored_pointer=sum(bool(r['literal_pointer_offsets']) for r in rows),
                      status='Unreviewed candidates, not an added translation denominator. Binary noise and engine literals require manual classification.',
                      source_only_inventory='work/source/executable_text_candidates.json',
                      scope='Aligned UTF-16 and null-terminated CP932 candidates in .rodata/.data; not every possible encoding or computed string.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    rows, report = collect()
    print(json.dumps(report, indent=2))
    print('Address samples:', [(hex(r['address']), r['encoding'], r['kana_present']) for r in rows[:8]])
    if args.write:
        (ROOT / 'work/source/executable_text_candidates.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
        (ROOT / 'docs/embedded_text_audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Inventory written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()
