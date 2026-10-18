"""Check actual MIPS date indices, year forwarding and percent-token safety."""
import struct
import json

import unicorn
from unicorn import mips_const as r

from build_setup_ui import BASE, BOUNDS, ROOT, CODE, IMAGE, native_date
from check_translation import tokens_equal


def main():
    source=(ROOT/'work/output/english-native-0.2.7/EBOOT.elf').read_bytes()
    native,report=native_date(source)
    m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN)
    m.mem_map(0x08800000,32<<20)
    ph=u32(native,28)
    for n in range(2):
        kind,off,addr,_,size,_,_,_=struct.unpack_from('<8I',native,ph+n*32)
        assert kind==1
        m.mem_write(addr,native[off:off+size])
    obj=0x09F00000
    for state,start,end in [(0,0,3),(1,5,6),(2,8,9)]:
        m.mem_write(obj,bytes(0xE00))
        m.mem_write(obj+0xD60,struct.pack('<I',state))
        m.reg_write(r.UC_MIPS_REG_A0,obj)
        m.reg_write(r.UC_MIPS_REG_SP,0x09F10000)
        m.emu_start(0x089706C8,0x08970718,count=100)
        assert m.reg_read(r.UC_MIPS_REG_S0)==start
        m.reg_write(r.UC_MIPS_REG_A0,0x12345678)
        m.reg_write(r.UC_MIPS_REG_A1,0x23456789)
        m.reg_write(r.UC_MIPS_REG_A2,start+1)
        m.reg_write(r.UC_MIPS_REG_RA,0x08970730)
        m.emu_start(int(report['wrapper_address'],16),BOUNDS,count=30)
        assert m.reg_read(r.UC_MIPS_REG_A2)==end
        assert m.reg_read(r.UC_MIPS_REG_A0)==0x12345678
        assert m.reg_read(r.UC_MIPS_REG_A1)==0x23456789
        assert m.reg_read(r.UC_MIPS_REG_RA)==0x08970730
    for year in [1926,1980,1989,2000,2011]:
        m.mem_write(obj,struct.pack('<H',year))
        m.reg_write(r.UC_MIPS_REG_S2,obj)
        m.reg_write(r.UC_MIPS_REG_S3,55)
        m.emu_start(0x089708BC,0x089708C0,count=1)
        assert m.reg_read(r.UC_MIPS_REG_A3)==year
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
    obj,descriptors,old_image,stop=0x09F00000,0x09F01000,0x09E00000,0x09F10000
    m.mem_write(0x09AF54E4,struct.pack('<I',old_image))
    cases=[(''.join(chr(c) for c in range(32,127)),True),('125%',True),
           ('\xa094%',True),('\xa0\xa05%',True),('A\xa0\u3042B',False)]
    for text,native_font in cases:
        m.mem_write(obj,bytes(0x120))
        m.mem_write(obj+0xD4,struct.pack('<I',descriptors))
        records=bytearray(28*(len(text)+1))
        for i,ch in enumerate(text):
            struct.pack_into('<HH4H4H',records,i*28+4,ord(ch),12,i*48,0,i*48+48,80,11,22,33,44)
        m.mem_write(descriptors,bytes(records))
        m.reg_write(r.UC_MIPS_REG_A0,obj)
        m.reg_write(r.UC_MIPS_REG_RA,stop)
        m.reg_write(r.UC_MIPS_REG_S1,0x12345678)
        m.emu_start(CODE,stop,count=10000)
        assert m.reg_read(r.UC_MIPS_REG_V0)==(IMAGE if native_font else old_image)
        assert m.reg_read(r.UC_MIPS_REG_S1)==0x12345678
        actual=bytes(m.mem_read(descriptors,len(records)))
        if not native_font:
            assert actual==records
        else:
            for i,ch in enumerate(text):
                metric=metrics[str(32 if ord(ch)==160 else ord(ch))]
                uv=struct.unpack_from('<4H',actual,i*28+16)
                assert uv==(metric['atlas_x']*64,metric['atlas_y']*64,
                            (metric['atlas_x']+metric['sample_width'])*64,
                            (metric['atlas_y']+metric['sample_height'])*64)
                assert actual[i*28:i*28+16]==records[i*28:i*28+16]
    assert tokens_equal('%1:3d％','%1:3d%%')
    assert tokens_equal('%d %%','%d %%')
    assert not tokens_equal('%1:3d％','%2:3d%%')
    assert not tokens_equal('%1:3d％','%1:3d%%%%')
    assert not tokens_equal('%d %%','%d')
    print('PASS: three MIPS cursor ranges, five Gregorian years, tail-call registers, five font cases including padded numbers/Japanese fallback, unchanged glyph codes/advances/quads and percent-token regressions.')


def u32(b,o):
    return struct.unpack_from('<I',b,o)[0]


if __name__=='__main__':
    main()
