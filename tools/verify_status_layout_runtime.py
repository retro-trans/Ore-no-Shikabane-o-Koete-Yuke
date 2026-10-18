"""Read back final-ISO status geometry and Potential grid; dry run first."""
import argparse,base64,json,struct,hashlib
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
if not a.execute:print('DRY RUN: read eight geometry/layer instructions, display scale and existing grid palette/pixels; no memory or save writes.');raise SystemExit
r=json.loads((ROOT/'work/output/english-native-0.2.35/status.report.json').read_text());proofs=[]
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
 for i,p in enumerate(r['patches']):
  addr=int(p['address'],16);expected=bytes.fromhex(p['after'])
  if i<8:
   lines=s.call('memory.disasm',address=addr,count=2,displaySymbols=False)['lines'];line=next(x for x in lines if x['address']<=addr<x['address']+x['addressSize']);words=line.get('macroEncoding') or [line['encoding']];assert words[(addr-line['address'])//4]==struct.unpack('<I',expected)[0]
  else:assert base64.b64decode(s.call('memory.read',address=addr,size=len(expected))['base64'])==expected
  proofs.append(dict(address=p['address'],bytes=len(expected),sha256=hashlib.sha256(expected).hexdigest()))
proof=dict(version='0.2.35',result='PASS',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],patches=proofs,texture_replacement=False,game_memory_writes=False,save_record_writes=False)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/status-layout-0.2.35/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n')
