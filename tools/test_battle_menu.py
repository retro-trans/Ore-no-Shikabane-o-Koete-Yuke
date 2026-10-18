"""Run actual MIPS tooltip wrapping against all consumable/equipment descriptions."""
import argparse,json,struct,unicorn
from unicorn import mips_const as reg
from catalog_text import ROOT
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();out=ROOT/'work/output/english-native-0.2.36';elf=(out/'EBOOT.bmenu.elf').read_bytes();r=json.loads((out/'battle-menu.report.json').read_text());m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
p=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
 _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,p+i*32);m.mem_write(addr,elf[off:off+size])
obj,source,stack,stop=0x09e00000,0x09e10000,0x09fe0000,0x09ff0000;vtable,position=0x09ed0000,0x09ff0100;seen=[];ys=[]
def wide(addr):
 b=bytes(m.mem_read(addr,2048));return b.decode('utf-16-le').split('\0')[0]
def calls(mu,pc,size,_):
 a0,a1=mu.reg_read(reg.UC_MIPS_REG_A0),mu.reg_read(reg.UC_MIPS_REG_A1)
 if pc==0x0882b544:assert a0==obj;seen.append(wide(a1))
 elif pc==0x09cbb6c0:
  assert a0==obj;t=wide(a1);assert mu.reg_read(reg.UC_MIPS_REG_A2)==len(t);seen.append(t);child=obj+0x1000+len(seen)*0x200;m.mem_write(child,struct.pack('<I',vtable));mu.reg_write(reg.UC_MIPS_REG_V0,child)
 elif pc==position:assert a1==0;ys.append(mu.reg_read(reg.UC_MIPS_REG_A2))
 elif pc==0x089aa690:mu.reg_write(reg.UC_MIPS_REG_V0,len(wide(a0)))
 elif pc not in (0x089bba6c,0x089bba88):return
 mu.reg_write(reg.UC_MIPS_REG_PC,mu.reg_read(reg.UC_MIPS_REG_RA))
m.mem_write(vtable+0x6c,struct.pack('<I',position));m.hook_add(unicorn.UC_HOOK_CODE,calls)
rows=[(x['id'],x['translation_en']) for x in json.loads((ROOT/'work/translation/en/ui_batch_010.json').read_text(encoding='utf-8'))['rows'] if x['file']=='item_help.mlb']
rows += [(x['id'],x['translation_en']) for x in json.loads((ROOT/'work/translation/en/combat_batch_001.json').read_text(encoding='utf-8'))['rows'] if x['section']==0 and x['index'] in (20,21,22)]
metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];measure=lambda t:sum(metrics.get(str(ord(c)),{'advance':14})['advance'] for c in t);results=[]
for row,text in rows:
 seen.clear();ys.clear();original=(text+'\0').encode('utf-16-le');m.mem_write(source,original);m.mem_write(stack-128,b'S'*128)
 for rr,v in [(reg.UC_MIPS_REG_A0,obj),(reg.UC_MIPS_REG_A1,source),(reg.UC_MIPS_REG_SP,stack),(reg.UC_MIPS_REG_RA,stop)]:m.reg_write(rr,v)
 for i in range(8):m.reg_write(reg.UC_MIPS_REG_S0+i,0x12340000+i)
 m.emu_start(int(r['wrappers'][0]['address'],16),stop,count=50000)
 assert m.reg_read(reg.UC_MIPS_REG_PC)==stop and m.reg_read(reg.UC_MIPS_REG_SP)==stack and m.reg_read(reg.UC_MIPS_REG_RA)==stop
 assert all(m.reg_read(reg.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8));assert bytes(m.mem_read(source,len(original)))==original
 assert ' '.join(' '.join(seen).split())==' '.join(text.split()),(row,seen,text)
 assert max([measure(t) for t in seen] or [0])<=280 and len(seen)<=3,(row,seen)
 assert ys==list(range(16,len(seen)*16,16));assert bytes(m.mem_read(int(r['guard'],16),16))==b'BATTLE_HELP_END!'
 results.append(dict(id=row,lines=list(seen)))
assert len(r['names'])==66 and all(x['metric_width']<=110 for x in r['names']) and len(set(x['after'] for x in r['names']))==66
proof=dict(version='0.2.36',result='PASS',elf_sha256=r['elf_sha256'],description_cases=len(results),consumable_names=66,max_lines=max(len(x['lines']) for x in results),checks=['Actual MIPS adapter execution','Complete text and source-buffer preservation','Caller stack, return address and callee-save registers','Measured line budget and 16-pixel child placement','Buffer guard and unique names within Young Leaf Pills width'],examples=[x for x in results if x['id'].endswith(('00:0004','00:0053','00:0022'))])
print(json.dumps(proof,indent=2))
if a.write:(ROOT/'work/ui/battle-menu-0.2.36/mips-tests.json').write_text(json.dumps(proof,indent=2)+'\n')
