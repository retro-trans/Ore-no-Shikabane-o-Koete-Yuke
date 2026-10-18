"""Execute the native home-tail and contextual studio-position hooks."""
import struct
import unicorn
from unicorn import mips_const as r

from build_menu_fixes import build


def main():
    elf,_,_,report = build()
    m = unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN)
    m.mem_map(0x08800000,32<<20)
    ph = struct.unpack_from('<I',elf,28)[0]
    for i in range(2):
        _,off,addr,_,size,_,_,_ = struct.unpack_from('<8I',elf,ph+i*32)
        m.mem_write(addr,elf[off:off+size])
    obj,sp,stop = 0x09F00000,0x09F10000,0x08802000
    m.reg_write(r.UC_MIPS_REG_S0,obj)
    m.reg_write(r.UC_MIPS_REG_SP,sp)
    m.reg_write(r.UC_MIPS_REG_V0,0x12345678)
    saved = [0x11111111,0x22222222,0x33333333,0x44444444,stop]
    m.mem_write(sp,struct.pack('<5I',*saved)+bytes(12))
    m.emu_start(0x0891F56C,stop,count=30)
    assert struct.unpack('<I',m.mem_read(obj+0x30,4))[0] == 0x8003
    assert m.reg_read(r.UC_MIPS_REG_SP) == sp+0x20
    assert m.reg_read(r.UC_MIPS_REG_RA) == stop
    assert m.reg_read(r.UC_MIPS_REG_V0) == 0x12345678
    for reg,value in zip([r.UC_MIPS_REG_S0,r.UC_MIPS_REG_S1,r.UC_MIPS_REG_S2,r.UC_MIPS_REG_S3],saved):
        assert m.reg_read(reg) == value
    for table,dy in [(0x08A37F80,56),(0x08A37F00,0),(0,0)]:
        m.reg_write(r.UC_MIPS_REG_S0,table)
        m.reg_write(r.UC_MIPS_REG_A0,obj)
        m.reg_write(r.UC_MIPS_REG_A2,0)
        m.emu_start(0x08967564,0x0882387C,count=30)
        assert m.reg_read(r.UC_MIPS_REG_A0) == obj
        assert m.reg_read(r.UC_MIPS_REG_A1) == 16
        assert m.reg_read(r.UC_MIPS_REG_A2) == dy
        assert m.reg_read(r.UC_MIPS_REG_S0) == table
        assert m.reg_read(r.UC_MIPS_REG_RA) == 0x0896756C
    print('PASS: actual MIPS home draw key, restored stack/registers/return value; studio offset only for its own table; other centered menus unchanged.')


if __name__ == '__main__':main()
