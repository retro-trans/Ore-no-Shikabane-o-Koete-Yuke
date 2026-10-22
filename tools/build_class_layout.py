"""Widen class descriptions and place button hints above them. Dry run first."""
import argparse
import hashlib
import json
import struct

from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import root_entries, rebuild_ez, rebuild_root

V = '0.2.44'
BASE = 0x08803000
PATCHES = [
    (0x0893838c, 0x240600f6, 0x240600b4, 'Back hint vertical anchor: 246 to 180'),
    (0x089383cc, 0x240600f6, 0x240600b4, 'Switch Gender hint top: 246 to 180'),
    (0x08938404, 0x24050060, 0x24050018, 'Description left: 96 to 24'),
    (0x0893840c, 0x240600c6, 0x240600cc, 'Description top: 198 to 204'),
    (0x0893842c, 0x24050120, 0x240501b0, 'Description width: 288 to 432'),
]
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.43'
    source = (src / 'EBOOT.investment.elf').read_bytes()
    data = (src / 'data.investment.ore').read_bytes()
    assert sha(source) == 'f640c9270e51e2d1b458928f0d98340af47664232debed34024db8296dc986b8'
    assert sha(data) == 'ef7f05e352f081cbf9e53a5f5c2efb79fba7fd2b894af5454d79731ce479777a'
    elf = bytearray(source)
    allowed = set()
    for pc, old, new, _ in PATCHES:
        off = pc - BASE
        assert struct.unpack_from('<I', elf, off)[0] == old
        struct.pack_into('<I', elf, off, new)
        allowed.update(range(off, off+4))
    assert len(elf) == len(source)
    assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(source, elf)))
    glyphs = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text())['glyphs']
    batch = json.loads((ROOT / 'work/translation/en/initial_batch.en.json').read_text(encoding='utf-8'))
    fits = []
    for row in batch['rows']:
        if row['file'] != 'home.mlb' or row['section'] != 4 or row['index'] >= 8:
            continue
        widths = [sum(glyphs[str(ord(c))]['advance'] for c in line) * 12 / 14 for line in row['translation_en'].split('\n')]
        assert len(widths) <= 3 and max(widths) <= 420
        fits.append(dict(id=row['id'], translation=row['translation_en'], line_advances=widths))
    assert len(fits) == 8
    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe, _ = root_entries(original)
    be, bend = root_entries(data)
    ti = next(i for i, _, _, o in oe if o == 0x1e8000)
    tb = next(o for i, _, _, o in be if i == ti)
    ta, te = container(data, tb)
    ot, ote = container(original, 0x1e8000)
    title, preview, fr = footer(member(ot, ote, 25), V)
    ore = rebuild_root(data, {tb: rebuild_ez(ta, {25: pack(title)})}, mutable=True)
    ae, aend = root_entries(ore)
    for n, (a, b) in enumerate(zip(be, ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend) - (a[2] & 2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend) - (b[2] & 2047)
        aa, bb = data[a[3]:sa], ore[b[3]:sb]
        if a[3] != tb:
            assert aa == bb
        else:
            _, ar = container(aa, 0)
            _, br = container(bb, 0)
            for j, ((_, z, p, _), (_, zz, pp, _)) in enumerate(zip(ar, br)):
                if j != 25:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V, source_version='0.2.43', elf_sha256=sha(elf), archive_sha256=sha(ore),
        elf_bytes=len(elf), archive_bytes=len(ore), patches=[dict(address=hex(pc), before=hex(old), after=hex(new), purpose=note) for pc, old, new, note in PATCHES],
        layout=dict(description_before=[96,198,288,66], description_after=[24,204,432,66],
            description_right=456, description_bottom=270, hint_anchor_before=246, hint_anchor_after=180,
            hint_row='Directly above description, below class labels', text_advance_budget=420),
        descriptions=fits, checks=dict(executable='Only five guarded position/width arguments changed; no new RAM/code',
            wording_and_controls='Unchanged', archive='Title version only; every other payload byte-identical',
            class_selection_unlocks_and_gender_switch='Unchanged', prior_fixes='Preserved'),
        footer=fr, texture_replacement=False, runtime_verification='pending', github_release=False)
    return elf, ore, preview, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    elf, ore, preview, report = build()
    print(json.dumps({k:v for k,v in report.items() if k not in ['footer','descriptions']}, indent=2))
    print('All eight descriptions fit; longest line:', max(max(x['line_advances']) for x in report['descriptions']))
    if args.write:
        out = ROOT / ('work/output/english-native-' + V)
        out.mkdir(exist_ok=True)
        assert not (out / 'EBOOT.class.elf').exists()
        (out / 'EBOOT.class.elf').write_bytes(elf)
        (out / 'data.class.ore').write_bytes(ore)
        (out / 'class.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        ui = ROOT / ('work/ui/class-layout-' + V)
        ui.mkdir(exist_ok=True)
        preview.save(ui / 'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')
