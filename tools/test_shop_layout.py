"""Execute actual native shop formatters and comparison paging in MIPS."""
import json,struct
import unicorn
from unicorn import mips_const as r
from catalog_text import ROOT

elf=(ROOT/'work/output/english-native-0.2.19/EBOOT.shop.elf').read_bytes()
report=json.loads((ROOT/'work/output/english-native-0.2.19/shop.report.json').read_text())
m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN);m.mem_map(0x08800000,32<<20)
phoff=struct.unpack_from('<I',elf,28)[0]
for i in range(2):
    _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i);m.mem_write(addr,elf[off:off+size])
stop=0x09ff0000;stack=0x09fe0000;src=0x09f10000;dst=0x09f20000;obj=0x09e00000
selected=[];positions=[];phase='format'
def hook(mu,pc,size,_):
    if pc==0x08976ce8:value=0
    elif pc==0x08977218:
        cp=mu.reg_read(r.UC_MIPS_REG_A0);value=cp+0xfee0 if cp!=32 else 0x3000
    elif phase=='paging' and pc in (0x0894eb90,0x0894ec18,0x0894fc4c):
        if pc==0x0894eb90:selected.append(mu.reg_read(r.UC_MIPS_REG_A1))
        value=0
    elif phase=='scroll' and pc==0x0894fbac:value=0
    elif phase=='position' and pc==0x089b6708:
        positions.append(tuple(mu.reg_read(r.UC_MIPS_REG_A0+i) for i in range(3)));value=0
    else:
        word=struct.unpack('<I',mu.mem_read(pc,4))[0]
        if word>>26==0 and word&63 in (0x2c,0x2d):
            rs,rt,rd=word>>21&31,word>>16&31,word>>11&31
            signed=lambda v:v if v<0x80000000 else v-0x100000000
            aa=signed(mu.reg_read(r.UC_MIPS_REG_0+rs));bb=signed(mu.reg_read(r.UC_MIPS_REG_0+rt))
            mu.reg_write(r.UC_MIPS_REG_0+rd,(max(aa,bb) if word&63==0x2c else min(aa,bb))&0xffffffff)
            mu.reg_write(r.UC_MIPS_REG_PC,pc+4)
        return
    mu.reg_write(r.UC_MIPS_REG_V0,value);mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
m.hook_add(unicorn.UC_HOOK_CODE,hook)
def call(pc,args=(),extras=()):
    for i,v in enumerate(args):m.reg_write(r.UC_MIPS_REG_A0+i,v&0xffffffff)
    for i,v in enumerate(extras):m.reg_write(r.UC_MIPS_REG_T0+i,v&0xffffffff)
    for i in range(8):m.reg_write(r.UC_MIPS_REG_S0+i,0x12340000+i)
    m.reg_write(r.UC_MIPS_REG_FP,0x23456789);m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
    m.emu_start(pc,stop,count=200000)
    assert m.reg_read(r.UC_MIPS_REG_PC)==stop,hex(m.reg_read(r.UC_MIPS_REG_PC))
    assert m.reg_read(r.UC_MIPS_REG_SP)==stack
    assert all(m.reg_read(r.UC_MIPS_REG_S0+i)==0x12340000+i for i in range(8))
    assert m.reg_read(r.UC_MIPS_REG_FP)==0x23456789
def wide(addr,text):m.mem_write(addr,(text+'\0').encode('utf-16-le'))
def read(addr):
    b=bytes(m.mem_read(addr,256));n=next(i for i in range(0,256,2) if b[i:i+2]==b'\0\0');return b[:n].decode('utf-16-le')
def guarded(addr):m.mem_write(addr-8,b'CANARY00'+b'X'*128+b'CANARY11')
def guards(addr):assert bytes(m.mem_read(addr-8,8))==b'CANARY00' and bytes(m.mem_read(addr+128,8))==b'CANARY11'

wrapper=int(report['spacing_wrapper']['address'],16)
wide(src,' ');wide(src+0x100,'Female');wide(src+0x200,'Swordfighters');wide(src+0x300,'Exclusive')
for gender,cl,expected in [('Female','Swordfighters',' Female Swordfighters Exclusive'),('Female','',' Female Exclusive'),('','Gunners',' Gunners Exclusive')]:
    wide(src+0x100,gender);wide(src+0x200,cl);guarded(dst)
    call(wrapper,(dst,128,0x08a411f4,src),(src+0x100,src+0x200,src+0x300))
    assert read(dst)==expected,(read(dst),expected);guards(dst)
# Exercise all four private buffers at their actual new offsets, including
# strings exceeding the original 8/16-character capacities.
fake_stack=dst+0x2000
for off in report['buffers']['private_buffers']:
    p=fake_stack+off;wide(src,'Z'*90);guarded(p)
    call(0x089aa6b8,(p,128,src));assert read(p)=='Z'*63;guards(p)
wide(src,'%+d')
for value in (-65535,-81,-1,0,1,81,65535):
    guarded(dst);call(0x089aa7ac,(dst,128,src,value));assert read(dst)==('%+d'%value);guards(dst)
wide(src,'%s\t%d%s');wide(src+0x100,'Funds:');wide(src+0x200,' ryo')
guarded(dst);call(0x089aa7ac,(dst,128,src,src+0x100),(1000,src+0x200));assert read(dst)=='Funds:\t1000 ryo';guards(dst)

# Execute each changed coordinate setup, starting with dirty argument values.
# This catches invalid MOVE-to-immediate rewrites and stale caller arguments.
phase='position'
for pc,end,offset,x,y in [(0x0894ea4c,0x0894ea5c,0x140,0,20),(0x0894eaa4,0x0894eab4,0x490,20,20)]:
    positions.clear();m.reg_write(r.UC_MIPS_REG_S0,obj)
    m.reg_write(r.UC_MIPS_REG_A1,0x4d082b9c);m.reg_write(r.UC_MIPS_REG_A2,0x4d082ba0)
    m.emu_start(pc,end,count=30)
    assert positions==[(obj+offset,x,y)],positions

def put(offset,v):m.mem_write(obj+offset,struct.pack('<I',v&0xffffffff))
def get(offset):return struct.unpack('<I',m.mem_read(obj+offset,4))[0]
phase='paging';cases=0
for n in range(0,13):
    seen=set()
    for off in range(max(1,n-4+1)):
        m.mem_write(obj,bytes(0x6000));put(0xa3c,n);put(0xa30,off);put(0xa38,1)
        for i in range(n):put(0xa40+i*4,100+i)
        selected.clear();call(0x0894fbac,(obj,))
        assert selected==list(range(100+off,100+off+min(n,4))),(n,off,selected)
        seen.update(selected);cases+=1
    assert seen==set(range(100,100+n))
phase='scroll'
for n in range(0,13):
    for off in range(max(1,n-4+1)):
        m.mem_write(obj,bytes(0x6000));put(0xa3c,n);put(0xa30,off);put(0xa38,1)
        call(0x0894fb58,(obj,));assert get(0xa30)==(off if n<=4 else min(off+1,n-4))
        put(0xa30,off);call(0x0894fb0c,(obj,));assert get(0xa30)==(off if n<=4 else max(off-1,0))
print('PASS: actual MIPS coordinate assignments, restriction joins, expanded 128-byte buffers/canaries, signed deltas, funds spacing, saved caller state, and %d comparison-page cases with all members reachable.'%cases)
