"""Read native shop patches from the isolated test instance. --write saves proof."""
import argparse,base64,hashlib,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    out=ROOT/'work/output/english-native-0.2.19';r=json.loads((out/'shop.report.json').read_text())
    elf=(out/'EBOOT.shop.elf').read_bytes();assert hashlib.sha256(elf).hexdigest()==r['elf_sha256']
    verified=[]
    with Session() as s:
        assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
        def raw(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
        def instruction(addr):return struct.pack('<I',s.call('memory.disasm',address=addr,count=1,displaySymbols=False)['lines'][0]['encoding'])
        for x in r['patches']:
            addr=int(x['address'],16);expected=bytes.fromhex(x['after'])
            method='original instruction beneath JIT markers' if addr<0x08a20000 else 'raw data'
            actual=instruction(addr) if addr<0x08a20000 else raw(addr,len(expected))
            assert actual==expected,(x,actual.hex())
            verified.append(dict(address=hex(addr),bytes=actual.hex(),method=method))
        phoff=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,phoff+32)
        cave=int(r['spacing_wrapper']['address'],16);off=ph[1]+cave-ph[2]
        for i in range(0,r['spacing_wrapper']['bytes'],4):assert instruction(cave+i)==elf[off+i:off+i+4]
        old_size=(ROOT/'work/output/english-native-0.2.18/EBOOT.inventory.elf').stat().st_size
        start=ph[2]+old_size-ph[1];assert raw(start,cave-start)==elf[old_size:off]
        assert s.call('cpu.breakpoint.list')['breakpoints']==[]
    proof=dict(version='0.2.19',iso='work/source/qa-shop-0.2.19c.iso',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],native_patches_verified=verified,appended_strings='pass',wrapper_original_opcodes='pass',game_memory_writes=False,save_record_writes=False)
    if a.write:(ROOT/'work/ui/shop-layout-0.2.19/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(patches=len(verified),appended_strings='pass',wrapper='pass',elf_sha256=r['elf_sha256'],write_proof=a.write),indent=2))

if __name__=='__main__':main()
