"""Read native equipment/deity patches from the isolated instance. --write saves proof."""
import argparse,base64,hashlib,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--iso',default='work/source/qa-equipment-0.2.20a.iso');a=ap.parse_args()
    out=ROOT/'work/output/english-native-0.2.20';r=json.loads((out/'equipment.report.json').read_text());elf=(out/'EBOOT.equipment.elf').read_bytes();assert hashlib.sha256(elf).hexdigest()==r['elf_sha256'];verified=[]
    with Session() as s:
        assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
        def raw(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
        def ins(addr):return struct.pack('<I',s.call('memory.disasm',address=addr,count=1,displaySymbols=False)['lines'][0]['encoding'])
        for x in r['patches']:
            addr=int(x['address'],16);expected=bytes.fromhex(x['after']);actual=ins(addr) if addr<0x08a20000 else raw(addr,len(expected));assert actual==expected,(x,actual.hex());verified.append(dict(address=hex(addr),bytes=actual.hex()))
        phoff=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,phoff+32);cave=int(r['wrapper']['address'],16);off=ph[1]+cave-ph[2]
        for i in range(0,r['wrapper']['bytes'],4):assert ins(cave+i)==elf[off+i:off+i+4]
        old=(ROOT/'work/output/english-native-0.2.19/EBOOT.shop.elf').stat().st_size;start=ph[2]+old-ph[1];assert raw(start,cave-start)==elf[old:off]
        assert s.call('cpu.breakpoint.list')['breakpoints']==[]
    proof=dict(version='0.2.20',iso=a.iso,elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],native_patches_verified=verified,appended_strings='pass',wrapper_original_opcodes='pass',game_memory_writes=False,save_record_writes=False)
    if a.write:(ROOT/'work/ui/equipment-deities-0.2.20/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(patches=len(verified),appended_strings='pass',wrapper='pass',elf_sha256=r['elf_sha256'],write_proof=a.write),indent=2))

if __name__=='__main__':main()
