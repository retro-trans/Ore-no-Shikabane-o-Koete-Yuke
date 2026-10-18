"""Read back Chronicle translations and positioning from the isolated final ISO."""
import argparse,base64,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
if not a.execute:print('DRY RUN: read five Chronicle instruction patches and both relocated English formats; no input, game memory or save writes.');raise SystemExit
r=json.loads((ROOT/'work/output/english-native-0.2.33/chronicle.report.json').read_text())
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
 for p in r['patches']:
  addr=int(p['address'],16);lines=s.call('memory.disasm',address=addr,count=2,displaySymbols=False)['lines']
  line=next(x for x in lines if x['address']<=addr<x['address']+x['addressSize'])
  words=line.get('macroEncoding') or [line['encoding']]
  assert words[(addr-line['address'])//4]==int(p['after'],16),p
 for p in r['literals']:
  expected=p['translation_en'].encode('ascii')+b'\0';actual=base64.b64decode(s.call('memory.read',address=int(p['address'],16),size=len(expected))['base64']);assert actual==expected
proof=dict(version='0.2.33',result='PASS',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],instruction_patches_verified=5,relocated_formats=r['literals'],texture_replacement=False,game_memory_writes=False,save_record_writes=False)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/chronicle-0.2.33/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
