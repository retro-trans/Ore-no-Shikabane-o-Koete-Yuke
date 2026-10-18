"""Compare the original and patched punctuation helper for every UTF-16 value."""
import struct, unicorn
from unicorn import mips_const as r
from catalog_text import ROOT
from build_exclamation_spacing import BASE, OFFSET_COMPARE

def machine(path):
    elf = path.read_bytes()
    m = unicorn.Uc(unicorn.UC_ARCH_MIPS, unicorn.UC_MODE_MIPS32 | unicorn.UC_MODE_LITTLE_ENDIAN)
    m.mem_map(0x089BB000, 0x1000)
    m.mem_write(0x089BB234, elf[0x089BB234-BASE:0x089BB270-BASE])
    return m

def result(m, c):
    m.reg_write(r.UC_MIPS_REG_A0, c); m.reg_write(r.UC_MIPS_REG_RA, 0x089BB300)
    m.reg_write(r.UC_MIPS_REG_SP, 0x12345678)
    for i in range(8): m.reg_write(r.UC_MIPS_REG_S0+i, 0x12340000+i)
    m.emu_start(0x089BB234, 0x089BB300, count=30)
    assert m.reg_read(r.UC_MIPS_REG_SP) == 0x12345678
    assert all(m.reg_read(r.UC_MIPS_REG_S0+i) == 0x12340000+i for i in range(8))
    return m.reg_read(r.UC_MIPS_REG_V0)

a = machine(ROOT/'work/output/english-native-0.2.23/EBOOT.disclaimer.elf')
b = machine(ROOT/'work/output/english-native-0.2.24/EBOOT.spacing.elf')
for c in range(65536):
    old, new = result(a, c), result(b, c)
    assert new == (0 if c == 33 else old), (c, old, new)
    if c == 33: assert old == 14
print('PASS: 65,536 actual MIPS before/after comparisons; only ASCII ! changes from offset 14 to 0. Question marks, fullwidth punctuation, null behavior, stack and saved registers preserved.')
