"""Observe the final-ISO ribbon's native palette, pixels, dimensions and UVs."""
import argparse,base64,hashlib,json,struct,time
from catalog_text import ROOT
from ppsspp_debug import Session
from hd_sprites import BIND,RECT,TAG
from build_menu_fixes import container,member
from repack_text import root_entries

ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');ap.add_argument('--context',required=True);ap.add_argument('--require',required=True)
ap.add_argument('--version',default='0.2.32');ap.add_argument('--report',default='banners.report.json');ap.add_argument('--elf',default='EBOOT.banners.elf');ap.add_argument('--ore',default='data.banners.ore');ap.add_argument('--output');a=ap.parse_args()
if not a.execute:print('DRY RUN: read final native rendering hooks; temporarily observe '+a.require+' palette/pixels and full UVs. No game memory/save writes.');raise SystemExit
out=ROOT/('work/output/english-native-'+a.version);r=json.loads((out/a.report).read_text());elf=(out/a.elf).read_bytes();data=(out/a.ore).read_bytes();p=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,p+32);offset=lambda addr:ph[1]+addr-ph[2] if addr>=ph[2] else addr-0x08803000
original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,_=root_entries(data);index=next(i for i,_,_,o in oe if o==0xb4a800);arc,en=container(data,next(z[3] for z in be if z[0]==index));del original,data
expected={}
for x in r['graphics']:
 b=member(arc,en,x['member_entry']);po=struct.unpack_from('<I',b,24)[0];expected[hashlib.sha256(b[32:po]).hexdigest()]=(x,b[po+16:po+1040])
pc=0x089b9778;found={}
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
 def read(addr,n):return b''.join(base64.b64decode(s.call('memory.read',address=addr+k,size=min(16384,n-k))['base64']) for k in range(0,n,16384))
 for hook in (BIND,RECT):assert s.call('memory.disasm',address=hook,count=1,displaySymbols=False)['lines'][0]['encoding']==struct.unpack_from('<I',elf,offset(hook))[0]
 s.call('cpu.breakpoint.add',address=pc)
 try:
  for i in range(600):
   end=time.monotonic()+8
   while not s.call('cpu.status')['stepping']:
    assert time.monotonic()<end;time.sleep(.005)
   regs=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];obj,desc=regs[17],regs[20]
   if 0x08800000<=desc<0x09ffffd0:
    head=read(desc,48);fmt=struct.unpack_from('<H',head,8)[0];pixels,palette=struct.unpack_from('<2I',head,32)
    if fmt==4 and 0x08800000<=palette<0x09fffff0 and 0x08800000<=pixels<0x09ffce80:
     colors=struct.unpack_from('<I',read(palette,16),8)[0]
     if 0x08800000<=colors<0x09fffc00 and struct.unpack('<I',read(colors+1020,4))[0]==TAG:
      payload=read(pixels,12672);match=expected.get(hashlib.sha256(payload).hexdigest())
      if match:
       e,pal=match;assert read(colors,1024)==pal
       logical=list(struct.unpack_from('<2H',head,16));uv=list(struct.unpack('<4H',read(obj+0xc0,8)))
       assert logical==e['logical_size'] and uv==[0,0]+e['physical_visible_size'],(e['file'],logical,uv)
       found[obj]=dict(text=e['translation_en'],file=e['file'],widget=hex(obj),descriptor=hex(desc),pixel_format=fmt,logical_size=logical,physical_uv=uv,native_texture=e['native_texture'],pixels_and_palette='Exact match with final data archive')
   s.call('cpu.resume')
   if a.require in {x['text'] for x in found.values()}:break
 finally:
  s.call('cpu.breakpoint.remove',address=pc)
  if s.call('cpu.status')['stepping']:s.call('cpu.resume')
 assert not s.call('cpu.breakpoint.list')['breakpoints']
assert a.require in {x['text'] for x in found.values()}
proof=dict(version=a.version,result='PASS',context=a.context,elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],required=a.require,rendering_hooks='Verified through JIT-aware disassembly',draws=list(found.values()),texture_replacement=False,game_memory_writes=False,save_record_writes=False)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/a.output if a.output else ROOT/('work/ui/left-banners-'+a.version+'/runtime-'+a.context+'.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
