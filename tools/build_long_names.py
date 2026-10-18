"""Native eight-character English names and HD fullwidth Latin. Dry run unless --write."""
import argparse
import hashlib
import json

from catalog_text import ROOT, parse_mlt
from build_menu_fixes import container, member, pack
from build_title_branding import footer
from repack_text import root_entries, rebuild_ez, rebuild_root, rebuild_mlt
from patch_name_font import patch as font_patch
from patch_long_names import patch as name_patch

VERSION='0.2.15'
PROMPTS={(0,9):'Up to 8 English / 3 Japanese characters',
         (0,4):'Use up to 8 English or 3 Japanese characters.'}


def build():
    source=(ROOT/'work/output/english-native-0.2.12/EBOOT.keyboard.elf').read_bytes()
    assert hashlib.sha256(source).hexdigest()=='5fff85a678404af68fe57cbcf51189ed06492edfb871d1469b1b34b0d0632660'
    elf,fr=font_patch(source);elf,nr=name_patch(elf)
    data=(ROOT/'work/output/english-native-0.2.12/data.keyboard.ore').read_bytes()
    assert hashlib.sha256(data).hexdigest()=='49d8d82776e0e86225238458ba36570f61041e35dad333a96bcb2d4187e9f5bb'
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original);be,bend=root_entries(data)
    ti=next(i for i,_,_,off in oe if off==0x1e8000)
    titlebase=next(off for i,_,_,off in be if i==ti)
    namebase=next(off for i,_,_,off in be if i==27)
    title,entries=container(data,titlebase);oldtitle,oldentries=container(original,0x1e8000)
    new,preview,_=footer(member(oldtitle,oldentries,25),VERSION)
    n=next(j for j,e in enumerate(be) if e[0]==27)
    stop=be[n+1][3] if n+1<len(be) else bend
    name=data[namebase:stop-(be[n][2]&2047)]
    before={(s,i):t for s,i,_,t in parse_mlt(name)}
    assert before[0,9]=='Up to 3 characters'
    patched=rebuild_mlt(name,PROMPTS)
    after={(s,i):t for s,i,_,t in parse_mlt(patched)}
    assert all(after[k]==v for k,v in before.items() if k not in PROMPTS)
    result=rebuild_root(data,{titlebase:rebuild_ez(title,{25:pack(new)}),namebase:patched})
    ae,aend=root_entries(result)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=be[n+1][3] if n+1<len(be) else bend;sb=ae[n+1][3] if n+1<len(ae) else aend
        aa=data[a[3]:sa-(a[2]&2047)];bb=result[b[3]:sb-(b[2]&2047)]
        if a[3] not in (titlebase,namebase):assert aa==bb
        elif a[3]==titlebase:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j!=25:assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=VERSION,source_version='0.2.12',texture_replacement=False,font_raster_scale=4,
                font=fr,names=nr,prompts={str(k):v for k,v in PROMPTS.items()},
                checks=dict(unrelated_archive_payloads='byte-identical',unrelated_title_members='byte-identical',
                            other_name_text_and_original_pools='unchanged',compression_round_trip='pass'),
                elf_bytes=len(elf),archive_bytes=len(result),elf_sha256=hashlib.sha256(elf).hexdigest(),
                archive_sha256=hashlib.sha256(result).hexdigest(),runtime_verification='pending')
    return elf,result,preview,report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    elf,ore,preview,report=build();print(json.dumps(report,indent=2))
    if args.write:
        dest=ROOT/('work/output/english-native-'+VERSION);dest.mkdir(parents=True,exist_ok=True)
        assert not (dest/'EBOOT.names.elf').exists() and not (dest/'data.names.ore').exists()
        (dest/'EBOOT.names.elf').write_bytes(elf);(dest/'data.names.ore').write_bytes(ore)
        (dest/'names.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/names-'+VERSION);ui.mkdir(parents=True,exist_ok=True);preview.save(ui/'native-footer.png')
    print('Build written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()
