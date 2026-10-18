"""Execute the patched MIPS glyph path with real native advance metrics."""
import json
import struct

import unicorn
from unicorn import mips_const as r

from catalog_text import ROOT
from patch_name_font import patch, HOOK, FONT_SERVICE


def main():
    source=(ROOT/'work/output/english-native-0.2.12/EBOOT.keyboard.elf').read_bytes()
    elf,report=patch(source)
    m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN)
    m.mem_map(0x08800000,32<<20)
    phoff=struct.unpack_from('<I',elf,28)[0]
    for i in range(2):
        _,off,addr,_,size,_,_,_=struct.unpack_from('<8I',elf,phoff+32*i)
        m.mem_write(addr,elf[off:off+size])
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
    seen=[]
    def service(mu,pc,size,unused):
        if pc==FONT_SERVICE:value=0x09e00000
        elif pc==0x089B5AB4:
            cp=mu.reg_read(r.UC_MIPS_REG_A1);seen.append(cp)
            value=metrics[str(cp)]['advance'] if str(cp) in metrics else 22
        elif pc==0x089BB234:value=0
        else:return
        mu.reg_write(r.UC_MIPS_REG_V0,value)
        mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
    m.hook_add(unicorn.UC_HOOK_CODE,service)
    cases=[(0xff50,ord('p')),(0xff4f,ord('o')),(0xff21,ord('A')),
           (0xff01,33),(0xff5e,126),(0x3000,32),(160,160),
           (0x3042,0x3042),(0x7530,0x7530),(0xff00,0xff00),(0xff5f,0xff5f)]
    for cp,expected in cases+[(x,x) for x in range(32,127)]:
        desc=0x09f00000;stack=0x09f10000
        m.mem_write(desc,bytes(28));m.reg_write(r.UC_MIPS_REG_S3,desc)
        m.reg_write(r.UC_MIPS_REG_S2,cp);m.reg_write(r.UC_MIPS_REG_FP,0)
        m.reg_write(r.UC_MIPS_REG_S0,0x1234);m.reg_write(r.UC_MIPS_REG_S6,0x09f20000)
        m.reg_write(r.UC_MIPS_REG_SP,stack)
        m.emu_start(HOOK,0x089BA724,count=100)
        code,advance=struct.unpack('<2H',m.mem_read(desc+4,4))
        assert code==expected and seen[-1]==expected
        assert advance==(metrics[str(expected)]['advance'] if str(expected) in metrics else 22)
        assert m.reg_read(r.UC_MIPS_REG_SP)==stack and m.reg_read(r.UC_MIPS_REG_S6)==0x09f20000
    print('PASS: fullwidth Latin, wide space, all 95 ASCII characters, NBSP and Japanese/boundary fallback; canonical code/advance descriptors and stack preserved.')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
