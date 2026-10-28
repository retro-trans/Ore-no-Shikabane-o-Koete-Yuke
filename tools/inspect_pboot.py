# SPDX-License-Identifier: GPL-2.0-or-later
"""Inspect the user's UCJS10117 update locally; dry run unless --write.

Decrypts only its verified type-5 tag, checks SHA-1 and both KIRK CMACs, and
reports ELF layout without printing game scripts. Format reference:
https://github.com/hrydgard/ppsspp/blob/master/Core/ELF/PrxDecrypter.cpp
Type-5 decryption port: GPL-2.0-or-later, like PPSSPP. See docs/licenses/GPL-2.0.txt.
Game files remain in ignored incoming/work/source directories.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from pack_hardware_eboot import ROOT,cbc,mac,MASTER,xor,elf_segments,sha

EXPECTED='b023e5942af7392abeac03407106b4f6e38915d58c7805a6f528b409ad77eaf7'


def decrypt_update(d):
    assert d[:4]==b'~PSP' and struct.unpack_from('<I',d,0xD0)[0]==0x2E5E10F0
    assert not any(d[0xD5:0x12C])
    slot=bytes.fromhex('09b1c705c35f536677c0eb3677df8307')
    seed=bytes.fromhex('9d5c5baf8cd8697e519f7096e6d5c4e8')
    keyxor=bytes.fromhex('69ba5534f0c0d671e31fdb97e07cd22a')
    k7=lambda b:cbc(slot,b,False)
    x=k7(b''.join(bytes([i])+seed[1:] for i in range(9)))
    t=bytearray(0x150);t[:4]=d[0xD0:0xD4]
    t[0x5C:0x6C]=d[0x140:0x150];t[0x6C:0x80]=d[0x12C:0x140]
    t[0x80:0xB0]=d[0x80:0xB0];t[0xB0:0xC0]=d[0xC0:0xD0]
    t[0xC0:0xD0]=d[0xB0:0xC0];t[0xD0:]=d[:0x80]
    first=t[0x80:0xC0]+t[0x6C:0x7C]
    first=k7(bytes(b^keyxor[i%16] for i,b in enumerate(first)))
    t[0x80:0xC0]=first[:64];t[0x6C:0x7C]=first[64:]
    t[0x5C:0xBC]=k7(bytes(b^keyxor[i%16] for i,b in enumerate(t[0x5C:0xBC])))
    digest=hashlib.sha1(t[:4]+x[:16]+t[4:0x5C]+t[0x5C:0x6C]+t[0x80:0xC0]+t[0xC0:0xD0]+t[0xD0:]).digest()
    assert digest==t[0x6C:0x80], 'Update header SHA-1 mismatch'
    kh=xor(k7(xor(t[0x80:0xC0],x[0x10:0x50])),x[0x50:0x90])
    keys=cbc(MASTER,kh[:32],False)
    header=bytearray(0x90);header[:0x40]=kh
    struct.pack_into('<I',header,0x60,1);header[0x70:0x80]=t[0xC0:0xD0]
    size,offset=struct.unpack_from('<II',header,0x70)
    assert 0x80<=offset<len(d) and 0<size<len(d)
    padded=(size+15)&~15
    body=d[:0x80]+d[0x150:]
    assert offset+padded<=len(body)
    assert mac(keys[16:],header[0x60:0x90])==kh[0x20:0x30], 'KIRK header CMAC mismatch'
    assert mac(keys[16:],header[0x60:0x90]+body[:offset+padded])==kh[0x30:0x40], 'KIRK body CMAC mismatch'
    elf=cbc(keys[:16],body[offset:offset+padded],False)[:size]
    assert len(elf)==struct.unpack_from('<I',d,0x28)[0]
    elf_segments(elf)
    return elf,dict(header_sha1=True,header_cmac=True,body_cmac=True,
        encrypted_tag='0x2E5E10F0',decrypt_mode=d[0x7C],data_offset=offset,
        payload_file_offset=0xD0+offset,decrypted_bytes=len(elf),decrypted_sha256=sha(elf))


def layout(elf):
    segs=elf_segments(elf)
    return dict(elf_type=hex(struct.unpack_from('<H',elf,16)[0]),
        entry=hex(struct.unpack_from('<I',elf,24)[0]),bytes=len(elf),sha256=sha(elf),
        segments=[dict(file_offset=hex(s[1]),address=hex(s[2]),module_info=hex(s[3]),
            file_bytes=s[4],memory_bytes=s[5],bss_bytes=s[5]-s[4],end=hex(s[2]+s[5])) for s in segs])


def build():
    pbp=(ROOT/'incoming/PBOOT.PBP').read_bytes();assert sha(pbp)==EXPECTED
    hdr=struct.unpack_from('<10I',pbp);assert hdr[0]==0x50425000
    starts=list(hdr[2:]);ends=starts[1:]+[len(pbp)]
    assert starts[0]>=40 and all(a<=b<=len(pbp) for a,b in zip(starts,ends))
    pieces={n:pbp[a:b] for n,a,b in zip(['PARAM.SFO','ICON0.PNG','ICON1.PMF','PIC0.PNG',
        'PIC1.PNG','SND0.AT3','DATA.PSP','DATA.PSAR'],starts,ends)}
    elf,crypto=decrypt_update(pieces['DATA.PSP'])
    original=(ROOT/'work/source/EBOOT.decrypted.elf').read_bytes()
    patched=(ROOT/'work/output/english-native-0.2.49/EBOOT.market.elf').read_bytes()
    report=dict(pboot_sha256=sha(pbp),pboot_bytes=len(pbp),original_file_modified=False,
        crypto=crypto,original=layout(original),update=layout(elf),patched=layout(patched),
        pieces={n:dict(bytes=len(b),sha256=sha(b)) for n,b in pieces.items()},
        release_created=False)
    return pieces,elf,report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    pieces,elf,report=build();print(json.dumps(report,indent=2))
    if args.write:
        out=ROOT/'work/source/pboot-analysis';assert not out.exists();out.mkdir()
        for name in ['PARAM.SFO','DATA.PSP']: (out/name).write_bytes(pieces[name])
        (out/'EBOOT.update.elf').write_bytes(elf)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()
