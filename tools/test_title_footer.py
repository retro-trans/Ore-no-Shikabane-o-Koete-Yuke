"""Verify footer draw registration and teardown preserve their callers."""
import struct
import unicorn
from unicorn import mips_const as r
from catalog_text import ROOT

elf=(ROOT/'work/output/english-native-0.2.16/EBOOT.latin.elf').read_bytes()
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
    _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i);m.mem_write(addr,elf[off:off+size])
stack=0x09fe0000;footer=0x09e00000;stop=0x09ff0000;manager=0x09d00000;table=manager+0x1000
m.mem_write(manager,struct.pack('<I',table));m.mem_write(table+0x104,struct.pack('<2I',0x09f00000,0x09f00010));events=[]
def stub(mu,pc,size,unused):
    if pc==0x08804d24:mu.reg_write(r.UC_MIPS_REG_V0,manager)
    elif pc in (0x09f00000,0x09f00010):
        assert mu.reg_read(r.UC_MIPS_REG_A0)==manager
        assert mu.reg_read(r.UC_MIPS_REG_A1)==footer
        assert mu.reg_read(r.UC_MIPS_REG_A2)==0x8003
        events.append('register' if pc==0x09f00000 else 'unregister')
    else:return
    mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,stub)
for pc in (0x08978f40,0x08978ffc):
    word=struct.unpack_from('<I',elf,pc-0x08803000)[0];target=(word&0x3ffffff)<<2
    m.reg_write(r.UC_MIPS_REG_A1,footer);m.reg_write(r.UC_MIPS_REG_S0,0x12345678)
    m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop);m.emu_start(target,stop,count=100)
    assert m.reg_read(r.UC_MIPS_REG_SP)==stack
    assert m.reg_read(r.UC_MIPS_REG_S0)==0x12345678
assert events==['register','unregister']
print('PASS: native footer register/unregister, correct manager/object/draw key, original caller, stack and saved register.')
