"""Index texture members in the decrypted Vita archive. Dry run unless --write."""
import argparse,json,re,struct,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'work/source/vita3k-icons-profile/ux0/app/PCSA00155/data.img'
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
offsets=[];rows=[]
with SOURCE.open('rb') as f:
 pos=0;tail=b''
 while True:
  b=f.read(8<<20)
  if not b:break
  block=tail+b;offsets.extend(pos-len(tail)+m.start() for m in re.finditer(b'EZBIND\0\0',block));pos+=len(b);tail=block[-7:]
 for base in offsets:
  f.seek(base);header=f.read(16);n,align=struct.unpack_from('<II',header,8)
  if not 0<n<8192 or align not in (4,16,128,2048):continue
  entries=f.read(n*16)
  if len(entries)!=n*16:continue
  first=min(struct.unpack_from('<I',entries,i*16+8)[0] for i in range(n));f.seek(base);meta=f.read(first)
  for i in range(n):
   no,size,off,h=struct.unpack_from('<4I',entries,i*16)
   if not 16+n*16<=no<first:continue
   name=meta[no:].split(b'\0')[0].decode('ascii',errors='replace')
   if name.lower().endswith(('.ppt','.gxt')):rows.append(dict(archive_offset=base,entry=i,name=name,member_offset=base+off,size=size))
prefix=collections.Counter(r['name'].split('_')[0] for r in rows)
print(json.dumps(dict(write=a.write,containers=len(offsets),textures=len(rows),prefixes=prefix.most_common(35),ui_candidates=[r for r in rows if r['name'].startswith(('ustx','uitx','uict','ui_'))][:100]),indent=2))
if a.write:
 dest=ROOT/'work/source/oreshika-textures';dest.mkdir(exist_ok=True);(dest/'inventory.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
