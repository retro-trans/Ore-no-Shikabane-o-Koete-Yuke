"""List a PSP ISO; --write extracts only research inputs, never modifies the ISO."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTED = {'PSP_GAME/PARAM.SFO', 'PSP_GAME/SYSDIR/BOOT.BIN',
            'PSP_GAME/SYSDIR/EBOOT.BIN', 'PSP_GAME/USRDIR/data.bin',
            'PSP_GAME/USRDIR/data.ore'}


def inventory(f):
    f.seek(16 * 2048)
    pvd = f.read(2048)
    if pvd[:7] != b'\x01CD001\x01':
        raise ValueError('Expected ISO9660 primary volume descriptor')
    def walk(extent, size, parent=''):
        directory_base = extent * 2048
        f.seek(directory_base)
        data = f.read(size)
        pos = 0
        while pos < len(data):
            record_offset = directory_base + pos
            n = data[pos]
            if not n:
                pos = (pos // 2048 + 1) * 2048
                continue
            record = data[pos:pos + n]
            pos += n
            name = record[33:33 + record[32]]
            if name in (b'\0', b'\1'):
                continue
            name = name.decode('ascii').split(';')[0]
            if name in ('.', '..') or '/' in name or '\\' in name:
                raise ValueError('Unsafe ISO entry')
            path = f'{parent}/{name}'.lstrip('/')
            extent = struct.unpack_from('<I', record, 2)[0]
            length = struct.unpack_from('<I', record, 10)[0]
            if record[25] & 2:
                yield from walk(extent, length, path)
            else:
                yield dict(path=path, size=length, iso_offset=extent * 2048,
                           directory_record_offset=record_offset)
    yield from walk(struct.unpack_from('<I', pvd, 158)[0],
                    struct.unpack_from('<I', pvd, 166)[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iso', type=Path)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    iso = args.iso or next(ROOT.glob('*.iso'))
    with iso.open('rb') as f:
        rows = list(inventory(f))
        for row in rows:
            if row['path'] not in SELECTED:
                continue
            f.seek(row['iso_offset'])
            data = f.read(row['size'])
            if len(data) != row['size']:
                raise ValueError('Truncated ISO')
            row['sha256'] = hashlib.sha256(data).hexdigest()
            row['header_hex'] = data[:64].hex(' ')
            print(json.dumps(row))
            if args.write:
                target = ROOT / 'work/source/iso' / row['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    if args.write:
        target = ROOT / 'work/source/iso_inventory.json'
        target.write_text(json.dumps({'iso': iso.name, 'size': iso.stat().st_size,
                                     'files': rows}, indent=2), encoding='utf-8')
    print('Extracted inputs.' if args.write else 'DRY RUN: no files written. Use --write to extract.')


if __name__ == '__main__':
    main()
