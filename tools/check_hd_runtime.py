"""Read native image descriptors and UVs in the isolated emulator. Dry run first."""
import argparse,base64,json,struct,time
from catalog_text import ROOT
from ppsspp_debug import Session
from hd_sprites import TAG
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--output');ap.add_argument('--minimum',type=int,default=1);ap.add_argument('--require-size',type=int,nargs=2);a=ap.parse_args()
if not a.execute:
    print('DRY RUN: temporarily break on image draw; read descriptor, palette metadata and UV crop; always remove breakpoint and resume.');raise SystemExit
pc=0x089b9778;found={}
with Session() as s:
    def read(addr,n):return base64.b64decode(s.call('memory.read',address=addr,size=n)['base64'])
    def u32(addr):return struct.unpack('<I',read(addr,4))[0]
    s.call('cpu.breakpoint.add',address=pc)
    try:
        if s.call('cpu.status')['stepping']:s.call('cpu.resume')
        for i in range(240):
            end=time.monotonic()+8
            while not s.call('cpu.status')['stepping']:
                if time.monotonic()>end:raise TimeoutError('No native image draw')
                time.sleep(.005)
            r=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];obj,desc=r[17],r[20]
            b=read(desc,40);pal=struct.unpack_from('<I',b,36)[0]
            if pal and struct.unpack_from('<H',b,8)[0]==5:
                p=read(pal,12)
                if struct.unpack_from('<HH',p,4)==(3,32):
                    colors=struct.unpack_from('<I',p,8)[0];meta=struct.unpack('<5I',read(colors+1004,20))
                    if meta[4]==TAG:
                        logical=struct.unpack_from('<2H',b,16);assert logical==meta[2:4]
                        uv=struct.unpack('<4H',read(obj+0xc0,8));assert uv[2]<=meta[0] and uv[3]<=meta[1]
                        found[obj]=dict(widget=hex(obj),descriptor=hex(desc),logical_size=logical,physical_visible=meta[:2],source_uv=uv,native_texture=struct.unpack_from('<2H',b,4),tag=hex(meta[4]))
            s.call('cpu.resume')
            if len(found)>=a.minimum and (not a.require_size or any(tuple(a.require_size)==x['logical_size'] for x in found.values())):break
    finally:
        s.call('cpu.breakpoint.remove',address=pc)
        if s.call('cpu.status')['stepping']:s.call('cpu.resume')
assert len(found)>=a.minimum,(len(found),a.minimum)
assert not a.require_size or any(tuple(a.require_size)==x['logical_size'] for x in found.values())
proof=dict(result='PASS',texture_replacement=False,game_memory_writes=False,images=list(found.values()))
print(json.dumps(proof,indent=2))
if a.output:(ROOT/a.output).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
