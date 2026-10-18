"""Verify reference element pixels and actual native draws in the isolated emulator."""
import argparse,base64,json,struct,time
from catalog_text import ROOT
from ppsspp_debug import Session
from hd_sprites import BIND,RECT
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');ap.add_argument('--context',default='status');ap.add_argument('--minimum',type=int,default=4);a=ap.parse_args()
if not a.execute:print('DRY RUN: read four embedded icon palettes/pixels and existing native hooks; capture element image descriptors/UVs with a temporary draw breakpoint. No game memory or save writes.');raise SystemExit
out=ROOT/'work/output/english-native-0.2.28';r=json.loads((out/'elements.report.json').read_text());elf=(out/'EBOOT.elements.elf').read_bytes();p=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,p+32);offset=lambda addr:ph[1]+addr-ph[2] if addr>=ph[2] else addr-0x08803000
expected={int(x['descriptor'],16):x for x in r['elements']};pc=0x089b9778;found={}
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
 def read(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
 for hook in (BIND,RECT):
  assert s.call('memory.disasm',address=hook,count=1,displaySymbols=False)['lines'][0]['encoding']==struct.unpack_from('<I',elf,offset(hook))[0]
 for desc,e in expected.items():
  for addr,n in [(int(e['palette'],16),1040),(int(e['pixels'],16),4096)]:assert read(addr,n)==elf[offset(addr):offset(addr)+n]
  b=read(desc,48);original=elf[offset(desc):offset(desc)+48]
  assert b[:16]==original[:16] and b[20:]==original[20:] and struct.unpack_from('<2H',b,16) in [(64,56),(16,14)]
 s.call('cpu.breakpoint.add',address=pc)
 try:
  for i in range(480):
   end=time.monotonic()+8
   while not s.call('cpu.status')['stepping']:
    assert time.monotonic()<end;time.sleep(.005)
   regs=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];obj,desc=regs[17],regs[20]
   if desc in expected:
    logical=struct.unpack('<2H',read(desc+16,4));uv=struct.unpack('<4H',read(obj+0xc0,8));assert logical==(16,14) and uv==(0,0,64,56),(hex(obj),logical,uv)
    found[obj]=dict(element=expected[desc]['element'],widget=hex(obj),descriptor=hex(desc),logical_size=logical,physical_uv=uv,native_texture=[64,64])
   s.call('cpu.resume')
   if len(found)>=a.minimum and {x['element'] for x in found.values()}=={'Fire','Water','Wind','Earth'}:break
 finally:
  s.call('cpu.breakpoint.remove',address=pc)
  if s.call('cpu.status')['stepping']:s.call('cpu.resume')
 assert not s.call('cpu.breakpoint.list')['breakpoints']
assert len(found)>=a.minimum and {x['element'] for x in found.values()}=={'Fire','Water','Wind','Earth'}
proof=dict(version='0.2.28',result='PASS',context=a.context,elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],palettes_and_pixels='All four match the built executable',existing_hooks='Unchanged original native instructions verified through JIT-aware disassembly',draws=list(found.values()),texture_replacement=False,game_memory_writes=False,save_record_writes=False)
print(json.dumps(dict(result='PASS',context=a.context,element_types=4,widgets=len(found),written=a.write)))
if a.write:(ROOT/('work/ui/element-icons-0.2.28/runtime-'+a.context+'.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
