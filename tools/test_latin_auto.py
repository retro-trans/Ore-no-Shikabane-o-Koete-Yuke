"""Run every shipped Latin Auto name through the actual native encoder/copy."""
import json,struct
import unicorn
from unicorn import mips_const as r
from catalog_text import ROOT
elf=(ROOT/'work/output/english-native-0.2.16/EBOOT.latin.elf').read_bytes()
report=json.loads((ROOT/'work/output/english-native-0.2.15/names.report.json').read_text(encoding='utf-8'))
names=json.loads((ROOT/'work/glossary/latin_auto_names.json').read_text(encoding='utf-8'))['rows']
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
    _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i);m.mem_write(addr,elf[off:off+size])
stack=0x09fe0000;stop=0x09ff0000;parent=0x09e00000;src=0x09f10000;dst=0x09f20000
def stub(mu,pc,size,unused):
    if pc==0x08976ce8:value=0
    elif pc==0x08977218:
        cp=mu.reg_read(r.UC_MIPS_REG_A0);value=cp+0xfee0 if cp<128 else cp
    elif pc==0x08977000:value=0x09f30000
    elif pc==0x0882491c:raise AssertionError('Auto name rejected')
    else:return
    mu.reg_write(r.UC_MIPS_REG_V0,value);mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,stub)
def call(pc,args):
    for i,v in enumerate(args):m.reg_write(r.UC_MIPS_REG_A0+i,v)
    m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
    for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x11111110+i)
    m.emu_start(pc,stop,count=20000)
    assert m.reg_read(r.UC_MIPS_REG_SP)==stack
    assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x11111110+i for i in range(8))
for row in names:
    text=row['latin'];assert text.isascii() and text.isalpha() and 1<=len(text)<=8
    wide=''.join(chr(ord(c)+0xfee0) for c in text)
    m.mem_write(src,(wide+'\0').encode('utf-16-le'));m.mem_write(parent+0x4e48,b'CANARY00'+b'........'+b'CANARY11')
    call(int(report['names']['functions']['encode'],16),(parent,src))
    assert bytes(m.mem_read(parent+0x4e48,8))==b'CANARY00' and bytes(m.mem_read(parent+0x4e58,8))==b'CANARY11'
    m.mem_write(src,bytes(m.mem_read(parent+0x4e50,8))+b'NEXTNEXT');m.mem_write(dst,b'X'*128)
    call(0x089aa6b8,(dst,128,src))
    expected=(''.join(chr(ord(c)+0xfee0) for c in text)+'\0').encode('utf-16-le')
    assert bytes(m.mem_read(dst,len(expected)))==expected,text
    m.mem_write(dst,(wide+'\0').encode('utf-16-le'));call(0x089ab0a8,(src,dst));assert m.reg_read(r.UC_MIPS_REG_V0)==0,text
print('PASS:',len(names),'shipped Auto names; actual MIPS encode/decode/duplicate comparison, original eight-byte records, adjacent canaries, stack and saved registers.')
