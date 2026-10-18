"""Execute the actual MIPS OSK initializer and compare all field bytes."""
import struct
import unicorn
from unicorn import mips_const as r
from build_english_keyboard import build, BASE, ROOT


def run(elf):
    m=unicorn.Uc(unicorn.UC_ARCH_MIPS,unicorn.UC_MODE_MIPS32|unicorn.UC_MODE_LITTLE_ENDIAN)
    m.mem_map(0x08800000,32<<20)
    m.mem_write(0x08804000,elf[0x1000:0x1000+0x341ef4])
    obj,field,stack,stop=0x09f00000,0x09f01000,0x09f10000,0x09f20000
    m.mem_write(field,bytes([0xA5])*52)
    m.reg_write(r.UC_MIPS_REG_A0,obj);m.reg_write(r.UC_MIPS_REG_A1,field)
    m.reg_write(r.UC_MIPS_REG_SP,stack);m.reg_write(r.UC_MIPS_REG_RA,stop)
    m.reg_write(r.UC_MIPS_REG_S0,0x12345678);m.reg_write(r.UC_MIPS_REG_S1,0x23456789)
    # Stub the original memset, preserving its return convention.
    def hook(mu,pc,size,unused):
        if pc==0x08a0c180:
            dst=mu.reg_read(r.UC_MIPS_REG_A0);count=mu.reg_read(r.UC_MIPS_REG_A2)
            mu.mem_write(dst,bytes([mu.reg_read(r.UC_MIPS_REG_A1)&255])*count)
            mu.reg_write(r.UC_MIPS_REG_V0,dst);mu.reg_write(r.UC_MIPS_REG_PC,mu.reg_read(r.UC_MIPS_REG_RA))
    m.hook_add(unicorn.UC_HOOK_CODE,hook)
    m.emu_start(0x0881b8c8,stop,count=100)
    assert m.reg_read(r.UC_MIPS_REG_SP)==stack
    assert m.reg_read(r.UC_MIPS_REG_S0)==0x12345678 and m.reg_read(r.UC_MIPS_REG_S1)==0x23456789
    return bytes(m.mem_read(field,52))


def main():
    native,_,_,_=build()
    before=run((ROOT/'work/output/english-native-0.2.11/EBOOT.destination.elf').read_bytes())
    after=run(native)
    fields=list(struct.unpack('<13I',after))
    assert fields[2]==2 and fields[4]==0xD00F
    assert fields[4]&0xD000==0xD000 and fields[4]&15==15
    assert all(a==b or i in {8,9,10,11,16,17,18,19} for i,(a,b) in enumerate(zip(before,after)))
    assert fields[9]==128 and fields[1]==0 and fields[12]==0
    print('PASS: actual MIPS enables all four Latin flags, defaults English, retains Japanese; all other field bytes, buffer capacity, stack and saved registers unchanged.')


if __name__=='__main__':main()
