"""Keep English button prompts on the native 4x font. Dry run before --write."""
import argparse
import hashlib
import json
import struct

import keystone
from PIL import Image, ImageDraw

from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from build_setup_ui import padded_selector
from build_vwf import CODE, HOOK, PIXELS, UVS
from repack_text import align, rebuild_ez, rebuild_root, root_entries

V = '0.2.39'
BASE = 0x08803000
SYMBOLS = {0x25cb: 'Circle', 0x25b3: 'Triangle'}
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.38'
    source = (src / 'EBOOT.home.elf').read_bytes()
    data = (src / 'data.home.ore').read_bytes()
    assert sha(source) == '007bfe919f1b916901a5de6ac99e4e9e86500bdac4dff6da48ab28035cffc9a5'
    assert sha(data) == 'f32ed958f35d9d317813e4871def7260cd3cfd1e71a970e59a610471f40a904f'
    elf = bytearray(source)
    po = struct.unpack_from('<I', elf, 28)[0]
    ph = list(struct.unpack_from('<8I', elf, po + 32))
    assert ph[1] + ph[4] == len(elf)

    def offset(address):
        return ph[1] + address - ph[2]

    def reserve(blob, alignment=16):
        elf.extend(bytes(align(len(elf), alignment) - len(elf)))
        address = ph[2] + len(elf) - ph[1]
        elf.extend(blob)
        return address

    old_selector = padded_selector()
    assert elf[offset(CODE):offset(CODE) + len(old_selector)] == old_selector
    assert struct.unpack_from('<I', elf, HOOK - BASE)[0] == 0x0c000000 | (CODE >> 2)
    packed = elf[offset(PIXELS):offset(PIXELS) + 131072]
    alpha = Image.new('L', (512, 512))
    alpha.putdata([value * 17 for b in packed for value in (b & 15, b >> 4)])
    metrics = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text())['glyphs']
    pages, previews = {}, {}
    for cp, name in SYMBOLS.items():
        # Repack unchanged ASCII rasters densely enough for one full-size
        # 22-pixel button glyph. Two hardware-sized pages handle both prompts.
        cells = [(int(c), m['sample_width']) for c, m in metrics.items()] + [(cp, 88)]
        used, slots = [0] * 6, {}
        for codepoint, width in sorted(cells, key=lambda x: (-x[1], x[0])):
            row = next(i for i in range(6) if used[i] + width <= 512)
            slots[codepoint] = (used[row], row * 80, width)
            used[row] += width
        image = Image.new('L', (512, 512))
        uv = bytearray(96 * 8)
        glyphs = {}
        for index, codepoint in enumerate(list(range(32, 127)) + [cp]):
            x, y, width = slots[codepoint]
            if codepoint < 127:
                m = metrics[str(codepoint)]
                crop = alpha.crop((m['atlas_x'], m['atlas_y'], m['atlas_x'] + width, m['atlas_y'] + 80))
            else:
                crop = Image.new('L', (88, 80))
                draw = ImageDraw.Draw(crop)
                if cp == 0x25cb:
                    draw.ellipse((16, 12, 71, 67), outline=255, width=4)
                else:
                    draw.line([(44, 12), (73, 66), (15, 66), (44, 12)], fill=255, width=4, joint='curve')
            image.paste(crop, (x, y))
            bounds = (x * 64, y * 64, (x + width) * 64, (y + 80) * 64)
            struct.pack_into('<4H', uv, index * 8, *bounds)
            glyphs[str(codepoint)] = dict(uv=list(bounds), sample_width=width, sample_height=80)
        values = list(image.getdata())
        pixels = bytes(values[i] // 17 | (values[i + 1] // 17 << 4) for i in range(0, len(values), 2))
        header = bytearray(source[offset(0x09b5c010):offset(0x09b5c010) + 0x30])
        address = reserve(bytes(0x40 + len(uv) + len(pixels)))
        uv_address, pixel_address = address + 0x40, address + 0x40 + len(uv)
        struct.pack_into('<I', header, 0x20, pixel_address)
        struct.pack_into('<I', header, 0x28, pixel_address)
        pos = offset(address)
        elf[pos:pos + len(header)] = header
        elf[offset(uv_address):offset(uv_address) + len(uv)] = uv
        elf[offset(pixel_address):offset(pixel_address) + len(pixels)] = pixels
        pages[cp] = dict(name=name, image=address, uv_address=uv_address, pixels=pixel_address,
                        glyphs=glyphs, dimensions=[512, 512], ascii_rasters='copied without resampling')
        previews[name.lower()] = image

    circle, triangle = pages[0x25cb], pages[0x25b3]
    assembly = f'''.set noreorder
    lui $t0,0x09af
    lw $v0,0x54e4($t0)
    lw $t1,0xd4($a0)
    beqz $t1,fallback
    move $t2,$t1
    move $t7,$zero
scan:
    lhu $t3,4($t2)
    beqz $t3,scanned
    li $t4,160
    beq $t3,$t4,next
    addiu $t4,$t3,-32
    sltiu $t4,$t4,95
    bnez $t4,next
    li $t4,0x25cb
    beq $t3,$t4,circle
    li $t4,0x25b3
    bne $t3,$t4,fallback
    nop
    li $t4,{triangle['image']}
    b choose
    nop
circle:
    li $t4,{circle['image']}
choose:
    beqz $t7,selected
    nop
    bne $t7,$t4,fallback
    nop
selected:
    move $t7,$t4
next:
    b scan
    addiu $t2,$t2,28
scanned:
    bnez $t7,remap
    nop
    j {CODE}
    nop
remap:
    move $t2,$t1
glyph:
    lhu $t3,4($t2)
    beqz $t3,ready
    li $t4,160
    bne $t3,$t4,index
    nop
    li $t3,32
index:
    addiu $t3,$t3,-32
    sltiu $t4,$t3,95
    bnez $t4,mapped
    nop
    li $t3,95
mapped:
    sll $t3,$t3,3
    addu $t4,$t7,$t3
    lw $t5,0x40($t4)
    lw $t6,0x44($t4)
    sw $t5,0x10($t2)
    sw $t6,0x14($t2)
    b glyph
    addiu $t2,$t2,28
ready:
    move $v0,$t7
    li $t0,1
    sb $t0,0xc0($a0)
fallback:
    jr $ra
    nop
'''
    elf.extend(bytes(align(len(elf), 16) - len(elf)))
    selector = ph[2] + len(elf) - ph[1]
    ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS32 | keystone.KS_MODE_LITTLE_ENDIAN)
    code = bytes(ks.asm(assembly, addr=selector)[0])
    elf.extend(code)
    struct.pack_into('<I', elf, HOOK - BASE, 0x0c000000 | (selector >> 2))
    ph[4] = ph[5] = len(elf) - ph[1]
    struct.pack_into('<8I', elf, po + 32, *ph)
    assert ph[2] + ph[5] < 0x0a000000
    allowed = set(range(HOOK - BASE, HOOK - BASE + 4)) | set(range(po + 48, po + 56))
    assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(source, elf)))

    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe, _ = root_entries(original)
    be, bend = root_entries(data)
    ti = next(i for i, _, _, o in oe if o == 0x1e8000)
    tb = next(o for i, _, _, o in be if i == ti)
    ta, te = container(data, tb)
    ot, ote = container(original, 0x1e8000)
    title, preview, fr = footer(member(ot, ote, 25), V)
    ore = rebuild_root(data, {tb: rebuild_ez(ta, {25: pack(title)})}, mutable=True)
    ae, aend = root_entries(ore)
    for n, (a, b) in enumerate(zip(be, ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend) - (a[2] & 2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend) - (b[2] & 2047)
        aa, bb = data[a[3]:sa], ore[b[3]:sb]
        if a[3] != tb:
            assert aa == bb
        else:
            _, ar = container(aa, 0)
            _, br = container(bb, 0)
            for j, ((_, z, p, _), (_, zz, pp, _)) in enumerate(zip(ar, br)):
                if j != 25:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V, source_version='0.2.38', elf_sha256=sha(elf), archive_sha256=sha(ore),
        elf_bytes=len(elf), archive_bytes=len(ore), hook=hex(HOOK), selector=hex(selector),
        selector_bytes=len(code), pages={hex(cp): page for cp, page in pages.items()},
        extra_ram_bytes=len(elf) - len(source), existing_ascii_atlas_and_metrics='byte-identical',
        script_wording_and_controls='byte-identical', archive_changes='title version only',
        fallback='Japanese, unsupported symbols and lines combining Circle with Triangle retain the original font.',
        texture_replacement=False, footer=fr, runtime_verification='pending')
    return elf, ore, previews, preview, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    elf, ore, previews, title, report = build()
    print(json.dumps({k: v for k, v in report.items() if k not in ('pages', 'footer')}, indent=2))
    if args.write:
        out = ROOT / ('work/output/english-native-' + V)
        out.mkdir(exist_ok=True)
        assert not (out / 'EBOOT.prompt.elf').exists()
        (out / 'EBOOT.prompt.elf').write_bytes(elf)
        (out / 'data.prompt.ore').write_bytes(ore)
        (out / 'prompt.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        ui = ROOT / ('work/ui/prompt-font-' + V)
        ui.mkdir(exist_ok=True)
        for name, image in previews.items():
            image.save(ui / (name + '-atlas.png'))
        title.save(ui / 'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')
