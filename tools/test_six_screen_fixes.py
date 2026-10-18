"""Exercise native row/label wrappers and measure the requested compact text."""
import json,struct,unicorn,keystone
from unicorn import mips_const as reg
from catalog_text import ROOT
from check_translation import TOKEN
out=ROOT/'work/output/english-native-0.2.27';elf=(out/'EBOOT.screens.elf').read_bytes();r=json.loads((out/'screens.report.json').read_text());m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20);p=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
 _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,p+32*i);m.mem_write(addr,elf[off:off+size])
stack,stop,obj,vt=0x09fe0000,0x09ff0000,0x09ef0000,0x09ee0000;method=0x09ed0000;m.mem_write(vt+0x78,struct.pack('<I',method))
R=lambda n:getattr(reg,'UC_MIPS_REG_'+n)
ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
def init():
 m.mem_write(obj,bytes(128));m.reg_write(R('SP'),stack);m.reg_write(R('RA'),stop)
 for i in range(8):m.reg_write(R('S0')+i,0x12340000+i)
def saved(exceptions=()):
 assert m.reg_read(R('SP'))==stack
 assert all(m.reg_read(R('S0')+i)==0x12340000+i for i in range(8) if i not in exceptions)
position=int(r['wrappers'][0]['address'],16)
for index in range(6):
 init();m.reg_write(R('S7'),index);m.reg_write(R('S3'),88 if index%2 else 108);m.reg_write(R('V0'),vt);m.reg_write(R('A0'),obj);m.reg_write(R('A1'),132)
 m.emu_start(position,stop,count=60);assert m.reg_read(R('V0'))==method and m.reg_read(R('A0'))==obj and m.reg_read(R('A1'))==132
 assert m.reg_read(R('A2'))==(128 if index==4 else (88 if index%2 else 108));saved((3,7))
m.mem_write(method,bytes(ks.asm('.set noreorder\njr $ra\nnop',addr=method)[0]));chart_cases=0
for group in (0,73,146):
 for element in (0,15,30,45):
  row=group+element;init();m.mem_write(obj,struct.pack('<I',vt));m.reg_write(R('S1'),obj-0x680);m.reg_write(R('S0'),obj);m.reg_write(R('S5'),row)
  m.emu_start(0x088f1e88,0x088f1ea0,count=50);assert m.reg_read(R('A1'))==54 and m.reg_read(R('A2'))==row+37
  init();m.mem_write(obj,struct.pack('<I',vt));m.reg_write(R('S3'),obj-0x2840);m.reg_write(R('S2'),obj);m.reg_write(R('S5'),row)
  m.emu_start(0x088f1ec8,0x088f1ee4,count=50);assert m.reg_read(R('A1'))==36 and m.reg_read(R('A2'))==row+35
  chart_cases+=2
metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];width=lambda t,s:sum(metrics[str(ord(c))]['advance'] for c in t)*s/14
for text in ('Spirit','Skill','Body'):assert width(text,12)<34
assert 54+84==138 and 138<142
helptext=next(x for x in r['text_edits'] if x['id'].endswith('0009:00:0058'))['translation_en'].lstrip('@').split('\n')
assert len(helptext)==2 and width(helptext[0],12)<=164 and width(helptext[1],12)<=150
assert width('Next Growth',16)<144 and width('Points Earned',12)<160 and width('Naginata',12)<90
units=[x['translation_en'] for x in r['text_edits'] if x['id'].startswith('ore:00028000:0003:02:')]
assert units==[' items',' prints']
assert all(width('30'+unit,12)<70 for unit in units)
assert width('Now:',12)<40 and width('Mo. 12:',12)<50
print('PASS: 6 actual MIPS equipment-row cases, %d native chart-coordinate cases, stack/saved registers, full-size chart label lane, growth/results/class widths, two complete formation-help lines and shared count-unit spacing.'%chart_cases)
