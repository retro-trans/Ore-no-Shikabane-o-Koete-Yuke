"""Read-only verification of loaded character/spell instructions and appended code."""
import argparse,base64,hashlib,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--tag',default='');ap.add_argument('--iso',required=True);ap.add_argument('--write',action='store_true');a=ap.parse_args()
 out=ROOT/('work/output/english-native-0.2.21'+a.tag);r=json.loads((out/'character.report.json').read_text());elf=(out/'EBOOT.character.elf').read_bytes();assert hashlib.sha256(elf).hexdigest()==r['elf_sha256'];verified=[]
 phoff=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,phoff+32)
 with Session() as s:
  assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
  def raw(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
  def ins(addr):return struct.pack('<I',s.call('memory.disasm',address=addr,count=1,displaySymbols=False)['lines'][0]['encoding'])
  for x in r['patches']:
   addr=int(x['address'],16);actual=ins(addr);assert actual.hex()==x['after'],(x,actual.hex());verified.append(dict(address=hex(addr),bytes=actual.hex()))
  for w in r['wrappers']:
   addr=int(w['address'],16);off=ph[1]+addr-ph[2]
   for i in range(0,w['bytes'],4):assert ins(addr+i)==elf[off+i:off+i+4]
  for t in r['literals']:
   expected=t['translation_en'].encode('ascii')+b'\0';assert raw(int(t['address'],16),len(expected))==expected
  assert not s.call('cpu.breakpoint.list')['breakpoints']
 proof=dict(version='0.2.21',iso=a.iso,elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],native_patches_verified=verified,appended_caption_and_selector_wrappers='pass',appended_literals='pass',game_memory_writes=False,save_record_writes=False)
 print(json.dumps(dict(patches=len(verified),wrappers=len(r['wrappers']),literals=len(r['literals']),elf_sha256=r['elf_sha256'],write=a.write),indent=2))
 if a.write:(ROOT/'work/ui/character-spells-0.2.21/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
