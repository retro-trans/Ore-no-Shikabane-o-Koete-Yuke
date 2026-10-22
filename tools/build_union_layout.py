"""Fit deity sorting and confirmation cost. Inspect dry run before --write."""
import argparse
import hashlib
import json
import re
import struct

from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import root_entries, rebuild_ez, rebuild_root

V = '0.2.47'
BASE = 0x08803000
PATCHES = [
    (0x088e3000,0x24050050,0x240500a0,'Deity sort cell width: 80 to 160'),
    (0x0893b018,0x24060030,0x2406003c,'Confirmation deity card height: 48 to 60'),
    (0x0893b0f0,0x2405000e,0x2405000c,'Full required-points caption font: 14 to 12'),
    (0x0893b110,0x2405013b,0x2405012b,'Required-points caption left: 315 to 299'),
    (0x0893b15c,0x240600a2,0x240600b2,'Required-points value on own row: y162 to y178'),
]
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.46'
    source = (src / 'EBOOT.weather.elf').read_bytes()
    data = (src / 'data.weather.ore').read_bytes()
    assert sha(source) == '2310261f36d77ec9a87da5cc9d8229a1b17a32fde0ff961b561d675d1a76fedc'
    assert sha(data) == '1e7985098d29a19cc37da0126acfeec4372c4e5b128a3e03fca1e834c0b0857e'
    elf = bytearray(source)
    allowed = set()
    for pc,old,new,_ in PATCHES:
        off = pc-BASE
        assert struct.unpack_from('<I',elf,off)[0] == old, hex(pc)
        struct.pack_into('<I',elf,off,new)
        allowed.update(range(off,off+4))
    assert len(elf) == len(source)
    assert all(a == b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    glyphs = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text())['glyphs']
    batch = json.loads((ROOT / 'work/translation/en/ui_batch_012.en.json').read_text(encoding='utf-8'))
    measurements = []
    for row in batch['rows']:
        if row['archive_offset'] != 0xc000 or row['member_entry'] != 4 or row['section'] != 0 or row['index'] not in [5,8,9,10,11,12,13,14,15]:
            continue
        text = re.sub(r'\[.*?\]','',row['translation_en'])
        size = 12 if row['index'] == 5 else 14
        advance = sum(glyphs[str(ord(c))]['advance'] for c in text)*size/14
        budget = 152 if row['index'] == 5 else 160
        assert advance < budget, (text,advance,budget)
        measurements.append(dict(id=row['id'],text=text,measured_font_size=size,advance=advance,budget=budget))
    assert len(measurements) == 9
    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_ = root_entries(original)
    be,bend = root_entries(data)
    ti = next(i for i,_,_,o in oe if o == 0x1e8000)
    tb = next(o for i,_,_,o in be if i == ti)
    ta,te = container(data,tb)
    ot,ote = container(original,0x1e8000)
    title,preview,fr = footer(member(ot,ote,25),V)
    ore = rebuild_root(data,{tb:rebuild_ez(ta,{25:pack(title)})},mutable=True)
    ae,aend = root_entries(ore)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend)-(a[2]&2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend)-(b[2]&2047)
        aa,bb = data[a[3]:sa],ore[b[3]:sb]
        if a[3] != tb:
            assert aa == bb
        else:
            _,ar = container(aa,0)
            _,br = container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j != 25:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V,source_version='0.2.46',elf_sha256=sha(elf),archive_sha256=sha(ore),
        elf_bytes=len(elf),archive_bytes=len(ore),
        patches=[dict(address=hex(pc),before=hex(old),after=hex(new),purpose=note) for pc,old,new,note in PATCHES],
        layout=dict(sort_cell_width_before=80,sort_cell_width_after=160,sort_rows=4,sort_columns=2,
            confirmation_frame_before=[291,136,160,48],confirmation_frame_after=[291,136,160,60],
            caption_left=299,caption_top=162,caption_size=12,caption_right_budget=451,
            value_top=178,value_right_anchor=447,value_size=14,
            card_bottom=196,confirmation_prompt_top=200,vertical_gap=4),
        measurements=measurements,
        checks=dict(executable='Only five guarded layout arguments; no added code or RAM',
            wording='All unchanged, including the full Offering Points Required caption',
            archive='Only title version; all other payloads byte-identical',
            sorting_and_union_logic='Unchanged',prior_fixes='Preserved'),
        footer=fr,runtime_verification='pending',texture_replacement=False,github_release=False)
    return elf,ore,preview,report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    elf,ore,preview,report = build()
    print(json.dumps({k:v for k,v in report.items() if k != 'footer'},indent=2))
    if args.write:
        out = ROOT / ('work/output/english-native-' + V)
        out.mkdir(exist_ok=True)
        assert not (out / 'EBOOT.union.elf').exists()
        (out / 'EBOOT.union.elf').write_bytes(elf)
        (out / 'data.union.ore').write_bytes(ore)
        (out / 'union.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui = ROOT / ('work/ui/union-layout-' + V)
        ui.mkdir(exist_ok=True)
        preview.save(ui / 'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')
