"""Execute the final MIPS selector and compare ASCII rasters on its button pages."""
import json
import struct
import argparse

from PIL import Image
import unicorn
from unicorn import mips_const as r

from build_prompt_font import build
from build_vwf import IMAGE, PIXELS, UVS
from catalog_text import ROOT

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--write', action='store_true', help='Save the test evidence after a dry run')
args = parser.parse_args()

elf, ore, previews, title, report = build()
m = unicorn.Uc(unicorn.UC_ARCH_MIPS, unicorn.UC_MODE_MIPS32 | unicorn.UC_MODE_LITTLE_ENDIAN)
m.mem_map(0x08800000, 32 << 20)
po = struct.unpack_from('<I', elf, 28)[0]
for i in range(2):
    _, off, address, _, size, _, _, _ = struct.unpack_from('<8I', elf, po + 32 * i)
    m.mem_write(address, bytes(elf[off:off+size]))
obj, descriptors, original, stop = 0x09f00000, 0x09f01000, 0x09e00000, 0x09f10000
m.mem_write(0x09af54e4, struct.pack('<I', original))
circle = report['pages']['0x25cb']
triangle = report['pages']['0x25b3']
ascii_text = ''.join(chr(c) for c in range(32, 127))
cases = [(ascii_text, IMAGE), (' 123\xa0%', IMAGE), ('and press the \u25cb button.', circle['image']),
         ('\u25cb\u25cb', circle['image']), ('Press \u25b3 to check status.', triangle['image']),
         (ascii_text + '\u25cb\xa0', circle['image']), (ascii_text + '\u25b3', triangle['image']),
         ('A\u3042B', original), ('A\u25cb\u3042B', original), ('A\u2606B', original),
         ('A\u25cb\u25b3B', original), ('', IMAGE)]
checked = 0
for text, expected_image in cases:
    m.mem_write(obj, bytes(0x120))
    m.mem_write(obj + 0xd4, struct.pack('<I', descriptors))
    records = bytearray(28 * (len(text) + 1))
    for i, char in enumerate(text):
        struct.pack_into('<HH4H4H', records, i * 28 + 4, ord(char), 22 if ord(char) > 255 else 8,
                         i * 48, 0, i * 48 + 48, 80, 11, 22, 33, 44)
    m.mem_write(descriptors, bytes(records))
    m.reg_write(r.UC_MIPS_REG_A0, obj)
    m.reg_write(r.UC_MIPS_REG_RA, stop)
    m.reg_write(r.UC_MIPS_REG_S1, 0x12345678)
    m.emu_start(int(report['selector'], 16), stop, count=50000)
    assert m.reg_read(r.UC_MIPS_REG_V0) == expected_image, (text, hex(m.reg_read(r.UC_MIPS_REG_V0)), hex(expected_image))
    assert m.reg_read(r.UC_MIPS_REG_S1) == 0x12345678
    actual = bytes(m.mem_read(descriptors, len(records)))
    if expected_image == original:
        assert actual == records
    else:
        for i, char in enumerate(text):
            cp = 32 if ord(char) == 160 else ord(char)
            if expected_image == IMAGE:
                uv = bytes(m.mem_read(UVS + (cp - 32) * 8, 8))
            else:
                page = circle if expected_image == circle['image'] else triangle
                uv = struct.pack('<4H', *page['glyphs'][str(cp)]['uv'])
            assert actual[i*28+16:i*28+24] == uv
            assert actual[i*28:i*28+16] == records[i*28:i*28+16]
            checked += 1
        assert m.mem_read(obj + 0xc0, 1) == b'\x01'

# Every ASCII glyph on both new pages must contain the original raster pixels.
packed = bytes(m.mem_read(PIXELS, 131072))
old = Image.new('L', (512, 512))
old.putdata([n * 17 for b in packed for n in (b & 15, b >> 4)])
for page in (circle, triangle):
    for cp in range(32, 127):
        old_uv = struct.unpack('<4H', bytes(m.mem_read(UVS + (cp-32)*8, 8)))
        new_uv = page['glyphs'][str(cp)]['uv']
        before = old.crop(tuple(n // 64 for n in old_uv))
        after = previews[page['name'].lower()].crop(tuple(n // 64 for n in new_uv))
        assert before.tobytes() == after.tobytes()
result = dict(result='PASS', mips_cases=len(cases), glyph_geometry_checks=checked,
    unchanged_ascii_rasters=190, fallback_preserves_entire_objects=True, caller_state_preserved=True)
print(json.dumps(result, indent=2))
if args.write:
    (ROOT / 'work/ui/prompt-font-0.2.39/mips-tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
