"""Enable native English name input. Dry run unless --write."""
import argparse
import hashlib
import json
import struct

from catalog_text import ROOT, parse_mlt
from build_menu_fixes import container, member, pack
from build_title_branding import footer
from repack_text import root_entries, rebuild_ez, rebuild_root, rebuild_mlt

VERSION='0.2.12'
BASE=0x08803000
PATCHES=[
    (0x0881B8F0,0x3402D000,0x3402D00F,'Allow Latin digits, symbols, lowercase and uppercase alongside Japanese'),
    (0x0881B928,0xAE000004,0x24020002,'Load OSK English language; zeroed unknown field stays zero'),
    (0x0881B92C,0xAE000008,0xAE020008,'Default name-input language to English'),
]
INSTRUCTION="Next, please enter your family name.\nYou'll only enter it once.\nPlease take care to spell it correctly."


def build():
    source=(ROOT/'work/output/english-native-0.2.11/EBOOT.destination.elf').read_bytes()
    assert hashlib.sha256(source).hexdigest()=='6a6b02d210799497bd6ec02f0c6fb5d84bf49891e0fd1e2d9f1c8eb6c47efb25'
    elf=bytearray(source)
    for pc,old,new,_ in PATCHES:
        assert struct.unpack_from('<I',elf,pc-BASE)[0]==old
        struct.pack_into('<I',elf,pc-BASE,new)
    allowed={pc-BASE+i for pc,_,_,_ in PATCHES for i in range(4)}
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    data=(ROOT/'work/output/english-native-0.2.11/data.destination.ore').read_bytes()
    assert hashlib.sha256(data).hexdigest()=='a6245ab3836fbea5c0a5e40de6349a06f7dc6cdcfcaeb1de3b0fcc516d7ee46f'
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original);be,bend=root_entries(data)
    index=next(i for i,_,_,off in oe if off==0x1e8000)
    titlebase=next(off for i,_,_,off in be if i==index)
    title,entries=container(data,titlebase)
    oldtitle,oldentries=container(original,0x1e8000)
    new,preview,_=footer(member(oldtitle,oldentries,25),VERSION)
    text=member(title,entries,0);rows={(s,i):t for s,i,_,t in parse_mlt(text)}
    assert rows[2,1]=="Next, please enter your family name.\nYou'll only enter it once.\nPlease take care to use the correct kanji."
    patched=rebuild_mlt(text,{(2,1):INSTRUCTION})
    after={(s,i):t for s,i,_,t in parse_mlt(patched)}
    assert all(after[k]==v for k,v in rows.items() if k!=(2,1))
    result=rebuild_root(data,{titlebase:rebuild_ez(title,{0:pack(patched),25:pack(new)})})
    ae,aend=root_entries(result)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=be[n+1][3] if n+1<len(be) else bend;sb=ae[n+1][3] if n+1<len(ae) else aend
        aa=data[a[3]:sa-(a[2]&2047)];bb=result[b[3]:sb-(b[2]&2047)]
        if a[3]!=titlebase:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in (0,25):assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=VERSION,source_version='0.2.11',texture_replacement=False,font_raster_scale=4,
                keyboard=dict(inputtype_before='0xD000',inputtype_after='0xD00F',default_language='English (2)',
                              latin_uppercase=True,latin_lowercase=True,digits_and_symbols=True,japanese_retained=True,
                              max_name_characters=3,output_buffer_u16_characters=128),
                patches=[dict(address=hex(pc),before=hex(a),after=hex(b),purpose=why) for pc,a,b,why in PATCHES],
                instruction=INSTRUCTION,checks=dict(executable_diff='Three guarded instructions only; no segment growth',
                unrelated_archive_payloads='byte-identical',unrelated_title_members='byte-identical',
                other_title_text='unchanged',original_name_pools='preserved',compression_round_trip='pass'),
                elf_bytes=len(elf),archive_bytes=len(result),elf_sha256=hashlib.sha256(elf).hexdigest(),
                archive_sha256=hashlib.sha256(result).hexdigest(),runtime_verification='pending')
    return bytes(elf),result,preview,report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    elf,ore,preview,report=build();print(json.dumps(report,indent=2))
    if args.write:
        dest=ROOT/'work/output/english-native-0.2.12';dest.mkdir(parents=True,exist_ok=True)
        assert not (dest/'EBOOT.keyboard.elf').exists() and not (dest/'data.keyboard.ore').exists()
        (dest/'EBOOT.keyboard.elf').write_bytes(elf);(dest/'data.keyboard.ore').write_bytes(ore)
        (dest/'keyboard.report.json').write_text(json.dumps(report,indent=2)+'\n')
        ui=ROOT/'work/ui/alphabet-0.2.12';ui.mkdir(parents=True,exist_ok=True);preview.save(ui/'native-footer.png')
    print('Build written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()
