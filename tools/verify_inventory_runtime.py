"""Read the final layout patches from the isolated emulator; --write saves proof."""
import argparse,base64,hashlib,json,struct
from catalog_text import ROOT
from ppsspp_debug import Session

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    out=ROOT/'work/output/english-native-0.2.18';r=json.loads((out/'inventory.report.json').read_text())
    elf=(out/'EBOOT.inventory.elf').read_bytes();assert hashlib.sha256(elf).hexdigest()==r['elf_sha256']
    verified=[]
    with Session() as s:
        assert s.call('game.status')['game']['id']=='UCJS10117'
        assert not s.call('cpu.status')['stepping']
        for x in r['patches']:
            addr=int(x['address'],16)
            if 0x08a45e00<=addr<=0x08a45fff:
                b=base64.b64decode(s.call('memory.read',address=addr,size=2)['base64']);value=int.from_bytes(b,'little');method='raw descriptor data'
            else:
                d=s.call('memory.disasm',address=addr,count=1,displaySymbols=False)
                value=d['lines'][0]['encoding'];method='original disassembly encoding beneath JIT markers'
            assert value==x['after'],(x,hex(value))
            verified.append(dict(address=hex(addr),value=hex(value),method=method))
        phoff=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,phoff+32)
        cave=int(r['wrapper']['address'],16);off=ph[1]+cave-ph[2]
        for i in range(0,r['wrapper']['bytes'],4):
            value=s.call('memory.disasm',address=cave+i,count=1,displaySymbols=False)['lines'][0]['encoding']
            assert value==struct.unpack_from('<I',elf,off+i)[0]
    proof=dict(version='0.2.18',iso='work/source/qa-inventory-0.2.18c.iso',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],native_patches_verified=verified,wrapper_original_opcodes='pass',game_memory_writes=False,save_record_writes=False)
    if a.write:(ROOT/'work/ui/menu-fit-0.2.18/runtime-patches.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(patches=len(verified),wrapper='pass',elf_sha256=r['elf_sha256'],write_proof=a.write),indent=2))

if __name__=='__main__':main()
