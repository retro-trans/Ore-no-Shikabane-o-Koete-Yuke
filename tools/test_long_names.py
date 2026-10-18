"""Exercise actual MIPS long-name encoding and native wide-string consumers."""
import random
import struct

import unicorn
from unicorn import mips_const as r

from catalog_text import ROOT
from patch_name_font import patch as font_patch
from patch_long_names import patch, encode_reference, decode_reference


def main():
    source=(ROOT/'work/output/english-native-0.2.12/EBOOT.keyboard.elf').read_bytes()
    elf,_=font_patch(source);elf,report=patch(elf)
    m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN)
    m.mem_map(0x08800000,32<<20)
    phoff=struct.unpack_from('<I',elf,28)[0]
    for i in range(2):
        _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i)
        m.mem_write(addr,elf[off:off+size])
    stop=0x09ff0000;stack=0x09fe0000;src=0x09f10000;dst=0x09f20000;parent=0x09e00000
    errors=[]
    def stub(mu,pc,size,unused):
        if pc==0x08976ce8:value=0
        elif pc==0x08977218:
            cp=mu.reg_read(r.UC_MIPS_REG_A0);value=cp+0xfee0 if cp!=32 else 0x3000
        elif pc==0x08977000:value=0x09f30000
        elif pc==0x0882491c:errors.append(True);value=0
        else:
            # PSP Allegrex MIN/MAX use these encodings; Unicorn's MIPS32
            # core does not implement them, so emulate that CPU operation.
            word=struct.unpack('<I',mu.mem_read(pc,4))[0]
            if word>>26==0 and word&63 in (0x2c,0x2d):
                rs,rt,rd=word>>21&31,word>>16&31,word>>11&31
                def signed(v):return v if v<0x80000000 else v-0x100000000
                a=signed(mu.reg_read(r.UC_MIPS_REG_0+rs));b=signed(mu.reg_read(r.UC_MIPS_REG_0+rt))
                mu.reg_write(r.UC_MIPS_REG_0+rd,(max(a,b) if word&63==0x2c else min(a,b))&0xffffffff)
                mu.reg_write(r.UC_MIPS_REG_PC,pc+4)
            return
        mu.reg_write(r.UC_MIPS_REG_V0,value);mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
    m.hook_add(unicorn.UC_HOOK_CODE,stub)
    saved=[r.UC_MIPS_REG_S0+i for i in range(8)]
    def call(pc,args=(),t0=None):
        for i,v in enumerate(args):m.reg_write(r.UC_MIPS_REG_A0+i,v)
        for i,reg in enumerate(saved):m.reg_write(reg,0x12000000+i)
        m.reg_write(r.UC_MIPS_REG_FP,0x12345678)
        m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
        if t0 is not None:m.reg_write(r.UC_MIPS_REG_T0,t0)
        m.emu_start(pc,stop,count=200000)
        assert m.reg_read(r.UC_MIPS_REG_SP)==stack,hex(m.reg_read(r.UC_MIPS_REG_PC))
        assert all(m.reg_read(reg)==0x12000000+i for i,reg in enumerate(saved))
        assert m.reg_read(r.UC_MIPS_REG_FP)==0x12345678
        return m.reg_read(r.UC_MIPS_REG_V0)
    def u16(text):return (text+'\0').encode('utf-16-le')
    def wide(text):return ''.join('\u3000' if c==' ' else chr(ord(c)+0xfee0) for c in text)
    patched_converter=bytes(m.mem_read(0x089ab210,8))
    def original_bytes(text):
        tmp=src+0x1000;dest=dst+0x1000
        m.mem_write(tmp,u16(text));m.mem_write(dest,b'X'*128)
        m.mem_write(0x089ab210,source[0x089ab210-0x08803000:0x089ab218-0x08803000])
        m.ctl_remove_cache(0x089ab210,0x089ab218)
        call(0x089ab210,(dest,tmp));result=bytes(m.mem_read(dest,128))
        m.mem_write(0x089ab210,patched_converter);m.ctl_remove_cache(0x089ab210,0x089ab218)
        return result
    def read_text(addr):
        b=bytes(m.mem_read(addr,512));out=[]
        for i in range(0,len(b),2):
            cp=struct.unpack_from('<H',b,i)[0]
            if not cp:break
            out.append(chr(cp))
        return ''.join(out)
    rng=random.Random(20261017)
    samples=['TestName','ABCDEFGH','AbZq',"O'Neilly",'John Doe','A-b!23?Z','WWWWWWWW']
    samples+=[''.join(chr(rng.randrange(33,127)) for _ in range(rng.randrange(4,9))) for _ in range(120)]
    for text in samples:
        packed=encode_reference(text);assert decode_reference(packed)==text and len(packed)==8
        m.mem_write(src,u16(text));m.mem_write(parent+0x4e48,b'CANARY00'+b'........'+b'CANARY11')
        call(int(report['functions']['encode'],16),(parent,src))
        assert bytes(m.mem_read(parent+0x4e50,8))==packed,text
        assert bytes(m.mem_read(parent+0x4e48,8))==b'CANARY00' and bytes(m.mem_read(parent+0x4e58,8))==b'CANARY11'
        m.mem_write(src,packed+b'NEXTNEXT')
        assert call(0x089aa690,(src,))==len(text)
        expected=wide(text)
        m.mem_write(dst,b'X'*128);call(0x089aa6b8,(dst,128,src));assert read_text(dst)==expected
        call(0x089aa700,(dst,8,src,2));assert read_text(dst)==expected[:2]
        reference=original_bytes(expected)
        m.mem_write(dst,b'X'*128);call(0x089ab210,(dst,src))
        assert bytes(m.mem_read(dst,128))==reference,text
        m.mem_write(dst,b'X'*32);call(0x089aa6b8,(dst,8,src))
        assert bytes(m.mem_read(dst,8))==packed and bytes(m.mem_read(dst+8,8))==b'X'*8
        m.mem_write(dst,u16(expected));assert call(0x089ab0a8,(src,dst))==0
        m.mem_write(dst,u16('prefix:'));call(0x089aa75c,(dst,src));assert read_text(dst)=='prefix:'+expected
        # The real native printf string loop uses the local iterator.
        fmt=dst+0x400;out=dst+0x800;m.mem_write(fmt,u16('"%s", correct?'))
        call(0x089aa7ac,(out,256,fmt,src));assert read_text(out)=='"'+expected+'", correct?'
        arglist=src+0x800;m.mem_write(arglist,struct.pack('<I',src))
        call(0x08969a30,(out,256,fmt,arglist));assert read_text(out)=='"'+expected+'", correct?'
        # A literal name must not read or interpret the following save field.
        m.mem_write(src,packed+u16('%s%sNEXT'))
        for formatter in (0x089aa7ac,0x08969a30):
            assert call(formatter,(out,256,src,0))==len(text)
            assert read_text(out)==expected
            assert call(formatter,(out,8,src,0))==3 and read_text(out)==expected[:3]
    for text in ['AbZ','\u7530\u4e2d','a']:
        m.mem_write(src,u16(text));call(int(report['functions']['encode'],16),(parent,src))
        expected=''.join(chr(ord(c)+0xfee0) if ord(c)<128 else c for c in text)
        assert read_text(parent+0x4e50)==expected
    # The unmodified byte converter is the reference for ordinary strings.
    # This protects its byte destination contract, including wide Latin/Japanese.
    for text in ['ABC xyz 0123','\u7530\u4e2d','\uff21\uff42\uff5e','\uff0f\uff0d\uff3c']:
        m.mem_write(src,u16(text));m.mem_write(dst,b'X'*128)
        call(0x089ab210,(dst,src));actual=bytes(m.mem_read(dst,128))
        assert original_bytes(text)==actual,text
    original=bytes(m.mem_read(parent+0x4e50,8))
    for text in ['TooLong09','\u7530\u4e2d\u5c71\u7530','        ']:
        m.mem_write(src,u16(text));n=len(errors);call(int(report['functions']['encode'],16),(parent,src))
        assert len(errors)==n+1 and bytes(m.mem_read(parent+0x4e50,8))==original
    # Inline marker expansion and a difference in the final character.
    m.mem_write(src,u16('Hi ')[:-2]+encode_reference('TestName')+u16('!'))
    call(0x089aa6b8,(dst,128,src));assert read_text(dst)=='Hi '+wide('TestName')+'!'
    m.mem_write(src,encode_reference('ABCDEFGH'));m.mem_write(dst,encode_reference('ABCDEFGI'))
    assert call(0x089ab0a8,(src,dst))==0xffffffff
    print('PASS: 127 actual MIPS codec/length/bounded and counted copy/compare/concatenate cases; both formatters and literal/substitution paths; original legacy byte conversion; eight-byte record canaries, invalid input, fullwidth decoding, embedded markers and saved registers.')


if __name__=='__main__':main()
