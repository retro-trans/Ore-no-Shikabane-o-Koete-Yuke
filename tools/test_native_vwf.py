"""Execute the actual MIPS selector and check native 4x geometry and fallback."""
import json
import struct
from pathlib import Path

import unicorn
from unicorn import mips_const as reg
from elftools.elf.elffile import ELFFile

from build_vwf import BASE, CODE, HOOK, IMAGE, LATIN_WIDTHS, ROOT, SEGMENT, UVS


def main():
    path = ROOT / 'work/output/vwf-0.2.0/EBOOT.elf'
    data = path.read_bytes()
    metrics = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text(encoding='utf-8'))['glyphs']
    machine = unicorn.Uc(unicorn.UC_ARCH_MIPS, unicorn.UC_MODE_MIPS32 | unicorn.UC_MODE_LITTLE_ENDIAN)
    machine.mem_map(0x08800000, 32 << 20)
    with path.open('rb') as f:
        elf = ELFFile(f)
        for segment in elf.iter_segments():
            if segment['p_type'] == 'PT_LOAD':
                machine.mem_write(segment['p_vaddr'], segment.data())
    obj, descriptors, original_image, stop = 0x09F00000, 0x09F01000, 0x09E00000, 0x09F10000
    machine.mem_write(0x09AF54E4, struct.pack('<I', original_image))
    assert struct.unpack('<I', machine.mem_read(HOOK, 4))[0] == 0x0C000000 | ((CODE >> 2) & 0x03FFFFFF)
    tested = 0
    for text, native in [('Wiii m0.', True), (''.join(chr(c) for c in range(32, 127)), True), ('A\u3042B', False)]:
        machine.mem_write(obj, bytes(0x120))
        machine.mem_write(obj + 0xD4, struct.pack('<I', descriptors))
        records = bytearray(28 * (len(text) + 1))
        for i, ch in enumerate(text):
            struct.pack_into('<HH4H4H', records, i * 28 + 4, ord(ch), 12, i * 48, 0, i * 48 + 48, 80,
                             11, 22, 33, 44)
        machine.mem_write(descriptors, bytes(records))
        machine.reg_write(reg.UC_MIPS_REG_A0, obj)
        machine.reg_write(reg.UC_MIPS_REG_RA, stop)
        machine.reg_write(reg.UC_MIPS_REG_S1, 0x12345678)
        machine.emu_start(CODE, stop, count=50000)
        result = machine.reg_read(reg.UC_MIPS_REG_V0)
        assert result == (IMAGE if native else original_image)
        assert machine.reg_read(reg.UC_MIPS_REG_S1) == 0x12345678
        actual = bytes(machine.mem_read(descriptors, len(records)))
        if not native:
            assert actual == records
        else:
            for i, ch in enumerate(text):
                m = metrics[str(ord(ch))]
                uv = struct.unpack_from('<4H', actual, i * 28 + 0x10)
                assert uv == (m['atlas_x'] * 64, m['atlas_y'] * 64,
                              (m['atlas_x'] + m['sample_width']) * 64,
                              (m['atlas_y'] + m['sample_height']) * 64)
                assert uv[2] - uv[0] == m['advance'] * 4 * 64
                assert uv[3] - uv[1] == 20 * 4 * 64
                assert actual[i * 28 + 8:i * 28 + 16] == records[i * 28 + 8:i * 28 + 16]
                tested += 1
    for c in range(32, 127):
        width = machine.mem_read(LATIN_WIDTHS + 1 + c, 1)[0]
        assert width == metrics[str(c)]['advance']
    assert metrics['87']['advance'] > metrics['105']['advance']
    print(json.dumps(dict(status='PASS', mips_execution_cases=3, glyph_geometry_checks=tested,
                          width_table_checks=95, non_ascii_fallback_preserves_descriptors=True,
                          source_to_destination_pixel_ratio=4, native_texture=[512, 512],
                          texture_replacement=False,
                          limitation='This checks MIPS behavior and geometry; game boot and visual checks are separate.'), indent=2))


if __name__ == '__main__':
    main()
