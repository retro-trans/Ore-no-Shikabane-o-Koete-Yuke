"""Execute native Chronicle date branches and relocated format pointers in MIPS."""
import argparse,json,struct,unicorn
from unicorn import mips_const as reg
from catalog_text import ROOT
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
out=ROOT/'work/output/english-native-0.2.33';elf=(out/'EBOOT.chronicle.elf').read_bytes();r=json.loads((out/'chronicle.report.json').read_text());m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
p=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
 _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,p+i*32);m.mem_write(addr,elf[off:off+size])
obj,stack,stop=0x09e00000,0x09fe0000,0x09ff0000;captures=[]
def narrow(addr):return bytes(m.mem_read(addr,96)).split(b'\0')[0].decode('ascii')
def calls(mu,pc,size,_):
 if pc==0x08824d10:
  fmt=narrow(mu.reg_read(reg.UC_MIPS_REG_A1));year=mu.reg_read(reg.UC_MIPS_REG_A2);month=mu.reg_read(reg.UC_MIPS_REG_A3)
  assert mu.reg_read(reg.UC_MIPS_REG_A1) in [int(x['address'],16) for x in r['literals']]
  if fmt.endswith('%s'):month=narrow(month)
  captures.append(dict(format=fmt,year=year,month=month,text=fmt%(year,month)))
 elif pc!=0x08824270:return
 mu.reg_write(reg.UC_MIPS_REG_PC,mu.reg_read(reg.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,calls)
cases=[0,1,10,11,12,24,25,26,34,35,36,37,38,39,47,48,1199,65535];results=[]
for index in cases:
 captures.clear();m.mem_write(obj+0x2430,b'Z'*32);m.mem_write(stack-64,b'S'*64)
 for register,value in [(reg.UC_MIPS_REG_A0,obj),(reg.UC_MIPS_REG_A1,index),(reg.UC_MIPS_REG_SP,stack),(reg.UC_MIPS_REG_RA,stop)]:m.reg_write(register,value)
 for n in range(8):m.reg_write(reg.UC_MIPS_REG_S0+n,0x12340000+n)
 m.emu_start(0x08918f70,stop,count=500)
 assert m.reg_read(reg.UC_MIPS_REG_PC)==stop and m.reg_read(reg.UC_MIPS_REG_SP)==stack and m.reg_read(reg.UC_MIPS_REG_RA)==stop
 assert all(m.reg_read(reg.UC_MIPS_REG_S0+n)==0x12340000+n for n in range(8))
 stored={35:26,36:35,37:38}.get(index,index);unknown=index in (35,37,38);expected_month='?' if unknown else stored%12+1
 assert len(captures)==1 and captures[0]['year']==1015+stored//12 and captures[0]['month']==expected_month
 assert struct.unpack('<H',m.mem_read(obj+0x2440,2))[0]==stored
 assert bytes(m.mem_read(obj+0x2430,16))==b'Z'*16 and bytes(m.mem_read(obj+0x2442,14))==b'Z'*14
 results.append(dict(month_index=index,**captures[0]))
proof=dict(version='0.2.33',result='PASS',elf_sha256=r['elf_sha256'],cases=len(cases),checks=['Both relocated ASCII format pointers reached through actual MIPS','Year/month arithmetic and all four special historical indices','16-bit upper boundary and year transitions','Stored record index, adjacent guards, stack and callee-save registers'],examples=results)
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/chronicle-0.2.33/mips-tests.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
