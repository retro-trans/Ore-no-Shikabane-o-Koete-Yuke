"""Read final home-description patch words in the isolated test instance."""
import argparse,json
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
if not a.execute:print('DRY RUN: read two home-description geometry instructions; no game writes.');raise SystemExit
r=json.loads((ROOT/'work/output/english-native-0.2.38/home.report.json').read_text())
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
 for p in r['patches']:
  addr=int(p['address'],16);line=next(x for x in s.call('memory.disasm',address=addr,count=2,displaySymbols=False)['lines'] if x['address']<=addr<x['address']+x['addressSize']);value=(line.get('macroEncoding') or [line['encoding']])[(addr-line['address'])//4];assert value==int(p['after'],16)
proof=dict(version='0.2.38',result='PASS',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],patches_verified=2,game_memory_writes=False,texture_replacement=False)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/home-help-0.2.38/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n')
