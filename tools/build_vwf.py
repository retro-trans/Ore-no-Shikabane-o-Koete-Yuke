"""Build a UCJS10117 native Latin VWF/4x-atlas executable. Dry run unless --write.

The original renderer already measures variable widths. This patch updates its
Latin metrics and selects an immutable atlas for entirely ASCII text objects.
Mixed/non-ASCII text objects retain the original cache and texture path.
"""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

import keystone
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.2.0'
BASE = 0x08803000
SEGMENT = 0x09B5C000
IMAGE = SEGMENT + 0x10
PALETTE = SEGMENT + 0x50
PIXELS = SEGMENT + 0x1000
CODE = SEGMENT + 0x100
UVS = SEGMENT + 0x200
HOOK = 0x089BA8B4
LATIN_WIDTHS = 0x08B2EA74
EXPECTED_SHA = 'fa0650a6caf567bd21b64d821ac22b036b6b5151302c40eb3f487b2ff4a113e3'


def font_assets(font_path):
    scale, width, height, row_height = 4, 512, 512, 80
    font = ImageFont.truetype(str(font_path), 14 * scale)
    alpha = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(alpha)
    metrics = {}
    x, y = 0, 0
    for code in range(32, 127):
        char = chr(code)
        bbox = font.getbbox(char, anchor='ls')
        left = max(0, -bbox[0])
        advance = max(4, math.ceil(max(font.getlength(char) + left, bbox[2] + left) / scale))
        sample_width = advance * scale
        if x + sample_width > width:
            x, y = 0, y + row_height
        if y + row_height > height:
            raise ValueError('Native 4x glyphs do not fit a hardware-sized atlas')
        draw.text((x + left, y + 16 * scale), char, font=font, fill=255, anchor='ls')
        metrics[str(code)] = dict(character=char, advance=advance, atlas_x=x, atlas_y=y,
                                  sample_width=sample_width, sample_height=row_height)
        x += sample_width
    values = list(alpha.getdata())
    packed = bytes((values[i] * 15 + 127) // 255 | (((values[i + 1] * 15 + 127) // 255) << 4)
                   for i in range(0, len(values), 2))
    # Diagnostic only: the embedded native palette uses white RGB.
    high = Image.new('RGBA', alpha.size, (30, 30, 30, 0))
    high.putalpha(alpha)
    return packed, high, metrics


def assemble_selector():
    source = f'''
    .set noreorder
    lui $t0, 0x09af
    lw $v0, 0x54e4($t0)
    lw $t1, 0xd4($a0)
    beqz $t1, fallback
    move $t2, $t1
scan:
    lhu $t3, 4($t2)
    beqz $t3, remap
    addiu $t3, $t3, -32
    sltiu $t4, $t3, 95
    beqz $t4, fallback
    nop
    b scan
    addiu $t2, $t2, 28
remap:
    move $t2, $t1
glyph:
    lhu $t3, 4($t2)
    beqz $t3, ready
    addiu $t3, $t3, -32
    sll $t3, $t3, 3
    li $t4, {UVS}
    addu $t4, $t4, $t3
    lw $t5, 0($t4)
    lw $t6, 4($t4)
    sw $t5, 0x10($t2)
    sw $t6, 0x14($t2)
    b glyph
    addiu $t2, $t2, 28
ready:
    li $v0, {IMAGE}
    li $t0, 1
    sb $t0, 0xc0($a0)
fallback:
    jr $ra
    nop
    '''
    assembler = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS32 | keystone.KS_MODE_LITTLE_ENDIAN)
    return bytes(assembler.asm(source, addr=CODE)[0])


def build():
    original = (ROOT / 'work/source/EBOOT.decrypted.elf').read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED_SHA:
        raise ValueError('Unsupported executable; expected the verified UCJS10117 ELF')
    if struct.unpack_from('<I', original, HOOK - BASE)[0] != (0x0C000000 | ((0x089B61F0 >> 2) & 0x03FFFFFF)):
        raise ValueError('Original font-texture call does not match')
    if struct.unpack_from('<I', original, HOOK + 4 - BASE)[0] != 0:
        raise ValueError('Original delay slot does not match')
    font_path = ROOT / 'incoming/noto-sans/NotoSans-Regular.ttf'
    packed, high, metrics = font_assets(font_path)
    native = bytearray(original)
    for code in range(32, 127):
        native[LATIN_WIDTHS - BASE + 1 + code] = metrics[str(code)]['advance']
    struct.pack_into('<II', native, HOOK - BASE,
                     0x0C000000 | ((CODE >> 2) & 0x03FFFFFF), 0x02202021)  # jal selector; move a0,s1
    code = assemble_selector()
    segment = bytearray(0x1000 + len(packed))
    # Native image descriptor: T4, linear (not swizzled), 512x512, one level.
    # The 4x glyph rectangles are sampled into unchanged 1x destination quads.
    struct.pack_into('<8H', segment, 0x10 + 4, 512, 512, 4, 0, 512, 512, 512, 512)
    segment[0x10 + 0x1c:0x10 + 0x1e] = bytes([9, 9])
    struct.pack_into('<III', segment, 0x10 + 0x20, PIXELS, PALETTE, PIXELS)
    # Palette descriptor, 16 RGBA4444 entries; white RGB with 0..15 alpha.
    struct.pack_into('<IHHII', segment, 0x50, 0, 2, 16, PALETTE + 16, 0)
    struct.pack_into('<16H', segment, 0x60, *(0xFFF | (i << 12) for i in range(16)))
    segment[0x100:0x100 + len(code)] = code
    if len(code) > 0x100:
        raise ValueError('Selector overlaps the UV map')
    for codepoint in range(32, 127):
        m = metrics[str(codepoint)]
        struct.pack_into('<4H', segment, 0x200 + (codepoint - 32) * 8,
                         m['atlas_x'] * 64, m['atlas_y'] * 64,
                         (m['atlas_x'] + m['sample_width']) * 64,
                         (m['atlas_y'] + m['sample_height']) * 64)
    segment[0x1000:] = packed
    phoff = struct.unpack_from('<I', original, 28)[0]
    phentsize, phnum = struct.unpack_from('<HH', original, 42)
    if phentsize != 32 or phnum != 1 or phoff + 64 > 0x1000:
        raise ValueError('Unexpected program-header layout')
    old_vaddr, old_memsz = struct.unpack_from('<I', original, phoff + 8)[0], struct.unpack_from('<I', original, phoff + 20)[0]
    if old_vaddr + old_memsz > SEGMENT:
        raise ValueError('Added segment overlaps the original BSS')
    offset = (len(native) + 0xFFF) & ~0xFFF
    native.extend(bytes(offset - len(native)))
    native.extend(segment)
    struct.pack_into('<H', native, 44, 2)
    struct.pack_into('<8I', native, phoff + 32, 1, offset, SEGMENT, SEGMENT, len(segment), len(segment), 7, 0x1000)
    report = dict(version=VERSION, source_elf_sha256=EXPECTED_SHA,
                  patched_elf_sha256=hashlib.sha256(native).hexdigest(), bytes=len(native),
                  hook=hex(HOOK), selector=hex(CODE), selector_bytes=len(code),
                  new_segment_address=hex(SEGMENT), added_ram_bytes=len(segment),
                  immutable_pixels_address=hex(PIXELS), bitmap_bytes=len(packed),
                  native_atlas=list(high.size), glyph_raster_scale=4, texture_replacement=False,
                  glyphs=95, font='Noto Sans Regular, 14 logical pixels',
                  fallback='Mixed/non-ASCII text uses the original native font cache.',
                  status='Experimental; requires runtime geometry and visual verification.',
                  widths_sample={c: metrics[str(ord(c))]['advance'] for c in 'Wi.m0 '})
    return bytes(native), high, metrics, report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    native, high, metrics, report = build()
    print(json.dumps(report, indent=2))
    if args.write:
        dest = ROOT / 'work/output' / ('vwf-' + VERSION)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / 'EBOOT.elf').write_bytes(native)
        high.save(dest / 'native-latin4x-preview.png')
        (dest / 'OFL-NotoSans.txt').write_bytes((ROOT / 'incoming/noto-sans/LICENSE.txt').read_bytes())
        (dest / 'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        (ROOT / 'work/ui/vwf_metrics.json').write_text(json.dumps(dict(version=VERSION, glyphs=metrics), indent=2), encoding='utf-8')
    print('VWF test assets written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()
