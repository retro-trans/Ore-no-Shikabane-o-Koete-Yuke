"""Widen the four-action sortie preparation popup. Dry run before --write."""
import argparse
import hashlib
import json
import struct

from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import root_entries, rebuild_ez, rebuild_root

V = '0.2.42'
BASE = 0x08803000
PC = 0x089012cc
OLD = 0x24050050
NEW = 0x24050078
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.41'
    source = (src / 'EBOOT.prologue.elf').read_bytes()
    data = (src / 'data.prologue.ore').read_bytes()
    assert sha(source) == 'eefe8ff11a6ceb4e8a34d71095370e285c4dbee6d6c9fb41c7ceea032a61b1e7'
    assert sha(data) == '045e2e32f4316078ccb5f8cf23ed236e7fec63c6b37aea21a2b1020ffe7b1b37'
    elf = bytearray(source)
    offset = PC - BASE
    assert struct.unpack_from('<I', elf, offset - 4)[0] == 0x0c000000 | (0x088222d4 >> 2)
    assert struct.unpack_from('<I', elf, offset)[0] == OLD
    struct.pack_into('<I', elf, offset, NEW)
    assert len(elf) == len(source) and elf[:offset] == source[:offset] and elf[offset+4:] == source[offset+4:]
    metrics = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text())['glyphs']
    labels = ['Select Party', 'Change Leader', 'Change Formation', 'Change Equipment']
    fits = [dict(text=t, advance=sum(metrics[str(ord(c))]['advance'] for c in t) * 12 / 14) for t in labels]
    assert all(x['advance'] + 8 <= 120 for x in fits)
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
    report = dict(version=V, source_version='0.2.41', elf_sha256=sha(elf), archive_sha256=sha(ore),
        elf_bytes=len(elf), archive_bytes=len(ore),
        patch=dict(address=hex(PC), before=hex(OLD), after=hex(NEW),
            native_setter='0x088222d4', text_cell_before=80, text_cell_after=120),
        labels=fits, layout='Native layout resizes the frame and highlight and recenters the whole popup; portrait icon space retained',
        checks=dict(executable='Only guarded width argument changed; no new RAM/code allocation',
            archive='Title version only; every other root/member payload byte-identical',
            text_and_controls='Unchanged', prologue_and_scratch_fixes='Preserved', gameplay_and_saves='Unchanged'),
        texture_replacement=False, footer=fr, runtime_verification='pending', github_release=False)
    return elf, ore, preview, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    elf, ore, preview, report = build()
    print(json.dumps({k: v for k, v in report.items() if k != 'footer'}, indent=2))
    if args.write:
        out = ROOT / ('work/output/english-native-' + V)
        out.mkdir(exist_ok=True)
        assert not (out / 'EBOOT.party.elf').exists()
        (out / 'EBOOT.party.elf').write_bytes(elf)
        (out / 'data.party.ore').write_bytes(ore)
        (out / 'party.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        ui = ROOT / ('work/ui/party-popup-' + V)
        ui.mkdir(exist_ok=True)
        preview.save(ui / 'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')
