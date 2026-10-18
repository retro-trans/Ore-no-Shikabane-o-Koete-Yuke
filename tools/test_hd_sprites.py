"""Execute HD image binding and crop mapping in actual MIPS instructions."""
import argparse,json,struct,unicorn
from unicorn import mips_const as r
from catalog_text import ROOT
from hd_sprites import BIND,RECT,TAG,PROXY_TAG
ap=argparse.ArgumentParser();ap.add_argument('--tag',default='-prototype');ap.add_argument('--elf');ap.add_argument('--report');args=ap.parse_args()
path=ROOT/args.elf if args.elf else ROOT/('work/output/english-native-0.2.26'+args.tag+'/EBOOT.hd.elf');elf=path.read_bytes()
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20);p=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
    _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,p+32*i);m.mem_write(addr,elf[off:off+size])
obj,desc,pal,colors,stack,stop=0x09f00000,0x09f01000,0x09f02000,0x09f03000,0x09fe0000,0x09ff0000
tests=0
for ow,oh,pw,ph in [(32,16,128,64),(24,16,96,64),(44,260,176,504),(44,260,88,260),(46,16,184,64),(20,20,80,80),(16,14,64,56)]:
    for tagged,pixel_format in [(t,f) for t in (True,False) for f in (4,5)]:
        m.mem_write(obj,bytes(512));m.mem_write(desc,bytes(64));m.mem_write(pal,bytes(16));m.mem_write(colors,bytes(1024))
        m.mem_write(obj+0xbc,struct.pack('<I',desc));m.mem_write(desc+8,struct.pack('<H',pixel_format));m.mem_write(desc+0x10,struct.pack('<2H',pw,ph));m.mem_write(desc+0x24,struct.pack('<I',pal));m.mem_write(pal+4,struct.pack('<HHI',3,32,colors))
        for index,value in [(251,pw),(252,ph),(253,ow),(254,oh),(255,TAG if tagged else 0)]:m.mem_write(colors+index*4,struct.pack('<I',value))
        m.reg_write(r.UC_MIPS_REG_A0,obj);m.reg_write(r.UC_MIPS_REG_A1,desc);m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
        for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
        m.emu_start(BIND,BIND+8,count=500)
        assert struct.unpack('<2H',m.mem_read(desc+0x10,4))==((ow,oh) if tagged else (pw,ph))
        assert m.reg_read(r.UC_MIPS_REG_V1)==desc and m.reg_read(r.UC_MIPS_REG_SP)==stack-16
        for rect in [(0,0,ow,oh),(0,0,min(24,ow),oh),(1,2,max(2,ow-1),max(3,oh-1)),(0,0,0,0)]:
            m.reg_write(r.UC_MIPS_REG_A0,obj);m.reg_write(r.UC_MIPS_REG_RA,stop)
            for reg,v in zip((r.UC_MIPS_REG_A1,r.UC_MIPS_REG_A2,r.UC_MIPS_REG_A3,r.UC_MIPS_REG_T0),rect):m.reg_write(reg,v)
            m.emu_start(RECT,stop,count=500)
            expect=(rect[0]*pw//ow,rect[1]*ph//oh,rect[2]*pw//ow,rect[3]*ph//oh) if tagged else rect
            assert struct.unpack('<4H',m.mem_read(obj+0xc0,8))==expect,(ow,oh,tagged,rect,expect)
            assert m.mem_read(obj+0xcc,1)==b'\1'
            assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
            tests+=1
report=json.loads((ROOT/args.report if args.report else path.with_name('hd.report.json')).read_text())
targets=report.get('renderer',{}).get('embedded_descriptors',[]) or [int(x['descriptor'],16) for x in report.get('elements',report.get('icons',[]))]
for target in targets:
    palette=struct.unpack('<I',m.mem_read(target+36,4))[0]
    color=struct.unpack('<I',m.mem_read(palette+8,4))[0]
    lw,lh=struct.unpack('<2I',m.mem_read(color+1012,8));expected=struct.pack('<2H',lw,lh)
    m.mem_write(desc,bytes(64));m.mem_write(pal,bytes(16));m.mem_write(colors,bytes(1024))
    m.mem_write(desc+8,struct.pack('<H',5));m.mem_write(desc+0x24,struct.pack('<I',pal));m.mem_write(pal+4,struct.pack('<HHI',3,32,colors))
    m.mem_write(colors+1004,struct.pack('<I',target));m.mem_write(colors+1020,struct.pack('<I',PROXY_TAG))
    m.reg_write(r.UC_MIPS_REG_A0,obj);m.reg_write(r.UC_MIPS_REG_A1,desc);m.reg_write(r.UC_MIPS_REG_SP,stack)
    m.emu_start(BIND,BIND+8,count=500)
    assert m.reg_read(r.UC_MIPS_REG_V1)==target and m.reg_read(r.UC_MIPS_REG_A1)==target
    assert bytes(m.mem_read(target+16,4))==expected
print('PASS: %d actual MIPS crop cases and %d embedded descriptor proxies; HD logical sizing, full/cropped/nonzero rectangles, repeated updates, ribbon limits, untagged fallback and saved registers.'%(tests,len(targets)))
