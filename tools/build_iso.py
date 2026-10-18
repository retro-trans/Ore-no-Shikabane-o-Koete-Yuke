"""Append verified replacement files to a local ISO copy. Dry run unless --write."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

from extract_iso import inventory

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--iso', type=Path)
    ap.add_argument('--elf', type=Path, default=ROOT / 'work/output/vwf-0.2.0/EBOOT.elf')
    ap.add_argument('--ore', type=Path)
    ap.add_argument('--sfo', type=Path, help='Optional localized game-menu metadata')
    ap.add_argument('--output', type=Path, default=ROOT / 'work/output/native-vwf-0.2.0.iso')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--version', default='0.2.0')
    args = ap.parse_args()
    iso = args.iso or next(ROOT.glob('*.iso'))
    if args.output.resolve() == iso.resolve():
        raise ValueError('Never replace the original ISO')
    replacements = {'PSP_GAME/SYSDIR/EBOOT.BIN': args.elf}
    if args.ore:
        replacements['PSP_GAME/USRDIR/data.ore'] = args.ore
    if args.sfo:
        replacements['PSP_GAME/PARAM.SFO'] = args.sfo
    with iso.open('rb') as f:
        files = {r['path']: r for r in inventory(f)}
    plans = []
    pos = (iso.stat().st_size + 2047) & ~2047
    for path, target in replacements.items():
        old = files[path]
        content = target.read_bytes()
        if path.endswith('EBOOT.BIN') and content[:4] != b'\x7fELF':
            raise ValueError('Replacement executable must be a verified plain ELF')
        if path.endswith('PARAM.SFO') and content[:4] != b'\0PSF':
            raise ValueError('Replacement metadata must be a valid SFO container')
        plans.append(dict(path=path, replacement=str(target), new_iso_offset=pos,
                          new_size=len(content), original_size=old['size'],
                          directory_record_offset=old['directory_record_offset'],
                          sha256=hashlib.sha256(content).hexdigest()))
        pos = (pos + len(content) + 2047) & ~2047
    print(json.dumps(dict(version=args.version, source=str(iso), output=str(args.output), output_size=pos,
                          mode='write' if args.write else 'dry run', files=plans), indent=2))
    if not args.write:
        return
    if args.output.exists():
        raise ValueError('Output already exists; preserve it and choose a new output name')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(iso, args.output)
    with args.output.open('r+b') as f:
        for plan in plans:
            f.seek(plan['new_iso_offset'])
            f.write(Path(plan['replacement']).read_bytes())
            record = plan['directory_record_offset']
            f.seek(record + 2)
            f.write(struct.pack('<I', plan['new_iso_offset'] // 2048))
            f.write(struct.pack('>I', plan['new_iso_offset'] // 2048))
            f.seek(record + 10)
            f.write(struct.pack('<I', plan['new_size']))
            f.write(struct.pack('>I', plan['new_size']))
        f.truncate(pos)
        f.seek(16 * 2048 + 80)
        f.write(struct.pack('<I', pos // 2048))
        f.write(struct.pack('>I', pos // 2048))
    with args.output.open('rb') as f:
        updated = {r['path']: r for r in inventory(f)}
        for plan in plans:
            row = updated[plan['path']]
            assert row['size'] == plan['new_size'] and row['iso_offset'] == plan['new_iso_offset']
            f.seek(row['iso_offset'])
            assert hashlib.sha256(f.read(row['size'])).hexdigest() == plan['sha256']
    args.output.with_suffix('.manifest.json').write_text(json.dumps(dict(version=args.version, files=plans, bytes=pos), indent=2), encoding='utf-8')
    print('ISO directory and replacement checksums verified.')


if __name__ == '__main__':
    main()
