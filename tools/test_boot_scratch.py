"""Execute both accessors and reproduce the graphics transfer that corrupted the HUD."""
import argparse
import json
import struct

import unicorn
from unicorn import mips_const as r
from build_boot_scratch import build, ROOT, SCRATCH_BYTES

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--write', action='store_true')
args = parser.parse_args()
elf, ore, preview, report = build()
m = unicorn.Uc(unicorn.UC_ARCH_MIPS, unicorn.UC_MODE_MIPS32 | unicorn.UC_MODE_LITTLE_ENDIAN)
m.mem_map(0x08800000, 32 << 20)
po = struct.unpack_from('<I', elf, 28)[0]
for i in range(2):
    _, off, address, _, size, _, _, _ = struct.unpack_from('<8I', elf, po + 32 * i)
    m.mem_write(address, bytes(elf[off:off+size]))
arg, stop, stack = 0x09f00000, 0x09ff0000, 0x09fe0000
scratch = int(report['scratch']['address'], 16)
for pc in (0x0881ad34, 0x0881ad4c):
    m.mem_write(arg, struct.pack('<I', 0x11223344))
    m.reg_write(r.UC_MIPS_REG_A0, arg)
    m.reg_write(r.UC_MIPS_REG_RA, stop)
    m.reg_write(r.UC_MIPS_REG_SP, stack)
    for i in range(8):
        m.reg_write(r.UC_MIPS_REG_S0+i, 0x12340000+i)
    m.emu_start(pc, stop, count=30)
    assert m.reg_read(r.UC_MIPS_REG_V0) == scratch
    assert m.reg_read(r.UC_MIPS_REG_RA) == stop and m.reg_read(r.UC_MIPS_REG_SP) == stack
    assert all(m.reg_read(r.UC_MIPS_REG_S0+i) == 0x12340000+i for i in range(8))
    assert struct.unpack('<I', m.mem_read(arg, 4))[0] == (SCRATCH_BYTES if pc == 0x0881ad34 else 0x11223344)
assert bytes(m.mem_read(scratch, 8)) == b'EZBIND\0\0'
old_region = 0x09b5c000
ph = struct.unpack_from('<8I', elf, po + 32)
old_end = ph[2] + ph[5]
before = bytes(m.mem_read(old_region, old_end-old_region))
# The observed GPU copy writes 480 RGBA pixels on each 512-pixel row.
for row in range(272):
    m.mem_write(scratch + row*512*4, bytes([row & 255, 23, 45, 0])*480)
assert bytes(m.mem_read(old_region, old_end-old_region)) == before
assert bytes(m.mem_read(0x09b85a74, 24)).decode('utf-16-le').startswith('Genta\0Orin\0')
# A full-size write is also safe, including the unused stride padding.
m.mem_write(scratch, b'\x5a'*SCRATCH_BYTES)
assert bytes(m.mem_read(old_region, old_end-old_region)) == before
proof = dict(result='PASS', actual_mips_accessor_cases=2, caller_state_and_original_size='preserved',
    observed_gpu_transfer_rows=272, stride_bytes=2048, row_bytes=1920,
    full_buffer_write_bytes=SCRATCH_BYTES, earlier_names_icons_code_and_font_pages='byte-identical after both writes')
print(json.dumps(proof, indent=2))
if args.write:
    (ROOT / 'work/ui/boot-scratch-0.2.40/mips-tests.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
