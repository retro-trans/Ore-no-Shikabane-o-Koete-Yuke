"""Localize the PSP game-menu title while retaining game/save compatibility IDs."""
import argparse
import hashlib
import json
import struct

from catalog_text import ROOT


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    source=(ROOT/'work/source/iso/PSP_GAME/PARAM.SFO').read_bytes()
    data=bytearray(source)
    magic,version,keys,values,count=struct.unpack_from('<5I',data)
    assert magic==0x46535000 and version==0x101
    entries={}
    for i in range(count):
        key_offset,fmt,length,capacity,offset=struct.unpack_from('<HHIII',data,20+i*16)
        key=data[keys+key_offset:data.index(0,keys+key_offset)].decode('ascii')
        entries[key]=(i,fmt,length,capacity,values+offset)
    _,_,length,_,offset=entries['DISC_ID']
    assert bytes(data[offset:offset+length])==b'UCJS10117\0'
    i,fmt,length,capacity,offset=entries['TITLE']
    assert fmt==0x204 and offset+capacity<=len(data)
    title='Over My Dead Body'
    encoded=title.encode('utf-8')+b'\0'
    assert len(encoded)<=capacity
    data[offset:offset+capacity]=encoded+bytes(capacity-len(encoded))
    struct.pack_into('<I',data,20+i*16+4,len(encoded))
    allowed=set(range(offset,offset+capacity))|set(range(20+i*16+4,20+i*16+8))
    assert all(a==b or p in allowed for p,(a,b) in enumerate(zip(source,data)))
    report=dict(version='0.2.6',title=title,disc_id='UCJS10117',
                changes='TITLE text and its length only; game/save IDs and other metadata preserved.',
                sha256=hashlib.sha256(data).hexdigest())
    print(json.dumps(report,indent=2))
    if args.write:
        dest=ROOT/'work/output/english-native-0.2.6'
        dest.mkdir(parents=True,exist_ok=True)
        (dest/'PARAM.SFO').write_bytes(data)
        (dest/'metadata.report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Localized metadata written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()
