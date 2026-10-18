"""Read the two reported dialogue lines and native glyph positions; dry run first."""
import argparse, base64, json, struct, time
from catalog_text import ROOT
from build_vwf import IMAGE
from ppsspp_debug import Session

LINES = ['Tch!!', 'Not even time to catch our breath!!']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true')
    ap.add_argument('--label', choices=['before','after'],required=True);a=ap.parse_args()
    if not a.execute:
        print('DRY RUN: read native draw descriptors and punctuation instruction in the isolated emulator; temporary breakpoint only.');return
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']; found={}; pc=0x089BA8BC
    with Session() as s:
        assert s.call('game.status')['game']['id']=='UCJS10117'
        assert not s.call('cpu.status')['stepping']
        def read(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
        instruction=s.call('memory.disasm',address=0x089BB24C,count=1)['lines'][0]
        s.call('cpu.breakpoint.add',address=pc)
        try:
            for i in range(180):
                deadline=time.monotonic()+5
                while not s.call('cpu.status')['stepping']:
                    assert time.monotonic()<deadline; time.sleep(.005)
                r=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];obj=r[17]
                ptr=struct.unpack('<I',read(obj+0xd4,4))[0]
                if ptr:
                    b=read(ptr,28*100); glyphs=[]
                    for j in range(100):
                        c=struct.unpack_from('<H',b,j*28+4)[0]
                        if not c:break
                        glyphs.append(dict(code=c,advance=struct.unpack_from('<H',b,j*28+6)[0],
                                           quad=list(struct.unpack_from('<4h',b,j*28+8)),
                                           uv=list(struct.unpack_from('<4H',b,j*28+16))))
                    text=''.join(chr(g['code']) for g in glyphs)
                    if text in LINES:
                        assert r[2]==IMAGE
                        for g in glyphs:
                            m=metrics[str(g['code'])]
                            assert g['uv']==[m['atlas_x']*64,m['atlas_y']*64,(m['atlas_x']+m['sample_width'])*64,(m['atlas_y']+m['sample_height'])*64]
                        found[text]=dict(text=text,object=hex(obj),atlas=hex(r[2]),glyphs=glyphs)
                s.call('cpu.resume')
                if len(found)==len(LINES):break
        finally:
            s.call('cpu.breakpoint.remove',address=pc)
            if s.call('cpu.status')['stepping']:s.call('cpu.resume')
    assert set(found)==set(LINES),list(found)
    proof=dict(label=a.label,result='PASS',texture_replacement=False,memory_writes=False,
               instruction=instruction,objects=[found[t] for t in LINES])
    if a.write:
        (ROOT/('work/ui/punctuation-0.2.24/runtime-'+a.label+'.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(result='PASS',label=a.label,lines=list(found),instruction=instruction),indent=2))

if __name__=='__main__':main()
