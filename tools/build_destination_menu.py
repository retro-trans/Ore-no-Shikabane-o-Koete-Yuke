"""Widen the dungeon destination menu for 0.2.11; dry run unless --write."""
import argparse
import hashlib
import json
import struct

from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_title_branding import footer
from repack_text import root_entries, rebuild_ez, rebuild_root

VERSION='0.2.11'
BASE=0x08803000
TABLE=0x08A39FA8


def build():
    source=(ROOT/'work/output/english-native-0.2.9/EBOOT.menu.elf').read_bytes()
    assert hashlib.sha256(source).hexdigest()=='78edad152ec75fcf17b9fc6445afa0b3616107f0935276ebeb67458e5c9bdec8'
    elf=bytearray(source)
    assert struct.unpack_from('<11h',elf,TABLE-BASE)==(1,3,15,4,30,16,10,10,15,15,0)
    struct.pack_into('<h',elf,TABLE-BASE+8,88)
    assert all(a==b or i in (TABLE-BASE+8,TABLE-BASE+9) for i,(a,b) in enumerate(zip(source,elf)))
    data=(ROOT/'work/output/english-native-0.2.10/data.map.ore').read_bytes()
    assert hashlib.sha256(data).hexdigest()=='9773657db296108739cac71a9af2c887f715587775d68cf3b4f10de745bbede0'
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original);be,bend=root_entries(data)
    index=next(i for i,_,_,off in oe if off==0x1e8000)
    titlebase=next(off for i,_,_,off in be if i==index)
    title,entries=container(data,titlebase)
    oldtitle,oldentries=container(original,0x1e8000)
    new,preview,_=footer(member(oldtitle,oldentries,25),VERSION)
    result=rebuild_root(data,{titlebase:rebuild_ez(title,{25:pack(new)})})
    ae,aend=root_entries(result)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=be[n+1][3] if n+1<len(be) else bend
        sb=ae[n+1][3] if n+1<len(ae) else aend
        aa=data[a[3]:sa-(a[2]&2047)];bb=result[b[3]:sb-(b[2]&2047)]
        if a[3]!=titlebase:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j!=25:assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=VERSION,source_version='0.2.10',texture_replacement=False,font_raster_scale=4,
                patch=dict(table=hex(TABLE),field=hex(TABLE+8),cell_width_before=30,cell_width_after=88,
                           scope='Dungeon destination: Enter / Oni Records / Treasures',columns=3,
                           menu_position='Original centering and y offset retained'),
                graphics='Existing native English destination banners from 0.2.10 retained, including Mount Oe',
                checks=dict(executable_diff='One guarded 16-bit data field; code unchanged',
                            unrelated_archive_payloads='byte-identical',unrelated_title_members='byte-identical',
                            prior_map_labels_font_and_menu_fixes='preserved',compression_round_trip='pass'),
                elf_bytes=len(elf),archive_bytes=len(result),elf_sha256=hashlib.sha256(elf).hexdigest(),
                archive_sha256=hashlib.sha256(result).hexdigest(),runtime_verification='pending')
    return bytes(elf),result,preview,report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    elf,ore,preview,report=build();print(json.dumps(report,indent=2))
    if args.write:
        dest=ROOT/'work/output/english-native-0.2.11';dest.mkdir(parents=True,exist_ok=True)
        assert not (dest/'EBOOT.destination.elf').exists() and not (dest/'data.destination.ore').exists()
        (dest/'EBOOT.destination.elf').write_bytes(elf);(dest/'data.destination.ore').write_bytes(ore)
        (dest/'destination.report.json').write_text(json.dumps(report,indent=2)+'\n')
        ui=ROOT/'work/ui/destination-fixes-0.2.11';ui.mkdir(parents=True,exist_ok=True);preview.save(ui/'native-footer.png')
    print('Build written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()
