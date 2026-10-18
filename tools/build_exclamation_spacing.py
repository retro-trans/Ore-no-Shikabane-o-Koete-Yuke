"""Remove the native ASCII exclamation offset. Dry run unless --write."""
import argparse, hashlib, json, struct
from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import root_entries, rebuild_ez, rebuild_root

VERSION = '0.2.24'
BASE = 0x08803000
OFFSET_COMPARE = 0x089BB24C

def sha(b): return hashlib.sha256(b).hexdigest()

def build():
    src = ROOT / 'work/output/english-native-0.2.23'
    source = (src / 'EBOOT.disclaimer.elf').read_bytes()
    data = (src / 'data.disclaimer.ore').read_bytes()
    assert sha(source) == '6bb601ecd0cecc789f980a20e03c4f5a9e7f5b3ad176427681c67088f87b09c9'
    assert sha(data) == '0f8a389746717c8d817a0a344490f476ebd30e815bc92832e901439f2434957e'
    elf = bytearray(source)
    # The native offset helper returns 14 quarter units for !, ?, and their
    # fullwidth counterparts. Disable only the ASCII ! comparison using -1,
    # which cannot equal its zero-extended UTF-16 character argument. Keep
    # question marks, fullwidth punctuation, advances, and null behavior.
    old, new = 0x24020021, 0x2402FFFF
    assert struct.unpack_from('<I', elf, OFFSET_COMPARE - BASE)[0] == old
    struct.pack_into('<I', elf, OFFSET_COMPARE - BASE, new)
    assert all(a == b or OFFSET_COMPARE-BASE <= i < OFFSET_COMPARE-BASE+4
               for i, (a, b) in enumerate(zip(source, elf)))
    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe, _ = root_entries(original); be, bend = root_entries(data)
    idx = next(i for i, _, _, o in oe if o == 0x1e8000)
    tb = next(o for i, _, _, o in be if i == idx)
    ta, te = container(data, tb); ot, ote = container(original, 0x1e8000)
    ppt, preview, fr = footer(member(ot, ote, 25), VERSION)
    del original
    ore = rebuild_root(data, {tb: rebuild_ez(ta, {25: pack(ppt)})}, mutable=True)
    ae, aend = root_entries(ore)
    for n, (a, b) in enumerate(zip(be, ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend) - (a[2] & 2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend) - (b[2] & 2047)
        aa, bb = data[a[3]:sa], ore[b[3]:sb]
        if a[3] != tb: assert aa == bb
        else:
            _, ar = container(aa, 0); _, br = container(bb, 0)
            for j, ((_, z, p, _), (_, zz, pp, _)) in enumerate(zip(ar, br)):
                if j != 25: assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=VERSION, source_version='0.2.23',
                  elf_sha256=sha(elf), archive_sha256=sha(ore),
                  elf_bytes=len(elf), archive_bytes=len(ore),
                  patch=dict(address=hex(OFFSET_COMPARE), before=hex(old), after=hex(new)),
                  ascii_exclamation_offset=dict(before=14, after=0, units='native quarter units before text scaling'),
                  checks=dict(other_executable_bytes='byte-identical', all_script_payloads='byte-identical',
                              unrelated_archive_members='byte-identical', font_atlas_and_advances='unchanged',
                              question_marks_and_fullwidth_punctuation='unchanged'),
                  footer=fr, texture_replacement=False, runtime_verification='pending')
    return elf, ore, preview, report

def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    elf, ore, preview, report = build(); print(json.dumps(report, indent=2))
    if a.write:
        out = ROOT / ('work/output/english-native-' + VERSION); out.mkdir(parents=True, exist_ok=True)
        assert not (out / 'EBOOT.spacing.elf').exists()
        (out / 'EBOOT.spacing.elf').write_bytes(elf); (out / 'data.spacing.ore').write_bytes(ore)
        (out / 'spacing.report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        ui = ROOT / ('work/ui/punctuation-' + VERSION); ui.mkdir(parents=True, exist_ok=True); preview.save(ui/'native-footer.png')
    print('Written.' if a.write else 'DRY RUN: no game changes.')

if __name__ == '__main__': main()
