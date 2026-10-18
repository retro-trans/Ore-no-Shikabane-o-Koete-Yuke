"""Verify shop English glyph draws use the embedded 4x atlas. Dry run by default."""
import argparse,base64,json,struct,time
from catalog_text import ROOT
from build_vwf import IMAGE
from ppsspp_debug import Session

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');ap.add_argument('--context',required=True);ap.add_argument('--require',nargs='+',required=True);ap.add_argument('--version',default='0.2.19');ap.add_argument('--output-dir',default='work/ui/shop-layout-0.2.19');a=ap.parse_args()
    if not a.execute:print('DRY RUN: read rendered shop text and atlas UVs; temporary draw breakpoint, no input or memory edits.');return
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];found={};pc=0x089ba8bc
    with Session() as s:
        assert not s.call('cpu.status')['stepping']
        def read(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
        s.call('cpu.breakpoint.add',address=pc)
        try:
            for i in range(150):
                end=time.monotonic()+4
                while not s.call('cpu.status')['stepping']:
                    assert time.monotonic()<end;time.sleep(.005)
                r=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];obj=r[17]
                ptr=struct.unpack('<I',read(obj+0xd4,4))[0]
                if ptr:
                    b=read(ptr,28*100);codes=[]
                    for j in range(0,len(b),28):
                        c=struct.unpack_from('<H',b,j+4)[0]
                        if not c:break
                        codes.append(c)
                    if codes and all(32<=c<=126 for c in codes):
                        text=''.join(map(chr,codes));assert r[2]==IMAGE,(text,hex(r[2]))
                        for j,c in enumerate(codes):
                            g=metrics[str(c)];assert struct.unpack_from('<4H',b,j*28+16)==(g['atlas_x']*64,g['atlas_y']*64,(g['atlas_x']+g['sample_width'])*64,(g['atlas_y']+g['sample_height'])*64)
                        found[obj]=dict(text=text,atlas=hex(r[2]),glyphs=len(codes),uvs='native 4x atlas verified')
                s.call('cpu.resume')
        finally:
            s.call('cpu.breakpoint.remove',address=pc)
            if s.call('cpu.status')['stepping']:s.call('cpu.resume')
    assert set(a.require)<={x['text'] for x in found.values()},a.require
    proof=dict(version=a.version,context=a.context,result='PASS',texture_replacement=False,game_memory_writes=False,required=a.require,objects=list(found.values()))
    if a.write:(ROOT/a.output_dir/('font-'+a.context+'.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(result='PASS',context=a.context,required=a.require,native_english_objects=len(found),written=a.write),indent=2))

if __name__=='__main__':main()
