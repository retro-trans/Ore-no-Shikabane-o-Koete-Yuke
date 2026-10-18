"""Read ancestors of rendered English text, using a temporary draw breakpoint."""
import argparse,base64,json,struct,time
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--contains',default='');ap.add_argument('--output');a=ap.parse_args()
if not a.execute:print('DRY RUN: read rendered English object ancestors; no game writes.');raise SystemExit
with Session() as s:
 def read(p,n):return base64.b64decode(s.call('memory.read',address=p,size=n)['base64'])
 seen={};pc=0x089ba8bc;s.call('cpu.breakpoint.add',address=pc)
 try:
  for _ in range(65):
   end=time.monotonic()+4
   while not s.call('cpu.status')['stepping']:
    assert time.monotonic()<end;time.sleep(.005)
   r=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];obj=r[17]
   if obj not in seen:
    p=struct.unpack('<I',read(obj+0xd4,4))[0];text=''
    if p:
     b=read(p,2800)
     for j in range(0,len(b),28):
      c=struct.unpack_from('<H',b,j+4)[0]
      if not c:break
      text+=chr(c)
    chain=[];parent=obj
    for _ in range(9):
     if not 0x08800000<=parent<0x0a000000:break
     b=read(parent,0x60);vt=struct.unpack_from('<I',b)[0];geo=struct.unpack_from('<4I',b,0x40);chain.append(dict(object=hex(parent),vtable=hex(vt),geometry=list(geo)));parent=struct.unpack_from('<I',b,0x14)[0]
    seen[obj]=dict(text=text,ancestors=chain)
   s.call('cpu.resume')
 finally:
  s.call('cpu.breakpoint.remove',address=pc)
  if s.call('cpu.status')['stepping']:s.call('cpu.resume')
 result=[x for x in seen.values() if a.contains in x['text']]
 print(json.dumps(result,indent=2))
 if a.output:
  from pathlib import Path
  Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
