"""Build local 0.2.51: disable obsolete disc EBOOT decryption request.

Only PARAM.SFO HRKGMP_VER (19 -> 0) and the title version change from 0.2.50.
The encrypted executable, decrypted instructions, data and RAM layout stay exact.
Dry run unless --write; never overwrites a prior candidate.
"""
import argparse,json,struct
from pack_hardware_eboot import ROOT,sha,unpack
from build_latin_auto import footer
from build_menu_fixes import container,member,pack
from repack_text import root_entries,rebuild_ez,rebuild_root

V='0.2.51'


def change_flag(source):
    assert source[:4]==b'\0PSF'
    _,_,ko,vo,count=struct.unpack_from('<5I',source)
    hits=[]
    for i in range(count):
        key,fmt,length,capacity,offset=struct.unpack_from('<HHIII',source,20+16*i)
        start=ko+key;name=source[start:source.index(b'\0',start)].decode('ascii')
        if name=='HRKGMP_VER':
            assert fmt==0x404 and length==capacity==4
            hits.append(vo+offset)
    assert len(hits)==1
    pos=hits[0];assert struct.unpack_from('<I',source,pos)[0]==19
    out=bytearray(source);struct.pack_into('<I',out,pos,0)
    assert all(a==b or pos<=i<pos+4 for i,(a,b) in enumerate(zip(source,out)))
    assert len(out)==len(source)
    return bytes(out),dict(key='HRKGMP_VER',offset=pos,before=19,after=0,
        changed_byte_offsets=[i for i,(a,b) in enumerate(zip(source,out)) if a!=b])


def build():
    src=ROOT/'work/output/english-native-0.2.50'
    executable=(src/'EBOOT.hardware.bin').read_bytes()
    data=(src/'data.hardware.ore').read_bytes();metadata=(src/'PARAM.SFO').read_bytes()
    assert sha(executable)=='cb12e50b013ca65f5c4949ba8c384fb7823f17d4db5c3a190df19b843bb0f0f2'
    assert sha(data)=='190b52e78fea22f2ad87ec72a8878fbd5aebc9e3f1c4acc41929225db3dfff7a'
    assert sha(metadata)=='92418e39e2c99ca68e48ff92c9668d459786eefc08a98959082d810dd5e40c80'
    elf=unpack(executable);assert sha(elf)=='e889461d7e2a7ab11ce9b32b3d12fed36c18219b49f0d6c63f1080330edc7dec'
    sfo,change=change_flag(metadata)
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original);be,bend=root_entries(data)
    title_id=next(r[0] for r in oe if r[3]==0x1E8000);tb=next(r[3] for r in be if r[0]==title_id)
    arc,_=container(data,tb);oa,oe2=container(original,0x1E8000)
    title,preview,fr=footer(member(oa,oe2,25),V)
    ore=rebuild_root(data,{tb:rebuild_ez(arc,{25:pack(title)})},mutable=True)
    ae,aend=root_entries(ore)
    for i,(a,b) in enumerate(zip(be,ae)):
        ea=(be[i+1][3] if i+1<len(be) else bend)-(a[2]&2047)
        eb=(ae[i+1][3] if i+1<len(ae) else aend)-(b[2]&2047)
        aa,bb=data[a[3]:ea],ore[b[3]:eb]
        if a[3]!=tb:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j!=25:assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=V,based_on='0.2.50',status='Hardware hypothesis; requires physical test',
        executable_sha256=sha(executable),decrypted_elf_sha256=sha(elf),executable_identical=True,
        sfo_sha256=sha(sfo),sfo_change=change,archive_sha256=sha(ore),archive_bytes=len(ore),
        archive_changes='Title version footer only; all other archive members exact',
        code_or_ram_changes=False,hardware_verified=False,github_release=False,footer=fr,
        evidence='Original ISO flag=19, working update omits flag; ARK-5 propagates this setting to game-info opnssmp_ver; firmware init uses it to request extra decryption module')
    return executable,ore,sfo,preview,report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    executable,ore,sfo,preview,report=build();print(json.dumps(report,indent=2))
    if a.write:
        out=ROOT/('work/output/english-native-'+V);assert not out.exists();out.mkdir()
        (out/'EBOOT.hardware.bin').write_bytes(executable);(out/'data.hardware.ore').write_bytes(ore)
        (out/'PARAM.SFO').write_bytes(sfo);(out/'boot-flag.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/psp-boot-flag-'+V);ui.mkdir(exist_ok=True);preview.save(ui/'native-footer.png')
    print('Written.' if a.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()
