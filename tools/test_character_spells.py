"""Execute the added MIPS captions/selector and original menu geometry."""
import json,struct,unicorn,sys
from unicorn import mips_const as r
from catalog_text import ROOT
out=ROOT/('work/output/english-native-0.2.21'+(sys.argv[1] if len(sys.argv)>1 else ''))
elf=(out/'EBOOT.character.elf').read_bytes();report=json.loads((out/'character.report.json').read_text())
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
 _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i);m.mem_write(addr,elf[off:off+size])
obj=0x09e00000;table=0x09e10000;resize=0x09f00000;stack=0x09fe0000;stop=0x09ff0000;calls=[];phase='caption'
def hook(mu,pc,size,_):
 if pc in (0x0882b12c,0x0882b2e0,0x0882afac):
  a0=mu.reg_read(r.UC_MIPS_REG_A0);a1=mu.reg_read(r.UC_MIPS_REG_A1)
  if pc==0x0882b2e0:calls.append(('text',bytes(mu.mem_read(a1,64)).split(b'\0')[0].decode('ascii')))
  elif pc==0x0882b12c:calls.append(('size',a1))
  else:mu.mem_write(obj+0x38,struct.pack('<2I',110,110))
  mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
 elif pc==resize:
  calls.append(('resize',mu.reg_read(r.UC_MIPS_REG_A1),mu.reg_read(r.UC_MIPS_REG_A2)))
  if phase=='geometry':mu.emu_stop()
  else:mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,hook)
for w in report['wrappers']:
 calls.clear();m.mem_write(obj,struct.pack('<I',table));m.mem_write(table+0x88,struct.pack('<I',resize))
 m.reg_write(r.UC_MIPS_REG_A0,obj);m.reg_write(r.UC_MIPS_REG_A1,127);m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
 for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
 m.emu_start(int(w['address'],16),stop,count=100)
 assert m.reg_read(r.UC_MIPS_REG_SP)==stack and m.reg_read(r.UC_MIPS_REG_RA)==stop
 assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
 if w['purpose'].startswith('English caption: '):
  label=w['purpose'].split(': ',1)[1];assert calls==[('size',16),('text',label)],calls
 elif w['purpose'].startswith('Portrait'):assert calls==[('resize',110,122)],calls
 else:assert calls==[('resize',108,110)],calls
phase='geometry'
for rows,cols,cell,gap,margins,expected in [(2,2,84,9,(10,8,7,10),(194,52)),(7,2,108,10,(6,6,8,8),(242,142))]:
 calls.clear();m.mem_write(obj,bytes(0x2600));m.mem_write(obj,struct.pack('<I',table));m.mem_write(table+0x88,struct.pack('<I',resize))
 m.mem_write(obj+0x2568,struct.pack('<10I',rows,cols,*margins,16,gap,2 if rows==2 else 3,cell))
 m.reg_write(r.UC_MIPS_REG_A0,obj);m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop);m.emu_start(0x08821f50,stop,count=120)
 assert calls==[('resize',*expected)],calls
print('PASS: seven actual MIPS caption wrappers, selector height +12, widened cell background, preserved caller state, two-column menu geometry and native spell paging geometry.')
