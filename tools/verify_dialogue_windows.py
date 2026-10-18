"""Read final dialogue patches and the active widened native panel; no game writes."""
import argparse,base64,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
if not a.execute:print('DRY RUN: read final code, Pack translations and active bottom-window geometry/alpha.');raise SystemExit
out=ROOT/'work/output/english-native-0.2.37';r=json.loads((out/'dialogue.report.json').read_text());elf=(out/'EBOOT.dialogue.elf').read_bytes();ph=struct.unpack_from('<8I',elf,struct.unpack_from('<I',elf,28)[0]+32)
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
 def read(p,n):return base64.b64decode(s.call('memory.read',address=p,size=n)['base64'])
 def ins(p):
  line=next(x for x in s.call('memory.disasm',address=p,count=2,displaySymbols=False)['lines'] if x['address']<=p<x['address']+x['addressSize']);return (line.get('macroEncoding') or [line['encoding']])[(p-line['address'])//4]
 for p in r['patches']:
  addr=int(p['address'],16);expected=bytes.fromhex(p['after'])
  if p['purpose'].startswith('Pack'):assert read(addr,len(expected))==expected
  else:assert ins(addr)==int.from_bytes(expected,'little')
 for w in (r['wrapper'],r['update_wrapper']):
  addr=int(w['address'],16);off=ph[1]+addr-ph[2]
  for i in range(0,w['bytes'],4):assert ins(addr+i)==struct.unpack_from('<I',elf,off+i)[0]
 b=read(0x08800000,0x1800000);start=0;panels=[]
 while True:
  i=b.find(struct.pack('<I',0x08a22ba8),start)
  if i<0:break
  start=i+4
  if i%4 or i+0x1808>len(b):continue
  geo=struct.unpack_from('<4I',b,i+0x40)
  if geo[0]!=24 or geo[1]<180:continue
  assert geo[2]==432,geo
  colors=struct.unpack_from('<4I',b,i+0x220);assert colors==(0xc8ffffff,0xc8ffffff,0xc8808080,0xc8808080),colors
  widths=[struct.unpack_from('<I',b,i+o)[0] for o in (0xb88,0xde8,0x1048)];assert widths==[412]*3,widths
  icon=struct.unpack_from('<2I',b,i+0x1640);assert icon[0]==412,icon
  panels.append(dict(object=hex(0x08800000+i),geometry=list(geo),background_alpha=200,line_widths=widths,advance_icon_position=list(icon)))
 assert panels,'Reach a bottom dialogue panel first'
proof=dict(version='0.2.37',result='PASS',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],patches_verified=4,wrapper_verified=True,panels=panels,game_memory_writes=False,texture_replacement=False)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/dialogue-window-0.2.37/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n')
