"""Widen the six-line Help panel. Inspect dry run before --write."""
import argparse
import hashlib
import json
import struct

from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import root_entries, rebuild_ez, rebuild_root

V = '0.2.45'
BASE = 0x08803000
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.44'
    source = (src / 'EBOOT.class.elf').read_bytes()
    data = (src / 'data.class.ore').read_bytes()
    assert sha(source) == 'bf1bfc2fe1981d05d6d64189c27263997cc0f759a3fda2a9579149cb229f7c82'
    assert sha(data) == 'f78400240d2e0d3213e6642092c5218f688d0fed801deb493d9fa7aaccb8147e'
    elf = bytearray(source)
    pc = 0x088fa718
    off = pc - BASE
    assert struct.unpack_from('<I', elf, off)[0] == 0x2405012c
    struct.pack_into('<I', elf, off, 0x24050150)
    assert len(elf) == len(source)
    assert all(a == b or off <= i < off+4 for i, (a, b) in enumerate(zip(source, elf)))
    glyphs = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text())['glyphs']
    batch = json.loads((ROOT / 'work/translation/en/ui_batch_009.en.json').read_text(encoding='utf-8'))
    row = next(r for r in batch['rows'] if r['id'] == 'ore:0000c000:0019:01:0301')
    widths = [sum(glyphs[str(ord(c))]['advance'] for c in line) * 12 / 14
              for line in row['translation_en'].split('\n')]
    assert len(widths) == 6 and max(widths) < 330
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
    report = dict(version=V, source_version='0.2.44', elf_sha256=sha(elf), archive_sha256=sha(ore),
        elf_bytes=len(elf), archive_bytes=len(ore),
        patches=[dict(address=hex(pc), before='0x2405012c', after='0x24050150', purpose='FAQ width 300 to 336')],
        layout=dict(before=[8,144,300,120], after=[8,144,336,120], text_width=330,
            background_opacity='Already fully opaque in the native Help class: texture/vertex alpha 255, sprite and ancestor opacity 1.0. Retained.'),
        measured_example=dict(id=row['id'], translation_en=row['translation_en'], line_advances=widths),
        checks=dict(executable='Only one guarded width argument; no new code or RAM',
            wording_and_controls='Unchanged', archive='Title version only; every other payload byte-identical',
            prior_fixes='Preserved', story_dialogue_opacity='Unchanged'),
        footer=fr, texture_replacement=False, runtime_verification='pending', github_release=False)
    return elf, ore, preview, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    elf, ore, preview, report = build()
    print(json.dumps({k:v for k,v in report.items() if k != 'footer'}, indent=2))
    if args.write:
        out = ROOT / ('work/output/english-native-' + V)
        out.mkdir(exist_ok=True)
        assert not (out / 'EBOOT.help.elf').exists()
        (out / 'EBOOT.help.elf').write_bytes(elf)
        (out / 'data.help.ore').write_bytes(ore)
        (out / 'help.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        ui = ROOT / ('work/ui/help-dialogue-' + V)
        ui.mkdir(exist_ok=True)
        preview.save(ui / 'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')
