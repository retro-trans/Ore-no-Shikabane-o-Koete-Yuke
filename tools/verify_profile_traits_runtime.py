"""Read native trait patches and the full formatted status line; no memory writes."""
import argparse,base64,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--expect',required=True);ap.add_argument('--context',required=True);ap.add_argument('--write',action='store_true');a=ap.parse_args()
p=ROOT/'work/output/english-native-0.2.30';r=json.loads((p/'traits.report.json').read_text());elf=(p/'EBOOT.traits.elf').read_bytes();ph=struct.unpack_from('<8I',elf,struct.unpack_from('<I',elf,28)[0]+32)
with Session() as s:
 assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
 def read(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
 def instruction(addr):return s.call('memory.disasm',address=addr,count=1,displaySymbols=False)['lines'][0]['encoding']
 for patch in r['patches']:assert instruction(int(patch['address'],16))==int(patch['after'],16),patch
 for w in r['wrappers']:
  addr=int(w['address'],16);off=ph[1]+addr-ph[2]
  for pos in range(0,w['bytes'],4):assert instruction(addr+pos)==struct.unpack_from('<I',elf,off+pos)[0]
 text=read(int(r['buffer'],16),1024).decode('utf-16-le').split('\0')[0]
 assert text.replace('\n',' ')==a.expect,(text,a.expect)
 assert read(int(r['guard'],16),17)==b'TRAIT_BUFFER_END!'
 assert not s.call('cpu.breakpoint.list')['breakpoints']
proof=dict(version=r['version'],result='PASS',context=a.context,elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],full_trait=text,patches_verified=len(r['patches']),wrappers='JIT-aware opcode verification',buffer_guard='unchanged',texture_replacement=False,game_memory_writes=False,save_record_writes=False)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/('work/ui/profile-traits-0.2.30/runtime-'+a.context+'.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
