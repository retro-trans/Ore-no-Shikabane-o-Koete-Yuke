"""Execute trait formatting/wrapping MIPS, checking buffer bounds and caller state."""
import json,struct,re,unicorn,hashlib
from unicorn import mips_const as r
from catalog_text import ROOT
out=ROOT/'work/output/english-native-0.2.30';elf=(out/'EBOOT.traits.elf').read_bytes();rep=json.loads((out/'traits.report.json').read_text());m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
 _,o,a,_,n,_,_,_=struct.unpack_from('<8I',elf,phoff+i*32);m.mem_write(a,elf[o:o+n])
stack=0x09fe0000;stop=0x09ff0000;src=0x09e00000;name=src+2048;city=src+2200;buf=int(rep['buffer'],16);guard=int(rep['guard'],16)
m.mem_write(name,'ABCDEFGH\0'.encode('utf-16-le'));m.mem_write(city,'Kyoto\0'.encode('utf-16-le'))
m.mem_write(0x0896a0f0,bytes(4)) # Allegrex min; emulate exactly in the test.
def native_min(mu,pc,size,_):
 a=mu.reg_read(r.UC_MIPS_REG_A1);b=mu.reg_read(r.UC_MIPS_REG_V0)
 signed=lambda v:v if v<0x80000000 else v-0x100000000
 mu.reg_write(r.UC_MIPS_REG_V0,min(signed(a),signed(b))&0xffffffff)
m.hook_add(unicorn.UC_HOOK_CODE,native_min,begin=0x0896a0f0,end=0x0896a0f0)
rows=[z for p in (ROOT/'work/translation/en').glob('traits_batch_*.en.json') for z in json.loads(p.read_text(encoding='utf-8')).get('rows',[])]
assert len(rows)==731
cases=[z['translation_en'] for z in rows]+['', 'A'*510, 'A'*800, 'One\nTwo', '100% literal']
maxlines=0;metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];results=[]
for text in cases:
 m.mem_write(src,(text+'\0').encode('utf-16-le'));m.mem_write(stack-128,b'Z'*128);m.mem_write(buf,b'\xcc'*1024);m.mem_write(stack+0x90,b'OLD_STACK_BUFFER_UNTOUCHED')
 for reg,val in [(r.UC_MIPS_REG_A0,stack+0x90),(r.UC_MIPS_REG_A1,20),(r.UC_MIPS_REG_A2,src),(r.UC_MIPS_REG_A3,name),(r.UC_MIPS_REG_T0,city),(r.UC_MIPS_REG_SP,stack),(r.UC_MIPS_REG_RA,stop)]:m.reg_write(reg,val)
 for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
 try:m.emu_start(int(rep['wrappers'][0]['address'],16),stop,count=200000)
 except unicorn.UcError:
  print('Exception at',hex(m.reg_read(r.UC_MIPS_REG_PC)),repr(text));raise
 assert m.reg_read(r.UC_MIPS_REG_PC)==stop,hex(m.reg_read(r.UC_MIPS_REG_PC))
 assert m.reg_read(r.UC_MIPS_REG_SP)==stack and m.reg_read(r.UC_MIPS_REG_RA)==stop
 assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
 assert bytes(m.mem_read(guard,17))==b'TRAIT_BUFFER_END!'
 assert bytes(m.mem_read(stack+0x90,26))==b'OLD_STACK_BUFFER_UNTOUCHED'
 raw=bytes(m.mem_read(buf,1024));s=''.join(chr(struct.unpack_from('<H',raw,i)[0]) for i in range(0,1024,2)).split('\0')[0]
 expected=text.replace('%1:s','ABCDEFGH').replace('%2:s','Kyoto')
 if text=='100% literal':continue # Deliberately invalid native format; bounds still checked.
 assert s.replace('\n',' ')==expected[:511].replace('\n',' '),(text,s)
 if text in [z['translation_en'] for z in rows]:
  lines=s.split('\n');maxlines=max(maxlines,len(lines));assert len(lines)<=2,(text,s)
  widths=[sum(metrics[str(ord(c))]['advance'] for c in line) for line in lines];assert max(widths or [0])<=rep['wrap_metric_budget']
  results.append(dict(text=s,maximum_metric_width=max(widths or [0])))
obj=0x09e10000;child=obj+0x1000;table=obj+0x2000;allocator=0x09f00000;show=allocator+16;position=allocator+32;calls=[]
m.mem_write(0x08b34a90,struct.pack('<I',table));m.mem_write(table,struct.pack('<I',allocator));m.mem_write(table+0xe8,struct.pack('<I',show));m.mem_write(table+0x6c,struct.pack('<I',position))
def text_at(a):return bytes(m.mem_read(a,1024)).decode('utf-16-le').split('\0')[0]
def services(mu,pc,size,_):
 if pc not in (allocator,show,position,0x0882b544,0x089ba188,0x089b8050,0x089bb080,0x089bb00c,0x089bba6c,0x089bba88):return
 args=[mu.reg_read(x) for x in (r.UC_MIPS_REG_A0,r.UC_MIPS_REG_A1,r.UC_MIPS_REG_A2,r.UC_MIPS_REG_A3)]
 if pc==allocator:assert args[:2]==[0x110,16];mu.reg_write(r.UC_MIPS_REG_V0,child)
 elif pc==0x0882b544:assert args[0]==obj;calls.append(('first',text_at(args[1])))
 elif pc==0x089ba188:mu.mem_write(child,struct.pack('<I',table));mu.reg_write(r.UC_MIPS_REG_V0,child)
 elif pc==0x089b8050:assert args[:2]==[obj,child];calls.append(('owned',True))
 elif pc==0x089bb00c:calls.append(('second',text_at(args[1])[:args[2]]))
 elif pc==position:calls.append(('position',args[1],args[2]))
 mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
handle=m.hook_add(unicorn.UC_HOOK_CODE,services)
for text in ['Saying: Knock on wood.','Creed: An iron heart and iron\nwill','First line\nSecond line']:
 calls.clear();m.mem_write(buf,(text+'\0').encode('utf-16-le'))
 for reg,val in [(r.UC_MIPS_REG_A0,obj),(r.UC_MIPS_REG_SP,stack),(r.UC_MIPS_REG_RA,stop)]:m.reg_write(reg,val)
 for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
 m.emu_start(int(rep['wrappers'][2]['address'],16),stop,count=10000)
 assert calls[0]==('first',text.split('\n')[0]),calls
 if '\n' in text:assert calls[1:]==[('owned',True),('second',text.split('\n')[1]),('position',0,14)],calls
 else:assert len(calls)==1,calls
 assert text_at(buf)==text and m.reg_read(r.UC_MIPS_REG_SP)==stack and m.reg_read(r.UC_MIPS_REG_RA)==stop
 assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
m.hook_del(handle);hide=allocator+48;m.mem_write(table+0xe4,struct.pack('<I',hide));stats=obj+0x2f20;trait=stats-7920;m.mem_write(trait,struct.pack('<I',table))
def tab_services(mu,pc,size,_):
 if pc not in (show,hide,0x08947e84,0x089b671c):return
 aa=mu.reg_read(r.UC_MIPS_REG_A0);bb=mu.reg_read(r.UC_MIPS_REG_A1);cc=mu.reg_read(r.UC_MIPS_REG_A2)
 if pc in (show,hide):calls.append(('show' if pc==show else 'hide',aa))
 elif pc==0x08947e84:assert aa==stats;calls.append(('tab',bb))
 else:calls.append(('resize',bb,cc))
 mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
handle=m.hook_add(unicorn.UC_HOOK_CODE,tab_services)
for mode in range(3):
 calls.clear();m.reg_write(r.UC_MIPS_REG_A0,stats);m.reg_write(r.UC_MIPS_REG_A1,mode);m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
 for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
 m.emu_start(int(rep['wrappers'][3]['address'],16),stop,count=1000)
 assert calls==[('tab',mode),('hide' if mode==2 else 'show',trait)],calls
 assert m.reg_read(r.UC_MIPS_REG_SP)==stack and m.reg_read(r.UC_MIPS_REG_RA)==stop and all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
 calls.clear();m.reg_write(r.UC_MIPS_REG_S1,stats);m.reg_write(r.UC_MIPS_REG_S3,mode);m.emu_start(0x08947fb4,0x08947fdc,count=100)
 assert calls==[('resize',260,108 if mode==2 else 80)],calls
proof=dict(version=rep['version'],elf_sha256=hashlib.sha256(elf).hexdigest(),result='PASS',actual_native_formatter=True,translated_rows=len(rows),stress_cases=len(cases)-len(rows),maximum_lines=maxlines,buffer_guard='unchanged',old_stack_buffer='untouched',caller_state='SP, RA, S0-S7 preserved',raw_setter='Three MIPS cases: first line, owned second text child, local position [0,14], full buffer restored',tabs='Three MIPS visibility cases and original frame resize branches: 260x80 for Status/Abilities, 260x108 for Equipment',dynamic_substitutions='Eight-letter name and city forwarded through original formatter',worst=max(results,key=lambda x:x['maximum_metric_width']))
(ROOT/'work/ui/profile-traits-0.2.30/mips-tests.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof,indent=2))
