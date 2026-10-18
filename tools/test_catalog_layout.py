"""Execute Scrolls display adapters with acquired counts and caller guards."""
import argparse,json,struct,unicorn
from unicorn import mips_const as reg
from catalog_text import ROOT
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
out=ROOT/'work/output/english-native-0.2.34';elf=(out/'EBOOT.catalog.elf').read_bytes();r=json.loads((out/'catalog.report.json').read_text());m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
p=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
 _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,p+i*32);m.mem_write(addr,elf[off:off+size])
obj,stack,stop=0x09e00000,0x09fe0000,0x09ff0000;seen=[]
def calls(mu,pc,size,_):
 if pc not in (0x0882b49c,0x0882b2e0):return
 assert mu.reg_read(reg.UC_MIPS_REG_A0)==obj
 ptr=mu.reg_read(reg.UC_MIPS_REG_A1)
 if pc==0x0882b49c:assert bytes(mu.mem_read(ptr,2))==b'\0\0';text=''
 else:
  fmt=bytes(mu.mem_read(ptr,6));assert fmt==b'%d/%d\0';assert mu.reg_read(reg.UC_MIPS_REG_A3)==73
  text=fmt[:-1].decode()%(mu.reg_read(reg.UC_MIPS_REG_A2),73)
 seen.append(text);mu.reg_write(reg.UC_MIPS_REG_PC,mu.reg_read(reg.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,calls);results=[]
for wrapper in r['wrappers']:
 for n in (0,1,9,10,72,73):
  seen.clear()
  for register,value in [(reg.UC_MIPS_REG_A0,obj),(reg.UC_MIPS_REG_A1,0xdead),(reg.UC_MIPS_REG_A2,n),(reg.UC_MIPS_REG_SP,stack),(reg.UC_MIPS_REG_RA,stop)]:m.reg_write(register,value)
  for i in range(8):m.reg_write(reg.UC_MIPS_REG_S0+i,0x12340000+i)
  m.emu_start(int(wrapper['address'],16),stop,count=30)
  assert m.reg_read(reg.UC_MIPS_REG_PC)==stop and m.reg_read(reg.UC_MIPS_REG_SP)==stack and m.reg_read(reg.UC_MIPS_REG_RA)==stop
  assert all(m.reg_read(reg.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
  assert seen==([''] if wrapper['name']=='empty_scrolls_unit' else ['%d/73'%n]);results.append(dict(adapter=wrapper['name'],acquired=n,text=seen[0]))
proof=dict(version='0.2.34',result='PASS',elf_sha256=r['elf_sha256'],cases=len(results),checks=['Actual MIPS adapter execution at original native setter/formatter targets','Zero, single and double digit counts through complete collection','Original cText receiver, stack, return address and callee-save registers retained'],examples=results)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/catalog-0.2.34/mips-tests.json').write_text(json.dumps(proof,indent=2)+'\n')
