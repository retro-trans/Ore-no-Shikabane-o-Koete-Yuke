"""Execute the dialogue window hook for matching and unrelated native geometries."""
import argparse,hashlib,json,struct
import unicorn
from unicorn import mips_const as R
from catalog_text import ROOT
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
p=ROOT/'work/output/english-native-0.2.37';b=(p/'EBOOT.dialogue.elf').read_bytes();report=json.loads((p/'dialogue.report.json').read_text());assert hashlib.sha256(b).hexdigest()==report['elf_sha256']
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
ph=struct.unpack_from('<I',b,28)[0]
for i in range(2):
 _,off,addr,_,n,_,_,_=struct.unpack_from('<8I',b,ph+32*i);m.mem_write(addr,b[off:off+n])
obj=0x09e00000;stack=0x09fe0000;stop=0x09ff0000;hook=int(report['wrapper']['address'],16);phase='layout';resize_calls=[]
def halt(mu,pc,size,_):
 if phase=='layout' and pc==0x08823610:mu.emu_stop()
 if phase=='update' and pc in (0x08823c90,0x0881e3f0):
  if pc==0x0881e3f0:resize_calls.append([mu.reg_read(reg) for reg in (R.UC_MIPS_REG_A0,R.UC_MIPS_REG_A1,R.UC_MIPS_REG_A2)])
  mu.reg_write(R.UC_MIPS_REG_V0,0x11223344);mu.reg_write(R.UC_MIPS_REG_V1,0x22334455);mu.reg_write(R.UC_MIPS_REG_PC,mu.reg_read(R.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,halt)
cases=[]
for x,y,w,h,changed in [(24,198,288,66,True),(24,196,288,66,True),(24,198,432,66,True),(24,180,288,66,True),(24,179,288,66,False),(90,6,300,70,False),(10,200,300,60,False),(24,198,220,48,False),(0,0,288,66,False),(206,134,264,64,False)]:
 before=bytearray([0x5a]*0x1810);struct.pack_into('<4I',before,0x40,x,y,w,h);m.mem_write(obj,bytes(before))
 regs={R.UC_MIPS_REG_A0:obj,R.UC_MIPS_REG_A1:0x12345678,R.UC_MIPS_REG_A2:0x23456789,R.UC_MIPS_REG_A3:0x34567890,R.UC_MIPS_REG_RA:stop,R.UC_MIPS_REG_SP:stack}
 regs.update({R.UC_MIPS_REG_S0+i:0x12340000+i for i in range(8)})
 for reg,val in regs.items():m.reg_write(reg,val)
 m.emu_start(hook,stop,count=80);assert m.reg_read(R.UC_MIPS_REG_PC)==0x08823610
 assert all(m.reg_read(reg)==val for reg,val in regs.items())
 after=bytes(m.mem_read(obj,len(before)));expected=bytearray(before)
 if changed:
  struct.pack_into('<I',expected,0x48,432)
  for o in (0xb88,0xde8,0x1048):struct.pack_into('<I',expected,o,412)
  struct.pack_into('<4I',expected,0x220,0xc8ffffff,0xc8ffffff,0xc8808080,0xc8808080);expected[0x1fc]=1
 assert after==bytes(expected),'Hook changed unexpected fields'
 cases.append(dict(geometry=[x,y,w,h],extended=changed,result='PASS'))
phase='update';updates=[]
for row in cases:
 x,y,w,h=row['geometry'];before=bytearray([0x5a]*0x1810);struct.pack_into('<4I',before,0x40,x,y,w,h);m.mem_write(obj,bytes(before));resize_calls.clear()
 for reg,val in regs.items():m.reg_write(reg,val)
 m.emu_start(int(report['update_wrapper']['address'],16),stop,count=100)
 assert m.reg_read(R.UC_MIPS_REG_SP)==stack and m.reg_read(R.UC_MIPS_REG_RA)==stop
 assert all(m.reg_read(R.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
 assert (m.reg_read(R.UC_MIPS_REG_V0),m.reg_read(R.UC_MIPS_REG_V1))==(0x11223344,0x22334455)
 expected=[[obj,432,h]] if x==24 and y>=180 and w==288 else []
 assert resize_calls==expected and bytes(m.mem_read(obj,len(before)))==bytes(before)
 updates.append(dict(geometry=row['geometry'],native_resize_calls=len(resize_calls),result='PASS'))
proof=dict(version='0.2.37',result='PASS',elf_sha256=report['elf_sha256'],cases=cases,update_cases=updates,caller_state='Stack, return address, saved registers preserved; update retains original return values',scope='Only width, three line widths and background corner alpha/dirty flag changed in selected bottom panels; late placement invokes real resize once')
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/dialogue-window-0.2.37/mips-tests.json').write_text(json.dumps(proof,indent=2)+'\n')
