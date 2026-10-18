"""Execute the margin wrapper and original native window geometry in MIPS."""
import struct
import unicorn
from unicorn import mips_const as r
from catalog_text import ROOT

elf=(ROOT/'work/output/english-native-0.2.18/EBOOT.inventory.elf').read_bytes()
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN)
m.mem_map(0x08800000,32<<20);phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
    _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i);m.mem_write(addr,elf[off:off+size])
obj=0x09e00000;table=0x09e10000;resize=0x09f00000;stack=0x09fe0000;stop=0x09ff0000
phase='geometry'
def hook(mu,pc,size,_):
    if pc==resize or (phase=='wrapper' and pc==0x08821f50):mu.emu_stop()
m.hook_add(unicorn.UC_HOOK_CODE,hook)
cases=[(0x088db354,4,2,232,2,472,90),(0x088db48c,4,2,232,2,472,90),(None,5,3,112,8,372,108)]
for pc,rows,cols,cell,gap,w,h in cases:
    m.mem_write(obj,bytes(0x2600));m.mem_write(obj,struct.pack('<I',table))
    m.mem_write(table+0x88,struct.pack('<I',resize))
    m.mem_write(obj+0x2568,struct.pack('<10I',rows,cols,10,10,10,10,16,gap,2,cell))
    m.reg_write(r.UC_MIPS_REG_A0,obj);m.reg_write(r.UC_MIPS_REG_RA,stop);m.reg_write(r.UC_MIPS_REG_SP,stack)
    for n in range(8):m.reg_write(r.UC_MIPS_REG_S0+n,0x12340000+n)
    if pc:
        word=struct.unpack_from('<I',elf,pc-0x08803000)[0];wrapper=(word&0x3ffffff)<<2
        before=bytes(m.mem_read(obj,0x2600))
        phase='wrapper';m.emu_start(wrapper,stop,count=20)
        assert m.reg_read(r.UC_MIPS_REG_SP)==stack and m.reg_read(r.UC_MIPS_REG_RA)==stop,(hex(m.reg_read(r.UC_MIPS_REG_PC)),hex(m.reg_read(r.UC_MIPS_REG_SP)),hex(m.reg_read(r.UC_MIPS_REG_RA)))
        assert m.reg_read(r.UC_MIPS_REG_A0)==obj
        assert all(m.reg_read(r.UC_MIPS_REG_S0+n)==0x12340000+n for n in range(8))
        after=bytes(m.mem_read(obj,0x2600))
        assert all(a==b or i in range(0x2578,0x2580) for i,(a,b) in enumerate(zip(before,after)))
        assert struct.unpack_from('<2I',after,0x2578)==(3,3)
    phase='geometry';m.emu_start(0x08821f50,stop,count=100)
    assert m.reg_read(r.UC_MIPS_REG_PC)==resize
    assert (m.reg_read(r.UC_MIPS_REG_A1),m.reg_read(r.UC_MIPS_REG_A2))==(w,h)
print('PASS: both inventory hooks preserve caller state and only change two margins; actual original MIPS geometry yields 472x90. Unhooked legacy menus retain 372x108 geometry.')
