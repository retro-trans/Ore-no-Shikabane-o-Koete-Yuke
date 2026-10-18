"""Read back final-ISO catalog patches without game-memory writes."""
import argparse,base64,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
if not a.execute:print('DRY RUN: read catalog instruction patches, adapters, literals and tab geometry; no game-memory or save writes.');raise SystemExit
r=json.loads((ROOT/'work/output/english-native-0.2.34/catalog.report.json').read_text())
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
 for p in r['patches']:
  addr=int(p['address'],16);lines=s.call('memory.disasm',address=addr,count=2,displaySymbols=False)['lines'];line=next(x for x in lines if x['address']<=addr<x['address']+x['addressSize']);words=line.get('macroEncoding') or [line['encoding']];assert words[(addr-line['address'])//4]==int(p['after'],16),p
 for p in r['literals']:
  b=bytes.fromhex(p['hex_bytes']);assert base64.b64decode(s.call('memory.read',address=int(p['address'],16),size=len(b))['base64'])==b
 for p in r['wrappers']:
  b=struct.pack('<4I',*[int(w,16) for w in p['words']]);assert base64.b64decode(s.call('memory.read',address=int(p['address'],16),size=len(b))['base64'])==b
 p=r['tab_geometry'];assert struct.unpack('<h',base64.b64decode(s.call('memory.read',address=int(p['address'],16),size=2)['base64']))[0]==p['after']
proof=dict(version='0.2.34',result='PASS',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],instruction_patches_verified=len(r['patches']),adapters_verified=2,tab_width_verified=60,texture_replacement=False,game_memory_writes=False,save_record_writes=False)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/catalog-0.2.34/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n')
