"""Execute native equipment/deity menu geometry and coordinate setup in MIPS."""
import json,struct
import unicorn
from unicorn import mips_const as r
from catalog_text import ROOT

elf=(ROOT/'work/output/english-native-0.2.20/EBOOT.equipment.elf').read_bytes();report=json.loads((ROOT/'work/output/english-native-0.2.20/equipment.report.json').read_text())
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
    _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i);m.mem_write(addr,elf[off:off+size])
obj=0x09e00000;table=0x09e10000;resize=0x09f00000;stack=0x09fe0000;stop=0x09ff0000;positions=[];phase='geometry'
def hook(mu,pc,size,_):
    if pc==resize or (phase=='wrapper' and pc==0x08821f50):mu.emu_stop()
    elif phase=='position' and pc==0x089b6708:
        positions.append(tuple(mu.reg_read(r.UC_MIPS_REG_A0+i) for i in range(3)));mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,hook)
for rows,cols,cell,gap,height,w,h in [(4,1,248,8,16,268,90),(4,1,240,8,16,260,90),(4,1,216,8,32,236,154),(8,1,216,8,16,236,162)]:
    m.mem_write(obj,bytes(0x2600));m.mem_write(obj,struct.pack('<I',table));m.mem_write(table+0x88,struct.pack('<I',resize))
    m.mem_write(obj+0x2568,struct.pack('<10I',rows,cols,10,10,10,10,16,gap,2,cell))
    m.reg_write(r.UC_MIPS_REG_A0,obj);m.reg_write(r.UC_MIPS_REG_RA,stop);m.reg_write(r.UC_MIPS_REG_SP,stack)
    for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
    if height==32:
        phase='wrapper';m.emu_start(int(report['wrapper']['address'],16),stop,count=20)
        assert m.reg_read(r.UC_MIPS_REG_PC)==0x08821f50 and m.reg_read(r.UC_MIPS_REG_SP)==stack and m.reg_read(r.UC_MIPS_REG_RA)==stop
        assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
        assert struct.unpack('<I',m.mem_read(obj+0x2580,4))[0]==32
    phase='geometry';m.emu_start(0x08821f50,stop,count=100)
    actual=(m.reg_read(r.UC_MIPS_REG_A1),m.reg_read(r.UC_MIPS_REG_A2));assert actual==(w,h),(actual,(w,h))
phase='position'
for pc,end,offset,x,y in [(0x0895bb08,0x0895bb18,0x3b0,90,16),(0x0895bb7c,0x0895bb8c,0x6f0,162,16)]:
    positions.clear();m.reg_write(r.UC_MIPS_REG_S0,obj);m.reg_write(r.UC_MIPS_REG_A1,0x4d082b9c);m.reg_write(r.UC_MIPS_REG_A2,0x4d082ba0)
    m.emu_start(pc,end,count=30);assert positions==[(obj+offset,x,y)],positions
print('PASS: actual native equipment/deity geometry, two-line row wrapper, saved caller state, and dirty-register coordinate setup.')
