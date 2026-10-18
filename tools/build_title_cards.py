"""Replace six title-card labels inside native game assets; no texture replacement.

Original flower art, palette, dimensions and geometry remain intact. Dry run first.
"""
import argparse
import hashlib
import json
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from catalog_text import ROOT, unpack_member
from inspect_native_textures import decode
from repack_text import rebuild_ez, rebuild_root, root_entries, align, u32

LABELS = {'bunsya.ppt':'SHARE DEITY', 'yousi.ppt':'ADOPTION', 'keizoku.ppt':'CONTINUE',
          'kaisi.ppt':'NEW GAME', 'jyosyou.ppt':'PROLOGUE', 'kekkon.ppt':'SOUL UNION'}


def card(blob, label):
    image, info = decode(blob)
    assert (info['width'], info['height'], info['format'], info['swizzled']) == (64, 96, 5, True)
    palette_offset = u32(blob, 24)
    assert struct.unpack_from('<H', blob, palette_offset + 4)[0] == 3
    palette = np.frombuffer(blob[palette_offset + 16:palette_offset + 16 + 1024], dtype=np.uint8).reshape(256, 4)
    pixels = np.asarray(image).copy()
    background = tuple(int(c) for c in pixels[80, 45])
    scale = 4
    label_image = Image.new('RGBA', (88 * scale, 20 * scale), background)
    font = ImageFont.truetype(str(ROOT / 'incoming/noto-sans/NotoSans-Regular.ttf'), 12 * scale)
    assert font.getlength(label) <= 86 * scale
    draw = ImageDraw.Draw(label_image)
    draw.text((44 * scale, 10 * scale), label, font=font, fill=(255,255,255,255), anchor='mm')
    label_image = label_image.rotate(270, expand=True).resize((20,88), Image.Resampling.LANCZOS)
    pixels[:94, 34:57] = background
    pixels[3:91, 35:55] = np.asarray(label_image)
    # Quantize only the label strip to the original palette. Preserve every
    # other source pixel index and every palette byte exactly.
    stored = blob[32:palette_offset]
    linear = np.frombuffer(bytes(stored[((y//8)*4+x//16)*128+(y%8)*16+x%16]
                                 for y in range(96) for x in range(64)),dtype=np.uint8).reshape(96,64).copy()
    desired = pixels[:94,34:57].reshape(-1,4).astype(np.int32)
    distance = ((desired[:,None,:]-palette.astype(np.int32)[None,:,:])**2).sum(axis=2)
    linear[:94,34:57] = distance.argmin(axis=1).reshape(94,23).astype(np.uint8)
    swizzled = bytearray(stored)
    for y in range(96):
        for x in range(34,57):
            swizzled[((y//8)*4+x//16)*128+(y%8)*16+x%16] = int(linear[y,x])
    result = blob[:32] + bytes(swizzled) + blob[palette_offset:]
    actual, _ = decode(result)
    assert np.array_equal(np.asarray(actual)[:,:34], np.asarray(image)[:,:34])
    assert result[palette_offset:] == blob[palette_offset:]
    return result, actual


def build(version='0.2.4'):
    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    base_path = ROOT / ('work/output/english-native-' + version + '/data.ore')
    data = base_path.read_bytes()
    original_base = 1998848
    index = next(i for i, _, _, off in root_entries(original)[0] if off == original_base)
    base = next(off for i, _, _, off in root_entries(data)[0] if i == index)
    inventory = json.loads((ROOT / 'work/source/archive_inventory.json').read_text())
    selected = [r for r in inventory if r['archive_offset'] == original_base and r['name'] in LABELS]
    assert len(selected) == 6
    updates, report, previews = {}, [], []
    import zlib
    for row in selected:
        _, size, pos, _ = struct.unpack_from('<4I', data, base + 16 + row['entry'] * 16)
        blob, compression = unpack_member(data[base + pos:base + pos + size])
        old, _ = unpack_member(original[row['member_offset']:row['member_offset']+row['size']])
        assert blob == old
        new, preview = card(blob, LABELS[row['name']])
        if compression == 'custom_deflate':
            z = zlib.compressobj(9, zlib.DEFLATED, -15)
            payload = b'\x1f\x8b\x09\0' + struct.pack('<I',len(new)) + z.compress(new) + z.flush()
        elif compression == 'raw':
            payload = new
        else:
            raise ValueError('Unexpected native asset compression')
        assert unpack_member(payload)[0] == new
        updates[row['entry']] = payload
        report.append(dict(file=row['name'], archive_offset=original_base, member_entry=row['entry'],
                           translation_en=LABELS[row['name']], status='draft',
                           source_sha256=hashlib.sha256(blob).hexdigest(),
                           output_sha256=hashlib.sha256(new).hexdigest(),
                           label_rectangle=[34,0,23,94], fit_status='unverified_in_game',
                           context='Title-menu flower card. Matches the corresponding title.mlb English label.'))
        previews.append((row['name'],preview))
    max_end = max(u32(data,base+16+i*16+8)+u32(data,base+16+i*16+4) for i in range(u32(data,base+8)))
    rebuilt = rebuild_ez(data[base:base+align(max_end,u32(data,base+12))],updates)
    output = rebuild_root(data,{base:rebuilt})
    return output, report, previews, hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--version', default='0.2.4')
    args = ap.parse_args()
    output, rows, previews, input_sha = build(args.version)
    report = dict(version=args.version, input_archive_sha256=input_sha,
                  output_archive_sha256=hashlib.sha256(output).hexdigest(), bytes=len(output),
                  native_graphic_labels=len(rows), texture_replacement=False,
                  checks='Unchanged flower art/palette/dimensions; decoded asset and compressed payload round trips pass.', rows=rows)
    print(json.dumps(report,indent=2))
    if args.write:
        dest = ROOT / ('work/output/english-native-' + args.version)
        (dest/'data.graphics.ore').write_bytes(output)
        (dest/'graphics.report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        trans = ROOT / 'work/translation/en/graphics'
        trans.mkdir(parents=True,exist_ok=True)
        (trans/'title_cards.en.json').write_text(json.dumps(dict(schema_version=1,version=args.version,language='en',status='draft',rows=rows),indent=2),encoding='utf-8')
        preview_dir = ROOT / ('work/ui/title-cards-' + args.version)
        preview_dir.mkdir(parents=True,exist_ok=True)
        sheet = Image.new('RGBA',(6*80,110),(45,45,45,255))
        for i,(name,img) in enumerate(previews):
            img.save(preview_dir/(name+'.png'))
            sheet.alpha_composite(img,(i*80+8,7))
        sheet.save(preview_dir/'preview.png')
    print('Native graphic labels written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()
