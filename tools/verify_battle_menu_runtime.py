"""Read final-ISO battle menu patches without memory writes."""
import argparse,base64,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
if not a.execute:print('DRY RUN: read battle geometry/hooks, submenu width, wrap code and buffer guard; no input or memory edits.');raise SystemExit
r=json.loads((ROOT/'work/output/english-native-0.2.36/battle-menu.report.json').read_text());elf=(ROOT/'work/output/english-native-0.2.36/EBOOT.bmenu.elf').read_bytes();ph=struct.unpack_from('<8I',elf,struct.unpack_from('<I',elf,28)[0]+32)
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
 def read(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
 def ins(addr):
  line=next(x for x in s.call('memory.disasm',address=addr,count=2,displaySymbols=False)['lines'] if x['address']<=addr<x['address']+x['addressSize']);return (line.get('macroEncoding') or [line['encoding']])[(addr-line['address'])//4]
 for p in r['patches']:assert ins(int(p['address'],16))==int(p['after'],16)
 for w in r['wrappers']:
  addr=int(w['address'],16);off=ph[1]+addr-ph[2]
  for i in range(0,w['bytes'],4):assert ins(addr+i)==struct.unpack_from('<I',elf,off+i)[0]
 assert struct.unpack('<h',read(int(r['submenu']['table'],16)+8,2))[0]==84;assert read(int(r['guard'],16),16)==b'BATTLE_HELP_END!'
proof=dict(version='0.2.36',result='PASS',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],patches_verified=len(r['patches']),submenu_width=84,wrap_code_verified=True,buffer_guard='Unchanged',texture_replacement=False,game_memory_writes=False,save_record_writes=False)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/battle-menu-0.2.36/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n')
