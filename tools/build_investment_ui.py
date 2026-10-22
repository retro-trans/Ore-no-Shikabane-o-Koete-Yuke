"""Translate the investment ribbon and amount-entry currency. Dry run first."""
import argparse
import hashlib
import json

from PIL import Image
from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from build_hd_ui import ribbon_image
from hd_sprites import encode
from repack_text import root_entries, rebuild_ez, rebuild_root

V = '0.2.43'
BASE = 0x08803000
UNIT = 0x08a40d5c
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.42'
    source = (src / 'EBOOT.party.elf').read_bytes()
    data = (src / 'data.party.ore').read_bytes()
    assert sha(source) == '2460b563ab994d6947eb1e74ac9c8c1cf080bd91065b388bbf69356ba513fc13'
    assert sha(data) == '931aa172f6fca45788d1593f66077002359e1a3d602186c058f209095f437e73'
    elf = bytearray(source)
    off = UNIT - BASE
    assert elf[off:off+8] == bytes.fromhex('cebe000000000000')
    elf[off:off+4] = b'ryo\0'
    assert elf[:off] == source[:off] and elf[off+4:] == source[off+4:]
    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe, _ = root_entries(original)
    be, bend = root_entries(data)
    rootmap = {o: next(z[3] for z in be if z[0] == i) for i, _, _, o in oe}
    base = rootmap[0xb4a800]
    arc, entries = container(data, base)
    oa, oen = container(original, 0xb4a800)
    old = member(arc, entries, 18)
    assert old == member(oa, oen, 18)
    inv = json.loads((ROOT / 'work/source/archive_inventory.json').read_text())
    assert any(r['archive_offset'] == 0xb4a800 and r['entry'] == 18 and r['name'] == '225.ppt' for r in inv)
    image, typography = ribbon_image(old, 'INVESTMENT')
    image = image.resize((96, 264), Image.Resampling.LANCZOS)
    ppt, actual, hd = encode(old, image, pixel_format=4)
    assert len(ppt) == len(old) == 13744
    assert hd['logical_size'] == [44, 260] and hd['physical_visible_size'] == [88, 260]
    updates = {base: rebuild_ez(arc, {18: pack(ppt)})}
    changed = {base: {18}}
    tb = rootmap[0x1e8000]
    ta, te = container(data, tb)
    ot, ote = container(original, 0x1e8000)
    title, preview, fr = footer(member(ot, ote, 25), V)
    updates[tb] = rebuild_ez(ta, {25: pack(title)})
    changed[tb] = {25}
    ore = rebuild_root(data, updates, mutable=True)
    ae, aend = root_entries(ore)
    for n, (a, b) in enumerate(zip(be, ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend) - (a[2] & 2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend) - (b[2] & 2047)
        aa, bb = data[a[3]:sa], ore[b[3]:sb]
        if a[3] not in updates:
            assert aa == bb
        else:
            _, ar = container(aa, 0)
            _, br = container(bb, 0)
            for j, ((_, z, p, _), (_, zz, pp, _)) in enumerate(zip(ar, br)):
                if j not in changed[a[3]]:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V, source_version='0.2.42', elf_sha256=sha(elf), archive_sha256=sha(ore),
        elf_bytes=len(elf), archive_bytes=len(ore), currency=dict(address=hex(UNIT),
            before_hex=source[off:off+4].hex(), after_hex=bytes(elf[off:off+4]).hex(), translation_en='ryo',
            native_caller='0x0892e89c', amount_entry='Investment amount field'),
        graphics=[dict(archive_offset=0xb4a800, member_entry=18, file='225.ppt', translation_en='INVESTMENT',
            resource_bytes=len(ppt), original_bytes=len(old), **typography, **hd)],
        checks=dict(currency_value_and_input='Unchanged; only visible unit text changes',
            executable='Only guarded currency literal changed; no extra RAM/code',
            archive='Only investment ribbon and title version; unrelated payloads byte-identical',
            script_and_prior_fixes='Byte-identical to 0.2.42', ribbon_loader_budget='Original 13744 bytes preserved'),
        footer=fr, texture_replacement=False, runtime_verification='pending', github_release=False)
    return elf, ore, actual, preview, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    elf, ore, actual, preview, report = build()
    print(json.dumps({k: v for k, v in report.items() if k != 'footer'}, indent=2))
    if args.write:
        out = ROOT / ('work/output/english-native-' + V)
        out.mkdir(exist_ok=True)
        assert not (out / 'EBOOT.investment.elf').exists()
        (out / 'EBOOT.investment.elf').write_bytes(elf)
        (out / 'data.investment.ore').write_bytes(ore)
        (out / 'investment.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        ui = ROOT / ('work/ui/investment-' + V)
        ui.mkdir(exist_ok=True)
        actual.save(ui / 'investment-ribbon.png')
        preview.save(ui / 'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')
