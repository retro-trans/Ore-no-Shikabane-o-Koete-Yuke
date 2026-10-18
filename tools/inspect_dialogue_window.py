"""Read native dialogue instances in the isolated test emulator; no memory writes."""
import argparse,base64,json,struct
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
if not a.execute:print('DRY RUN: inspect dialogue geometry, background colors and line objects; no game writes.');raise SystemExit
with Session() as s:
 def read(p,n):return base64.b64decode(s.call('memory.read',address=p,size=n)['base64'])
 b=read(0x08800000,0x1800000);needle=struct.pack('<I',0x08a22ba8);start=0;out=[]
 while True:
  i=b.find(needle,start)
  if i<0:break
  start=i+4
  if i%4 or i+0x1808>len(b):continue
  p=0x08800000+i
  vals=lambda o,n:list(struct.unpack_from('<'+'I'*n,b,i+o))
  row=dict(object=hex(p),geometry=vals(0x40,8),background_corners=[hex(v) for v in vals(0x220,4)],lines=[])
  for off in (0xb40,0xda0,0x1000):
   row['lines'].append(dict(object=hex(p+off),geometry=vals(off+0x40,4),glyph_array=hex(vals(off+0x214,1)[0])))
  out.append(row)
 print(json.dumps(out,indent=2))
