"""Decode selected native PPT textures for an ignored local graphics audit.

Does not replace textures or modify the game. Dry run unless --write.
"""
import argparse
import json
import struct
from pathlib import Path

from PIL import Image, ImageDraw

from catalog_text import unpack_member

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = ['bunsya.ppt', 'yousi.ppt', 'keizoku.ppt', 'kaisi.ppt', 'jyosyou.ppt',
            'kekkon.ppt', 'sub_ituka.ppt', 'sub_kitsuto.ppt', 'copyright_sce.ppt',
            'pm_subtitle_00.ppt', 'pm_subtitle_01.ppt']


def decode(blob):
    if blob[:4] != b'ppt\0':
        raise ValueError('Not a native PPT image')
    texture_width, texture_height, fmt, swizzled = struct.unpack_from('<4H', blob, 4)
    width, height = struct.unpack_from('<2H', blob, 12)
    # Storage is padded to swizzle blocks, even for a 2x2 GPU texture.
    assert 0 < texture_width <= 512 and 0 < texture_height <= 512
    assert 0 < width <= ((texture_width + 15)//16)*16 <= 512
    assert 0 < height <= ((texture_height + 7)//8)*8 <= 512
    bits = {0:16, 1:16, 2:16, 3:32, 4:4, 5:8}.get(fmt)
    if bits is None:
        raise ValueError('Unsupported pixel format: ' + str(fmt))
    stride = (width * bits + 7) // 8
    pixels = blob[32:32 + stride * height]
    assert len(pixels) == stride * height
    if swizzled:
        assert stride % 16 == 0 and height % 8 == 0
        pixels = bytes(pixels[((y // 8) * (stride // 16) + x // 16) * 128 + (y % 8) * 16 + x % 16]
                       for y in range(height) for x in range(stride))

    def colors(raw, kind):
        if kind == 3:
            return list(zip(*[iter(raw)] * 4))
        values = struct.unpack('<' + str(len(raw) // 2) + 'H', raw)
        if kind == 2:
            return [(v & 15, v >> 4 & 15, v >> 8 & 15, v >> 12 & 15) for v in values]
        if kind == 0:
            return [(round((v & 31) * 255 / 31), round((v >> 5 & 63) * 255 / 63), round((v >> 11 & 31) * 255 / 31), 255) for v in values]
        if kind == 1:
            return [(round((v & 31) * 255 / 31), round((v >> 5 & 31) * 255 / 31), round((v >> 10 & 31) * 255 / 31), 255 if v & 32768 else 0) for v in values]
        raise ValueError('Unsupported palette format')

    if fmt in (4, 5):
        palette_offset = struct.unpack_from('<I', blob, 24)[0]
        assert blob[palette_offset:palette_offset + 4] == b'ppc\0'
        kind = struct.unpack_from('<H', blob, palette_offset + 4)[0]
        count = 16 if fmt == 4 else 256
        raw = blob[palette_offset + 16:palette_offset + 16 + count * (4 if kind == 3 else 2)]
        palette = colors(raw, kind)
        if kind == 2:
            palette = [tuple(c * 17 for c in color) for color in palette]
        indices = pixels if fmt == 5 else bytes(c for byte in pixels for c in (byte & 15, byte >> 4))
        rgba = [palette[i] for i in indices[:width * height]]
    else:
        rgba = colors(pixels, fmt)
        if fmt == 2:
            rgba = [tuple(c * 17 for c in color) for color in rgba]
    image = Image.new('RGBA', (width, height))
    image.putdata(rgba)
    logical_width, logical_height = struct.unpack_from('<2H', blob, 16)
    return image, dict(width=width, height=height, logical_width=logical_width,
                       logical_height=logical_height, texture_width=texture_width,
                       texture_height=texture_height, format=fmt, swizzled=bool(swizzled))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--names', nargs='+', default=DEFAULTS)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    inventory = json.loads((ROOT / 'work/source/archive_inventory.json').read_text())
    selected = [r for r in inventory if r['name'] in args.names]
    images, report = [], []
    with (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').open('rb') as stream:
        for row in selected:
            stream.seek(row['member_offset'])
            decoded, _ = unpack_member(stream.read(row['size']))
            img, info = decode(decoded)
            filename = f'{row["archive_offset"]:08x}-{row["entry"]:04d}-{row["name"]}.png'
            report.append(dict(name=row['name'], archive_offset=row['archive_offset'], entry=row['entry'], preview=filename, **info))
            images.append((filename, img))
    print(json.dumps(report, indent=2))
    if args.write:
        dest = ROOT / 'work/source/texture-audit'
        dest.mkdir(parents=True, exist_ok=True)
        sheet = Image.new('RGB', (900, ((len(images) + 2) // 3) * 210), (45, 45, 45))
        draw = ImageDraw.Draw(sheet)
        for i, (filename, img) in enumerate(images):
            img.save(dest / filename)
            thumb = img.copy()
            thumb.thumbnail((290, 180))
            x, y = i % 3 * 300, i // 3 * 210
            sheet.paste(thumb, (x, y + 22), thumb)
            draw.text((x + 2, y + 2), filename[-36:], fill='white')
        sheet.save(dest / 'selected-contact-sheet.png')
        (dest / 'inventory.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Audit previews written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()
