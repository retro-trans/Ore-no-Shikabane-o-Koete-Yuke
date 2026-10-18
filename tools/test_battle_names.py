"""Execute the parent display-name trampoline, including untouched variadic arguments."""
import argparse,json,struct,unicorn
from unicorn import mips_const as r
from catalog_text import ROOT
from build_battle_hud import HOOK
ap=argparse.ArgumentParser();ap.add_argument('--tag',default='');args=ap.parse_args()
path=ROOT/('work/output/english-native-0.2.25'+args.tag+'/EBOOT.battle.elf');elf=path.read_bytes();report=json.loads((path.parent/'battle.report.json').read_text())
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20);phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
    _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i);m.mem_write(addr,elf[off:off+size])
src=0x09f00000;stack=0x09fe0000
cases=[(None,None),('',None),('Genta',None),('Orin',None),('\u6e90\u592a','Genta'),('\u304a\u8f2a','Orin'),('\u6e90\u592a\u306e',None),('\u304a\u8f2a\u306e',None),('@\u6e90\u592a',None),('abcdefgh',None),('\u6e90',None),('\u304a',None),('%s',None)]
for text,expected in cases:
    m.mem_write(src,((text or '')+'\0').encode('utf-16-le')+bytes(64));ptr=0 if text is None else src
    m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_A1,ptr)
    saved=[r.UC_MIPS_REG_A0,r.UC_MIPS_REG_A2,r.UC_MIPS_REG_A3,r.UC_MIPS_REG_T0,r.UC_MIPS_REG_T1,r.UC_MIPS_REG_T2,r.UC_MIPS_REG_T3,r.UC_MIPS_REG_RA]+[r.UC_MIPS_REG_S0+i for i in range(8)]
    for i,reg in enumerate(saved):m.reg_write(reg,0x12340000+i)
    m.emu_start(HOOK,HOOK+8,count=100)
    out=m.reg_read(r.UC_MIPS_REG_A1)
    assert out==(int(report['names']['names'][expected],16) if expected else ptr),(ascii(text),hex(out))
    assert m.reg_read(r.UC_MIPS_REG_SP)==stack-64
    assert struct.unpack('<I',m.mem_read(stack-20,4))[0]==0x1234000b
    assert all(m.reg_read(reg)==0x12340000+i for i,reg in enumerate(saved))
lines=[];stop=0x09ff0000;parent=0x09f10000
def wide(ptr):
    text=''
    if not ptr:return text
    for i in range(128):
        c=struct.unpack('<H',m.mem_read(ptr+i*2,2))[0]
        if not c:return text
        text+=chr(c)
    raise AssertionError('unterminated')
def stub(mu,pc,size,unused):
    if pc not in (0x0882b798,0x089bbaec,0x089bba6c,0x089ab074,0x0882b694,0x0882b1d4,0x089bba88):return
    if pc==0x0882b694:
        ptr=mu.reg_read(r.UC_MIPS_REG_A1);count=mu.reg_read(r.UC_MIPS_REG_A2);text=wide(ptr)
        assert count==len(text);lines.append(text)
    mu.reg_write(r.UC_MIPS_REG_V0,0)
    mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,stub)
for text,expected in cases:
    raw=((text or '')+'\0').encode('utf-16-le')+bytes(64);m.mem_write(src,raw);m.mem_write(parent,bytes(0x2000));lines.clear()
    m.reg_write(r.UC_MIPS_REG_A0,parent);m.reg_write(r.UC_MIPS_REG_A1,0 if text is None else src)
    m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
    for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
    m.emu_start(HOOK,stop,count=10000)
    assert lines==([expected or text] if text else []),(ascii(text),lines)
    assert bytes(m.mem_read(src,len(raw)))==raw
    assert m.reg_read(r.UC_MIPS_REG_SP)==stack
    assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
print('PASS: %d actual MIPS trampoline cases and %d full native text-setter cases; exact aliases only, source records untouched, child line text/counts correct, original stack/store instructions replayed, arguments and saved registers preserved.'%(len(cases),len(cases)))
