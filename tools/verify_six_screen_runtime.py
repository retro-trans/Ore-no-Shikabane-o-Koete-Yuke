"""Read final native patches in the isolated emulator, including original JIT opcodes."""
import argparse,base64,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
r=json.loads((ROOT/'work/output/english-native-0.2.27/screens.report.json').read_text());verified=[]
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
 def read(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
 def instruction(addr):return struct.pack('<I',s.call('memory.disasm',address=addr,count=1,displaySymbols=False)['lines'][0]['encoding'])
 for patch in r['patches']:
  addr=int(patch['address'],16);expected=bytes.fromhex(patch['after'])
  if addr<0x08a20000:assert instruction(addr)==expected
  else:
   for pos in range(0,len(expected),16384):assert read(addr+pos,min(16384,len(expected)-pos))==expected[pos:pos+16384]
  verified.append(dict(address=hex(addr),bytes=len(expected),purpose=patch['purpose']))
 elf=(ROOT/'work/output/english-native-0.2.27/EBOOT.screens.elf').read_bytes();p=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,p+32)
 for w in r['wrappers']:
  addr=int(w['address'],16);off=ph[1]+addr-ph[2]
  for pos in range(0,w['bytes'],4):assert instruction(addr+pos)==elf[off+pos:off+pos+4]
 assert not s.call('cpu.breakpoint.list')['breakpoints']
proof=dict(version='0.2.27',result='PASS',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],patches=verified,wrappers='Original native opcodes verified through JIT-aware disassembly',game_memory_writes=False,save_record_writes=False)
print(json.dumps(dict(result='PASS',patches=len(verified),wrappers=len(r['wrappers']),written=a.write)))
if a.write:(ROOT/'work/ui/six-screens-0.2.27/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
