"""Translate and relocate the two executable-embedded MLT tables.

Dry run by default. Leaves the source ELF and all previous builds untouched.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from catalog_text import parse_mlt
from check_translation import TOKEN
from repack_text import rebuild_mlt, align
from strip_jp import FIELDS

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.2.3'
BASE = 0x08803000
SOURCE_SHA = 'fa0650a6caf567bd21b64d821ac22b036b6b5151302c40eb3f487b2ff4a113e3'
FONT_SHA = '8b465f18ca7d5dc550dba2f5a5d1cb451fa801e65e9f5b35d37d508948018b5c'
# Explicit original LUI/ADDIU pairs: each address materializes the table base
# passed to the MLT loader. Similar low halves with another LUI are unrelated.
TABLES = [
    (0x21C9F0, 0x100, 0x0881BC68, 0x0881BC78, {
        (0, 0): 'Over My Dead Body', (0, 1): 'Save Data', (0, 2): '(Detail)',
        (0, 3): 'New Save Data', (1, 0): 'Over My Dead Body',
        (1, 1): 'Year %d, month %d, at %s',
        (1, 2): 'Screenshot saving failed.\nThe system entered sleep mode\nwhile saving the screenshot.',
        (1, 3): 'Kyoto',
    }),
    (0x246F84, 0x1BC, 0x08968AA4, 0x08968AB0, {
        (0, 0): 'No storage media is inserted.',
        (0, 1): 'The storage media was removed.',
        (0, 2): 'There is not enough free space on the storage media.',
        (0, 3): 'The data is corrupted.',
        (0, 4): 'The storage media cannot be accessed.',
        (0, 5): 'An internal error occurred.',
        (0, 6): '%1:s\n\nThis game needs storage media with\nat least %2:d KB of free space.\n\nStart the game anyway?',
        (0, 7): 'The data is from an older version.\nDelete it?',
        (0, 8): 'Deleted.', (0, 9): 'Deletion failed.',
    }),
]


def build():
    source = (ROOT / 'work/source/EBOOT.decrypted.elf').read_bytes()
    native = bytearray((ROOT / 'work/output/vwf-0.2.0/EBOOT.elf').read_bytes())
    assert hashlib.sha256(source).hexdigest() == SOURCE_SHA
    assert hashlib.sha256(native).hexdigest() == FONT_SHA
    phoff = struct.unpack_from('<I', native, 28)[0]
    header = list(struct.unpack_from('<8I', native, phoff + 32))
    segment_offset, segment_address = header[1], header[2]
    assert segment_offset + header[4] == len(native)
    rows, patches = [], []
    for offset, size, high_pc, low_pc, english in TABLES:
        table = source[offset:offset + size]
        records = list(parse_mlt(table))
        assert set(english) == {(s, i) for s, i, _, _ in records}
        for section, index, text_offset, jp in records:
            en = english[section, index]
            assert TOKEN.findall(jp) == TOKEN.findall(en)
            assert jp.count('\n') == en.count('\n')
            rows.append(dict(id=f'elf:{offset:08x}:{section:02d}:{index:04d}',
                             file=f'EBOOT:{offset:08x}.mlt', section=section, index=index,
                             text_offset=text_offset, source_jp=jp,
                             source_sha256=hashlib.sha256(jp.encode()).hexdigest(),
                             category='executable_system_messages', translation_en=en,
                             status='draft', kind='system_message', fit_status='unverified_in_game',
                             meaning_review='self_reviewed',
                             context='Executable-embedded save metadata or storage error message; runtime placeholders remain in order.',
                             review_notes=['Project English title is a translation, not a claim of an official PSP English release.'] if index == 0 and offset == 0x21C9F0 else []))
        rebuilt = rebuild_mlt(table, english)
        native.extend(bytes(align(len(native), 16) - len(native)))
        address = segment_address + len(native) - segment_offset
        native.extend(rebuilt)
        high, low = struct.unpack_from('<I', native, high_pc - BASE)[0], struct.unpack_from('<I', native, low_pc - BASE)[0]
        assert high >> 26 == 15 and low >> 26 == 9
        reg = (high >> 16) & 31
        assert (low >> 21) & 31 == reg and (low >> 16) & 31 == reg
        old_address = ((high & 65535) << 16) + struct.unpack('<h', struct.pack('<H', low & 65535))[0]
        assert old_address == offset + BASE
        high_new = high & 0xFFFF0000 | ((address + 0x8000) >> 16)
        low_new = low & 0xFFFF0000 | (address & 65535)
        struct.pack_into('<I', native, high_pc - BASE, high_new)
        struct.pack_into('<I', native, low_pc - BASE, low_new)
        assert ((high_new & 65535) << 16) + struct.unpack('<h', struct.pack('<H', low_new & 65535))[0] == address
        patches.append(dict(original_table_address=hex(old_address), relocated_address=hex(address),
                            original_bytes=size, rebuilt_bytes=len(rebuilt), records=len(records),
                            high_instruction=hex(high_pc), low_instruction=hex(low_pc)))
    header[4] = header[5] = len(native) - segment_offset
    struct.pack_into('<8I', native, phoff + 32, *header)
    bilingual = dict(schema_version=1, version=VERSION, language='en', status='draft', rows=rows)
    safe = {k: bilingual[k] for k in ('schema_version', 'version', 'language', 'status')}
    safe['rows'] = [{k: r[k] for k in FIELDS if k in r} for r in rows]
    report = dict(version=VERSION, font_component_version='0.2.0', translated_embedded_records=len(rows),
                  texture_replacement=False, source_elf_sha256=SOURCE_SHA,
                  input_native_elf_sha256=FONT_SHA, patched_elf_sha256=hashlib.sha256(native).hexdigest(),
                  bytes=len(native), added_ram_beyond_font=len(native) - (segment_offset + 0x21000),
                  patches=patches, status='Round trips and address materialization pass; runtime save/error layout not yet verified.')
    return native, bilingual, safe, report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    native, bilingual, safe, report = build()
    print(json.dumps(report, indent=2))
    print('English samples:', [r['translation_en'] for r in bilingual['rows'][:4]])
    if args.write:
        dest = ROOT / 'work/output' / ('native-' + VERSION)
        if (dest / 'EBOOT.elf').exists():
            raise ValueError('Preserve an existing build; choose a new version')
        dest.mkdir(parents=True, exist_ok=True)
        (dest / 'EBOOT.elf').write_bytes(native)
        (dest / 'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        trans = ROOT / 'work/translation/en/executable'
        trans.mkdir(parents=True, exist_ok=True)
        (trans / 'system_messages.json').write_text(json.dumps(bilingual, ensure_ascii=False, indent=2), encoding='utf-8')
        # Use the same allowlist as strip_jp; compare a fresh strip export in QA.
        (trans / 'system_messages.en.json').write_text(json.dumps(safe, indent=2), encoding='utf-8')
    print('Executable and translation files written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()
