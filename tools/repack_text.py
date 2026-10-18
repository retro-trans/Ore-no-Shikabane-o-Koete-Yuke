"""Relocate translated MLT strings and rebuild EZBIND/root offsets. Dry run by default."""
import argparse
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

from catalog_text import ROOT, category, parse_mlt, unpack_member, u32
from check_translation import TOKEN, tokens_equal


def align(value, multiple):
    return (value + multiple - 1) & ~(multiple - 1)


def rebuild_mlt(original, changes, encoding='utf-16-le'):
    records = list(parse_mlt(original, encoding))
    by_section = {}
    for section, index, offset, text in records:
        by_section.setdefault(section, []).append((index, text))
    result = bytearray(original[:4] + bytes(original[3] * 4))
    locations = []
    for section in range(original[3]):
        result.extend(b'\xff' * (align(len(result), 4) - len(result)))
        section_start = len(result)
        struct.pack_into('<I', result, 4 + section * 4, section_start)
        old_section = u32(original, 4 + section * 4)
        header = u32(original, old_section)
        count, flags = header & 65535, header >> 16
        result.extend(struct.pack('<I', header))
        if flags == 0x1111:
            timing_len = align(count * 2, 4)
            result.extend(original[old_section + 4:old_section + 4 + timing_len])
        table = len(result)
        result.extend(bytes(count * 4))
        for index, old_text in by_section.get(section, []):
            locations.append((table + index * 4, changes.get((section, index), old_text)))
    shared = {}
    for pointer, text in locations:
        encoded = text.encode(encoding) + (b'\0\0' if encoding == 'utf-16-le' else b'\0')
        if encoded not in shared:
            shared[encoded] = len(result)
            result.extend(encoded)
        struct.pack_into('<I', result, pointer, shared[encoded])
    result.extend(b'\xff' * (align(len(result), 4) - len(result)))
    actual = [(s, i, t) for s, i, _, t in parse_mlt(result, encoding)]
    expected = [(s, i, changes.get((s, i), t)) for s, i, _, t in records]
    if actual != expected:
        raise ValueError('Rebuilt MLT failed round-trip verification')
    return bytes(result)


def rebuild_ez(original, updates):
    count, alignment = struct.unpack_from('<II', original, 8)
    entries = [struct.unpack_from('<4I', original, 16 + i * 16) for i in range(count)]
    names_end = max(original.index(b'\0', no) + 1 for no, _, _, _ in entries)
    result = bytearray(original[:align(names_end, alignment)])
    for i, (no, size, pos, name_hash) in enumerate(entries):
        result.extend(bytes(align(len(result), alignment) - len(result)))
        payload = updates.get(i, original[pos:pos + size])
        struct.pack_into('<4I', result, 16 + i * 16, no, len(payload), len(result), name_hash)
        result.extend(payload)
    result.extend(bytes(align(len(result), alignment) - len(result)))
    return bytes(result)


def root_entries(data):
    entries = []
    count = u32(data, 0x4004)
    for i in range(2, count + 2):
        name_hash, packed = struct.unpack_from('<II', data, 0x4000 + i * 8)
        offset = packed & 0x7FFFF800
        if not 0xC000 <= offset < len(data):
            raise ValueError('Invalid root index entry')
        entries.append((i, name_hash, packed, offset))
    if any(b[3] <= a[3] for a, b in zip(entries, entries[1:])):
        raise ValueError('Non-monotonic root payload offsets')
    end = u32(data, 0x4004 + (count + 2) * 8) & 0x7FFFF800
    if not entries or not entries[-1][3] < end <= len(data):
        raise ValueError('Invalid root byte-length field')
    return entries, end


def rebuild_root(data, changed, mutable=False):
    entries, end = root_entries(data)
    valid = {e[3] for e in entries}
    if set(changed) - valid:
        raise ValueError('Changed EZBIND is not a top-level indexed payload')
    result = bytearray(data[:0xC000])
    for n, (index, name_hash, packed, off) in enumerate(entries):
        next_off = entries[n + 1][3] if n + 1 < len(entries) else end
        size = next_off - off - (packed & 2047)
        if size < 0:
            raise ValueError('Root padding exceeds payload size')
        payload = changed.get(off, data[off:off + size])
        start = len(result)
        if start % 2048:
            raise ValueError('Root payload is not sector aligned')
        result.extend(payload)
        pad = align(len(result), 2048) - len(result)
        struct.pack_into('<I', result, 0x4004 + index * 8,
                         start | pad | (packed & 0x80000000))
        result.extend(data[off + size:next_off] if off not in changed and pad == (packed & 2047) else bytes(pad))
    # The first 16 KiB are hash buckets, not a byte-length header. Keep them intact.
    sentinel = 0x4004 + (len(entries) + 2) * 8
    old_sentinel = u32(data, sentinel)
    struct.pack_into('<I', result, sentinel, len(result) | (old_sentinel & 0x80000000))
    # Large native archives can exceed a 32-bit Python's contiguous allocation
    # budget when copied a second time. Callers may retain the finished buffer.
    return result if mutable else bytes(result)


def build(exports):
    data = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    if rebuild_root(data, {}) != data:
        raise ValueError('Unmodified root round trip is not byte-identical')
    translations = {}
    versions = []
    for export in exports:
        batch = json.loads(export.read_text(encoding='utf-8'))
        versions.append(batch['version'])
        for row in batch['rows']:
            if row.get('status') in ('untranslated', 'blocked') or 'translation_en' not in row:
                continue
            if not row['translation_en'] and row['source_sha256'] != hashlib.sha256(b'').hexdigest():
                raise ValueError('Cannot erase a nonempty source record: ' + row['id'])
            if row['id'] in translations and translations[row['id']]['translation_en'] != row['translation_en']:
                raise ValueError('Conflicting translation ID: ' + row['id'])
            translations[row['id']] = row
    grouped = {}
    for row in translations.values():
        grouped.setdefault(row['archive_offset'], {}).setdefault(row['member_entry'], []).append(row)
    changed, reports = {}, []
    for base, members in grouped.items():
        updates = {}
        max_end = 0
        for entry in range(u32(data, base + 8)):
            _, size, pos, _ = struct.unpack_from('<4I', data, base + 16 + entry * 16)
            max_end = max(max_end, pos + size)
        for entry, rows in members.items():
            no, size, pos, _ = struct.unpack_from('<4I', data, base + 16 + entry * 16)
            name = data[base + no:data.index(b'\0', base + no)].decode('ascii')
            stored = data[base + pos:base + pos + size]
            decoded, compression = unpack_member(stored)
            encoding = 'ascii' if category(name) == 'voice_or_event_metadata' else 'utf-16-le'
            originals = {(s, i): t for s, i, _, t in parse_mlt(decoded, encoding)}
            changes = {}
            for row in rows:
                key = row['section'], row['index']
                text = originals[key]
                if hashlib.sha256(text.encode()).hexdigest() != row['source_sha256']:
                    raise ValueError('Source hash mismatch: ' + row['id'])
                en = row['translation_en']
                if not tokens_equal(text, en):
                    raise ValueError('Changed controls: ' + row['id'])
                changes[key] = en
            new = rebuild_mlt(decoded, changes, encoding)
            if compression == 'custom_deflate':
                compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
                payload = b'\x1f\x8b\x09\0' + struct.pack('<I', len(new)) + compressor.compress(new) + compressor.flush()
            elif compression == 'raw':
                payload = new
            else:
                raise ValueError('Unsupported member compression')
            if unpack_member(payload)[0] != new:
                raise ValueError('Recompressed message failed verification')
            updates[entry] = payload
            reports.append(dict(file=name, rows=len(rows), old_decoded_bytes=len(decoded), new_decoded_bytes=len(new)))
        changed[base] = rebuild_ez(data[base:base + align(max_end, u32(data, base + 12))], updates)
    new_root = rebuild_root(data, changed)
    version = max(versions, key=lambda v: tuple(map(int, v.split('.'))))
    return new_root, dict(version=version, translated_records=len(translations),
                          retained_empty_records=sum(not r['translation_en'] for r in translations.values()),
                          changed_archives=len(changed), files=reports, source_bytes=len(data),
                          output_bytes=len(new_root), sha256=hashlib.sha256(new_root).hexdigest(),
                          checks='Byte-identical unmodified root; every MLT row round-tripped; source hashes and engine tokens matched.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--translations', type=Path, nargs='+')
    ap.add_argument('--output', type=Path)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()
    exports = args.translations or sorted((ROOT / 'work/translation/en').glob('*.en.json'))
    data, report = build(exports)
    args.output = args.output or ROOT / 'work/output' / ('english-native-' + report['version']) / 'data.ore'
    print(json.dumps(report if args.verbose else {k: v for k, v in report.items() if k != 'files'}, indent=2))
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
        args.output.with_suffix('.report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Rebuilt text archive written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()
