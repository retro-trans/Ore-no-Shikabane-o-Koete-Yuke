"""Decode EZBIND/MLT tables and measure Japanese text. Dry run unless --write."""
import argparse
import collections
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JP = re.compile(r'[\u3041-\u3096\u30a1-\u30fa\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9d]')


def u32(data, off):
    return struct.unpack_from('<I', data, off)[0]


def unpack_member(data):
    if data[:4] == b'\x1f\x8b\x09\x00':
        decoder = zlib.decompressobj(-15)
        result = decoder.decompress(data[8:], 64 * 1024 * 1024)
        if not decoder.eof or len(result) != u32(data, 4):
            raise ValueError('Invalid custom deflate length or missing end')
        return result, 'custom_deflate'
    if data[:3] == b'\x1f\x8b\x08':
        return zlib.decompress(data, 31), 'gzip'
    return data, 'raw'


def parse_mlt(data, encoding='utf-16-le'):
    if data[:3] != b'MLT':
        raise ValueError('Missing MLT magic')
    nsections = data[3]
    sections = [u32(data, 4 + s * 4) for s in range(nsections)]
    for section, off in enumerate(sections):
        end = sections[section + 1] if section + 1 < nsections else len(data)
        header = u32(data, off)
        count, flags = header & 65535, header >> 16
        pointers = off + 4
        if flags == 0x1111:
            # Movie tables prefix pointers with u16 frame positions, padded by FFFF.
            sentinel = pointers + count * 2
            if count % 2 and data[sentinel:sentinel + 2] != b'\xff\xff':
                raise ValueError('Invalid subtitle timing sentinel')
            pointers = (sentinel + 3) & ~3
        elif flags:
            raise ValueError('Unknown MLT section flags')
        table_end = pointers + count * 4
        if not 4 + nsections * 4 <= off < end <= len(data) or table_end > end:
            raise ValueError('Invalid MLT section table')
        for index in range(count):
            p = u32(data, pointers + index * 4)
            # Cross-section aliases occur in normal tables (e.g. Itsuka greetings).
            stride = 2 if encoding == 'utf-16-le' else 1
            if p % stride or not 4 + nsections * 4 <= p < len(data):
                raise ValueError('Invalid MLT string pointer')
            e = p
            terminator = b'\0' * stride
            while e + stride <= len(data) and data[e:e + stride] != terminator:
                e += stride
            if e + stride > len(data):
                raise ValueError('Unterminated MLT string')
            yield section, index, p, data[p:e].decode(encoding)


def category(name):
    if name.endswith(('_NA.mlb', '_v.mlb')) or 'narration' in name:
        return 'voice_or_event_metadata'
    if name.endswith('_NAME.mlb'):
        return 'speaker_names'
    if 'kana' in name or 'yomi' in name:
        return 'pronunciation_readings'
    if name == 'intro.mlb':
        return 'character_profile_traits'
    if name.startswith('ev_') or name in {'itsuka.mlb', 'hiruko.mlb',
                                         'ending.mlb', 'prologue.mlb', 'will.mlb',
                                         'spirit_voice.mlb', 'moviesubtitle.mlb'}:
        return 'dialogue_narration_subtitles'
    if name in {'item_name.mlb', 'monster.mlb', 'boss_name.mlb', 'spirit_name.mlb',
                'chara_name.mlb', 'spell.mlb', 'skill.mlb'}:
        return 'names_and_terms'
    return 'ui_system_help'


def collect():
    source = ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore'
    data = source.read_bytes()
    rows, members, errors, other_text = [], [], [], []
    archives = list(re.finditer(b'EZBIND\0\0', data))
    for match in archives:
        base = match.start()
        count, alignment = struct.unpack_from('<II', data, base + 8)
        if alignment not in (4, 64) or count > 100000:
            raise ValueError(f'Unexpected EZBIND header at {base:x}')
        for entry in range(count):
            no, size, pos, name_hash = struct.unpack_from('<4I', data, base + 16 + entry * 16)
            ne = data.index(b'\0', base + no)
            # Some non-text assets have opaque filename bytes; retain them losslessly.
            name = data[base + no:ne].decode('ascii', errors='backslashreplace')
            if not base + pos + size <= len(data):
                raise ValueError(f'Member outside archive: {name}')
            info = dict(archive_offset=base, entry=entry, name=name, size=size,
                        member_offset=base + pos, name_hash=name_hash, alignment=alignment)
            members.append(info)
            if not name.lower().endswith(('.mlb', '.txt')):
                continue
            try:
                decoded, compression = unpack_member(data[base + pos:base + pos + size])
                info.update(compression=compression, decoded_size=len(decoded),
                            sha256=hashlib.sha256(decoded).hexdigest())
                if name.lower().endswith('.txt'):
                    other_text.append(dict(**info, preview_hex=decoded[:96].hex(),
                                           ascii_only=all(byte < 128 for byte in decoded)))
                    continue
                enc = 'ascii' if category(name) == 'voice_or_event_metadata' else 'utf-16-le'
                parsed = list(parse_mlt(decoded, enc))
                for section, index, offset, text in parsed:
                    rows.append(dict(id=f'ore:{base:08x}:{entry:04d}:{section:02d}:{index:04d}',
                                     file=name, archive_offset=base, member_entry=entry,
                                     section=section, index=index, text_offset=offset,
                                     source_jp=text, source_sha256=hashlib.sha256(text.encode()).hexdigest(),
                                     category=category(name), has_japanese=bool(JP.search(text)),
                                     japanese_characters=len(JP.findall(text))))
            except (ValueError, UnicodeError, zlib.error, struct.error) as exc:
                errors.append(dict(**info, error=str(exc)))
    japanese = [r for r in rows if r['has_japanese']]
    unique = {r['source_jp'] for r in japanese}
    core = [r for r in japanese if r['category'] not in
            {'pronunciation_readings', 'speaker_names', 'voice_or_event_metadata'}]
    stats = dict(schema_version=1, version='0.1.0', date='2026-10-17',
                 archive_count=len(archives), member_count=len(members),
                 mlt_files=sum(m['name'].endswith('.mlb') for m in members),
                 all_mlt_records=len(rows), japanese_records=len(japanese),
                 unique_japanese_strings=len(unique),
                 japanese_characters_with_repetitions=sum(r['japanese_characters'] for r in japanese),
                 japanese_characters_unique_strings=sum(len(JP.findall(t)) for t in unique),
                 main_workload_records=len(core),
                 main_workload_unique_strings=len({r['source_jp'] for r in core}),
                 main_workload_japanese_characters=sum(r['japanese_characters'] for r in core),
                 main_workload_unique_japanese_characters=sum(len(JP.findall(t)) for t in {r['source_jp'] for r in core}),
                 categories={c: dict(records=sum(r['category'] == c for r in japanese),
                                     unique_strings=len({r['source_jp'] for r in japanese if r['category'] == c}))
                             for c in sorted({r['category'] for r in rows})},
                 errors=errors, non_mlt_txt_files=len(other_text),
                 non_mlt_txt_ascii_only=sum(m['ascii_only'] for m in other_text),
                 scope='Indexed MLT records in data.ore only; not a full-game final total.')
    return rows, members, other_text, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    rows, members, other_text, stats = collect()
    print(json.dumps({**stats, 'errors': stats['errors'][:3], 'error_count': len(stats['errors'])}, indent=2))
    print('First record IDs:', [r['id'] for r in rows[:4]])
    if args.write:
        dest = ROOT / 'work/source'
        for name, obj in [('corpus.json', {'schema_version': 1, 'rows': rows}),
                          ('archive_inventory.json', members), ('other_text_inventory.json', other_text)]:
            (dest / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
        report = ROOT / 'docs/text_inventory.json'
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(stats, indent=2), encoding='utf-8')
    print('Catalog written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()
