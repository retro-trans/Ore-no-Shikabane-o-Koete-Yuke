"""Build local 0.2.50 PSP startup candidate; dry run unless --write."""
import argparse,json
from pathlib import Path
from pack_hardware_eboot import ROOT,pack,sha
from build_latin_auto import footer
from build_menu_fixes import container,member,pack as pack_member
from repack_text import root_entries,rebuild_ez,rebuild_root
from extract_iso import inventory

V='0.2.50'


def build():
    base=ROOT/'work/output/english-native-0.2.49'
    elf=(base/'EBOOT.market.elf').read_bytes()
    data=(base/'data.market.ore').read_bytes()
    assert sha(elf)=='e889461d7e2a7ab11ce9b32b3d12fed36c18219b49f0d6c63f1080330edc7dec'
    assert sha(data)=='4795f88824b760117968373e0ef0892949811780dee42a53836a6a4cab39c925'
    packed,report=pack(elf,(ROOT/'work/source/iso/PSP_GAME/SYSDIR/EBOOT.BIN').read_bytes())
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original); be,bend=root_entries(data)
    title_id=next(r[0] for r in oe if r[3]==0x1E8000)
    tb=next(r[3] for r in be if r[0]==title_id)
    arc,entries=container(data,tb); old_arc,old_entries=container(original,0x1E8000)
    title,preview,fr=footer(member(old_arc,old_entries,25),V)
    ore=rebuild_root(data,{tb:rebuild_ez(arc,{25:pack_member(title)})},mutable=True)
    ae,aend=root_entries(ore)
    for i,(a,b) in enumerate(zip(be,ae)):
        ea=(be[i+1][3] if i+1<len(be) else bend)-(a[2]&2047)
        eb=(ae[i+1][3] if i+1<len(ae) else aend)-(b[2]&2047)
        aa,bb=data[a[3]:ea],ore[b[3]:eb]
        if a[3]!=tb: assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j!=25: assert aa[p:p+z]==bb[pp:pp+zz]
    with (ROOT/'work/output/english-native-0.2.49.iso').open('rb') as f:
        row=next(r for r in inventory(f) if r['path']=='PSP_GAME/PARAM.SFO')
        f.seek(row['iso_offset']);sfo=f.read(row['size'])
    assert sha(sfo)=='92418e39e2c99ca68e48ff92c9668d459786eefc08a98959082d810dd5e40c80'
    report.update(version=V,source_version='0.2.49',archive_sha256=sha(ore),sfo_sha256=sha(sfo),
        archive_bytes=len(ore),archive_changes='Title version footer only; all other members identical',
        runtime_status='Pending emulator and physical PSP tests',github_release=False,footer=fr)
    return packed,ore,sfo,preview,report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    packed,ore,sfo,preview,report=build()
    print(json.dumps(report,indent=2))
    if args.write:
        out=ROOT/('work/output/english-native-'+V);assert not out.exists();out.mkdir()
        (out/'EBOOT.hardware.bin').write_bytes(packed)
        (out/'data.hardware.ore').write_bytes(ore)
        (out/'PARAM.SFO').write_bytes(sfo)
        (out/'hardware.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/hardware-startup-'+V);ui.mkdir(exist_ok=True);preview.save(ui/'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()
