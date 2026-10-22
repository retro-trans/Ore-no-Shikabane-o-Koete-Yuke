"""Historical startup accessor check; later framebuffer reuse requires test_boot_scratch.py."""
import json,struct,unicorn
from unicorn import mips_const as r
from catalog_text import ROOT
elf=(ROOT/'work/output/english-native-0.2.23/EBOOT.disclaimer.elf').read_bytes();report=json.loads((ROOT/'work/output/english-native-0.2.23/disclaimer.report.json').read_text())
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20);phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
 _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i);m.mem_write(addr,elf[off:off+size])
arg=0x09e00000;stack=0x09fe0000;stop=0x09ff0000;expected=int(report['embedded_archive']['new_address'],16)
for pc in (0x0881ad34,0x0881ad4c):
 m.reg_write(r.UC_MIPS_REG_A0,arg);m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
 for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
 m.emu_start(pc,stop,count=20);assert m.reg_read(r.UC_MIPS_REG_V0)==expected
 assert m.reg_read(r.UC_MIPS_REG_SP)==stack and m.reg_read(r.UC_MIPS_REG_RA)==stop
 assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
assert struct.unpack('<I',m.mem_read(arg,4))[0]==0x88000
assert bytes(m.mem_read(expected,8))==b'EZBIND\0\0'
print('PASS: both actual MIPS archive accessors return the relocated asset, preserve caller state, and retain the original 0x88000 resource allocation.')
