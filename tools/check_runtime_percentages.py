"""Verify all three difficulty percentages use the native font, including padding.

Run at the difficulty-selection screen in the isolated test emulator. Dry run
unless --execute; --write records source-free evidence. Sends no game input.
"""
import argparse
import base64
import json
import re
import struct
import time

from build_vwf import IMAGE, ROOT
from ppsspp_debug import Session

BREAK=0x089BA8BC


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute',action='store_true')
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    if not args.execute:
        print('DRY RUN: verify game/native atlas, temporarily inspect glyph draws, check three percentage objects and their native atlas UVs; remove breakpoint and resume. No buttons sent.')
        return
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
    captures={}
    with Session() as s:
        def read(a,n):return base64.b64decode(s.call('memory.read',address=a,size=n)['base64'])
        assert s.call('game.status')['game']['id']=='UCJS10117'
        assert not s.call('cpu.status')['stepping']
        # JIT block markers replace instructions in runtime memory. Verify the
        # immutable atlas, then test padding behavior through actual draws.
        assert read(IMAGE+4,6)==struct.pack('<3H',512,512,4)
        s.call('cpu.breakpoint.add',address=BREAK)
        try:
            for attempt in range(140):
                deadline=time.monotonic()+8
                while not s.call('cpu.status')['stepping']:
                    if time.monotonic()>deadline:raise TimeoutError('No text draw observed')
                    time.sleep(.01)
                category=s.call('cpu.getAllRegs')['categories'][0]
                regs=dict(zip(category['registerNames'],category['uintValues']))
                assert regs['pc']==BREAK
                obj=regs['s1'];ptr=u32(read(obj+0xD4,4),0)
                raw=read(ptr,28*180)
                codes=[]
                for o in range(0,len(raw),28):
                    c=struct.unpack_from('<H',raw,o+4)[0]
                    if not c:break
                    codes.append(c)
                text=''.join(map(chr,codes))
                if re.fullmatch(r'[ \xa0]*[0-9]+%',text):
                    assert regs['v0']==IMAGE,(repr(text),hex(regs['v0']))
                    for i,c in enumerate(codes):
                        metric=metrics[str(32 if c==160 else c)]
                        uv=struct.unpack_from('<4H',raw,i*28+16)
                        assert uv==(metric['atlas_x']*64,metric['atlas_y']*64,
                                    (metric['atlas_x']+metric['sample_width'])*64,
                                    (metric['atlas_y']+metric['sample_height'])*64)
                        if c!=160:
                            assert struct.unpack_from('<H',raw,i*28+6)[0]==metric['advance']
                    captures[obj]=dict(text=text,codepoints=codes,native_image=hex(regs['v0']),glyphs_verified=len(codes),
                                       observed_padding_advance=struct.unpack_from('<H',raw,6)[0] if codes[0]==160 else None)
                if len(captures)==3:break
                s.call('cpu.resume')
        finally:
            s.call('cpu.breakpoint.remove',address=BREAK)
            if s.call('cpu.status')['stepping']:s.call('cpu.resume')
    assert len(captures)==3
    assert any(160 in row['codepoints'] for row in captures.values())
    report=dict(version='0.2.8',status='PASS',percentage_objects=3,source_sampling_scale=4,
                texture_replacement=False,padded_value_verified=True,captures=list(captures.values()))
    print(json.dumps(report,indent=2))
    if args.write:
        p=ROOT/'work/ui/setup-fixes-0.2.8/percent-native-font.json'
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


def u32(b,o):return struct.unpack_from('<I',b,o)[0]


if __name__=='__main__':main()
